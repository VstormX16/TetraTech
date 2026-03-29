const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let apiProcess;
let serverProcess;

function getBackendPath(exeName) {
  // If packaged, extraResources goes to process.resourcesPath
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend_bin', exeName);
  }
  // If developing locally, look for the backend_bin folder created by PyInstaller script
  return path.join(__dirname, '../../backend_bin', exeName);
}

function startBackend() {
  const apiExe = getBackendPath('api.exe');
  const serverExe = getBackendPath('server.exe');

  console.log('Arka plan servisleri baslatiliyor...');
  console.log('API Yolu:', apiExe);
  console.log('Server Yolu:', serverExe);
  
  // API process
  if (fs.existsSync(apiExe)) {
    try {
      apiProcess = spawn(apiExe, [], { detached: false, stdio: 'ignore' });
      console.log('API (.exe) basariyla calistirildi.');
    } catch(e) { console.error('API calistirma hatasi:', e); }
  } else {
    console.error('UYARI: API exe dosyasi bulunamadi. Sadece arayuz calisabilir.');
  }

  // Server process
  if (fs.existsSync(serverExe)) {
    try {
      serverProcess = spawn(serverExe, [], { detached: false, stdio: 'ignore' });
      console.log('Fizik Motoru (.exe) basariyla calistirildi.');
    } catch(e) { console.error('Fizik motoru calistirma hatasi:', e); }
  } else {
    console.error('UYARI: Fizik motoru exe dosyasi bulunamadi.');
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    },
    title: "TetraTech Görev Kontrol Merkezi",
    autoHideMenuBar: true
  });

  if (app.isPackaged) {
    // Proje derlendiğinde Vite'nin ciktisi olan dist klasorunu okuyacak
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  } else {
    // Gelistirme asamasinda localhost:5173 e baglanabilir veya build dosyasina gider
    mainWindow.loadURL('http://localhost:5173').catch(() => {
        mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
    });
  }

  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

app.on('ready', () => {
  startBackend();
  // Arka plan servislerinin ayağa kalkması için arayüzü çok kısa bir gecikmeyle açalım
  setTimeout(createWindow, 2000); 
});

app.on('will-quit', () => {
  // Uygulama kapanırken arka plan servislerini de öldür
  if (apiProcess) apiProcess.kill();
  if (serverProcess) serverProcess.kill();
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', function () {
  if (mainWindow === null) createWindow();
});
