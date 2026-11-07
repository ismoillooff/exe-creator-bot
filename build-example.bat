@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Avval setup.bat ni ishga tushiring.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m creator.builder --url https://example.com --name "Namuna Sayt" --ask-password
pause
