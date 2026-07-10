# Contributing to DikiliGeothermal SCADA

We welcome contributions to the DikiliGeothermal SCADA and Digital Twin platform! This guide outlines the standard procedures for contributing code, drivers, and documentation.

## 1. Branching Strategy
We use standard Git Flow:
- `main`: Production-ready, certified code. Never commit directly to `main`.
- `develop`: The active integration branch for the next release.
- `feature/<name>`: For new capabilities (e.g., `feature/bacnet-driver`). Branch from `develop`.
- `bugfix/<name>`: For fixing non-critical issues on `develop`.
- `hotfix/<name>`: For emergency fixes. Branch directly from `main` and merge to both `main` and `develop`.

## 2. Testing Requirements
We maintain a **Zero Regression Policy**.
Before opening a Pull Request (PR):
1. Write `pytest` unit tests for your new feature.
2. Run the full regression suite:
   ```bash
   python -m pytest
   ```
3. Your PR will be rejected if test coverage drops or if any tests fail.

## 3. Pull Request Checklist
Ensure your PR meets the following criteria:
- [ ] Code follows PEP 8 standards.
- [ ] Type hints are included for all function signatures.
- [ ] The `walkthrough_*.md` (if applicable) is updated.
- [ ] If changing architecture, the Mermaid diagrams in `docs/diagrams/` are updated.
- [ ] 100% of the regression suite passes.

## 4. Code Review Expectations
All PRs require at least one approving review from a core maintainer. Reviewers will check for:
- Adherence to the `BaseDriver` contract if modifying the DAL.
- Thread-safety (use `threading.RLock()` for internal state mutations).
- No hardcoded secrets (use `SystemConfig` and `APP_ENV`).
