# WandB Sweeps

## Verified Source

All config syntax verified against official WandB Sweeps docs:
https://docs.wandb.ai/guides/sweeps/define-sweep-configuration

---

## Overview

WandB Sweeps is cloud-managed hyperparameter search. Unlike Optuna (local),
Sweeps coordinates multiple agents — useful for parallel Kaggle notebooks.

Initialize sweep once → start agents in multiple notebooks → WandB assigns
trials to agents without duplication.

---

## 1. Sweep Config (YAML format)

```yaml
# configs/sweep/wandb_teacher_sweep.yaml
program: scripts/run_sweep_agent.py
name: teacher-gnn-sweep
method: bayes          # bayes | random | grid
metric:
  name: val/auroc
  goal: maximize

# Early termination (Hyperband)
early_terminate:
  type: hyperband
  min_iter: 5          # minimum epochs before pruning
  eta: 3               # bracket multiplier

parameters:
  hidden_dim:
    values: [64, 128, 256]
  num_layers:
    min: 2
    max: 4
  dropout:
    min: 0.1
    max: 0.5
  lr:
    distribution: log_uniform_values
    min: 0.0001
    max: 0.01
  weight_decay:
    distribution: log_uniform_values
    min: 0.00001
    max: 0.001
  batch_size:
    values: [16, 32, 64]
```

**Verified distribution names** (from official docs):
- `uniform` — float, uniform between min/max
- `log_uniform_values` — float, log-uniform (use for lr, weight_decay)
- `int_uniform` — integer, uniform between min/max
- `q_log_uniform_values` — quantized log-uniform (use for batch_size)
- `values` — categorical list
- `value` — fixed value (single value, not a list)

---

## 2. Sweep Agent Wrapper Script

WandB Sweeps calls `program` with hyperparameters available via `wandb.config`.
Create a thin wrapper that translates WandB config to Hydra overrides:

```python
# scripts/run_sweep_agent.py
import wandb
import subprocess
import sys


def main():
    with wandb.init() as run:
        cfg = run.config

        overrides = [
            f"model.params.teacher_cfg.params.hidden_dim={cfg.hidden_dim}",
            f"model.params.teacher_cfg.params.num_layers={cfg.num_layers}",
            f"model.params.teacher_cfg.params.dropout={cfg.dropout}",
            f"trainer.params.lr={cfg.lr}",
            f"trainer.params.weight_decay={cfg.weight_decay}",
            f"trainer.params.batch_size={cfg.batch_size}",
            f"trainer.params.epochs=20",
            "hydra.run.dir=/kaggle/working/outputs/sweep/${now:%H-%M-%S}",
        ]

        cmd = (
            ["python", "-m", "ugtsdti.main", "model=only_teacher", "data=tdc_davis"]
            + overrides
        )
        result = subprocess.run(cmd)
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
```

---

## 3. Initialize and Run Sweep

### Initialize (run once — creates sweep ID)

```python
import wandb

sweep_id = wandb.sweep(
    sweep="configs/sweep/wandb_teacher_sweep.yaml",
    project="ugtsdti-sweeps"
)
print(f"Sweep ID: {sweep_id}")
# e.g. "abc123xyz" — save this for starting agents
```

Or via CLI:
```bash
wandb sweep configs/sweep/wandb_teacher_sweep.yaml --project ugtsdti-sweeps
# Output: wandb: Created sweep with ID: abc123xyz
# wandb: View sweep at: https://wandb.ai/<username>/ugtsdti-sweeps/sweeps/abc123xyz
```

### Start Agent (run in each Kaggle notebook)

```python
import wandb

SWEEP_ID = "<username>/ugtsdti-sweeps/<sweep-id>"
wandb.agent(SWEEP_ID, count=10)  # run 10 trials per agent
```

Or via CLI:
```bash
wandb agent <username>/ugtsdti-sweeps/<sweep-id>
```

---

## 4. Parallel Agents on Multiple Kaggle Notebooks

Each Kaggle notebook runs one agent. Start multiple notebooks simultaneously:

```
Notebook 1: wandb.agent(SWEEP_ID, count=10)  → trials 1-10
Notebook 2: wandb.agent(SWEEP_ID, count=10)  → trials 11-20
Notebook 3: wandb.agent(SWEEP_ID, count=10)  → trials 21-30
```

WandB coordinates — no duplicate trials. Total: 30 trials across 3 notebooks.

**Setup in each notebook:**
```python
from kaggle_secrets import UserSecretsClient
import os
import wandb

os.environ["WANDB_API_KEY"] = UserSecretsClient().get_secret("WANDB_API_KEY")
wandb.login()

SWEEP_ID = "<username>/ugtsdti-sweeps/<sweep-id>"
wandb.agent(SWEEP_ID, count=10)
```

---

## 5. Sweep Methods Comparison

| Method | Best for | Trials needed |
|--------|----------|---------------|
| `random` | Quick exploration, many params | 20–50 |
| `bayes` | Efficient search, few params (≤10) | 30–100 |
| `grid` | Exhaustive, small discrete space | N^k |

**Recommended workflow:**
1. `random` with n=20 → identify promising regions
2. `bayes` with n=50 → refine within promising regions

---

## 6. Sweep Visualization in WandB Dashboard

After running trials, go to:
`wandb.ai/<username>/ugtsdti-sweeps/sweeps/<sweep-id>`

Key views:
- **Parallel Coordinates Plot** — which param combinations → high AUROC
- **Parameter Importance** — which params matter most
- **Scatter Plot** — AUROC vs individual params
- **Run Table** — sort by metric, filter by param ranges
