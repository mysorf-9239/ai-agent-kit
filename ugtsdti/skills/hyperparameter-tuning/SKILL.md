---
name: hyperparameter-tuning
description: >
  Hyperparameter optimization for UGTS-DTI using Optuna and WandB Sweeps.
  Covers Optuna integration with Hydra (hydra-optuna-sweeper), WandB Sweeps
  config, Bayesian optimization vs random search, pruning strategies
  (MedianPruner), multi-objective optimization (AUROC + CI), and reading
  results to select the best config. Use when tuning Teacher GNN, Student
  encoder, fusion module, or KD loss hyperparameters.
compatibility: PyTorch 2.1+, Optuna 3.x, WandB, hydra-optuna-sweeper
metadata:
  author: mysorf
  version: "1.0"
  domain: bioinformatics/UGTS-DTI/optimization
---

# Hyperparameter Tuning for UGTS-DTI

## Overview

Two complementary tools for hyperparameter search:
- **Optuna** — programmatic, integrates with Hydra via `hydra-optuna-sweeper`,
  supports pruning (stop bad trials early), multi-objective, and Bayesian search.
- **WandB Sweeps** — cloud-managed, easy visualization, good for grid/random
  search across multiple machines.

Use Optuna for local/Kaggle single-machine tuning. Use WandB Sweeps when
running across multiple Kaggle notebooks in parallel.

---

## Instructions

- **Optuna + Hydra integration (search spaces, pruning, multi-objective):**
  Read `.agent/skills/hyperparameter-tuning/references/optuna_hydra.md`

- **WandB Sweeps config and agent setup:**
  Read `.agent/skills/hyperparameter-tuning/references/wandb_sweeps.md`

- **Reading results and selecting best config:**
  Read `.agent/skills/hyperparameter-tuning/references/results_analysis.md`

---

## Quick Rules

1. Always tune on validation set — never on test set.
2. Use S4 (cold-start) as primary tuning metric — it's the hardest and most realistic.
3. Start with random search (n_trials=20) before Bayesian (n_trials=50).
4. Enable pruning — bad trials waste GPU time on Kaggle.
5. Log all trials to WandB for comparison across sessions.
6. Fix random seed for reproducibility: `seed=42` in all trial configs.
