---
name: extract-dti-features
description: Extract deterministic drug and target features from a validated DTI dataset manifest and emit feature manifests plus a state patch.
version: 1.0.0
inputs:
  - validated_dataset_report
  - experiment_config
  - execution_context
outputs:
  - feature_manifest
  - state_patch
side_effects:
  - writes feature manifest
  - updates state
---

# Extract DTI Features

## When to use this skill

- Use after dataset validation succeeds.
- Use before model build or training when the model requires explicit feature artifacts.
- Do not use when the workflow consumes raw representations directly and no feature manifest is required.

## What this skill does

This skill resolves the required drug and target encoders from the experiment configuration.
This skill emits a deterministic feature manifest for downstream model build and training.

## Inputs

- `validated_dataset_report`: structured dataset validation output.
- `experiment_config`: path to experiment config.
- `execution_context`: object containing workspace root and run id.

## Outputs

- `feature_manifest`: JSON file describing extracted or declared features.
- `state_patch`: feature extraction patch.

## Workflow

1. Load `validated_dataset_report`.
2. Validate dataset status is `completed`.
3. Load `experiment_config`.
4. Resolve required drug and target encoders.
5. Validate encoder compatibility with dataset representations.
6. Write `feature_manifest.json`.
7. Emit a feature extraction state patch.

## Best Practices

- feature extraction must be deterministic
- encoder names must match experiment config exactly
- feature manifest must record source dataset and run id

## Failure Handling

- incompatible encoder -> `unsupported_configuration`
- missing validated dataset report -> `missing_artifact`
- missing encoder settings -> `validation_error`

## Examples

### Input

Extract features for `graphdta` on validated BindingDB manifest.

### Output

- `artifacts/dti-graphdta-bindingdb-seed-42/feature_manifest.json`

## Anti-Patterns

- inferring encoders from model family without config validation
- writing feature outputs without run id
