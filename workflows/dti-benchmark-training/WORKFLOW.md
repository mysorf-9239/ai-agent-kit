# DTI Benchmark Training Workflow

## Objective

Train and evaluate one deterministic DTI benchmark run from a validated manifest and fixed experiment configuration.

## Required Inputs

- `dataset_manifest`
- `experiment_config`
- `execution_context`

## Steps

1. Run `validate-dti-dataset`.
2. Validate dataset report status.
3. Run `extract-dti-features`.
4. Validate feature manifest.
5. Run `build-dti-model`.
6. Validate model spec.
7. Run `train-dti-model`.
8. Validate run manifest and model artifact.
9. Run `evaluate-dti-model`.
10. Validate metrics output and predictions output.
11. Run `export-experiment-report`.
12. Validate summary report.
13. Emit final workflow completion patch.

## Branch Logic

- If `experiment_config.model.family == "graphdta"`, use graph path.
- If `experiment_config.model.family == "deepdta"`, use sequence path.
- Else stop with `unsupported_configuration`.

## Completion Criteria

- model artifact exists
- metrics report exists
- predictions file exists
- final state status is `completed`

## Failure Handling

- stop on validation failure
- retry once on `resource_exhausted` only if training contract allows batch-size reduction
- quarantine invalid outputs

## Anti-Patterns

- skipping dataset validation
- changing seed during execution
- continuing after missing model artifact
