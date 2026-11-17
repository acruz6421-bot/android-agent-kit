@echo off
setlocal
cd /d "%~dp0.."
where adb >nul 2>nul
if errorlevel 1 (echo ERRO: adb nao encontrado no PATH. Instale Platform-Tools.& exit /b 1)
if not exist .venv\Scripts\python.exe python -m venv .venv
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
echo Dispositivos ADB:
adb devices
echo Copie .env.example para .env e configure ANDROID_SERIAL.
endlocal
