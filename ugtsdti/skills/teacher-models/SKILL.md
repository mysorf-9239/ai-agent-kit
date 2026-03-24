---
name: teacher-models
description: >
  Teacher branch architectures for UGTS-DTI: GCN, GAT, GATv2, GIN, GraphSAGE on
  Drug-Drug (DD) and Protein-Protein (PP) similarity graphs. Covers graph construction
  from RDKit fingerprints / k-mer features, kNN sparsification, graph caching, and
  wiring any Teacher variant into HybridDTIModel via config.
  Use when implementing or swapping Teacher GNN models, building similarity graphs,
  debugging transductive lookup, or tuning Teacher architecture hyperparameters.
compatibility: PyTorch 2.1+, torch-geometric, rdkit, scikit-learn
metadata:
  author: mysorf
  version: "1.0"
  domain: bioinformatics/UGTS-DTI/teacher
---

# Teacher Models — GNN Architectures for UGTS-DTI

## Overview

The Teacher branch is a **transductive** encoder: it operates on pre-built global
Drug-Drug (DD) and Protein-Protein (PP) similarity graphs. At inference time it
looks up node embeddings by `drug_index` / `target_index` (MD5-hashed IDs stored
in the batch dict).

The Teacher is strong at **S1 (warm-start)** because it sees the full graph context.
It degrades at **S4 (cold-start)** because new nodes have no edges — this is
intentional: high MC-Dropout variance at cold-start signals PairGate to trust
the Student instead.

**Key constraint:** Every Teacher model MUST have `nn.Dropout` layers so that
MC-Dropout uncertainty estimation works correctly.

---

## Instructions

- **Graph construction (DD/PP similarity graphs, kNN, caching):**
  Read `.agent/skills/teacher-models/references/graph_construction.md`

- **GNN architecture catalogue (GCN, GAT, GATv2, GIN, GraphSAGE) + PyG code:**
  Read `.agent/skills/teacher-models/references/gnn_catalogue.md`

- **Wiring a new Teacher into HybridDTIModel + config examples:**
  Read `.agent/skills/teacher-models/references/wiring_guide.md`

---

## Quick Rules

1. Always register with `@MODELS.register("snake_case_name")`.
2. `forward(batch)` must accept the standard batch dict and return `{"logits": tensor}`.
3. Teacher reads `batch["drug_index"]` and `batch["target_index"]` — NOT `batch["drug"]`.
4. Graphs must be loaded via `set_graphs(dd_graph, pp_graph)` before training starts.
5. Dropout rate ≥ 0.2 required for meaningful MC-Dropout uncertainty.
6. Config lives in `configs/model/teacher/<name>.yaml`.
7. Import in `ugtsdti/models/__init__.py` to trigger `@MODELS.register`.
