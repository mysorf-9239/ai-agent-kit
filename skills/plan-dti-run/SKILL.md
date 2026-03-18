---
name: plan-dti-run
description: Resolve the correct DTI workflow and run identifier from a dataset manifest, experiment configuration, and execution context.
version: 1.0.0
inputs:
  - dataset_manifest
  - experiment_config
  - execution_context
outputs:
  - run_plan
  - state_patch
side_effects:
  - writes run plan
  - updates state
---

# Plan DTI Run

## When to use this skill

- Use before starting a DTI workflow.
- Use when the agent must choose between training-plus-evaluation and evaluation-only paths.
- Do not use when the workflow is already fixed and the run id already exists.

## What this skill does

This skill inspects the dataset manifest, experiment configuration, and execution context.
This skill derives a deterministic `run_id`.
This skill selects the correct workflow and emits a run plan.

## Inputs

- `dataset_manifest`: path to dataset manifest.
- `experiment_config`: path to experiment config.
- `execution_context`: object containing workspace root and requested mode.

## Outputs

- `run_plan`: JSON file conforming to `templates/output-schemas/dti-run-plan-output.yaml`.
- `state_patch`: state patch that registers the planned run.

## Workflow

1. Load `dataset_manifest`.
2. Load `experiment_config`.
3. Validate `task_type == "drug-target-interaction"`.
4. Derive deterministic `run_id` from task, model, dataset, and seed.
5. If `execution_context.mode == "evaluation_only"`, select `dti-evaluation-only`.
6. Else select `dti-benchmark-training`.
7. Write `run_plan.json`.
8. Emit a planning state patch.

## Best Practices

- one config maps to one run id
- workflow choice must be explicit
- planning must not create training artifacts

## Failure Handling

- unsupported task type -> `unsupported_configuration`
- missing seed -> `validation_error`
- missing mode -> default to `train_and_evaluate`

## Examples

### Input

Plan a BindingDB `graphdta` run with seed `42`.

### Output

- `artifacts/dti-graphdta-bindingdb-seed-42/run_plan.json`
- state patch registering the run under `experiments.planned`

## Anti-Patterns

- choosing workflow from memory only
- deriving run id from current timestamp
