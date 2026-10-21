"""6회차 메시지 3 검증 — SEM 입자: Fiji 기본 방식(임계값 + watershed) vs NP-SAM(딥러닝).

이 스크립트에서 배우는 것: 떨어진 입자는 고전 방식으로 충분하고, 뭉친 입자에서 딥러닝이 값을 하는지 숫자로 본다.
입력:
  A) BAM TiO2 SEM 1908248.tif + 수동 정답 1908248_m.tif (Rühle et al., Sci Rep 2021; CC BY-NC-ND 4.0)
     → 정답과 채점한 숫자만 남긴다. NC-ND 라서 결과 그림(변형물)은 만들지 않는다.
  B) NFFA-EUROPE SEM Particles 의 이미지 1장 (Aversa et al., Sci Data 2018; CC BY 4.0) → 두 방식 윤곽선 그림.
출력: outputs/sem_summary.json, outputs/sem_nffa_compare.jpg
사용법 (session6 폴더에서):
  python tools/sem_check.py --fetch                      # BAM 2파일 + NFFA 앞쪽 12장
  python tools/sem_check.py --fiji "C:/.../fiji-windows-x64.exe"   # Fiji 를 헤드리스로 돌려 라벨 이미지 생성
  (NP-SAM 은 별도 환경에서) python tools/npsam_run.py --model fast / --model huge
  python tools/sem_check.py --score                      # 채점 + 그림
"""
import argparse
import json
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "sem"
OUT = ROOT / "outputs"
WORK = OUT / "sem_work"
BAM_IMG = "https://raw.githubusercontent.com/BAMresearch/automatic-sem-image-segmentation/master/Datasets/Electron%20Microscopy%20Images/SEM/1908248.tif"
BAM_GT = "https://raw.githubusercontent.com/BAMresearch/automatic-sem-image-segmentation/master/Datasets/Electron%20Microscopy%20Image%20Masks/TiO2_Masks_Manual_4connected/1908248_m.tif"
NFFA_TAR = "https://b2share.eudat.eu/api/records/862nr-cn036/files/Particles.tar/content"
NFFA_PICK = "L2_05532cf79b416a759a9f3bb336896ade.jpg"     # 뭉친 곳과 떨어진 곳이 한 화면에 있는 이미지
BAM_NM_PER_PX = 7520 / 1024                                # 정보 막대: Width = 7.520 µm (1024 px)
IOU_THR = 0.5


def fetch():
    (DATA / "nffa").mkdir(parents=True, exist_ok=True)
    for url, name in ((BAM_IMG, "1908248.tif"), (BAM_GT, "1908248_m.tif")):
        if not (DATA / name).exists():
            urllib.request.urlretrieve(url, DATA / name)
    # tar 는 목차가 없으므로 앞에서부터 흘려 읽다가 12장에서 멈춘다 (2.5 GB 전체를 받지 않는다)
    with urllib.request.urlopen(NFFA_TAR, timeout=120) as r:
        tf = tarfile.open(fileobj=r, mode="r|")
        n = 0
        for m in tf:
            if m.isfile():
                (DATA / "nffa" / Path(m.name).name).write_bytes(tf.extractfile(m).read())
                n += 1
            if n >= 12:
                break
    print("받음:", sorted(p.name for p in DATA.rglob("*") if p.is_file()))


def bar_row(img, start=None):
    """SEM 아래쪽 정보 막대가 시작하는 줄 (거의 검은 줄이 처음 나오는 곳)."""
    rm = img.mean(1)
    s = start if start is not None else int(img.shape[0] * 0.8)
    for r in range(s, img.shape[0]):
        if rm[r] < 5:
            return r
    return img.shape[0]


def load_gray(path):
    from skimage.io import imread
    a = imread(path)
    if a.ndim == 3:
        a = a[..., :3].mean(-1)
    return a.astype(np.uint8)


def prepare_inputs():
    """채점·실행용 입력: 정보 막대를 잘라낸 PNG 를 sem_work/ 에 만든다."""
    from PIL import Image
    from skimage.measure import label
    WORK.mkdir(parents=True, exist_ok=True)
    img = load_gray(DATA / "1908248.tif")
    gt = load_gray(DATA / "1908248_m.tif")
    h = bar_row(img)
    Image.fromarray(img[:h]).save(WORK / "bam.png")
    np.save(WORK / "bam_gt.npy", label(gt[:h] > 0, connectivity=1))   # 정답: 1 px 선으로 나뉜 입자 (4-연결)
    nf = load_gray(DATA / "nffa" / NFFA_PICK)
    hn = bar_row(nf)
    Image.fromarray(nf[:hn]).save(WORK / "nffa.png")
    return h, hn


FIJI_MACRO = r'''
// Fiji 기본 방식 — 강의 자료 '따라 해 보기'의 메뉴 순서 그대로 (헤드리스)
args = split(getArgument(), "|");
setBatchMode(true);
open(args[0]);
title = getTitle();
run("Set Scale...", "distance=1 known=" + args[1] + " unit=nm");
run("8-bit");
setOption("BlackBackground", true);      // Process > Binary > Options > Black background — 꺼져 있으면 입자 대신 배경이 잡힌다
setAutoThreshold("Default dark");        // 어두운 바탕 위 밝은 입자
run("Convert to Mask");
run("Watershed");
run("Set Measurements...", "area feret's redirect=None decimal=3");
run("Analyze Particles...", "size=" + args[3] + "-Infinity show=[Count Masks] display clear");
saveAs("Results", args[2] + ".csv");
selectImage("Count Masks of " + title);
saveAs("Tiff", args[2] + "_labels.tif");
'''


def run_fiji(fiji_exe):
    h, hn = prepare_inputs()
    macro = WORK / "fiji_particles.ijm"
    macro.write_text(FIJI_MACRO, encoding="utf-8")
    jobs = [("bam", BAM_NM_PER_PX, 200), ("nffa", 1.0, 20)]   # 최소 면적(nm² 또는 px²) — 노이즈 점 제거
    for name, scale, min_area in jobs:
        arg = f"{(WORK / (name + '.png')).as_posix()}|{scale}|{(WORK / ('fiji_' + name)).as_posix()}|{min_area if name == 'nffa' else min_area * scale * scale}"
        cmd = [fiji_exe, "--console", "-batch", str(macro), arg]   # --headless 는 입자 분석에서 NullPointerException (Fiji 2.16, 2026-10-22)
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        ok = (WORK / f"fiji_{name}_labels.tif").exists()
        print(name, "Fiji 종료코드", r.returncode, "라벨 생성" if ok else "라벨 없음")
        if not ok:
            print(r.stdout[-1500:], r.stderr[-1500:])


def relabel(m):
    from skimage.segmentation import relabel_sequential
    return relabel_sequential(np.asarray(m).astype(np.int64))[0]


def match(gt, pr, thr=IOU_THR):
    ng, npr = gt.max() + 1, pr.max() + 1
    ov = np.bincount((gt.ravel() * npr + pr.ravel()), minlength=ng * npr).reshape(ng, npr)
    ag, ap = ov.sum(1), ov.sum(0)
    inter = ov[1:, 1:].astype(float)
    union = ag[1:, None] + ap[None, 1:] - inter
    iou = np.divide(inter, union, out=np.zeros_like(inter), where=union > 0)
    gi, pi = np.nonzero(iou > thr)
    dice = 2 * inter[gi, pi] / (ag[1:][gi] + ap[1:][pi])
    return gi + 1, pi + 1, dice


def score_one(gt, pr):
    gi, pi, dice = match(gt, pr)
    n_gt, n_pr, tp = int(gt.max()), int(pr.max()), len(gi)
    p = tp / n_pr if n_pr else 0.0
    r = tp / n_gt if n_gt else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return dict(n_gt=n_gt, n_pred=n_pr, tp=tp, precision=round(p, 3), recall=round(r, 3), f1=round(f, 3),
                mean_dice_matched=round(float(dice.mean()), 3) if len(dice) else 0.0)


def score():
    from skimage.io import imread
    gt = relabel(np.load(WORK / "bam_gt.npy"))
    res = {"bam_image": "1908248.tif (BAM TiO2, CC BY-NC-ND 4.0)", "iou_threshold": IOU_THR, "methods": {}}
    cands = [("fiji_threshold_watershed", WORK / "fiji_bam_labels.tif")]
    cands += [(f"npsam_{m}{f}", WORK / f"npsam_bam_labels_{m}{f}.npy") for m in ("fast", "huge") for f in ("", "_filt")]
    for name, f in cands:
        if not f.exists():
            res["methods"][name] = "결과 없음"
            continue
        pr = relabel(np.load(f) if f.suffix == ".npy" else imread(f))
        res["methods"][name] = score_one(gt, pr)
    (OUT / "sem_summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))
    figure()


def figure():
    """NFFA (CC BY) 이미지: [원본 | Fiji 윤곽(주황) | NP-SAM 윤곽(초록)]. NP-SAM 은 GPU 없는 PC 의 기본값인 fast(FastSAM) 결과, 없으면 칸을 뺀다."""
    from PIL import Image
    from skimage.io import imread
    from skimage.segmentation import find_boundaries
    from skimage.morphology import dilation, disk
    img = imread(WORK / "nffa.png")
    panels = [np.stack([img] * 3, -1)]
    for f, col in ((WORK / "fiji_nffa_labels.tif", (255, 160, 0)), (WORK / "npsam_nffa_labels_fast.npy", (0, 230, 120))):
        if not f.exists():
            continue
        lab = relabel(np.load(f) if f.suffix == ".npy" else imread(f))
        rgb = np.stack([img] * 3, -1).copy()
        rgb[dilation(find_boundaries(lab, mode="inner"), disk(1))] = col
        panels.append(rgb)
    gap = 12
    h, w = img.shape
    canvas = Image.new("RGB", (len(panels) * w + (len(panels) - 1) * gap, h), "white")
    for i, p in enumerate(panels):
        canvas.paste(Image.fromarray(p.astype(np.uint8)), (i * (w + gap), 0))
    canvas.save(OUT / "sem_nffa_compare.jpg", quality=88)
    print("그림:", OUT / "sem_nffa_compare.jpg", len(panels), "칸")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--fiji", default=None, help="Fiji 실행 파일 경로")
    ap.add_argument("--score", action="store_true")
    a = ap.parse_args()
    if a.fetch:
        fetch()
    if a.fiji:
        run_fiji(a.fiji)
    if a.score:
        score()
