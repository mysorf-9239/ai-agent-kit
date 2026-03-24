# UGTSDTI — Agent Entry Point

Đọc file này đầu tiên mỗi session. Nó cho bạn biết đọc gì tiếp theo.

---

## Reading Order

```
ALWAYS READ (every session):
  AGENT.md      ← you are here
  CONTEXT.md    ← project domain, architecture, current state
  task.md       ← what to do next (current phase only)

READ WHEN ADDING CODE:
  workflows/ADD_MODEL.md       ← new encoder, fusion module, any nn.Module
  workflows/ADD_DATASET.md     ← new dataset or split strategy
  workflows/ADD_LOSS.md        ← new loss function
  workflows/RUN_EXPERIMENT.md  ← ablation, sweep, evaluation

READ WHEN IMPLEMENTING SPECIFIC FEATURES:
  workflows/IMPLEMENT_TEACHER_GNN.md  ← Phase 11 (highest priority)

READ WHEN YOU NEED DEEP KNOWLEDGE:
  skills/teacher-models/     ← GCN/GAT/GATv2/GIN/SAGE, graph construction, wiring
  skills/student-models/     ← GIN/MPNN/AttentiveFP drug + ESM-2 protein, LoRA, wiring
  skills/fusion-strategies/  ← PairGate/ConcatMLP/CrossAttn, KD loss, training schedule
  skills/advanced-ml/        ← KD theory, MC-Dropout, PairGate math
  skills/graph-networks/     ← GNN fundamentals, PyG patterns
  skills/cheminformatics/    ← RDKit, Morgan fingerprints, Tanimoto
  skills/evaluation/         ← AUROC/CI/AUPRC, cold-start protocols
  skills/kaggle-gpu-training/ ← Kaggle filesystem, WandB secrets, checkpoint resume
  skills/hyperparameter-tuning/ ← Optuna+Hydra sweeps, WandB Sweeps, results analysis

READ WHEN YOU NEED HISTORICAL CONTEXT:
  DECISIONS.md  ← why we chose this approach, alternatives rejected
  roadmap.md    ← completed phases (Phase 1–10 history)
```

---

## Skill Trigger Guide

| You need to... | Read this skill |
|----------------|-----------------|
| Implement Teacher GNN (GCN/GAT/GATv2) | `teacher-models` + `graph-networks` |
| Build DD/PP similarity graph | `teacher-models/references/graph_construction.md` |
| Implement drug encoder (GIN/MPNN) | `student-models/references/drug_encoders.md` |
| Implement protein encoder (ESM-2/CNN1D) | `student-models/references/protein_encoders.md` |
| Add new fusion module | `fusion-strategies/references/fusion_catalogue.md` |
| Tune KD loss or training schedule | `fusion-strategies/references/kd_loss_and_schedule.md` |
| Wire new fusion into codebase | `fusion-strategies/references/wiring_guide.md` |
| Use RDKit fingerprints | `cheminformatics` |
| Evaluate cold-start (S1–S4) | `evaluation` |
| Train on Kaggle GPU | `kaggle-gpu-training` |
| Tune hyperparameters (Optuna/WandB) | `hyperparameter-tuning` |

---

## Hard Rules (never violate)

```python
# 1. Every model/dataset/loss must use the registry
@MODELS.register("snake_case_name")    # models
@DATASETS.register("snake_case_name")  # datasets
@LOSSES.register("snake_case_name")    # losses

# 2. Every model must return this dict
return {"logits": tensor}  # shape (B,)

# 3. core/ is FROZEN — never edit these files
ugtsdti/core/trainer.py
ugtsdti/core/registry.py
ugtsdti/core/metrics.py

# 4. Always import new modules in __init__.py
# (triggers the @register decorator at package load time)

# 5. No hardcoded hyperparameters in Python — use YAML + Hydra
```

---

## Naming Conventions

| Thing | Convention |
|-------|-----------|
| Entry point | `python -m ugtsdti.main` |
| Dataset to use | `tdc_caching_dataset` (NOT `dti_standard_dataset` — scaffold) |
| Batch keys | `drug`, `target_ids`, `target_mask`, `label`, `drug_index`, `target_index` |
| `drug_index` / `target_index` | Sequential node index 0..N-1 (per-split unique list) — NOT MD5 hash |
| Hybrid outputs | `student_logits`, `teacher_logits`, `student_uncertainty`, `teacher_uncertainty`, `fused_logits` |
| MC-Dropout fn | `_mc_forward(branch, batch, mc_samples)` → `(mean_logit, epistemic_var)` |
| Metrics params | `y_score` (not `y_prob`), `affinity_threshold` (not `threshold`) |

---

## Current Status (one line)

> Phase 11 — Teacher GNN. Pipeline runs (15 runs 2026-03-23). Teacher is dummy `nn.Embedding` — implement real GNN next.
