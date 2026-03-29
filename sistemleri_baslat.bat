@echo off
color 0A
echo ===================================================
echo TETRATECH SISTEMLERI BASLATILIYOR...
echo ===================================================
echo.

echo [1] Ana Yonetim ve Karar Motoru API (8010) baslatiliyor...
start "TetraTech Ana API (8010)" cmd /k "title TetraTech Ana API & python api.py"

echo.
echo [2] Fizik ve Ucus Simulasyn Sunucusu (5000) baslatiliyor...
cd "Roket Simulasyon Aracı\roketsim-main"
start "TetraTech Fizik Motoru (5000)" cmd /k "title TetraTech Fizik Motoru & python server.py"
cd "..\.."

echo.
echo Islem tamamlandi! Arka planda 2 adet komut satiri acildi.
echo Lutfen roket ucusu veya API komutlari islerken bu pencereleri KAPATMAYIN.
echo.
timeout /t 5
exit
