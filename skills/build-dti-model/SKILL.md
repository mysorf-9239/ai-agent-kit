---
name: build-dti-model
description: Build a deterministic DTI model specification from experiment configuration and feature manifest, then emit a model spec plus state patch.
version: 1.0.0
inputs:
  - experiment_config
  - feature_manifest
  - execution_context
outputs:
  - model_spec
  - state_patch
side_effects:
  - writes model spec
  - updates state
---

# Build DTI Model

## When to use this skill

- Use after feature extraction succeeds.
- Use before training when the workflow requires an explicit model spec artifact.
- Do not use when training embeds builder logic and the workflow has no model spec layer.

## What this skill does

This skill validates the requested model family and encoder combination.
This skill emits a model specification artifact for downstream training.

## Inputs

- `experiment_config`: path to experiment config.
- `feature_manifest`: feature manifest from `extract-dti-features`.
- `execution_context`: object containing workspace root and run id.

## Outputs

- `model_spec`: JSON file describing model family, encoders, and dimensions.
- `state_patch`: model build patch.

## Workflow

1. Load `experiment_config`.
2. Load `feature_manifest`.
3. Validate feature manifest run id matches execution context run id.
4. Validate model family and encoder compatibility.
5. Write `model_spec.json`.
6. Emit a model build state patch.

## Best Practices

- model spec must be immutable per run
- all hidden dimensions must be explicit
- family-specific defaults must be expanded before output

## Failure Handling

- unsupported model family -> `unsupported_configuration`
- mismatched run ids -> `validation_error`
- missing feature manifest -> `missing_artifact`

## Examples

### Input

Build a `graphdta` model spec for `dti-graphdta-bindingdb-seed-42`.

### Output

- `artifacts/dti-graphdta-bindingdb-seed-42/model_spec.json`

## Anti-Patterns

- relying on undocumented default dimensions
- building model spec before feature validation
