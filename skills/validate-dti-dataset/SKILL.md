---
name: validate-dti-dataset
description: Validate a DTI dataset manifest, reject unsupported schemas, and emit a validated dataset report plus state patch.
version: 1.0.0
inputs:
  - dataset_manifest
  - execution_context
outputs:
  - validated_dataset_report
  - state_patch
side_effects:
  - writes validation report
  - updates state
---

# Validate DTI Dataset

## When to use this skill

- Use when a workflow needs to confirm that a DTI dataset manifest is structurally valid before feature extraction or training.
- Use when the task references BindingDB, Davis, KIBA, or another benchmark manifest already present in workspace.
- Do not use when the task is only to summarize prior results.
- Do not use when raw dataset ingestion has not yet produced a manifest.

## What this skill does

This skill validates one dataset manifest.
This skill checks schema version, required keys, split integrity, file existence, and representation support.
This skill emits a structured validation report and a state patch.

## Inputs

- `dataset_manifest`: path to a JSON or YAML manifest file.
- `execution_context`: object containing workspace root, writable output directory, and run id.

## Outputs

- `validated_dataset_report`: path to a JSON report conforming to `templates/output-schemas/dataset-validation-output.yaml`.
- `state_patch`: object conforming to `templates/state-patches/dataset-validation-state-patch.yaml`.

## Workflow

1. Load `dataset_manifest`.
2. Validate manifest schema version against supported versions in `references/dti-dataset-spec.md`.
3. Validate required top-level keys: `dataset_id`, `task_type`, `drug_representation`, `target_representation`, `splits`.
4. Validate `task_type == "drug-target-interaction"`.
5. Validate supported representations.
6. Validate all declared split files exist.
7. Validate train, validation, and test splits are non-empty.
8. Write `validated_dataset_report` to the run report directory.
9. Emit a state patch that marks dataset validation completed.
10. Stop immediately on first critical validation failure.

## Best Practices

- Reject unsupported schema versions.
- Reject manifests with implicit paths.
- Reject manifests that omit split strategy.
- Do not infer missing split files.
- Keep validation failure messages short and typed.

## Validation

- schema validation is mandatory
- file existence validation is mandatory
- split non-empty validation is mandatory
- representation validation is mandatory

## Failure Handling

- On missing manifest: return `missing_artifact`.
- On unsupported schema: return `schema_mismatch`.
- On unsupported representation: return `unsupported_configuration`.
- On missing split file: return `missing_artifact`.
- On empty split: return `validation_error`.

## Examples

### Input

Validate `manifests/bindingdb/bindingdb_v1.yaml` for run `dti-graphdta-bindingdb-seed-42`.

### Output

- `reports/dti-graphdta-bindingdb-seed-42/dataset_validation.json`
- state patch moving dataset status from `raw` to `validated`

## Anti-Patterns

- continuing after split file absence
- inferring task type from filename
- accepting a manifest with missing schema version
