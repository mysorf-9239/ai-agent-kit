# Scripts

This directory stores local helper scripts for deterministic demo execution.

Current scripts:
- `run_dti_demo.py`
- `compare_dti_runs.py`

Rules:
- scripts MUST read declared manifests and templates
- scripts MUST write only inside `artifacts/`, `reports/`, and `state/`
- scripts MUST emit deterministic outputs for the same inputs
