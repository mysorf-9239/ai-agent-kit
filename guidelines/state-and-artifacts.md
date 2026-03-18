# State And Artifacts

## 1. Purpose

This document defines the canonical relationship between runtime state and generated artifacts.

## 2. State Source Of Truth

Structured state is the source of truth for execution status.
Artifacts are outputs referenced by state.
Reports are derived views.

## 3. Required State Keys

The global state MUST include:
- `schema_version`
- `session`
- `datasets`
- `experiments`
- `artifacts`
- `memory`

Recommended additional keys:
- `features`
- `evaluation`
- `lineage`

## 4. Artifact Contract

Every artifact MUST have:
- `run_id`
- `artifact_type`
- `path`
- `producer`
- `created_at_utc`
- `validation_status`

Example:

    run_id: dti-graphdta-bindingdb-seed-42
    artifact_type: model
    path: artifacts/dti-graphdta-bindingdb-seed-42/model.pt
    producer: train-dti-model
    created_at_utc: 2026-03-18T00:00:00Z
    validation_status: valid

## 5. Run Identity

Every state update and every artifact MUST map to one `run_id`.
One run MUST correspond to one objective, one configuration, and one seed.

## 6. Lineage

Lineage SHOULD be tracked when one artifact is derived from another.

Example lineage:
- validated dataset manifest -> feature matrix
- feature matrix -> model artifact
- model artifact -> evaluation report

## 7. Retention

Completed artifacts MUST be retained until explicit cleanup policy says otherwise.
Failed artifacts MUST be retained or quarantined based on validation status.

## 8. Anti-Patterns

The following patterns are prohibited:
- artifacts with no run id
- state pointing to missing artifacts
- reports used as the only execution source of truth
- overwriting validated artifacts in place

## 9. Review Checklist

State and artifacts are acceptable only if:
- state is authoritative
- artifacts are typed
- run identity is stable
- lineage is traceable where needed
