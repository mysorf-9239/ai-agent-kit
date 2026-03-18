---
name: train-dti-model
description: Train a deterministic DTI model from a validated manifest and fixed experiment configuration, then emit model artifacts and a state patch.
version: 1.0.0
inputs:
  - validated_dataset_report
  - experiment_config
  - feature_manifest
  - model_spec
  - execution_context
outputs:
  - model_artifact
  - run_manifest
  - state_patch
side_effects:
  - writes model artifacts
  - writes run manifest
  - updates state
---

# Train DTI Model

## When to use this skill

- Use after dataset validation succeeds.
- Use when one deterministic DTI training run is requested.
- Do not use for hyperparameter search.
- Do not use when experiment config omits seed.

## What this skill does

This skill validates the experiment configuration, resolves the model family, runs one deterministic training job, and emits a run manifest plus state patch.

## Inputs

- `validated_dataset_report`: output from `validate-dti-dataset`.
- `experiment_config`: path to an experiment template instance.
- `feature_manifest`: output from `extract-dti-features`.
- `model_spec`: output from `build-dti-model`.
- `execution_context`: object containing workspace root and run id.

## Outputs

- `model_artifact`: path to persisted trained model.
- `run_manifest`: path to structured run manifest.
- `state_patch`: object conforming to state patch template.

## Workflow

1. Validate `validated_dataset_report.status == "completed"`.
2. Load `experiment_config`.
3. Validate seed, model family, output directory, and required hyperparameters.
4. Load `feature_manifest` and `model_spec`.
5. Validate both artifacts match `run_id`.
6. Resolve model builder from the declared model family.
7. Create deterministic run directory from `run_id`.
8. Train using fixed seed and declared hyperparameters only.
9. Persist model artifact and optimizer state.
10. Write `run_manifest.json`.
11. Emit a training-completed state patch.
12. Stop on validation failure or determinism violation.

## Best Practices

- one config produces one run id
- one run id produces one output directory
- do not mutate dataset splits during training
- do not change seed during retry unless workflow explicitly permits it

## Validation

- seed is mandatory
- output directory is mandatory
- model family must be supported
- run manifest must exist before return

## Failure Handling

- Missing seed -> `validation_error`
- Unsupported model family -> `unsupported_configuration`
- Write failure -> `execution_error`
- Conflicting run directory -> `state_conflict`

## Examples

### Input

Train `graphdta` on validated BindingDB manifest with seed `42`.

### Output

- `artifacts/dti-graphdta-bindingdb-seed-42/model.pt`
- `artifacts/dti-graphdta-bindingdb-seed-42/run_manifest.json`

## Anti-Patterns

- training before dataset validation
- mutating config during execution
- writing outputs to non-deterministic paths
