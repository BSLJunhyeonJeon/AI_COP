@echo off
REM ============================================================
REM setup_env.bat - session2 로컬 conda 환경 자동 셋업 (윈도우)
REM ============================================================
REM 전제: 아나콘다(또는 미니콘다)가 설치돼 있어야 합니다. (이 스크립트는 conda 를 설치하지 않습니다)
REM 권장: "Anaconda Prompt" 에서 실행하세요.
chcp 65001 >nul
setlocal enabledelayedexpansion

set "ENV_NAME=ai_cop_session2"

REM 코랩과 Python 버전을 맞추려면 아래에 버전을 적습니다(예: set "PY_VERSION=3.11").
REM 비워 두면 conda 기본 Python 으로 생성됩니다. (코랩 셀5에서 확인된 값으로 고정)
set "PY_VERSION=3.12"

REM 스크립트 위치(session2\) 로 이동
cd /d "%~dp0"

REM 1) conda 확인
where conda >nul 2>nul
if errorlevel 1 (
  echo [오류] conda 를 찾지 못했습니다.
  echo        아나콘다/미니콘다를 설치하고 "Anaconda Prompt" 에서 다시 실행하세요.
  echo        ^(이 스크립트는 conda 자체를 설치하지 않습니다.^)
  exit /b 1
)

REM 2) env 존재 확인 (멱등). findstr 가 찾으면 errorlevel 0.
call conda env list | findstr /R /C:"\<%ENV_NAME%\>" >nul
if not errorlevel 1 (
  echo [정보] env '%ENV_NAME%' 가 이미 있습니다. 새로 만들지 않고 사용합니다.
) else (
  REM PY_VERSION 이 비어 있지 않을 때만 python 핀을 건다(빈 문자열 안전 검사).
  if not "%PY_VERSION%"=="" (
    echo [정보] env '%ENV_NAME%' 생성 ^(python=%PY_VERSION%^)
    call conda create -y -n "%ENV_NAME%" "python=%PY_VERSION%" pip
  ) else (
    echo [정보] env '%ENV_NAME%' 생성 ^(conda 기본 python^)
    echo        * 코랩과 Python 버전을 맞추려면 이 스크립트 상단 PY_VERSION 을 채우세요.
    call conda create -y -n "%ENV_NAME%" pip
  )
)

REM 3) 활성화 (배치가 중단되지 않도록 call 사용)
call conda activate "%ENV_NAME%"
if errorlevel 1 (
  echo [경고] conda activate 에 실패했습니다.
  echo        "conda init cmd.exe" 를 한 번 실행한 뒤 새 창에서 다시 시도하세요.
)

REM 4) 의존성 설치
if exist requirements.txt (
  echo [정보] requirements.txt 설치
  call pip install -r requirements.txt
) else (
  echo [경고] requirements.txt 가 없습니다. session2\ 안에서 실행했는지 확인하세요.
)

REM 5) 다음 단계 안내
echo.
echo === 셋업 완료 ===
echo 환경 이름 : %ENV_NAME%
echo 다음 단계 : conda activate %ENV_NAME%
echo             jupyter notebook notebooks\00_setup.ipynb
echo (참고) torch 핀(requirements.txt)과 PY_VERSION 은 코랩 00_setup 셀 5 값으로 확정하세요.
endlocal
