import React from 'react';
import RocketCanvas from './components/RocketCanvas';
import Sidebar from './components/Sidebar';
import { TelemetryOverlay, EnvironmentHud, LiveLogConsole } from './components/OverlayUI';
import ReportModal from './components/ReportModal';

export default function App() {
  return (
    <div className="flex w-full h-screen relative overflow-hidden text-slate-100 antialiased font-sans">
      {/* Sol: Simülasyon Canvas + Overlay'ler */}
      <div className="flex-1 relative overflow-hidden">
        <RocketCanvas />
        <TelemetryOverlay />
        <EnvironmentHud />
        <LiveLogConsole />
      </div>

      {/* Sağ: Parametre Paneli */}
      <Sidebar />

      {/* Fullscreen Report Modal */}
      <ReportModal />
    </div>
  );
}
