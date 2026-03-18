# DTI Orchestrator

## Purpose

This orchestrator resolves the correct DTI execution path from task inputs, state, and available artifacts.

## Required Inputs

- `dataset_manifest`
- `experiment_config`
- `execution_context`
- `state/state.json`

## Decision Flow

1. Load `state/state.json`.
2. Run `plan-dti-run`.
3. If selected workflow is `dti-benchmark-training`, run:
   - `validate-dti-dataset`
   - `train-dti-model`
   - `evaluate-dti-model`
4. If selected workflow is `dti-evaluation-only`, run:
   - `evaluate-dti-model`
5. Validate final outputs.
6. Emit final workflow result.

## Preconditions

- dataset manifest exists when training is requested
- run manifest exists when evaluation-only mode is requested
- state schema version is supported

## Failure Rules

- stop on unsupported workflow
- stop on incompatible state
- stop on missing required artifacts
- quarantine invalid outputs

## Anti-Patterns

- selecting workflow from conversational memory only
- bypassing `plan-dti-run`
- evaluating without model artifact validation
