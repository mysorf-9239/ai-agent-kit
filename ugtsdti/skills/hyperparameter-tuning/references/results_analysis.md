# Reading Results & Selecting Best Config

## Verified Source

Multi-objective API verified against official Optuna docs:
https://optuna.readthedocs.io/en/stable/tutorial/20_recipes/002_multi_objective.html

---

## 1. From Optuna Study

```python
import optuna
import pandas as pd

study = optuna.load_study(
    study_name="teacher_gnn_study",
    storage="sqlite:///optuna_study.db"
)

# Summary
print(f"Total trials: {len(study.trials)}")
completed = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
pruned = [t for t in study.trials if t.state == optuna.trial.TrialState.PRUNED]
print(f"Completed: {len(completed)}, Pruned: {len(pruned)}")
print(f"Best AUROC: {study.best_value:.4f}")
print(f"Best params: {study.best_params}")

# All trials as DataFrame
df = study.trials_dataframe()
df = df.sort_values("value", ascending=False)
print(df[["number", "value", "params_hidden_dim", "params_lr", "params_dropout"]].head(10))
```

---

## 2. From WandB Runs

```python
import wandb
import pandas as pd

api = wandb.Api()
runs = api.runs("<username>/ugtsdti-sweeps")

records = []
for run in runs:
    if run.state == "finished":
        records.append({
            "run_id": run.id,
            "name": run.name,
            "auroc": run.summary.get("val/auroc"),
            "ci": run.summary.get("val/ci"),
            **run.config
        })

df = pd.DataFrame(records).sort_values("auroc", ascending=False)
print(df.head(10))
```

---

## 3. Parameter Importance

```python
# Requires scikit-learn: pip install scikit-learn
importances = optuna.importance.get_param_importances(study)
for param, importance in sorted(importances.items(), key=lambda x: -x[1]):
    print(f"  {param}: {importance:.3f}")

# Example output:
# lr: 0.412
# hidden_dim: 0.287
# dropout: 0.198
# num_layers: 0.103
```

High importance → tune carefully. Low importance → use default.

---

## 4. Selecting Best Config

### Single-Objective

```python
best = study.best_trial
print(f"Best trial #{best.number}: AUROC = {best.value:.4f}")
for k, v in best.params.items():
    print(f"  {k}: {v}")
```

### Multi-Objective (Pareto Front)

From official Optuna docs — use `study.best_trials` to get Pareto front:

```python
print(f"Pareto front trials: {len(study.best_trials)}")

# Pick trial with highest AUROC from Pareto front
best = max(study.best_trials, key=lambda t: t.values[0])
print(f"Trial #{best.number}: AUROC={best.values[0]:.4f}, CI={best.values[1]:.4f}")
print(f"Params: {best.params}")

# Visualize Pareto front (requires plotly)
# pip install plotly
optuna.visualization.plot_pareto_front(study, target_names=["AUROC", "CI"])
```

### Robustness Check

Don't just pick the single best trial — check stability across top-5:

```python
top5 = df.nlargest(5, "value")  # or "auroc" for WandB df

for param in ["params_hidden_dim", "params_lr", "params_dropout"]:
    vals = top5[param].values
    print(f"{param}: {vals}")
    # If all 5 agree → that value is robust
    # If they disagree → param is not critical, use default
```

---

## 5. Converting Best Params to YAML Config

```python
import yaml

def best_params_to_yaml(best_params: dict, output_path: str):
    """Convert Optuna best params to a Hydra YAML config."""
    config = {
        "name": "gcn_teacher",  # or gatv2_teacher, etc.
        "params": {
            "hidden_dim": best_params.get(
                "model.params.teacher_cfg.params.hidden_dim", 128
            ),
            "num_layers": best_params.get(
                "model.params.teacher_cfg.params.num_layers", 3
            ),
            "dropout": best_params.get(
                "model.params.teacher_cfg.params.dropout", 0.3
            ),
        }
    }
    with open(output_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    print(f"Config saved to {output_path}")

best_params_to_yaml(
    study.best_params,
    "configs/model/teacher/gatv2_tuned.yaml"
)
```

---

## 6. Validation Protocol After Tuning

After selecting best config, validate on all 4 cold-start splits:

```bash
for split in s1 s2 s3 s4; do
    python -m ugtsdti.main \
        model=only_teacher \
        data=tdc_davis_${split} \
        model.params.teacher_cfg.params.hidden_dim=128 \
        model.params.teacher_cfg.params.dropout=0.3 \
        trainer.params.lr=5e-4 \
        trainer.params.epochs=50 \
        trainer.wandb.name=gatv2_tuned_${split}
done
```

Expected pattern after good tuning:
- S1 AUROC > 0.75 (Teacher strong on warm-start)
- S4 AUROC > 0.60 (Teacher weaker on cold-start — expected)
- Hybrid AUROC on S4 > Teacher AUROC on S4 (fusion helps)

---

## 7. Tuning Priority Order

```
1. Teacher GNN (Phase 11)
   Tune: hidden_dim, num_layers, dropout, heads, k_neighbors, lr
   Metric: S1 AUROC (Teacher should be strong on warm-start)

2. Student Encoder (Phase 11)
   Tune: drug_hidden_dim, protein_hidden_dim, drug_num_layers, lora_r
   Metric: S4 AUROC (Student should be strong on cold-start)

3. Fusion + KD Loss (Phase 12)
   Tune: gate_hidden, mc_samples, alpha, temperature
   Metric: S4 AUROC (Hybrid should beat Student alone)

4. Joint Fine-tuning (Phase 13)
   Tune: lr schedule, weight_decay, grad_clip
   Metric: Average AUROC across S1+S4
```
