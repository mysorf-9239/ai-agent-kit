# UGTSDTI — Project Context

Last updated: 2026-03-24 (Phase 11 complete)

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
- Dataset indexing: sequential `drug_index`/`target_index` (0..N-1), `unique_smiles`/`unique_fasta` exposed as public attrs
- Graph builder: `graph_builder.py` — DD (Tanimoto kNN) + PP (k-mer cosine kNN), disk cache, EMA update, edge churn
- Models:
  - `baseline_student`: GlobalMeanPool on raw atom features + protein Embedding — pipeline validation only
  - `baseline_teacher`: `nn.Embedding` via sequential node ID — dummy, no real signal (kept for ablation)
  - `GCNTeacher`: real GCN encoder on DD/PP graphs, `set_graphs()` + `forward()`, MC-Dropout ≥ 0.2
  - `pairgate_fusion`: gate MLP from `(student_var, teacher_var)` — logic correct, untested with real Teacher
  - `HybridDTIModel`: orchestration, supports only-student / only-teacher / hybrid via config
- Pipeline wiring: `_wire_teacher_graphs()` in `main.py` auto-builds and sets graphs before training
- Losses: `BCEWithLogitsLossWrapper`, `KDDualLoss` (MSE distillation + BCE)
- Metrics: AUROC, AUPRC, F1, MSE, CI (Concordance Index)
- Ablation configs: `only_student.yaml`, `only_teacher.yaml`, `only_teacher_gcn.yaml`, `hybrid_baseline.yaml`
- Test suite: `test_data`, `test_models`, `test_losses`, `test_registry`, `test_teacher_gnn` (P1–P9)
- 15 baseline runs completed (2026-03-23)

### Not yet implemented / placeholder:
- **`cnn1d_student`**: forward pass uses mock input handling, not integrated with multimodal batch.
- **`esm_student`**: exists but not tested end-to-end.
- **KD loss wiring**: `KDDualLoss` untested with real Teacher logits — Phase 12 next.
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
| Node ID | Sequential index 0..N-1 | Collision-free, direct graph lookup |
| Config system | Hydra + Registry | Composable, CLI-overridable, no core edits needed |
| Experiment tracking | WandB | Better UI, native sweep support |
