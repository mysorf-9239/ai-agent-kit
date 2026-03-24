# Checkpoint Save & Resume Across Sessions

## The Session Limit Problem

Kaggle interactive sessions run up to **9 hours** (not 12h — common misconception).
Files in `/kaggle/working/` are **ephemeral by default** — lost when session ends.

Two strategies to persist checkpoints:

**Strategy A — Persistence setting (simplest):**
Right panel → Session options → Persistence → "Variables and Files"
Files in `/kaggle/working/` survive session end and are available next session.

**Strategy B — Upload to Kaggle Dataset (most reliable):**
Push checkpoints to a Kaggle Dataset at end of session. Next session loads
from `/kaggle/input/ugtsdti-weights/`.

Use Strategy A for quick iteration, Strategy B for important checkpoints.

---

## 1. Saving Checkpoints

Ensure `checkpoint_dir` points to `/kaggle/working/`:

```python
"trainer.params.checkpoint_dir=/kaggle/working/checkpoints"
```

For manual saves (if Trainer doesn't support periodic saves):

```python
import torch
import os
from datetime import datetime

def save_checkpoint(model, optimizer, epoch, metrics, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save({
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "metrics": metrics,
        "timestamp": datetime.now().isoformat(),
    }, path)
    print(f"Saved: {path}")

# Save every 5 epochs
if epoch % 5 == 0:
    save_checkpoint(
        model, optimizer, epoch, metrics,
        f"/kaggle/working/checkpoints/epoch_{epoch:03d}.pt"
    )
```

---

## 2. Resuming from Checkpoint

```python
import torch

def load_checkpoint(model, optimizer, path, device="cuda"):
    ckpt = torch.load(path, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    if optimizer is not None:
        optimizer.load_state_dict(ckpt["optimizer_state_dict"])
    print(f"Resumed from epoch {ckpt['epoch']}, metrics: {ckpt['metrics']}")
    return ckpt["epoch"] + 1

# Usage:
ckpt_path = "/kaggle/input/ugtsdti-weights/last_model.pt"
start_epoch = 0
if os.path.exists(ckpt_path):
    start_epoch = load_checkpoint(model, optimizer, ckpt_path)
```

---

## 3. Pushing Checkpoints to Kaggle Dataset (Strategy B)

```python
import subprocess
import json
import os

def push_checkpoints_to_dataset(local_dir, dataset_id, message):
    """
    Push checkpoint files to a Kaggle Dataset for cross-session persistence.
    dataset_id: "<username>/ugtsdti-weights"
    Requires: kaggle CLI installed, kaggle.json credentials set up.
    """
    meta = {
        "title": dataset_id.split("/")[1],
        "id": dataset_id,
        "licenses": [{"name": "other"}]
    }
    with open(os.path.join(local_dir, "dataset-metadata.json"), "w") as f:
        json.dump(meta, f)

    result = subprocess.run([
        "kaggle", "datasets", "version",
        "-p", local_dir,
        "-m", message,
        "--dir-mode", "zip"
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print(f"Pushed to {dataset_id}: {message}")
    else:
        print(f"Push failed:\n{result.stderr}")

# Call at end of training:
push_checkpoints_to_dataset(
    local_dir="/kaggle/working/checkpoints",
    dataset_id="<your-username>/ugtsdti-weights",
    message="Stage 1 teacher pretrained epoch 20"
)
```

---

## 4. Session Time Budget

Session limit is **~9 hours**. Estimated time on T4:

| Task | Time |
|------|------|
| Package install (wheels dataset) | ~1 min |
| Package install (pip, internet on) | ~5 min |
| TDC data download + cache build | ~10 min |
| DD/PP graph construction (DAVIS) | ~5 min |
| Stage 1: Teacher pretrain (20 epochs) | ~30–60 min |
| Stage 2: Student pretrain (20 epochs, ESM-2 t6) | ~45–90 min |
| Stage 3: Joint hybrid (50 epochs) | ~2–3 hours |
| **Total (with pre-built data)** | **~4–5 hours** ✅ |

With pre-built data + wheels: fits comfortably in 9h.

---

## 5. Cross-Session Workflow

```
Session 1 (~5h):
  ├── Install packages (wheels dataset)
  ├── Stage 1: Teacher pretrain (20 epochs)
  ├── Stage 2: Student pretrain (20 epochs)
  └── Push checkpoints → ugtsdti-weights dataset
      OR enable Persistence: Variables and Files

Session 2 (~5h):
  ├── Load checkpoints from /kaggle/input/ugtsdti-weights/
  │   OR from /kaggle/working/ (if persistence was enabled)
  ├── Stage 3: Joint hybrid (50 epochs)
  ├── Run ablations (only_student, only_teacher, hybrid)
  └── Push final checkpoints + results

Session 3 (optional):
  ├── Hyperparameter tuning (see hyperparameter-tuning skill)
  └── Final evaluation on S1/S2/S3/S4
```

---

## 6. Time Guard

Add a time check before starting long stages:

```python
import time

SESSION_START = time.time()
SESSION_LIMIT_HOURS = 8.5  # 30 min buffer before 9h limit

def hours_remaining():
    elapsed = (time.time() - SESSION_START) / 3600
    return SESSION_LIMIT_HOURS - elapsed

# Before Stage 3:
if hours_remaining() < 2.0:
    print(f"WARNING: Only {hours_remaining():.1f}h left — skipping Stage 3")
    push_checkpoints_to_dataset(...)
else:
    # run Stage 3
    ...
```
