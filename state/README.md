# State

This directory stores persisted runtime state and state schemas.

Files:
- `state-schema.yaml`
- `state.json`

Rules:
- `state.json` is the runtime source of truth
- schemas MUST be versioned
- state patches MUST align with `templates/state-patches/`
