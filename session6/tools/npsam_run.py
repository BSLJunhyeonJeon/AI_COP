"""NP-SAM 을 SEM 이미지에 학습 없이 돌려 라벨 이미지를 저장한다 (tools/sem_check.py 가 채점).

NP-SAM 은 의존성이 많고 버전을 고정하므로 별도 conda 환경에서 돌린다:
    conda create -n ai_cop_npsam python=3.10
    set PYTHONUTF8=1          (한국어 윈도우: 의존성 clip 설치가 cp949 디코딩 오류로 실패하는 것을 막는다)
    pip install npsam
    python tools/npsam_run.py --model fast     # GPU 가 없을 때 NP-SAM 이 자동으로 고르는 모델 (FastSAM)
    python tools/npsam_run.py --model huge     # GPU 메모리 7 GB 초과일 때 자동으로 고르는 모델 (SAM ViT-H)
입력: outputs/sem_work/bam.png, nffa.png (sem_check.py 가 정보 막대를 잘라 만든 것)
출력: outputs/sem_work/npsam_<bam|nffa>_labels_<model>.npy, npsam_timing_<model>.json
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "outputs" / "sem_work"


def to_labels(masks):
    """(N, H, W) 마스크 묶음 → 2D 라벨. 큰 마스크를 먼저 칠하고 작은 것을 위에 덮는다."""
    lab = np.zeros(masks.shape[1:], np.int32)
    order = np.argsort(-masks.reshape(len(masks), -1).sum(1))
    for i, k in enumerate(order, 1):
        lab[masks[k] > 0] = i
    return lab


def main(model, filt):
    from npsam import NPSAMImage
    import torch
    timing = {"model": model, "cuda": torch.cuda.is_available()}
    for name in ("bam", "nffa"):
        img = NPSAMImage(str(WORK / f"{name}.png"))
        t0 = time.time()
        # 기본값 그대로, 단 채점 대상(정답)이 가장자리 입자도 포함하므로 edge_filter 만 끈다
        img.segment(device="auto", SAM_model=model, edge_filter=False, verbose=False)
        dt = time.time() - t0
        sfx = ""
        if filt:
            # 걸러내기 한 가지: 다른 마스크와 2개 이상 겹치는 마스크(= 입자 여러 개를 덮은 덩어리 마스크)를 뺀다
            img.filter_nogui({"number_of_overlapping_masks": 1})
            sfx = "_filt"
        masks = img.get_filtered_masks()
        lab = to_labels(np.asarray(masks))
        np.save(WORK / f"npsam_{name}_labels_{model}{sfx}.npy", lab)
        timing[name] = {"seconds": round(dt, 1), "masks": int(len(masks))}
        print(name, model, f"{dt:.1f} s", len(masks), "masks")
    (WORK / f"npsam_timing_{model}{'_filt' if filt else ''}.json").write_text(json.dumps(timing, indent=2), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="auto", help="fast | base | large | huge | auto")
    ap.add_argument("--filter", action="store_true", help="겹치는 마스크가 2개 이상인 덩어리 마스크를 뺀다")
    a = ap.parse_args()
    main(a.model, a.filter)
