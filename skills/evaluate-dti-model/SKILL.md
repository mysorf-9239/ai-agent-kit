---
name: evaluate-dti-model
description: Evaluate a trained DTI model on declared validation and test splits, then emit structured metrics, predictions, and a state patch.
version: 1.0.0
inputs:
  - run_manifest
  - validated_dataset_report
  - execution_context
outputs:
  - metrics_report
  - predictions_file
  - state_patch
side_effects:
  - writes metrics
  - writes predictions
  - updates state
---

# Evaluate DTI Model

## When to use this skill

- Use after `train-dti-model` completes.
- Use when the task requires benchmark metrics, prediction export, or evaluation summary generation.
- Do not use if the model artifact is missing.

## What this skill does

This skill loads the trained model, evaluates it on declared splits, writes machine-checkable metrics, exports predictions, and emits an evaluation state patch.

## Workflow

1. Load `run_manifest`.
2. Validate model artifact path exists.
3. Load validated dataset report.
4. Resolve evaluation metrics from experiment and task type.
5. Run deterministic evaluation.
6. Write `metrics.json`.
7. Write `predictions.csv`.
8. Emit evaluation-completed state patch.

## Best Practices

- primary metric must be explicit
- metric ranges must be validated
- predictions file must include record ids
- evaluation must not mutate the model artifact

## Failure Handling

- missing model artifact -> `missing_artifact`
- invalid metric range -> `validation_error`
- unsupported task type -> `unsupported_configuration`

## Examples

### Input

Evaluate `dti-graphdta-bindingdb-seed-42` on validation and test splits.

### Output

- `reports/dti-graphdta-bindingdb-seed-42/metrics.json`
- `reports/dti-graphdta-bindingdb-seed-42/predictions.csv`

## Anti-Patterns

- generating prose-only evaluation
- omitting `run_id` from metrics output
- skipping prediction export when schema requires it
