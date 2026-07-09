@echo off
setlocal
title Werkstudent Job Agent

cd /d "%~dp0"

set "PYTHON_EXE=.venv\Scripts\python.exe"

if not exist "config.json" (
    if exist "config.example.json" (
        echo Erstelle lokale config.json aus config.example.json ...
        copy "config.example.json" "config.json" >nul
    )
)

if not exist "%PYTHON_EXE%" (
    echo Erstelle lokale Python-Umgebung .venv ...
    py -3 -m venv .venv
    if errorlevel 1 (
        python -m venv .venv
    )
    if errorlevel 1 (
        echo.
        echo Python 3 wurde nicht gefunden. Bitte Python 3.11 oder neuer installieren.
        pause
        exit /b 1
    )
)

echo Installiere/aktualisiere Abhaengigkeiten ...
"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Abhaengigkeiten konnten nicht installiert werden.
    pause
    exit /b 1
)

echo Starte Werkstudent Job Agent ...
"%PYTHON_EXE%" run.py
if errorlevel 1 (
    echo.
    echo Die App wurde mit einem Fehler beendet.
    pause
    exit /b 1
)

exit /b 0
