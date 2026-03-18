---
name: export-experiment-report
description: Export a human-readable experiment summary from validated machine outputs for one DTI run.
version: 1.0.0
inputs:
  - run_manifest
  - metrics_report
  - execution_context
outputs:
  - summary_report
  - state_patch
side_effects:
  - writes markdown summary
  - updates state
---

# Export Experiment Report

## When to use this skill

- Use after evaluation completes.
- Use when a workflow must generate a portable markdown summary for one run.
- Do not use before metrics are validated.

## What this skill does

This skill transforms structured run outputs into a concise markdown report.
This skill does not create new scientific facts.
This skill only renders validated state and artifact data.

## Inputs

- `run_manifest`: structured run manifest.
- `metrics_report`: structured metrics output.
- `execution_context`: object containing workspace root and run id.

## Outputs

- `summary_report`: markdown file at `reports/<run_id>/summary.md`
- `state_patch`: report-export patch

## Workflow

1. Load `run_manifest`.
2. Load `metrics_report`.
3. Validate both inputs share the same `run_id`.
4. Validate metrics schema and required fields.
5. Render summary markdown from `templates/report-templates/dti-summary-template.md`.
6. Write `summary.md`.
7. Emit a report-export state patch.

## Best Practices

- report facts must come from structured inputs only
- report headings must remain stable
- report must include run id, dataset id, model family, seed, and primary metrics

## Failure Handling

- missing metrics report -> `missing_artifact`
- mismatched run ids -> `validation_error`
- invalid metrics schema -> `validation_error`

## Examples

### Input

Export summary for `dti-graphdta-bindingdb-seed-42`.

### Output

- `reports/dti-graphdta-bindingdb-seed-42/summary.md`

## Anti-Patterns

- inventing interpretations not present in metrics
- generating summary before evaluation completes
