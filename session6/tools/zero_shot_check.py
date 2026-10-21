"""6회차 검증 예시 — 학습 없이 Cellpose 를 공개 H&E 이미지에 돌리고 정답과 비교한다.

이 노트에서 배우는 것: 빌려 온 모델도 정답 몇 개로 '재 보면' 얼마나 맞는지 숫자로 말할 수 있다.
입력: NuInsSeg (Mahbod et al., Sci Data 11, 295, 2024; CC BY 4.0; zenodo.org/records/10518968) 중
      사람 흑색종·편도·비장의 H&E 이미지와 핵 정답 마스크 (zip 전체 1.6 GB 중 필요한 파일만 부분 다운로드)
출력: outputs/zero_shot_metrics.csv (이미지별), outputs/zero_shot_summary.json (장기별), outputs/zero_shot_example.jpg

사용법 (session6 폴더에서, conda env ai_cop_session6):
    python tools/zero_shot_check.py --fetch
    python tools/zero_shot_check.py --run
채점: 정답 핵과 예측 핵을 IoU > 0.5 로 1:1 짝짓는다 → 정밀도·재현율·F1, 짝지은 핵들의 평균 Dice.
      데이터셋의 '애매한 영역(vague areas)' 안에 절반 이상 걸친 핵은 양쪽 모두 채점에서 뺀다.
      정답 라벨 정리(기본): 같은 번호가 여러 조각으로 흩어진 경우 가장 큰 조각만, 30 px 미만 조각은 제외 (--raw-gt 로 끔).
"""
import argparse
import io
import json
import sys
import time
import zipfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]          # session6/
DATA = ROOT / "data" / "nuinsseg"
OUT = ROOT / "outputs"
URL = "https://zenodo.org/api/records/10518968/files/NuInsSeg.zip/content"
ORGANS = ["human melanoma", "human tonsile", "human spleen"]
IOU_THR = 0.5
SEED = 0
RAW_GT = False      # True 면 정답 라벨을 정리하지 않고 그대로 채점 (--raw-gt)


def fetch():
    sys.path.insert(0, str(Path(__file__).parent))
    from remote_zip import HttpRangeFile
    z = zipfile.ZipFile(HttpRangeFile(URL))
    want = []
    for info in z.infolist():
        parts = info.filename.split("/")
        if info.is_dir() or parts[0] not in ORGANS:
            continue
        if len(parts) == 3 and parts[1] in ("tissue images", "label masks"):
            want.append(info)
        elif parts[1] == "vague areas" and info.filename.endswith(".roi"):   # ImageJ ROI 다각형
            want.append(info)
    t0 = time.time()
    for i, info in enumerate(want, 1):
        dst = DATA / info.filename
        if dst.exists() and dst.stat().st_size == info.file_size:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(z.read(info))
        if i % 20 == 0:
            print(f"  {i}/{len(want)} 파일")
    print(f"완료: {len(want)} 파일 → {DATA}  ({time.time() - t0:.0f} s)")


def relabel(m):
    from skimage.segmentation import relabel_sequential
    return relabel_sequential(m.astype(np.int64))[0]


def clean_gt(lab, min_area=30):
    """정답 라벨 정리: 같은 번호가 여러 조각이면 가장 큰 조각만 남기고, min_area 미만 조각은 뺀다.
    반환: (정리된 라벨, 흩어진 조각이 있던 물체 수, 너무 작아 뺀 물체 수)"""
    from skimage.measure import label as cc_label
    cc = cc_label(lab, connectivity=2, background=0)          # 같은 값끼리 이어진 덩어리마다 새 번호 (대각선 포함)
    n = cc.max() + 1
    cc_area = np.bincount(cc.ravel(), minlength=n)
    owner = np.zeros(n, np.int64)
    owner[cc.ravel()] = lab.ravel()
    best = {}
    for c in range(1, n):
        o = owner[c]
        if o and (o not in best or cc_area[c] > cc_area[best[o]]):
            best[o] = c
    keep = np.zeros(n, bool)
    keep[list(best.values())] = True
    n_frag = int(sum(1 for o in set(owner[1:]) if o and (owner[1:] == o).sum() > 1))
    out = np.where(keep[cc], lab, 0)
    out = relabel(out)
    area = np.bincount(out.ravel())
    small = np.nonzero(area < min_area)[0]
    small = small[small > 0]
    out[np.isin(out, small)] = 0
    return relabel(out), n_frag, int(len(small))


def drop_in_vague(lab, vague):
    """애매한 영역에 절반 이상 걸친 물체를 0 으로 지운다."""
    if vague is None:
        return lab
    n = lab.max() + 1
    area = np.bincount(lab.ravel(), minlength=n)
    inside = np.bincount(lab.ravel(), weights=vague.ravel().astype(float), minlength=n)
    bad = np.nonzero((area > 0) & (inside / np.maximum(area, 1) > 0.5))[0]
    bad = bad[bad > 0]
    out = lab.copy()
    out[np.isin(out, bad)] = 0
    return relabel(out)


def match(gt, pr, thr=IOU_THR):
    ng, npr = gt.max() + 1, pr.max() + 1
    ov = np.bincount((gt.ravel() * npr + pr.ravel()), minlength=ng * npr).reshape(ng, npr)
    ag, ap = ov.sum(1), ov.sum(0)
    inter = ov[1:, 1:].astype(float)
    union = ag[1:, None] + ap[None, 1:] - inter
    iou = np.divide(inter, union, out=np.zeros_like(inter), where=union > 0)
    gi, pi = np.nonzero(iou > thr)              # IoU > 0.5 이면 짝은 유일하다
    dice = 2 * inter[gi, pi] / (ag[1:][gi] + ap[1:][pi])
    return gi + 1, pi + 1, dice


def scores(tp, n_gt, n_pr):
    p = tp / n_pr if n_pr else 0.0
    r = tp / n_gt if n_gt else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def load_vague(org_dir, stem, shape):
    """'vague areas/Imagj_zips/<stem>/*.roi' (ImageJ ROI) 를 채운 마스크로 바꾼다. 없으면 None."""
    rois = sorted((org_dir / "vague areas" / "Imagj_zips" / stem).glob("*.roi"))
    if not rois:
        return None
    from roifile import ImagejRoi
    from skimage.draw import polygon
    v = np.zeros(shape, bool)
    for f in rois:
        xy = ImagejRoi.fromfile(f).coordinates()
        if xy is None or len(xy) < 3:
            continue
        rr, cc = polygon(xy[:, 1], xy[:, 0], shape)
        v[rr, cc] = True
    return v


def outline_overlay(img, gt, pr, gi, pi):
    """맞힌 예측 = 초록, 헛것(예측만 있음) = 빨강, 놓친 정답 = 노랑. 선 두께 2 px."""
    from skimage.segmentation import find_boundaries
    from skimage.morphology import binary_dilation, disk
    rgb = img[..., :3].copy()
    green, red, yellow = (0, 230, 120), (255, 40, 40), (255, 215, 0)
    tp_pr = np.isin(pr, pi)
    fp_pr = (pr > 0) & ~tp_pr
    fn_gt = (gt > 0) & ~np.isin(gt, gi)
    for mask, col in ((np.where(fn_gt, gt, 0), yellow), (np.where(fp_pr, pr, 0), red), (np.where(tp_pr, pr, 0), green)):
        b = binary_dilation(find_boundaries(mask, mode="inner"), disk(1))
        rgb[b] = col
    return rgb


def object_stats(img, gt, gi):
    """정답 핵마다 (면적 px, 평균 밝기 0~255, 맞혔는지)."""
    gray = img[..., :3].mean(-1)
    n = gt.max() + 1
    area = np.bincount(gt.ravel(), minlength=n)[1:]
    bright = np.bincount(gt.ravel(), weights=gray.ravel(), minlength=n)[1:] / np.maximum(area, 1)
    hit = np.zeros(n - 1, bool)
    hit[np.asarray(gi, int) - 1] = True
    edge_ids = np.unique(np.concatenate([gt[0], gt[-1], gt[:, 0], gt[:, -1]]))
    edge = np.zeros(n, bool)
    edge[edge_ids] = True
    return area, bright, hit, edge[1:]


def make_engine(engine, model_name, gpu, cellprob, diameter, pixel_size):
    """engine='cellpose' 또는 'instanseg' → (설명 문자열, 이미지 → 라벨 함수)."""
    if engine == "instanseg":
        from instanseg import InstanSeg
        m = InstanSeg(model_name or "brightfield_nuclei", device="cuda" if gpu else "cpu", verbosity=0)

        def seg(img):
            lab = m.eval_small_image(img, pixel_size=pixel_size, return_image_tensor=False, target="nuclei")
            return np.asarray(lab.squeeze().cpu().numpy(), dtype=np.int64)
        return f"InstanSeg {model_name or 'brightfield_nuclei'} (pixel_size={pixel_size})", seg
    from cellpose import models
    model = models.CellposeModel(gpu=gpu, pretrained_model=model_name) if model_name else models.CellposeModel(gpu=gpu)

    def seg(img):
        return model.eval(img, batch_size=8, cellprob_threshold=cellprob, diameter=diameter)[0]
    return f"Cellpose {Path(str(getattr(model, 'pretrained_model', model_name))).name} (cellprob={cellprob}, diameter={diameter})", seg


def run(model_name, cellprob=0.0, tag="", diameter=None, engine="cellpose", pixel_size=None):
    import torch
    from skimage.io import imread
    from PIL import Image

    torch.manual_seed(SEED)
    np.random.seed(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    gpu = torch.cuda.is_available()
    used, seg = make_engine(engine, model_name, gpu, cellprob, diameter, pixel_size)
    device = torch.cuda.get_device_name(0) if gpu else "CPU"
    print(f"모델: {used} | 장치: {device}")
    sfx = f"_{tag}" if tag else ""

    rows, examples, stats = [], {}, []
    for org in ORGANS:
        org_dir = DATA / org
        imgs = sorted((org_dir / "tissue images").glob("*.png"))
        for f in imgs:
            img = imread(f)
            if img.ndim == 2:
                img = np.stack([img] * 3, -1)
            img = img[..., :3]
            gt = relabel(imread(org_dir / "label masks" / f"{f.stem}.tif"))
            n_frag = n_tiny = 0
            if not RAW_GT:
                gt, n_frag, n_tiny = clean_gt(gt)
            t0 = time.time()
            pr = seg(img)
            dt = time.time() - t0
            pr = relabel(pr)
            vague = load_vague(org_dir, f.stem, gt.shape)
            gt_e, pr_e = drop_in_vague(gt, vague), drop_in_vague(pr, vague)
            gi, pi, dice = match(gt_e, pr_e)
            n_gt, n_pr, tp = int(gt_e.max()), int(pr_e.max()), len(gi)
            p, r, fs = scores(tp, n_gt, n_pr)
            rows.append(dict(organ=org, image=f.name, n_gt=n_gt, n_pred=n_pr, tp=tp, fp=n_pr - tp, fn=n_gt - tp,
                             precision=round(p, 3), recall=round(r, 3), f1=round(fs, 3),
                             mean_dice_matched=round(float(dice.mean()) if len(dice) else 0.0, 3),
                             vague_mask=vague is not None, gt_fragmented=n_frag, gt_tiny_removed=n_tiny,
                             seconds=round(dt, 2)))
            examples.setdefault(org, []).append((fs, f, img, gt_e, pr_e, gi, pi))
            stats.append(object_stats(img, gt_e, gi))
            print(f"  {org:15s} {f.name:24s} 정답 {n_gt:4d}  예측 {n_pr:4d}  F1 {fs:.3f}  ({dt:.1f} s)")

    import csv
    with open(OUT / f"zero_shot_metrics{sfx}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    area = np.concatenate([s[0] for s in stats])
    bright = np.concatenate([s[1] for s in stats])
    hit = np.concatenate([s[2] for s in stats])
    edge = np.concatenate([s[3] for s in stats])
    big = area >= np.median(area)
    inner = ~edge                                   # 가장자리에 잘린 핵 조각을 뺀 것
    big_in = area >= np.median(area[inner])
    q = np.quantile(area[inner], [0.25, 0.5, 0.75])
    qbin = np.digitize(area, q)                    # 0..3 = 면적 사분위
    summary = {"model": str(used), "device": device, "iou_threshold": IOU_THR,
               "gt_cleaning": "raw" if RAW_GT else {"fragmented_objects_kept_largest": sum(x["gt_fragmented"] for x in rows),
                                                   "tiny_objects_removed(<30px)": sum(x["gt_tiny_removed"] for x in rows)},
               "dataset": "NuInsSeg (zenodo 10518968, CC BY 4.0)",
               "missed_vs_found": {
                   "median_area_px_found": float(np.median(area[hit])), "median_area_px_missed": float(np.median(area[~hit])),
                   "median_brightness_found": round(float(np.median(bright[hit])), 1),
                   "median_brightness_missed": round(float(np.median(bright[~hit])), 1),
                   "recall_small_half": round(float(hit[~big].mean()), 3), "recall_large_half": round(float(hit[big].mean()), 3),
                   "recall_dark_half": round(float(hit[bright < np.median(bright)].mean()), 3),
                   "recall_bright_half": round(float(hit[bright >= np.median(bright)].mean()), 3),
                   "edge_objects": int(edge.sum()), "recall_edge": round(float(hit[edge].mean()), 3),
                   "recall_inner": round(float(hit[inner].mean()), 3),
                   "inner_recall_small_half": round(float(hit[inner & ~big_in].mean()), 3),
                   "inner_recall_large_half": round(float(hit[inner & big_in].mean()), 3),
                   "inner_area_quartiles_px": [float(x) for x in q],
                   "inner_recall_by_area_quartile": [round(float(hit[inner & (qbin == k)].mean()), 3) for k in range(4)],
                   "inner_count_by_area_quartile": [int((inner & (qbin == k)).sum()) for k in range(4)]},
               "organs": {}}
    for org in ORGANS + ["all"]:
        rs = [x for x in rows if org == "all" or x["organ"] == org]
        tp, ng, npr = sum(x["tp"] for x in rs), sum(x["n_gt"] for x in rs), sum(x["n_pred"] for x in rs)
        p, r, fs = scores(tp, ng, npr)
        dices = [x["mean_dice_matched"] for x in rs if x["tp"] > 0]
        summary["organs"][org] = dict(images=len(rs), n_gt=ng, n_pred=npr, tp=tp, precision=round(p, 3),
                                      recall=round(r, 3), f1=round(fs, 3),
                                      mean_dice_matched=round(float(np.mean(dices)), 3) if dices else 0.0,
                                      f1_min=min(x["f1"] for x in rs), f1_max=max(x["f1"] for x in rs))
    (OUT / f"zero_shot_summary{sfx}.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"all": summary["organs"]["all"], "missed_vs_found": summary["missed_vs_found"]}, ensure_ascii=False, indent=1))
    if tag:
        return

    # 그림: 흑색종·편도에서 F1 이 중간값에 가장 가까운 이미지 한 장씩 (좋은 것만 고르지 않는다)
    tiles = []
    for org in ["human melanoma", "human tonsile"]:
        ex = sorted(examples[org], key=lambda e: e[0])
        fs, f, img, gt_e, pr_e, gi, pi = ex[len(ex) // 2]
        tiles.append((img, outline_overlay(img, gt_e, pr_e, gi, pi)))
        summary.setdefault("figure", []).append(dict(organ=org, image=f.name, f1=round(fs, 3)))
    (OUT / "zero_shot_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    gap = 12
    h, w = tiles[0][0].shape[:2]
    canvas = Image.new("RGB", (2 * w + gap, len(tiles) * h + (len(tiles) - 1) * gap), (255, 255, 255))
    for i, (a, b) in enumerate(tiles):
        canvas.paste(Image.fromarray(a.astype(np.uint8)), (0, i * (h + gap)))
        canvas.paste(Image.fromarray(b.astype(np.uint8)), (w + gap, i * (h + gap)))
    canvas.save(OUT / "zero_shot_example.jpg", quality=88)
    print("그림:", OUT / "zero_shot_example.jpg", summary["figure"])
    missed_gallery(seg)


GALLERY = [("human tonsile", "human_tonsile_4"), ("human tonsile", "human_tonsile_7"),
           ("human melanoma", "human_melanoma_12"), ("human melanoma", "human_melanoma_05"),
           ("human spleen", "human_spleen_16"), ("human spleen", "human_spleen_25")]


def missed_gallery(seg, per_image=2, small_px=295, S=128):
    """면적 하위 25%(< small_px) 인데 놓친 정답 핵을 64×64 로 잘라 [원본 | 정답(노랑)+예측(초록)] 쌍으로 모은다."""
    from skimage.io import imread
    from skimage.segmentation import find_boundaries
    from PIL import Image
    pairs = []
    for org, stem in GALLERY:
        d = DATA / org
        img = imread(d / "tissue images" / f"{stem}.png")[..., :3]
        gt = relabel(imread(d / "label masks" / f"{stem}.tif"))
        if not RAW_GT:
            gt = clean_gt(gt)[0]
        pr = relabel(seg(img))
        v = load_vague(d, stem, gt.shape)
        gt, pr = drop_in_vague(gt, v), drop_in_vague(pr, v)
        gi, _, _ = match(gt, pr)
        area = np.bincount(gt.ravel())[1:]
        hit = set(int(x) for x in gi)
        taken = 0
        for k in range(1, gt.max() + 1):
            if k in hit or area[k - 1] >= small_px or taken >= per_image:
                continue
            ys, xs = np.nonzero(gt == k)
            y0, x0 = int(ys.mean()) - 32, int(xs.mean()) - 32
            if y0 < 0 or x0 < 0 or y0 + 64 > gt.shape[0] or x0 + 64 > gt.shape[1]:
                continue
            c = img[y0:y0 + 64, x0:x0 + 64].copy()
            c2 = c.copy()
            c2[find_boundaries(pr[y0:y0 + 64, x0:x0 + 64], mode="inner")] = (0, 230, 120)
            c2[find_boundaries((gt == k)[y0:y0 + 64, x0:x0 + 64], mode="inner")] = (255, 215, 0)
            pairs.append((c, c2))
            taken += 1
    cols, gap = 6, 10
    rows = (len(pairs) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * 2 * S + (cols - 1) * gap, rows * S + (rows - 1) * gap), "white")
    for i, (a, b) in enumerate(pairs):
        r, q = divmod(i, cols)
        x, y = q * (2 * S + gap), r * (S + gap)
        canvas.paste(Image.fromarray(a).resize((S, S), Image.NEAREST), (x, y))
        canvas.paste(Image.fromarray(b).resize((S, S), Image.NEAREST), (x + S, y))
    canvas.save(OUT / "zero_shot_missed_small.jpg", quality=90)
    print("놓친 작은 핵 모음:", OUT / "zero_shot_missed_small.jpg", len(pairs), "쌍")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--model", default=None, help="Cellpose 모델 이름 (기본: 설치된 버전의 기본 모델)")
    ap.add_argument("--cellprob", type=float, default=0.0, help="cellprob_threshold — 낮출수록 더 많이 잡는다 (웹 데모에도 있는 손잡이)")
    ap.add_argument("--diameter", type=float, default=None, help="예상 핵 지름(px). 작게 주면 이미지를 키워서 처리한다 (기본: 모델이 정함)")
    ap.add_argument("--engine", default="cellpose", choices=["cellpose", "instanseg"], help="비교용: QuPath 가 쓰는 InstanSeg 로도 돌릴 수 있다")
    ap.add_argument("--pixel-size", type=float, default=None, help="InstanSeg 전용 — 이미지 픽셀 크기(µm). 모르면 비워 둔다")
    ap.add_argument("--tag", default="", help="결과 파일 이름 뒤에 붙일 꼬리표 (그림은 기본 설정에서만 만든다)")
    ap.add_argument("--raw-gt", action="store_true", help="정답 라벨 정리(흩어진 조각·30 px 미만 제거)를 끈다")
    a = ap.parse_args()
    RAW_GT = a.raw_gt
    if a.fetch:
        fetch()
    if a.run:
        run(a.model, a.cellprob, a.tag, a.diameter, a.engine, a.pixel_size)
