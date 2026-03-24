---
name: fusion-strategies
description: >
  Fusion module architectures for UGTS-DTI: how to combine Student and Teacher
  branch outputs. Covers PairGate (uncertainty-gated), simple concat, weighted
  average, bilinear, cross-attention, and stacking (meta-learner) fusion.
  Also covers KD loss variants (MSE, KL-div, temperature scaling) and staged
  training schedules (teacher pretrain → student pretrain → joint fusion).
  Use when implementing new fusion modules, tuning KD loss, designing training
  schedules, or comparing fusion strategies in ablation experiments.
compatibility: PyTorch 2.1+
metadata:
  author: mysorf
  version: "1.0"
  domain: bioinformatics/UGTS-DTI/fusion
---

# Fusion Strategies for UGTS-DTI

## Overview

Fusion is the layer that combines Student and Teacher branch outputs into a
single prediction. The choice of fusion strategy directly impacts:
- How well the model handles warm-start (S1) vs cold-start (S4)
- Whether uncertainty information is used adaptively
- Training stability and convergence speed

**Current implementation:** `PairGateFusion` in `ugtsdti/models/fusion/pairgate.py`
— uncertainty-gated MLP using MC-Dropout variance from both branches.

---

## Instructions

- **Fusion module catalogue (all strategies + PyTorch code):**
  Read `.agent/skills/fusion-strategies/references/fusion_catalogue.md`

- **KD loss variants (MSE, KL-div, temperature scaling) + loss schedule:**
  Read `.agent/skills/fusion-strategies/references/kd_loss_and_schedule.md`

- **Wiring new fusion modules + configs + ablation setup:**
  Read `.agent/skills/fusion-strategies/references/wiring_guide.md`

---

## Quick Rules

1. Register with `@MODELS.register("snake_case_name")`.
2. `forward(student_logits, teacher_logits, student_var=None, teacher_var=None)` — match PairGate signature.
3. Return fused logit tensor (not a dict — fusion is called inside `HybridDTIModel`).
4. Config lives in `configs/model/fusion/<name>.yaml`.
5. Import in `ugtsdti/models/__init__.py`.
6. Always run ablation: `only_student` vs `only_teacher` vs `fusion` to verify fusion adds value.
