# Optuna + Hydra Integration

## Verified Source

All syntax verified against official Hydra Optuna Sweeper plugin docs:
https://hydra.cc/docs/plugins/optuna_sweeper/

---

## Setup

```bash
pip install hydra-core --upgrade   # requires >= 1.1.0
pip install hydra-optuna-sweeper --upgrade
pip install optuna
```

---

## 1. Enable Optuna Sweeper in Config

Add to your Hydra defaults:

```yaml
# configs/default.yaml (or any config file)
defaults:
  - override hydra/sweeper: optuna
```

Or pass on command line:
```bash
python -m ugtsdti.main hydra/sweeper=optuna --multirun ...
```

---

## 2. Search Space Syntax (Verified from Official Docs)

The `hydra.sweeper.params` block uses Hydra's override grammar.
These are the exact supported syntaxes:

```yaml
hydra:
  sweeper:
    params:
      # choice → CategoricalDistribution
      model.params.teacher_cfg.params.hidden_dim: choice(64, 128, 256)

      # range → IntUniformDistribution
      model.params.teacher_cfg.params.num_layers: range(2, 5)

      # interval → UniformDistribution (float)
      model.params.teacher_cfg.params.dropout: interval(0.1, 0.5)

      # int(interval(...)) → IntUniformDistribution
      trainer.params.batch_size: int(interval(16, 64))

      # tag(log, interval(...)) → LogUniformDistribution (float)
      trainer.params.lr: tag(log, interval(1e-4, 1e-2))

      # tag(log, int(interval(...))) → IntLogUniformDistribution
      # (less common, use for log-scale integer params)
```

**Important:** `tag(log, interval(...))` is the correct syntax for log-scale
float params (e.g., learning rate). NOT `log_uniform` — that doesn't exist
in hydra-optuna-sweeper.

---

## 3. Full Sweep Config Example

```yaml
# configs/sweep/teacher_gnn_sweep.yaml
defaults:
  - override hydra/sweeper: optuna

hydra:
  sweeper:
    sampler:
      _target_: optuna.samplers.TPESampler
      seed: 42
    direction: maximize          # maximize AUROC (single objective)
    n_trials: 50
    n_jobs: 1                    # 1 on Kaggle (single GPU)
    storage: null                # in-memory; use sqlite for persistence
    study_name: teacher_gnn_study

    params:
      model.params.teacher_cfg.params.hidden_dim: choice(64, 128, 256)
      model.params.teacher_cfg.params.num_layers: range(2, 5)
      model.params.teacher_cfg.params.dropout: interval(0.1, 0.5)
      model.params.teacher_cfg.params.heads: choice(2, 4, 8)
      trainer.params.lr: tag(log, interval(1e-4, 1e-2))
      trainer.params.weight_decay: tag(log, interval(1e-5, 1e-3))
      trainer.params.batch_size: choice(16, 32, 64)
```

### Run Sweep

```bash
python -m ugtsdti.main \
    --config-name default \
    --config-dir configs \
    +sweep=teacher_gnn_sweep \
    --multirun \
    model=only_teacher \
    data=tdc_davis \
    trainer.params.epochs=20
```

The `--multirun` flag is required for sweeps. Hydra will launch `n_trials`
sequential runs (or parallel if `n_jobs > 1`).

---

## 4. Objective Function

The function decorated with `@hydra.main()` must return a float.
Optuna maximizes/minimizes this value.

```python
# In ugtsdti/main.py — verify this returns the metric:
@hydra.main(config_path="../configs", config_name="default", version_base=None)
def main(cfg: DictConfig) -> float:
    # ... build components, train ...
    val_metrics = trainer.evaluate(val_loader)
    return val_metrics["auroc"]  # Optuna uses this value
```

If `main()` currently returns `None`, add the return value.
The best params and best value are saved to `optimization_results.yaml`
in the multirun output directory.

---

## 5. Pruning (Stop Bad Trials Early)

Pruning requires the Trainer to report intermediate values to Optuna.
Since `core/trainer.py` is FROZEN, implement pruning via a callback wrapper
or by checking `trial.should_prune()` in a custom training loop.

```yaml
# In sweep config, add pruner:
hydra:
  sweeper:
    sampler:
      _target_: optuna.samplers.TPESampler
      seed: 42
    pruner:
      _target_: optuna.pruners.MedianPruner
      n_startup_trials: 5      # don't prune first 5 trials
      n_warmup_steps: 5        # don't prune first 5 epochs per trial
      interval_steps: 1        # check every epoch
```

For pruning to work, the training loop must call:
```python
import optuna

# Inside epoch loop (if you have access to the trial object):
trial.report(val_auroc, epoch)
if trial.should_prune():
    raise optuna.exceptions.TrialPruned()
```

**Note:** `hydra-optuna-sweeper` passes the trial object via Hydra's callback
mechanism. Check the plugin docs for the exact integration pattern if the
Trainer needs modification.

---

## 6. Persistent Storage (Cross-Session on Kaggle)

By default, Optuna stores trials in memory — lost when session ends.
Use SQLite for persistence across sessions:

```yaml
hydra:
  sweeper:
    storage: "sqlite:////kaggle/working/optuna_study.db"
    study_name: teacher_gnn_study
    load_if_exists: true   # resume existing study
```

After session ends, download `optuna_study.db` (or enable Persistence setting).
Next session: attach the file and the study resumes from where it left off.

```python
# Inspect study outside of Hydra:
import optuna

study = optuna.load_study(
    study_name="teacher_gnn_study",
    storage="sqlite:////kaggle/working/optuna_study.db"
)
print(f"Best AUROC: {study.best_value:.4f}")
print(f"Best params: {study.best_params}")
```

---

## 7. Multi-Objective Optimization (AUROC + CI)

Use `NSGAIISampler` and set `direction` to a list.
Returns a Pareto front instead of a single best trial.

```yaml
hydra:
  sweeper:
    sampler:
      _target_: optuna.samplers.NSGAIISampler
      seed: 42
      population_size: 50
    direction:
      - maximize   # AUROC
      - maximize   # CI
    n_trials: 50
```

```python
# main.py must return tuple for multi-objective:
@hydra.main(...)
def main(cfg) -> tuple:
    # ... train ...
    metrics = trainer.evaluate(val_loader)
    return metrics["auroc"], metrics["ci"]
```

```python
# Inspect Pareto front (from official Optuna docs):
print(f"Pareto front trials: {len(study.best_trials)}")

# Pick trial with highest AUROC from Pareto front
best = max(study.best_trials, key=lambda t: t.values[0])
print(f"Trial #{best.number}: AUROC={best.values[0]:.4f}, CI={best.values[1]:.4f}")
print(f"Params: {best.params}")
```

---

## 8. Search Space Reference for UGTS-DTI

```yaml
# Teacher GNN
model.params.teacher_cfg.params.hidden_dim: choice(64, 128, 256)
model.params.teacher_cfg.params.num_layers: range(2, 5)
model.params.teacher_cfg.params.dropout: interval(0.1, 0.5)
model.params.teacher_cfg.params.heads: choice(2, 4, 8)       # GAT/GATv2
model.params.teacher_cfg.params.k_neighbors: choice(5, 10, 20)

# Student Encoder
model.params.student_cfg.params.drug_hidden_dim: choice(64, 128, 256)
model.params.student_cfg.params.protein_hidden_dim: choice(64, 128, 256)
model.params.student_cfg.params.drug_num_layers: range(2, 5)
model.params.student_cfg.params.dropout: interval(0.1, 0.5)
model.params.student_cfg.params.lora_r: choice(4, 8, 16)

# Fusion
model.params.fusion_cfg.params.gate_hidden: choice(32, 64, 128)
model.params.fusion_cfg.params.mc_samples: choice(5, 10, 20)

# KD Loss
trainer.loss.params.alpha: interval(0.1, 0.9)
trainer.loss.params.temperature: choice(1.0, 2.0, 4.0, 8.0)

# Training
trainer.params.lr: tag(log, interval(1e-4, 1e-2))
trainer.params.weight_decay: tag(log, interval(1e-5, 1e-3))
trainer.params.batch_size: choice(16, 32, 64)
trainer.params.grad_clip: choice(0.5, 1.0, 5.0)
```

---

## 9. Optuna Dashboard (Local Only)

```bash
pip install optuna-dashboard
optuna-dashboard sqlite:///optuna_study.db
# Open: http://localhost:8080
```

Shows trial history, parameter importance, parallel coordinate plots.
Not available on Kaggle (no port forwarding), but useful locally after
downloading the `.db` file.
