@echo off
chcp 65001 >nul 2>&1
title Instalador Panel MI.COM.CO

echo.
echo  ============================================================
echo   PANEL WEB DE RENOVACIONES - MI.COM.CO
echo   Instalador v1.0
echo  ============================================================
echo.

:: ---- Buscar Python -------------------------------------------------------
set PYTHON_EXE=
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
) do ( if exist %%P ( set PYTHON_EXE=%%~P & goto :pyok ) )

echo  Python no encontrado. Descargando...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe' -OutFile '%TEMP%\py.exe'"
"%TEMP%\py.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
timeout /t 8 /nobreak >nul
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
) do ( if exist %%P ( set PYTHON_EXE=%%~P & goto :pyok ) )
echo  ERROR: No se pudo instalar Python. Ve a https://python.org/downloads
pause & exit /b 1

:pyok
echo  [1/4] Python: %PYTHON_EXE%  OK
echo %PYTHON_EXE%> "%~dp0python_path.txt"
echo.

:: ---- Instalar dependencias -----------------------------------------------
echo  [2/4] Instalando dependencias del panel web...
echo        (Flask, SQLAlchemy, pandas, anthropic...)
echo.
echo        Paso 1/7: pip...
"%PYTHON_EXE%" -m pip install --upgrade pip 2>&1 | findstr /i "success\|already\|error"

echo        Paso 2/7: flask...
"%PYTHON_EXE%" -m pip install flask==3.0.3 2>&1 | findstr /i "success\|already\|error"

echo        Paso 3/7: flask-sqlalchemy...
"%PYTHON_EXE%" -m pip install flask-sqlalchemy==3.1.1 2>&1 | findstr /i "success\|already\|error"

echo        Paso 4/7: flask-login...
"%PYTHON_EXE%" -m pip install flask-login==0.6.3 2>&1 | findstr /i "success\|already\|error"

echo        Paso 5/7: flask-talisman...
"%PYTHON_EXE%" -m pip install flask-talisman 2>&1 | findstr /i "success\|already\|error"

echo        Paso 6/7: pandas + openpyxl...
"%PYTHON_EXE%" -m pip install pandas openpyxl 2>&1 | findstr /i "success\|already\|error"

echo        Paso 7/7: anthropic...
"%PYTHON_EXE%" -m pip install anthropic 2>&1 | findstr /i "success\|already\|error"
echo.

:: ---- Verificar --------------------------------------------------------
"%PYTHON_EXE%" -c "import flask, flask_sqlalchemy, flask_login, pandas, anthropic; print('        Verificacion OK')"
if %errorlevel% neq 0 ( echo ERROR en dependencias. & pause & exit /b 1 )
echo.

:: ---- Crear tarea programada (10 AM) -----------------------------------
echo  [3/4] Creando tarea programada diaria (10:00 AM)...
set TASK=RenovacionesPanel_Notificador
schtasks /delete /tn "%TASK%" /f >nul 2>&1
schtasks /create /tn "%TASK%" /tr "\"%PYTHON_EXE%\" \"%~dp0run_notificador.py\"" /sc DAILY /st 10:00 /ru "%USERNAME%" /rl HIGHEST /f >nul 2>&1
if %errorlevel% equ 0 ( echo        Tarea programada: 10:00 AM diario  OK ) else ( echo        Advertencia: tarea no creada. )
echo.

:: ---- Iniciar panel web ------------------------------------------------
echo  [4/4] Iniciando el panel web...
echo.
echo  ============================================================
echo   INSTALACION COMPLETADA
echo  ============================================================
echo.
echo   El panel se abrira en tu navegador en:
echo   http://localhost:5000
echo.
echo   Credenciales iniciales: las definidas en api\.env
echo   (variables ADMIN_EMAIL y ADMIN_PASSWORD).
echo.
echo   Copia api\.env.example a api\.env antes de iniciar,
echo   completando los placeholders con valores reales.
echo.
echo   Presiona cualquier tecla para iniciar el panel...
pause >nul

start "" http://localhost:5000
"%PYTHON_EXE%" "%~dp0run.py"
