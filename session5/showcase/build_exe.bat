@echo off
REM ============================================================
REM build_exe.bat - 재생기를 단일 Windows exe 로 묶는다 (PyInstaller). 이 폴더(session5\showcase)에서 실행.
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0"
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 ( echo [오류] 패키지 설치 실패 & exit /b 1 )
python -m PyInstaller --noconfirm --clean --onefile --windowed --name FlyBrainPlayer --add-data "pack;pack" player.py
if errorlevel 1 ( echo [오류] PyInstaller 실패 & exit /b 1 )
echo.
echo === 완료: dist\FlyBrainPlayer.exe ===
echo 처음 실행 시 Windows SmartScreen 경고가 뜨면 "추가 정보 > 실행" 을 누르세요(서명 없는 exe).
