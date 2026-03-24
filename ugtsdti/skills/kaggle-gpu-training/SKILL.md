---
name: kaggle-gpu-training
description: >
  How to train UGTS-DTI models on Kaggle Notebooks using free GPU (T4/P100).
  Covers filesystem layout, uploading datasets/weights as Kaggle Datasets,
  Hydra config overrides, WandB via Kaggle Secrets, checkpoint save/resume
  across 12-hour sessions, mixed precision, and Kaggle-specific gotchas.
  Use when setting up a Kaggle training notebook, debugging Kaggle-specific
  errors, or optimizing GPU memory usage on T4/P100.
compatibility: Kaggle Notebooks, PyTorch 2.1+, CUDA 11.8+
metadata:
  author: mysorf
  version: "1.0"
  domain: bioinformatics/UGTS-DTI/infrastructure
---

# Kaggle GPU Training for UGTS-DTI

## Overview

Kaggle provides free GPU compute (T4 ×1 or P100 ×1, 16 GB VRAM, 12h session
limit). The environment differs significantly from local development:
- Read-only input at `/kaggle/input/`, writable output at `/kaggle/working/`
- Internet access is OFF by default (must enable per-notebook)
- No persistent filesystem between sessions — must save to `/kaggle/working/`
  and download or push to Kaggle Datasets
- pip installs work but are slow — pre-bake heavy deps into a Kaggle Dataset

---

## Instructions

- **Filesystem, environment setup, and pip install strategy:**
  Read `.agent/skills/kaggle-gpu-training/references/environment_setup.md`

- **Uploading code, data, and model weights as Kaggle Datasets:**
  Read `.agent/skills/kaggle-gpu-training/references/dataset_upload.md`

- **Hydra config overrides and WandB integration on Kaggle:**
  Read `.agent/skills/kaggle-gpu-training/references/config_and_wandb.md`

- **Checkpoint save/resume across 12-hour sessions:**
  Read `.agent/skills/kaggle-gpu-training/references/checkpoint_resume.md`

- **GPU memory optimization (AMP, gradient checkpointing, batch sizing):**
  Read `.agent/skills/kaggle-gpu-training/references/gpu_memory.md`

---

## Quick Rules

1. Always save checkpoints to `/kaggle/working/checkpoints/` — download before session ends.
2. Enable internet in notebook settings BEFORE running — can't change mid-run.
3. Use `WANDB_API_KEY` from Kaggle Secrets (not hardcoded).
4. Override Hydra output dir: `hydra.run.dir=/kaggle/working/outputs/${now:%Y-%m-%d}/${now:%H-%M-%S}`.
5. T4 has 16 GB VRAM — use AMP (`torch.cuda.amp`) and batch_size ≤ 32 for ESM-2 t6.
6. Pre-install heavy packages (torch-geometric, rdkit) via a Kaggle Dataset to avoid timeout.
