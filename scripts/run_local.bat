@echo off
cd /d "%~dp0.."

py -3.11 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=py -3.11
    goto python_found
)
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=py -3.12
    goto python_found
)
py -3.10 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=py -3.10
    goto python_found
)

echo Python 3.10, 3.11 ou 3.12 est requis. Installez Python puis relancez ce script.
pause
exit /b 1

:python_found
if not exist .venv %PYTHON% -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts\generate_sounds.py
python -m streamlit run app.py
