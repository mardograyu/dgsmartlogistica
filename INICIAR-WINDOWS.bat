@echo off
cd /d "%~dp0"
title DG Smart Logistica
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 iniciar.py
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Instale Python 3.10 ou superior pelo site https://www.python.org/downloads/
    echo Marque Add Python to PATH na instalacao.
    pause
    exit /b 1
  )
  python iniciar.py
)
pause
