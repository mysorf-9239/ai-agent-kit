# Current Work

> For completed phases (1–10), see `roadmap.md`.

---

## Phase 11: Teacher GNN — COMPLETE ✓

All tasks done. See `.kiro/specs/teacher-gnn/tasks.md` for full checklist.

**Deliverables:**
- `ugtsdti/data/graph_builder.py` — DD/PP graph build + cache + EMA + churn
- `ugtsdti/models/teacher/gcn_teacher.py` — `GCNTeacher` registered, `set_graphs()`, `forward()`
- `ugtsdti/main.py` — `_wire_teacher_graphs()` auto-wires graphs before training
- `configs/model/teacher/gcn.yaml` + `configs/model/only_teacher_gcn.yaml`
- `tests/test_teacher_gnn.py` — unit tests + P1–P9 property tests

**Smoke test command:**
```
python -m ugtsdti.main model=only_teacher_gcn data=tdc_davis trainer=default_trainer
```

---

## Phase 12: Gate & Loss Fixes — NEXT (unblocked)

### 12.2 KD Loss wiring
- [ ] Test `kd_dual_loss` with real Teacher logits (GCNTeacher)
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
