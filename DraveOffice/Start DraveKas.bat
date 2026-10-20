@echo off
setlocal enabledelayedexpansion
title DraveKas

set "PY="
for %%V in (3.13 3.12 3.11 3.10) do (
    if not defined PY (
        py -%%V -c "import PyQt6" >nul 2>&1 && set "PY=py -%%V"
    )
)
if not defined PY (
    python -c "import PyQt6" >nul 2>&1 && set "PY=python"
)
if not defined PY (
    echo Python met PyQt6 niet gevonden.
    echo Installeer met:  py -m pip install PyQt6
    echo.
    pause
    exit /b 1
)

!PY! DraveKas.py
endlocal
