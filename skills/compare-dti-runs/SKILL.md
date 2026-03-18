---
name: compare-dti-runs
description: Compare two or more validated DTI run outputs and emit a structured comparison report plus state patch.
version: 1.0.0
inputs:
  - metrics_reports
  - comparison_config
  - execution_context
outputs:
  - comparison_report
  - state_patch
side_effects:
  - writes comparison artifact
  - updates state
---

# Compare DTI Runs

## When to use this skill

- Use when two or more completed DTI runs must be compared.
- Use after all candidate runs have validated metrics outputs.
- Do not use when any run is incomplete.

## What this skill does

This skill compares structured metrics across runs.
This skill emits one machine-checkable comparison output.
This skill may also emit a markdown summary when configured.

## Inputs

- `metrics_reports`: list of metrics output files.
- `comparison_config`: object defining primary metric and ranking direction.
- `execution_context`: object containing workspace root and comparison id.

## Outputs

- `comparison_report`: JSON file conforming to `templates/output-schemas/dti-run-comparison-output.yaml`
- `state_patch`: comparison state patch

## Workflow

1. Load all metrics reports.
2. Validate all reports use the same task type and metric schema version.
3. Validate `comparison_config.primary_metric`.
4. Rank runs by configured primary metric.
5. Write structured comparison output.
6. Emit state patch.

## Best Practices

- compare only runs with compatible task type
- compare only runs with compatible metric schema
- ranking direction must be explicit

## Failure Handling

- incompatible schema versions -> `schema_mismatch`
- missing primary metric -> `validation_error`
- empty input list -> `invalid_input`

## Examples

### Input

Compare three BindingDB DTI runs by `auroc`.

### Output

- `reports/comparisons/bindingdb-auroc-comparison.json`

## Anti-Patterns

- comparing metrics from incompatible tasks
- mixing incomplete and complete runs
