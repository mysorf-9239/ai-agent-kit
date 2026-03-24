---
name: evaluation
description: >
  DTI model evaluation: AUROC, AUPRC, Concordance Index (CI), F1, MSE.
  Cross-validation setup for DTI including 4 cold-start scenarios (S1-S4).
  Benchmark datasets (DAVIS, KIBA, DrugBank, Human, C.elegans) and standard thresholds.
  Use when evaluating DTI model performance, setting up cross-validation, comparing models,
  or interpreting metric values in DTI papers.
compatibility: Requires scikit-learn, scipy, numpy
metadata:
  author: mysorf
  version: "2.0"
  domain: bioinformatics/evaluation
---

# DTI Evaluation Metrics & Protocols

## Overview
Evaluating DTI models requires specific classification and regression metrics due to extreme class imbalance and domain-specific challenges (e.g., the cold-start problem).

## Instructions

- **Classification (AUROC, AUPRC) & regression (CI, MSE) metrics:**
  Read `.agent/skills/evaluation/references/metrics.md`

- **Cross-validation procedures và S1-S4 cold-start scenarios:**
  Read `.agent/skills/evaluation/references/cv_protocols.md`
