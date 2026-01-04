# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-01-04

### Added

- **Ground Station Service**: FastAPI-based client interface for uploading training jobs
  - Data Shuttle Protocol implementation for simulating launch logistics
  - REST API endpoint `POST /upload_job` for job submission
  
- **Uplink Service**: Chaos proxy middleware enforcing orbital network constraints
  - Variable latency injection (500ms–2000ms) simulating RF/Optical alignment
  - Packet loss simulation for Loss of Signal (LOS) scenarios
  
- **Orbital Node Service**: Compute worker with physics-based thermal management
  - `RadiatorSystem` class implementing Stefan-Boltzmann heat rejection
  - `ThermalConfig` with Starcloud White Paper parameters
  - `ThermalThrottlingException` for 80°C safety limit enforcement
  
- **Docker Compose Infrastructure**
  - Isolated network topology (`terrestrial_mesh` and `orbital_mesh`)
  - Resource-constrained orbital node (0.5 CPU, 512MB RAM)
  - Dev container configuration for Python 3.12

- **Testing Suite**
  - `test_stefan_boltzmann_accuracy`: Validates ~385 W/m² heat rejection at 20°C
  - `test_system_cools_down`: Verifies cooling behavior in vacuum with 0 load
  - `test_overheating_trip`: Confirms thermal throttling at temperature limits

- **Documentation**
  - Comprehensive README with Mermaid architecture diagrams
  - Operational sequence diagram showing job flow
  - Setup and configuration instructions

### Security

- Added `.gitignore` to prevent `.env` files with API keys from being committed

---

[Unreleased]: https://github.com/LEDazzio01/Orbital-Sim-Fault-Tolerant-Distributed-AI-Uplink/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/LEDazzio01/Orbital-Sim-Fault-Tolerant-Distributed-AI-Uplink/releases/tag/v0.1.0
