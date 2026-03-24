---
name: cheminformatics
description: >
  Cheminformatics knowledge for DTI: SMILES notation, molecular fingerprints (Morgan/ECFP, MACCS),
  Tanimoto similarity, drug-drug similarity matrices, RDKit usage, molecular graphs.
  Use when processing drug molecules, computing drug similarity, parsing SMILES,
  working with RDKit, or building DD/DP similarity matrices for DTI models.
compatibility: Requires RDKit (`pip install rdkit`)
metadata:
  author: mysorf
  version: "2.0"
  domain: bioinformatics/cheminformatics
---

# DTI Cheminformatics

## Overview
This skill provides instructions on handling chemical data for DTI prediction. It covers how to process SMILES strings, generate molecular fingerprints, calculate drug-drug similarity (Tanimoto), and convert chemicals into graphs for Machine Learning models.

## Instructions

- **SMILES parsing, fingerprints, molecular graphs với RDKit:**
  Read `.agent/skills/cheminformatics/references/rdkit_operations.md`

- **Drug similarity matrices (Tanimoto, DD matrices):**
  Read `.agent/skills/cheminformatics/references/similarity_metrics.md`
