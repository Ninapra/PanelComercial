@echo off
chcp 65001 >nul 2>&1
title Panel de Renovaciones MI.COM.CO

set PYTHON_EXE=
if exist "%~dp0python_path.txt" set /p PYTHON_EXE=<"%~dp0python_path.txt"
if not defined PYTHON_EXE (
    for %%P in (
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    ) do ( if exist %%P ( set PYTHON_EXE=%%~P & goto :ok ) )
    echo Python no encontrado. Ejecuta primero INSTALAR.bat
    pause & exit /b 1
)
:ok
echo.
echo  Panel de Renovaciones MI.COM.CO iniciando...
echo  Abre tu navegador en:  http://localhost:5000
echo.
echo  Para cerrar el panel, cierra esta ventana.
echo.
start "" http://localhost:5000
"%PYTHON_EXE%" "%~dp0run.py"
