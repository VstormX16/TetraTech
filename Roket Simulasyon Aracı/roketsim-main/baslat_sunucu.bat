@echo off
REM SKYBOUNDARY Python Sunucu Başlatıcı
REM Sistemde "python" komutu çalışmadığında kullanılacak yedek çalıştırıcı

echo 🚀 SKYBOUNDARY Python Sunucusu Baslatiliyor...
echo.

REM 1. Önce normal python komutunu deneriz
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [Normal Python Algilandi]
    python server.py
    pause
    exit /b
)

REM 2. py komutunu deneriz
py --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [PY Launcher Algilandi]
    py server.py
    pause
    exit /b
)

REM 3. Kesin yüklü olan özel konumu deneriz
set "MY_PYTHON=C:\Users\demir\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if exist "%MY_PYTHON%" (
    echo [Yerel Python Kurulumu Algilandi]
    "%MY_PYTHON%" server.py
    pause
    exit /b
)

echo HATA: Python bulunamadi!
pause
