# Hydra Config Overrides & WandB on Kaggle

## Running UGTS-DTI on Kaggle

Entry point: `python -m ugtsdti.main` with Hydra overrides.
On Kaggle, run via `subprocess` from a notebook cell.

---

## 1. Basic Training Invocation

```python
import subprocess

result = subprocess.run([
    "python", "-m", "ugtsdti.main",
    "model=only_teacher",
    "data=tdc_davis",
    "trainer.params.epochs=20",
    "trainer.params.batch_size=32",
    "trainer.params.device=cuda",
    # Hydra output dir — must point to /kaggle/working/
    "hydra.run.dir=/kaggle/working/outputs/${now:%Y-%m-%d}/${now:%H-%M-%S}",
    "data.params.cache_dir=/kaggle/working/cache",
], check=True)
# Use capture_output=False (default) so stdout appears in real-time in notebook
```

---

## 2. Hydra Output Directory

By default Hydra writes to `outputs/` relative to CWD. On Kaggle, CWD is
`/kaggle/working/` so this works, but be explicit to avoid surprises:

```python
"hydra.run.dir=/kaggle/working/outputs/${now:%Y-%m-%d}/${now:%H-%M-%S}"
```

Creates timestamped dirs like:
```
/kaggle/working/outputs/2026-03-24/14-30-00/
├── .hydra/config.yaml
├── train.log
└── checkpoints/best_model.pt
```

---

## 3. WandB via Kaggle Secrets

Kaggle Secrets are stored under **Add-ons → Secrets** in the notebook editor
(not in account settings — this is a per-notebook setting).

### Setup (one-time per notebook)

1. Notebook editor → **Add-ons** → **Secrets**
2. Click **Add a new secret**
3. Name: `WANDB_API_KEY`, Value: your WandB API key from wandb.ai/settings
4. Toggle **"Attach to notebook"** ON

**Note:** Secrets require internet ON. If internet is off, `UserSecretsClient`
will raise an error. Source: [WandB community](https://community.wandb.ai/t/clarity-on-wandb-offline/429)

### In Notebook

```python
from kaggle_secrets import UserSecretsClient
import os
import wandb

# Fetch secret (requires internet ON)
secrets = UserSecretsClient()
os.environ["WANDB_API_KEY"] = secrets.get_secret("WANDB_API_KEY")
wandb.login()
```

### WandB Config Override

```python
subprocess.run([
    "python", "-m", "ugtsdti.main",
    "model=hybrid_baseline",
    "data=tdc_davis",
    "trainer.wandb.project=ugtsdti-kaggle",
    "trainer.wandb.name=gatv2-teacher-stage1",
    "hydra.run.dir=/kaggle/working/outputs/${now:%Y-%m-%d}/${now:%H-%M-%S}",
], check=True)
```

### Offline Mode (internet OFF)

```python
import os
os.environ["WANDB_MODE"] = "offline"
# Logs saved to /kaggle/working/wandb/
# Sync later locally: wandb sync /path/to/wandb/run-*
```

---

## 4. Multi-Stage Training

Run all 3 stages in one 9-hour session (check time budget first):

```python
import subprocess
import time

SESSION_START = time.time()

def hours_elapsed():
    return (time.time() - SESSION_START) / 3600

BASE = ["python", "-m", "ugtsdti.main"]
HYDRA = "hydra.run.dir=/kaggle/working/outputs/${now:%Y-%m-%d}/${now:%H-%M-%S}"

# Stage 1: Teacher pretrain
print(f"=== Stage 1 (elapsed: {hours_elapsed():.1f}h) ===")
subprocess.run(BASE + [
    "model=only_teacher", "data=tdc_davis",
    "trainer.params.epochs=20", "trainer.params.batch_size=32",
    "trainer.params.checkpoint_dir=/kaggle/working/checkpoints/stage1",
    HYDRA,
], check=True)

# Stage 2: Student pretrain
print(f"=== Stage 2 (elapsed: {hours_elapsed():.1f}h) ===")
subprocess.run(BASE + [
    "model=only_student", "data=tdc_davis",
    "trainer.params.epochs=20", "trainer.params.batch_size=32",
    "trainer.params.checkpoint_dir=/kaggle/working/checkpoints/stage2",
    HYDRA,
], check=True)

# Stage 3: Joint hybrid (only if enough time remains)
remaining = 9.0 - hours_elapsed()
if remaining > 2.0:
    print(f"=== Stage 3 (elapsed: {hours_elapsed():.1f}h, {remaining:.1f}h left) ===")
    subprocess.run(BASE + [
        "model=hybrid_baseline", "data=tdc_davis",
        "trainer.params.epochs=50", "trainer.params.batch_size=32",
        "trainer.params.checkpoint_dir=/kaggle/working/checkpoints/stage3",
        "trainer.params.teacher_ckpt=/kaggle/working/checkpoints/stage1/best_model.pt",
        "trainer.params.student_ckpt=/kaggle/working/checkpoints/stage2/best_model.pt",
        HYDRA,
    ], check=True)
else:
    print(f"Skipping Stage 3 — only {remaining:.1f}h remaining")
```

---

## 5. Common Config Mistakes on Kaggle

| Mistake | Symptom | Fix |
|---------|---------|-----|
| No `hydra.run.dir` override | Hydra writes to `/` → `PermissionError` | Add `hydra.run.dir=/kaggle/working/...` |
| WandB without internet | `ConnectionError` or `UserSecretsClient` fails | Set `WANDB_MODE=offline` or enable internet |
| HuggingFace downloads ESM-2 | Slow / fails if internet off | Pre-upload weights, set `TRANSFORMERS_CACHE` |
| TDC downloads data | Slow / fails if internet off | Pre-build cache, set `cache_dir` |
| `batch_size=128` on T4 with ESM-2 | OOM | Use `batch_size=32` + AMP (see `gpu_memory.md`) |
| Forgot to enable internet | `pip install` fails silently | Enable internet in Settings before running |
