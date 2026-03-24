# Current Work

> For completed phases (1–10), see `roadmap.md`.

---

## Phase 11: Teacher GNN — IN PROGRESS (Highest Priority)

`baseline_teacher` is `nn.Embedding` only — no real signal. This blocks
PairGate and KD from working meaningfully. See `workflows/IMPLEMENT_TEACHER_GNN.md`
for full implementation guide.

### 11.1 Feature-based Graph Initialization
- [ ] Implement RDKit Morgan fingerprint extractor for Drug nodes
- [ ] Implement k-mer feature extractor for Protein nodes
- [ ] Build DD (Drug-Drug) similarity graph from Tanimoto similarity on fingerprints
- [ ] Build PP (Protein-Protein) similarity graph from k-mer cosine similarity
- [ ] Save graphs to disk cache (`.pt`) to avoid recompute

### 11.2 GNN Teacher Model
- [ ] Implement `GCNTeacher` or `GATTeacher` with `@MODELS.register("gcn_teacher")`
- [ ] Model receives `batch["drug_index"]` and `batch["target_index"]` for global graph lookup
- [ ] Add Dropout layers so MC-Dropout can measure uncertainty
- [ ] Create config `configs/model/teacher/gcn.yaml`
- [ ] Import into `ugtsdti/models/__init__.py`
- [ ] Unit test in `tests/test_models.py`
- [ ] Smoke test: `model=only_teacher` AUROC > 0.5 on S1

### 11.3 Graph Stability Controls
- [ ] Add `warmup_epochs` config: freeze graph for first N epochs
- [ ] Add `rebuild_every` config: rebuild kNN graph every N epochs
- [ ] Add EMA embedding update: `feat_ema = decay * feat_ema + (1-decay) * feat`
- [ ] Log "edge churn" (% edges changed after rebuild) to WandB

---

## Phase 12: Gate & Loss Fixes — BLOCKED on Phase 11

### 12.2 KD Loss wiring
- [ ] Test `kd_dual_loss` with real Teacher logits
- [ ] Add KL-divergence option (with temperature scaling) alongside MSE
- [ ] Wire `kd_weight` and `reg_weight` from config instead of hardcoded `alpha`

### 12.3 Loss schedule
- [ ] Stage 1: teacher-only pretrain (graph stable)
- [ ] Stage 2: student-only pretrain
- [ ] Stage 3: fusion + KD + gate regularizer

---

## Phase 13: Experiments & Ablations — BLOCKED on Phase 12

- [ ] Full ablation: only_student vs only_teacher vs hybrid on DAVIS S1/S4
- [ ] Compare with MIDTI baseline
- [ ] Log gate stats (mean, percentiles, histogram) per epoch
- [ ] Log uncertainty stats (u_s, u_t mean + histogram)
- [ ] Log edge churn vs metric stability

---

## Known Issues (fix before trusting metrics)

| Issue | Impact | Status |
|-------|--------|--------|
| `cnn1d_student` mock input handling | Can't use in experiments | Not fixed |
| `esm_student` not tested end-to-end | Can't use in experiments | Not fixed |
| KD loss untested with real Teacher | Phase 12 blocked | Blocked on Phase 11 |
| Negative sampling audit (before or after split?) | Metrics may be inflated | Not done |
