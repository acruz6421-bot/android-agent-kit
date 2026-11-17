@echo off
setlocal
set /p ANDROID_ENDPOINT=Informe IP:porta exibido em Depuracao sem fio:
if "%ANDROID_ENDPOINT%"=="" (echo Endereco nao informado.& exit /b 1)
adb connect %ANDROID_ENDPOINT%
adb devices
endlocal
