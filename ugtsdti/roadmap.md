# Project Roadmap — Completed Phases

This file records completed work. For current tasks, see `task.md`.

---

## Phase 1–9: Foundation (COMPLETED)

All phases 1–9 completed. Includes:
- Architecture design and refactor
- Data pipeline (PyTDC, RDKit, ESM tokenizer, disk cache)
- Registry/plugin system (Hydra + `@register` decorators)
- Baseline models (student, teacher dummy, pairgate fusion)
- Ablation tooling (only_student, only_teacher, hybrid configs)
- AI agent skills and workflows
- Documentation scaffolding

See git history for details.

---

## Phase 10: Baseline Validation (COMPLETED 2026-03-23)

### 10.1 Baseline runs
- [x] End-to-end pipeline runs (15 runs on 2026-03-23)
- [x] `baseline_student` + `baseline_teacher` (dummy) + `pairgate_fusion` working
- [x] Metrics (AUROC, AUPRC, CI) printing correctly
- [x] WandB logging working
- [x] Early stopping working

### 10.2 Data pipeline audit
- [x] Confirmed PyTDC split happens BEFORE negative sampling (no leakage)
- [x] Fixed `davis_s1.yaml` — was pointing to non-existent path, now uses `tdc_caching_dataset`
- [x] Verified `tdc_davis.yaml` format is correct

### 10.3 Docs and codebase cleanup
- [x] Updated `CONTEXT.md` to reflect actual state
- [x] Rewrote `README.md` — research project standard, mermaid diagrams
- [x] Fixed env name: `conda-recipes/full.yaml` and `Makefile` changed `ugtsdti-full` → `ugtsdti`
- [x] Commented `cnn1d_student` — not integrated with multimodal batch
- [x] Deleted `configs/callbacks/default_callbacks.yaml` — orphan file
- [x] Standardized `.agent/` — added AGENT.md, DECISIONS.md, workflows/, skills/

### 10.4 MC-Dropout consistency fix
- [x] Replaced `_estimate_epistemic_uncertainty()` with `_mc_forward()` — logit and
  uncertainty now come from the same `mc_logits` tensor (Gal & Ghahramani 2016)
- [x] Guard: training mode uses 1 forward pass, eval mode uses N MC passes
