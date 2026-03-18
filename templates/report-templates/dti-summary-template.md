# Experiment Summary

## Run Metadata

- Run ID: {{ run_id }}
- Dataset ID: {{ dataset_id }}
- Model Family: {{ model_family }}
- Seed: {{ seed }}

## Metrics

- AUROC: {{ metrics.auroc }}
- AUPRC: {{ metrics.auprc }}
- F1: {{ metrics.f1 }}

## Artifacts

- Model: {{ artifacts.model_path }}
- Metrics: {{ artifacts.metrics_path }}
- Predictions: {{ artifacts.predictions_path }}
