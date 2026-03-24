---
name: student-models
description: >
  Student branch architectures for UGTS-DTI: sequence-based inductive encoders for
  drug (SMILES) and protein (FASTA) inputs. Covers GIN/MPNN molecular graph encoders,
  ESM-2 protein language models (PLM), ChemBERTa drug encoders, CNN1D baselines,
  memory-efficient fine-tuning (LoRA, gradient checkpointing), and wiring any Student
  variant into HybridDTIModel via config.
  Use when implementing or swapping Student encoders, fixing PLM memory issues,
  choosing between drug/protein encoder architectures, or tuning Student hyperparameters.
compatibility: PyTorch 2.1+, transformers, torch-geometric, peft (for LoRA)
metadata:
  author: mysorf
  version: "1.0"
  domain: bioinformatics/UGTS-DTI/student
---

# Student Models — Sequence Encoders for UGTS-DTI

## Overview

The Student branch is an **inductive** encoder: it processes raw SMILES strings
(drug) and amino acid sequences (protein) directly — no pre-built graph needed.
This makes it robust to **cold-start (S4)**: new drugs/proteins unseen during
training can still be encoded from their sequence.

The Student is the backbone of generalization. When the Teacher is uncertain
(cold-start), PairGate shifts weight to the Student.

**Architecture split:**
- Drug encoder: processes `batch["drug"]` (PyG molecular graph from SMILES)
- Protein encoder: processes `batch["target_ids"]` + `batch["target_mask"]` (tokens)
- Both outputs are concatenated → MLP predictor → `{"logits": tensor}`

---

## Instructions

- **Drug encoders (GIN, MPNN, GCN on molecular graph):**
  Read `.agent/skills/student-models/references/drug_encoders.md`

- **Protein encoders (ESM-2, CNN1D, scratch Transformer):**
  Read `.agent/skills/student-models/references/protein_encoders.md`

- **Memory-efficient fine-tuning (LoRA, gradient checkpointing, mixed precision):**
  Read `.agent/skills/student-models/references/memory_efficient_training.md`

- **Wiring, configs, unit tests, common errors:**
  Read `.agent/skills/student-models/references/wiring_guide.md`

---

## Quick Rules

1. Register with `@MODELS.register("snake_case_name")`.
2. `forward(batch)` reads `batch["drug"]` (PyG Data) and `batch["target_ids"]`/`batch["target_mask"]`.
3. Return `{"logits": tensor}` minimum.
4. Must have `nn.Dropout` layers for MC-Dropout uncertainty to work.
5. PLM (ESM-2, ChemBERTa) should be frozen by default; use LoRA for fine-tuning.
6. Config lives in `configs/model/student/<name>.yaml`.
7. Import in `ugtsdti/models/__init__.py` to trigger `@MODELS.register`.
