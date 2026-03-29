@echo off
color 0B
echo ===================================================
echo TETRATECH PROJESI DERLENIYOR (.EXE OLUSTURULUYOR)
echo ===================================================
echo.
echo [!] Bu islem bilgisayarinizin hizina gore 3-5 dakika surebilir.
echo Lutfen pencereleri kapatmayiniz.
echo.

echo [1/3] Ana Yonetim API (Python) Exe'sine Donusturuluyor...
pyinstaller --noconfirm --noconsole --onefile --distpath frontend\backend_bin --name api api.py

echo.
echo [2/3] Fizik Motoru (Python) Exe'sine Donusturuluyor...
cd "Roket Simulasyon Aracı\roketsim-main"
pyinstaller --noconfirm --noconsole --onefile --distpath ..\..\frontend\backend_bin --name server server.py
cd "..\.."

echo.
echo [3/3] Arayuz (React) Derleniyor ve Masaustu Uygulamasi Paketleniyor (Electron)...
cd frontend
call npm run build:electron
cd ..

echo.
echo ===================================================
echo TUM ISLEMLER BASARIYLA TAMAMLANDI!
echo Masaustu uygulamaniza ve kurulum dosyasina su adresten ulasabilirsiniz:
echo - TetraTech\frontend\release
echo ===================================================
pause
