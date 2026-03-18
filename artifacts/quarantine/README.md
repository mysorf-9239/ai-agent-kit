# Quarantine

This directory stores suspect or invalid artifacts that MUST NOT be consumed by downstream workflows.

Rules:
- quarantined artifacts must keep original run id
- quarantine reason must be stored alongside the artifact
- downstream workflows must reject quarantined outputs
