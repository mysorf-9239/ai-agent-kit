---
name: graph-networks
description: >
  Graph Neural Networks for DTI: GCN, GAT, MPNN, multi-view graphs, heterogeneous graphs,
  PyTorch Geometric (PyG) usage, message passing, graph construction.
  Use when working with GNN layers, building drug-protein interaction graphs,
  implementing GCN_homo/GCN_bi/GCN_hete (MIDTI patterns), or any PyG-based graph learning.
compatibility: Requires torch-geometric, torch-scatter, torch-sparse
metadata:
  author: mysorf
  version: "2.0"
  domain: bioinformatics/graph-learning
---

# DTI Graph Neural Networks

## Overview
This skill covers Graph Neural Network architectures, specifically tailored for DTI prediction models like MIDTI and UGTS-DTI. It includes multi-view graph learning (DD, PP, DP matrices), heterogeneous graphs, and Deep Interactive Attention (DIA).

## Instructions

- **PyG code, GNN baselines, và graph construction:**
  Read `.agent/skills/graph-networks/references/gnn_architectures.md`

- **MIDTI-specific architectures (GCN_homo, GCN_bi, GCN_hete, DIA):**
  Read `.agent/skills/graph-networks/references/midti_graphs.md`

- **Implement Teacher GNN cho UGTSDTI:**
  Read `.agent/workflows/IMPLEMENT_TEACHER_GNN.md`
