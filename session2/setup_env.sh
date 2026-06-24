#!/usr/bin/env bash
# ============================================================
# setup_env.sh — session2 로컬 conda 환경 자동 셋업 (맥 / 리눅스)
# ============================================================
# 실행권한이 없으면:  chmod +x setup_env.sh   후   ./setup_env.sh
# 전제: 아나콘다(또는 미니콘다)가 설치돼 있어야 합니다. (이 스크립트는 conda 를 설치하지 않습니다)
# 애플 실리콘도 표준 설치로 충분합니다(MPS 폴백은 런타임 사안이라 셋업에 넣지 않음).
set -euo pipefail

ENV_NAME="ai_cop_session2"

# 코랩과 Python 버전을 맞추려면 아래에 버전을 적습니다(예: PY_VERSION="3.11").
# 비워 두면 conda 기본 Python 으로 생성됩니다(파이썬 패리티 미적용 — 코랩 00_setup 셀 5에서 확인 후 채우세요).
PY_VERSION=""

# 스크립트 위치(session2/) 기준으로 동작
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1) conda 확인
if ! command -v conda >/dev/null 2>&1; then
  echo "[오류] conda 를 찾지 못했습니다."
  echo "       아나콘다/미니콘다를 설치하고, conda 가 활성화된 터미널에서 다시 실행하세요."
  echo "       (이 스크립트는 conda 자체를 설치하지 않습니다.)"
  exit 1
fi

# 2) conda activate 를 셸 스크립트에서 쓰기 위한 초기화
source "$(conda info --base)/etc/profile.d/conda.sh"

# 3) env 멱등 생성 (이미 있으면 그대로 사용)
if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  echo "[정보] env '$ENV_NAME' 가 이미 있습니다. 새로 만들지 않고 사용합니다."
else
  if [ -n "$PY_VERSION" ]; then
    echo "[정보] env '$ENV_NAME' 생성 (python=$PY_VERSION)"
    conda create -y -n "$ENV_NAME" "python=$PY_VERSION" pip
  else
    echo "[정보] env '$ENV_NAME' 생성 (conda 기본 python)"
    echo "       * 코랩과 Python 버전을 맞추려면 이 스크립트 상단 PY_VERSION 을 채우세요."
    conda create -y -n "$ENV_NAME" pip
  fi
fi

# 4) 활성화 + 의존성 설치
conda activate "$ENV_NAME"
if [ -f requirements.txt ]; then
  echo "[정보] requirements.txt 설치"
  pip install -r requirements.txt
else
  echo "[경고] requirements.txt 가 없습니다. session2/ 안에서 실행했는지 확인하세요."
fi

# 5) 다음 단계 안내
echo
echo "=== 셋업 완료 ==="
echo "환경 이름 : $ENV_NAME"
echo "다음 단계 : conda activate $ENV_NAME"
echo "            jupyter notebook notebooks/00_setup.ipynb"
echo "(참고) torch 핀(requirements.txt)과 PY_VERSION 은 코랩 00_setup 셀 5 값으로 확정하세요."
