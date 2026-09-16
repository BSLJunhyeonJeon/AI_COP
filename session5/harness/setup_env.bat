@echo off
REM ============================================================
REM setup_env.bat - session5/harness 로컬 conda 환경 자동 셋업 (윈도우)
REM ============================================================
REM 전제: 아나콘다(또는 미니콘다)가 설치돼 있어야 합니다. (이 스크립트는 conda 를 설치하지 않습니다)
REM 권장: "Anaconda Prompt" 에서 실행하세요.
chcp 65001 >nul
setlocal enabledelayedexpansion

set "ENV_NAME=ai_cop_session5"

REM 코랩과 Python 버전을 맞춘 값(session2 에서 확인).
set "PY_VERSION=3.12"

REM 스크립트 위치(harness\) 로 이동
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
  if not "%PY_VERSION%"=="" (
    echo [정보] env '%ENV_NAME%' 생성 ^(python=%PY_VERSION%^)
    call conda create -y -n "%ENV_NAME%" "python=%PY_VERSION%" pip
  ) else (
    echo [정보] env '%ENV_NAME%' 생성 ^(conda 기본 python^)
    call conda create -y -n "%ENV_NAME%" pip
  )
)

REM 3) 활성화 (배치가 중단되지 않도록 call 사용)
call conda activate "%ENV_NAME%"

REM 활성화가 실제로 됐는지 확인한다. 실패한 채 진행하면 pip 가 base 환경을 오염시킨다. 반드시 중단할 것.
if not "%CONDA_DEFAULT_ENV%"=="%ENV_NAME%" (
  echo [오류] conda activate 에 실패했습니다. ^(현재 환경: "%CONDA_DEFAULT_ENV%"^)
  echo        base 환경을 오염시키지 않기 위해 여기서 중단합니다.
  echo.
  echo        해결: "Anaconda Prompt" 를 열어 다시 실행하거나,
  echo              일반 cmd 라면 "conda init cmd.exe" 를 한 번 실행하고 새 창에서 재시도하세요.
  exit /b 1
)

REM 4) 의존성 설치
if exist requirements.txt (
  echo [정보] requirements.txt 설치
  call pip install -r requirements.txt
) else (
  echo [경고] requirements.txt 가 없습니다. harness\ 안에서 실행했는지 확인하세요.
)

REM 5) 다음 단계 안내
echo.
echo === 셋업 완료 ===
echo 환경 이름 : %ENV_NAME%
echo 다음 단계 : conda activate %ENV_NAME%
echo             같은 터미널에서 에이전트(예: claude)를 실행하고 README.md 의 문장을 붙여넣으세요.
echo (참고) GPU 는 필요 없습니다. 전뇌 시뮬레이션 1초에 노트북 CPU 로 수십 초 정도 걸립니다.
endlocal
