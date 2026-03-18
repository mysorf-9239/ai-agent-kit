# DTI Run Comparison Workflow

## Objective

Compare two or more completed DTI runs and emit a structured comparison result plus optional summary outputs.

## Required Inputs

- `metrics_reports`
- `comparison_config`
- `execution_context`

## Steps

1. Validate all metrics reports exist.
2. Validate all runs are completed and schema-compatible.
3. Run `compare-dti-runs`.
4. Validate comparison output.
5. Emit final workflow completion patch.

## Completion Criteria

- comparison report exists
- comparison ranking is non-empty
- final workflow status is `completed`

## Failure Handling

- stop on incompatible schemas
- stop on empty metrics input list
- quarantine invalid comparison outputs

## Anti-Patterns

- comparing failed runs with completed runs
- ranking on an undeclared primary metric
