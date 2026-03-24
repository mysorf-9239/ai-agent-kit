# UGTSDTI — Project Context

Last updated: 2026-03-24

---

## 1. Problem Domain

**Drug-Target Interaction (DTI) Prediction** — predict whether a drug molecule
interacts with a protein target. Critical screening step in drug discovery,
replacing expensive wet-lab experiments.

**Core challenge: Cold-Start Problem**

Standard models fail on unseen drugs/proteins. Benchmark splits:

| Split | Drug | Target | Difficulty |
|-------|------|--------|------------|
| S1 | seen | seen | Easy (warm start) |
| S2 | new | seen | Medium |
| S3 | seen | new | Medium |
| S4 | new | new | Hard (most realistic) |

**Standard datasets:** DAVIS (Kd affinity), KIBA (composite score), BindingDB.

---

## 2. Research Approach

**Hybrid Teacher-Student + Uncertainty Gating (PairGate)**

Two complementary encoders combined via an adaptive uncertainty-based gate:

- **Teacher** (graph-based, transductive): Learns from global Drug-Drug and
  Protein-Protein similarity graphs. Strong on S1 (full graph context), weak
  on S4 (new nodes not in graph).

- **Student** (sequence-based, inductive): Learns from SMILES/FASTA directly.
  Generalizes to new drugs/proteins. Strong on S4, weaker on S1.

- **PairGate Fusion**: Uses MC-Dropout epistemic variance from both branches
  as gate input. When Teacher is uncertain (cold-start), Student gets higher
  weight. Adaptive per-sample.

**Inspiration:** MIDTI (Multi-view GCN + Deep Interactive Attention).
UGTS-DTI inherits multi-view graph idea for Teacher, adds Student branch and
uncertainty-aware fusion.

**Novelty:** Adaptive uncertainty-based fusion is rare in DTI literature.
Most SOTA picks one encoder type and does not handle cold-start automatically.

---

## 3. Current State (2026-03-24)

### Working and validated:
- Registry/plugin system (`@MODELS.register`, `@DATASETS.register`, `@LOSSES.register`)
- Trainer loop: fit/evaluate, early stopping, WandB logging, gradient clipping
- Data pipeline: `TDCCachingDataset` with PyTDC, RDKit molecular graph, ESM tokenizer, disk cache `.pt`
- Transforms: `smiles_to_graph` (OGB-standard 7 atom + 3 bond features), `ESMSequenceTokenizer`
- Models:
  - `baseline_student`: GlobalMeanPool on raw atom features + protein Embedding — pipeline validation only
  - `baseline_teacher`: `nn.Embedding` via MD5-hashed node ID — **dummy, no real signal**
  - `pairgate_fusion`: gate MLP from `(student_var, teacher_var)` — logic correct, untested with real Teacher
  - `HybridDTIModel`: orchestration, supports only-student / only-teacher / hybrid via config
- Losses: `BCEWithLogitsLossWrapper`, `KDDualLoss` (MSE distillation + BCE)
- Metrics: AUROC, AUPRC, F1, MSE, CI (Concordance Index)
- Ablation configs: `only_student.yaml`, `only_teacher.yaml`, `hybrid_baseline.yaml`
- Test suite: `test_data`, `test_models`, `test_losses`, `test_registry`
- 15 baseline runs completed (2026-03-23)

### Not yet implemented / placeholder:
- **Teacher GNN** — highest priority. `baseline_teacher` is `nn.Embedding` only.
  Needs real GNN (GAT/GCN) with DD/PP similarity graphs from RDKit fingerprints + k-mer features.
- **`cnn1d_student`**: forward pass uses mock input handling, not integrated with multimodal batch.
- **`esm_student`**: exists but not tested end-to-end.
- **KD loss wiring**: `KDDualLoss` untested with real Teacher logits.
- **`dti_standard_dataset`**: scaffold only, no split logic. Do not use.

---

## 4. Technical Architecture

```
ugtsdti/
├── main.py              # Entry point (@hydra.main)
├── core/                # FROZEN: registry.py, trainer.py, metrics.py
├── data/
│   ├── datasets/        # tdc_dataset.py (use this), dti_dataset.py (scaffold)
│   └── transforms/      # chemistry.py (smiles_to_graph), sequence.py (ESMTokenizer)
├── models/
│   ├── hybrid.py        # HybridDTIModel (orchestration)
│   ├── student/         # baseline.py (working), cnn1d.py (mock), plm.py (untested)
│   ├── teacher/         # baseline.py (dummy embedding only)
│   └── fusion/          # pairgate.py (correct logic, untested with real Teacher)
├── losses/              # bce_with_logits, kd_dual_loss
└── utils/               # logger.py, seed.py

configs/
├── default.yaml
├── model/               # only_student.yaml, only_teacher.yaml, hybrid_baseline.yaml
├── data/                # tdc_davis.yaml
└── trainer/             # default_trainer.yaml
```

**Stack:** PyTorch 2.1+, PyTorch Geometric, Hydra-core, WandB, PyTDC, RDKit,
HuggingFace Transformers, Loguru.

---

## 5. Key Design Decisions (summary)

Full rationale in `DECISIONS.md`. Quick reference:

| Decision | Choice | Why |
|----------|--------|-----|
| Uncertainty estimation | MC-Dropout | Deep Ensembles too expensive |
| Gate type | Soft scalar alpha in (0,1) | Hard switch not differentiable |
| KD loss | MSE (current), KL-div (planned) | MSE simpler until Teacher has real logits |
| Data source | PyTDC | Standardized S1-S4 splits, reproducible |
| Cache format | `.pt` disk cache | RDKit + ESM tokenizer too slow on-the-fly |
| Node ID | MD5(SMILES) % 100003 | Deterministic, low collision rate |
| Config system | Hydra + Registry | Composable, CLI-overridable, no core edits needed |
| Experiment tracking | WandB | Better UI, native sweep support |
