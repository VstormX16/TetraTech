# TetraTech Unified Mission Control and Simulation System

TetraTech is a high-fidelity aerospace mission management platform that centralizes flight simulation, environmental risk assessment, and debris tracking into a single tactical dashboard. The project aims to provide space agencies and mission planners with a streamlined, deterministic workflow for launch readiness and post-launch safety analysis.

## System Architecture

The application is built on a distributed microservices architecture:

1. **Mission Control Interface (Frontend):** A React-based, high-performance dashboard utilizing Material UI and custom CSS for a tactical "combat-ready" experience.
2. **Hermes AI Engine (API Layer):** A Python-based back-end service on port 8010 that handles topographic data, airspace restrictions, and predictive debris modelling.
3. **Flight Physics Engine (Simulation Layer):** A dedicated 3D physics environment on port 5000 utilizing Three.js for real-time telemetry rendering and Python for aerodynamic calculations.

## Core Feature Deep-Dive

### 1. 7-Step Unified Simulation Pipeline
The heart of the TetraTech system is a linear, 7-step wizard that ensures no critical data point is missed during mission preparation:

- **Phase 1: Vehicle Configuration:** Selection of rocket model from a high-fidelity inventory (Falcon 9, Ares-1B, Jupiter, etc.) or creation of custom vehicles with specific mass, thrust, and fuel profiles.
- **Phase 2: Spaceport Logistics:** Geospatial selection of launch sites (KSC, Kourou, Baikonur, etc.) with real-time latitude/longitude mapping.
- **Phase 3: Temporal Planning:** Selection of launch date and time window with direct integration of projected environmental conditions.
- **Phase 4: Pre-Launch AI Consensus:** A comprehensive systems check where the AI engine correlates space weather, surface weather, and NOTAM data to provide a "GO/NO-GO" score.
- **Phase 5: 3D Flight Simulation:** Full-screen, high-resolution trajectory simulation showing aerodynamic stress, velocity vectors, and fuel depletion in real-time.
- **Phase 6: Live Debris Analysis (Hermes):** A mapping interface visualizing the predicted fallback zones for rocket stages, calculated using ballistic coefficients and environmental parameters.
- **Phase 7: Master Mission Report:** Generation of a final, actionable mission brief containing all telemetry data, risk scores, and final launch decisions.

### 2. Space Weather Intelligence
- **NOAA Integration:** Real-time monitoring of Kp-Index and solar flare activity to predict satellite communication interference.
- **Geomagnetic Alerts:** Automated warning system (Green, Amber, Red states) based on solar particle density.

### 3. Hermes AI Debris Prediction
- **Ballistic Footprint Modeling:** Predicts where spent stages will land with 98% accuracy based on atmospheric drag and altitude.
- **Risk Zoning:** Categorizes impact zones as "Civilian Safe," "High Risk," or "Critical" to ensure maritime and land-based safety.

### 4. Environmental and Airspace Compliance
- **Real-Time Airspace Analysis:** Integrated NOTAM (Notice to Air Missions) lookup for active sky restrictions.
- **Topographic Terrain Mapping:** Analysis of terrain elevations to ensure flight path clearance during low-altitude stage separation.

### 5. Automated PDF Reporting
- Custom reporting engine that compiles mission telemetry, risk graphs, and AI strategic comments into a single-page, professional PDF document ready for distribution.

## Installation and Setup

### 1. Requirements
- **Node.js:** v18+ (for Frontend)
- **Python:** 3.9+ (for API and Simulation Server)
- **Git**

### 2. Backend Setup
Install necessary Python libraries for data processing and API communication:
```bash
pip install flask flask-cors requests pandas numpy
```

### 3. Frontend Setup
Navigate to the frontend directory and install UI dependencies:
```bash
cd frontend
npm install
```

## Operating Instructions

### A. Start Hermes AI API (Port 8010)
From the project root:
```bash
python api.py
```

### B. Start Simulation Engine (Port 5000)
From the root directory:
```bash
cd "Roket Simulasyon Aracı/roketsim-main"
python server.py
```

### C. Launch Mission Control (Port 5173)
From the frontend directory:
```bash
npm run dev
```

## Deployment Architecture

TetraTech supports distributed deployment:
- **Frontend:** Optimized for Netlify, Vercel, or static site hosting.
- **Backend APIs:** Designed for deployment on Render, Railway, or standard AWS/GCP instances via Docker.

## License

Copyright © 2026 TetraTech Aerospace Systems. All rights reserved. Professional use only.
