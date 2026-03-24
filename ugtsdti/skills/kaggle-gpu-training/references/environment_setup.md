# Kaggle Environment Setup

## Verified Facts (from official docs + community, 2025)

- GPU quota: **~30 hours/week** (resets weekly), shared across T4 and P100
- Session limit: **up to 9 hours** per interactive session (not 12h — common misconception)
- Filesystem: `/kaggle/input/` (read-only), `/kaggle/working/` (read-write, ~20 GB)
- Internet: **OFF by default** — must enable in Settings before running
- Persistence: **NOT automatic** — files in `/kaggle/working/` are lost when session ends
  unless you enable "Persistence: Variables and Files" in Session Options

---

## Filesystem Layout

```
/kaggle/
├── input/                    # READ-ONLY — all attached datasets appear here
│   ├── ugtsdti-code/         # your uploaded code dataset
│   │   └── ugtsdti/          # package source
│   ├── ugtsdti-data/         # TDC cache, pre-built DD/PP graphs
│   │   ├── tdc_cache/
│   │   └── graphs/
│   └── ugtsdti-weights/      # pretrained weights (ESM-2, teacher checkpoints)
│       └── esm2_t6_8M_UR50D/
└── working/                  # READ-WRITE — ~20 GB, ephemeral by default
    ├── outputs/              # Hydra run outputs
    ├── checkpoints/          # model checkpoints
    └── cache/                # TDC cache if building fresh
```

**Critical:** `/kaggle/working/` is ephemeral. Files are lost when session ends
unless you enable persistence (see below) or download them manually.

---

## Persistence Setting (IMPORTANT — often missed)

By default, `/kaggle/working/` is wiped when session ends. To keep files:

1. Right panel → **Session options** → **Persistence**
2. Select **"Variables and Files"** (keeps both in-memory variables and disk files)
   or **"Files Only"** (keeps disk files only)

This is the correct way to persist checkpoints between sessions without
downloading/re-uploading. Note: this uses Kaggle's storage quota.

---

## GPU Types Available

| GPU | VRAM | Notes |
|-----|------|-------|
| T4 | 16 GB | Most common, CUDA 11.8+, Tensor Cores for FP16 |
| T4 ×2 | 32 GB | Available in some notebooks, use `DataParallel` |
| P100 | 16 GB | Faster FP32, no Tensor Cores (AMP less effective) |

Check GPU type at runtime:
```python
import torch
print(torch.cuda.get_device_name(0))
# "Tesla T4" or "Tesla P100-PCIE-16GB"
print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
```

---

## Internet Access

Internet is **OFF by default**. Enable in notebook settings:
`Settings (right panel) → Internet → On`

**Must be done BEFORE running the notebook.** Cannot change mid-run.

Required for:
- `pip install` packages not pre-installed
- WandB online logging
- Downloading HuggingFace models (ESM-2)
- PyTDC data download

**Important:** Kaggle User Secrets (for WandB API key) also require internet ON.
If internet is off, `UserSecretsClient` will fail.

---

## Package Installation

### Option A: pip install at runtime (requires internet ON)

```python
# Cell 1 — run once at session start
import subprocess

packages = [
    "torch-geometric",
    "torch-scatter",
    "torch-sparse",
    "rdkit",
    "PyTDC",
    "wandb",
    "hydra-core",
    "hydra-optuna-sweeper",
    "omegaconf",
    "loguru",
    "peft",
    "optuna",
]
for pkg in packages:
    subprocess.run(["pip", "install", "-q", pkg], check=True)
```

### Option B: Pre-baked wheels as Kaggle Dataset (works with internet OFF)

This is the correct approach for competitions with internet disabled, or to
speed up repeated sessions.

**Local — download wheels:**
```bash
pip download torch-geometric torch-scatter torch-sparse rdkit PyTDC \
    wandb hydra-core hydra-optuna-sweeper omegaconf loguru peft optuna \
    -d ./kaggle_wheels/ \
    --platform manylinux2014_x86_64 \
    --python-version 3.10
```

**Upload as Kaggle Dataset** (see `dataset_upload.md`).

**In notebook — install from local wheels:**
```python
import subprocess
subprocess.run([
    "pip", "install", "-q", "--no-index",
    "--find-links=/kaggle/input/ugtsdti-wheels/",
    "torch-geometric", "rdkit", "PyTDC", "wandb",
    "hydra-core", "hydra-optuna-sweeper", "peft", "optuna"
], check=True)
```

Source: [Kaggle Setup Guide](https://isaac-flath.github.io/fastblog/kaggle/getting%20started/2021/03/25/KaggleSetupGuide.html)

---

## Installing UGTS-DTI Package

```python
import subprocess
subprocess.run(
    ["pip", "install", "-e", "/kaggle/input/ugtsdti-code/"],
    check=True
)
import ugtsdti
print("ugtsdti installed:", ugtsdti.__version__)
```

---

## Environment Variables

```python
import os

os.environ["UGTSDTI_DATA_DIR"] = "/kaggle/input/ugtsdti-data"
os.environ["UGTSDTI_CACHE_DIR"] = "/kaggle/working/cache"

# HuggingFace — point to pre-downloaded weights if internet is off
os.environ["TRANSFORMERS_CACHE"] = "/kaggle/input/ugtsdti-weights/hf_cache"
os.environ["HF_DATASETS_OFFLINE"] = "1"
```

---

## Notebook Cell Order Template

```python
# Cell 1: Enable internet in Settings FIRST (UI action, not code)

# Cell 2: Install packages
# (Option A or B above)

# Cell 3: Install ugtsdti
import subprocess
subprocess.run(["pip", "install", "-e", "/kaggle/input/ugtsdti-code/"], check=True)

# Cell 4: Set env vars
import os
os.environ["UGTSDTI_CACHE_DIR"] = "/kaggle/working/cache"
# ... WandB secret (see config_and_wandb.md)

# Cell 5: Verify GPU
import torch
assert torch.cuda.is_available(), "No GPU — check Settings > Accelerator"
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

# Cell 6: Run training (see config_and_wandb.md)

# Cell 7: Save/push checkpoints (see checkpoint_resume.md)
```
