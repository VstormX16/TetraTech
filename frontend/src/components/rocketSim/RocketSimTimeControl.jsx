import React from 'react';
import { motion } from 'framer-motion';
import { useRocketSimStore } from './rocketSimStore';
import { fmt } from './rocketSimPhysics';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import FastForwardIcon from '@mui/icons-material/FastForward';
import FastRewindIcon from '@mui/icons-material/FastRewind';

export function RocketSimTimeControl() {
  const { timeScale, setTimeScale, isPaused, togglePause, metrics } = useRocketSimStore();

  const SpeedBtn = ({ targetScale, icon: Icon, label }) => (
    <button
      onClick={() => {
        if (isPaused) togglePause();
        setTimeScale(targetScale);
      }}
      style={{
        background: timeScale === targetScale && !isPaused ? '#CE1212' : 'transparent',
        color: timeScale === targetScale && !isPaused ? '#EEEBDD' : '#1B1717',
        border: '1px solid ' + (timeScale === targetScale && !isPaused ? '#CE1212' : 'rgba(27,23,23,0.3)'),
        borderRadius: '4px',
        padding: '0.4rem 0.6rem',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        fontWeight: 900,
        fontSize: '0.65rem'
      }}
    >
      <Icon fontSize="small" /> {label}
    </button>
  );

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
      }}
    >
      <div style={{ fontSize: '0.65rem', fontWeight: 900, color: 'rgba(27,23,23,0.5)', marginRight: '0.5rem', letterSpacing: '2px' }}>ZAMAN</div>
      <SpeedBtn targetScale={0.2} icon={FastRewindIcon} label="x0.2" />
      <SpeedBtn targetScale={0.5} icon={FastRewindIcon} label="x0.5" />
      
      <button
        onClick={togglePause}
        style={{
          background: isPaused ? '#1B1717' : 'transparent',
          color: isPaused ? '#EEEBDD' : '#1B1717',
          border: '1px solid ' + (isPaused ? '#1B1717' : 'rgba(27,23,23,0.3)'),
          borderRadius: '4px',
          padding: '0.4rem 0.6rem',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          fontWeight: 900,
          fontSize: '0.65rem',
          marginLeft: '4px',
          marginRight: '4px'
        }}
      >
        {isPaused ? <PlayArrowIcon fontSize="small" /> : <PauseIcon fontSize="small" />}
        {isPaused ? 'DEVAM ET' : 'DURDUR'}
      </button>

      <SpeedBtn targetScale={1.0} icon={PlayArrowIcon} label="x1(N)" />
      <SpeedBtn targetScale={2.0} icon={FastForwardIcon} label="x2.0" />
      <SpeedBtn targetScale={5.0} icon={FastForwardIcon} label="x5.0" />
      
      <div style={{ marginLeft: '1rem', background: '#1B1717', color: '#EEEBDD', padding: '0.4rem 0.8rem', borderRadius: '4px', fontSize: '0.65rem', fontWeight: 900, fontFamily: "'JetBrains Mono', monospace" }}>
        T+{fmt(metrics.t, 2)}s
      </div>
    </div>
  );
}
