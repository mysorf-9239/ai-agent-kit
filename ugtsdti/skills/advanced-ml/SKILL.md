---
name: advanced-ml
description: >
  Advanced Machine Learning techniques for DTI: Teacher-Student architecture,
  Knowledge Distillation (KD), Uncertainty Quantification (MC Dropout), and Uncertainty Gating.
  Use when designing hybrid models, implementing knowledge transfer between models,
  estimating prediction confidence/variance, or fusing multiple branches using adaptive gates.
compatibility: PyTorch
metadata:
  author: mysorf
  version: "1.0"
  domain: bioinformatics/advanced-ml
---

# Advanced ML: KD & Uncertainty Gating

## Overview
This skill contains the theoretical foundation and PyTorch implementation patterns for three advanced techniques heavily used in modern hybrid DTI projects (like UGTS-DTI):
1. **Teacher-Student Models & Knowledge Distillation (KD)**
2. **Uncertainty Quantification (via MC Dropout)**
3. **Uncertainty Gating (PairGate Fusion)**

## Instructions

- **Teacher-Student architectures và Knowledge Distillation formulas/code:**
  Read `.agent/skills/advanced-ml/references/knowledge_distillation.md`

- **MC-Dropout, uncertainty metrics, và uncertainty gating formulas/code:**
  Read `.agent/skills/advanced-ml/references/uncertainty_gating.md`
