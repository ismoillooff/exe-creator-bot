@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m creator.tools_setup
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m creator.builder --doctor
if errorlevel 1 goto failed
if not exist .env copy .env.example .env >nul
echo.
echo Tayyor! .env fayliga BOT_TOKEN ni kiriting, keyin start.bat ni oching.
pause
exit /b 0
:failed
echo.
echo Sozlash amalga oshmadi. Yuqoridagi xatoni tekshiring.
pause
exit /b 1
