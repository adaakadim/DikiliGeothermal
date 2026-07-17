# Changelog

All notable changes to the Dikili Geothermal SCADA Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.0.0 Release Candidate] - 2026-07-17
### Added
- Phase 11 complete: Reliability Framework, Scenario Manager, Configuration Center.
- Enterprise Reporting Engine.
- Historical Playback integration.
- Final Application architecture documentation and system tests.

### Changed
- ISA-101 UI standardizations applied universally across all HMI panels.
- Optimized Matplotlib redraw routines resulting in 60% lower CPU overhead.
- Centralized Data Historian batch writes to prevent thread locks.

### Fixed
- Handled edge cases where AI inference vectors crashed the main thread during sensor faults.
- Fixed overlapping widgets during dynamic window resizing.

## [v0.9.0-beta] - 2026-07-15
### Added
- SHAP Explainability Engine.
- AI Operator Assistant recommendations.
- Core Digital Twin Thermodynamic simulation engine.
