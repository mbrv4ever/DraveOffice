@echo off
setlocal enabledelayedexpansion
title Maak DraveKas EXE

echo ============================================
echo   DraveKas - EXE bouwen (Dravenlock)
echo ============================================
echo.

rem --- Python zoeken: keten 3.13 - 3.10, anders python ---
set "PY="
for %%V in (3.13 3.12 3.11 3.10) do (
    if not defined PY (
        py -%%V -c "import sys" >nul 2>&1 && set "PY=py -%%V"
    )
)
if not defined PY (
    python -c "import sys" >nul 2>&1 && set "PY=python"
)
if not defined PY (
    echo Geen geschikte Python gevonden ^(3.10 t/m 3.13^).
    echo Installeer Python van python.org en probeer opnieuw.
    echo.
    pause
    exit /b 1
)
echo Python gevonden: !PY!
echo.

rem --- PyInstaller controleren / installeren ---
!PY! -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo PyInstaller niet gevonden - bezig met installeren...
    !PY! -m pip install --upgrade pyinstaller
    if errorlevel 1 (
        echo Installeren van PyInstaller is mislukt.
        echo.
        pause
        exit /b 1
    )
)
echo.

rem --- De EXE bouwen via de spec ---
echo Bezig met bouwen... dit kan even duren.
echo.
!PY! -m PyInstaller --noconfirm --clean "DraveKas.spec"
echo.

rem --- Resultaat controleren ---
if exist "dist\DraveKas.exe" (
    echo ============================================
    echo   KLAAR. De EXE staat hier:
    echo   dist\DraveKas.exe
    echo ============================================
) else (
    echo Er ging iets mis: geen EXE gevonden in de map dist.
    echo Lees de meldingen hierboven voor de oorzaak.
)
echo.
pause
endlocal
