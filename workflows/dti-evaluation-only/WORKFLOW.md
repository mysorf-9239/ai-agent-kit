# DTI Evaluation Only Workflow

## Objective

Evaluate an existing trained DTI model without retraining.

## Required Inputs

- `run_manifest`
- `validated_dataset_report`
- `execution_context`

## Steps

1. Validate `run_manifest` exists.
2. Validate model artifact path exists.
3. Run `evaluate-dti-model`.
4. Validate metrics output and predictions output.
5. Emit final workflow completion patch.

## Completion Criteria

- metrics report exists
- predictions file exists
- final state status is `completed`

## Failure Handling

- stop on missing model artifact
- quarantine invalid outputs

## Anti-Patterns

- retraining inside evaluation-only workflow
- skipping run manifest validation
