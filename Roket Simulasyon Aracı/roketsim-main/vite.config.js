import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { spawn } from 'child_process';

// Auto-start Python Server
const pythonServerPlugin = () => ({
  name: 'python-server',
  configureServer() {
    console.log("Starting Python Physics Backend...");
    // Attempt multiple fallbacks for python binary including Local AppData
    const exePath = "C:/Users/demir/AppData/Local/Python/pythoncore-3.14-64/python.exe";
    let child = spawn(exePath, ['server.py'], { shell: true, stdio: 'ignore' });
    child.on('error', () => {
       child = spawn('python', ['server.py'], { shell: true, stdio: 'ignore' })
       child.on('error', () => spawn('py', ['server.py'], { shell: true, stdio: 'ignore' }));
    });
    process.on('exit', () => { if(child) child.kill(); });
  }
});

export default defineConfig({
  plugins: [react(), tailwindcss(), pythonServerPlugin()],
});
