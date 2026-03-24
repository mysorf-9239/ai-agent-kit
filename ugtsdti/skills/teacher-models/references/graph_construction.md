# Graph Construction for Teacher Branch

## Overview

The Teacher needs two global graphs loaded once at training start:
- **DD graph**: Drug-Drug similarity via Tanimoto on Morgan fingerprints
- **PP graph**: Protein-Protein similarity via cosine on k-mer frequency vectors

Both are stored as `torch_geometric.data.Data` objects and cached to disk as `.pt`
files to avoid recomputation.

---

## 1. Drug-Drug (DD) Graph

### Node features
Morgan fingerprint bit-vector (radius=2, nBits=2048) — OGB-compatible, same as
`smiles_to_graph` atom features used by Student.

### Edge construction
Tanimoto similarity between fingerprint pairs. Two strategies:

**Threshold-based** (simple, fast):
```python
if tanimoto(fp_i, fp_j) >= threshold:  # typical: 0.4–0.6
    add_edge(i, j)
```

**kNN-based** (recommended — controls graph density):
```python
# Keep top-k most similar neighbors per node
# Typical: k=5 to k=15 for DAVIS (68 drugs)
```

### Full implementation

```python
# ugtsdti/data/graph_builder.py
import numpy as np
import torch
import itertools
from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs
from torch_geometric.data import Data


def build_drug_drug_graph(
    smiles_list: list[str],
    radius: int = 2,
    nbits: int = 2048,
    top_k: int = 10,
) -> Data:
    """
    Build Drug-Drug similarity graph using Morgan fingerprints + kNN.

    Args:
        smiles_list: list of canonical SMILES strings (ordered by drug_index)
        radius: Morgan fingerprint radius (2 = ECFP4)
        nbits: fingerprint bit length
        top_k: keep top-k most similar neighbors per node

    Returns:
        PyG Data with x=(n_drugs, nbits), edge_index=(2, E)
    """
    n = len(smiles_list)
    fps = []
    x_rows = []

    for smi in smiles_list:
        mol = Chem.MolFromSmiles(smi)
        if mol:
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=nbits)
            arr = np.zeros(nbits, dtype=np.float32)
            DataStructs.ConvertToNumpyArray(fp, arr)
            fps.append(fp)
            x_rows.append(arr)
        else:
            fps.append(None)
            x_rows.append(np.zeros(nbits, dtype=np.float32))

    x = torch.from_numpy(np.stack(x_rows))  # (n, nbits)

    # Compute full similarity matrix using BulkTanimotoSimilarity (fast)
    sim_matrix = np.zeros((n, n), dtype=np.float32)
    for i in range(n):
        if fps[i] is None:
            continue
        sims = DataStructs.BulkTanimotoSimilarity(fps[i], fps)
        sim_matrix[i] = sims

    # kNN sparsification: keep top_k per row (excluding self)
    edge_index = []
    for i in range(n):
        row = sim_matrix[i].copy()
        row[i] = -1.0  # exclude self-loop
        top_k_idx = np.argsort(row)[-top_k:]
        for j in top_k_idx:
            if row[j] > 0:
                edge_index.append([i, j])
                edge_index.append([j, i])  # undirected

    # Deduplicate
    edge_index = list({tuple(e) for e in edge_index})
    if edge_index:
        ei = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    else:
        ei = torch.zeros((2, 0), dtype=torch.long)

    return Data(x=x, edge_index=ei, num_nodes=n)
```

---

## 2. Protein-Protein (PP) Graph

### Node features
k-mer frequency vector (k=3 → 20³ = 8000 dims). Normalized to unit sum.

### Edge construction
Cosine similarity on k-mer vectors, kNN sparsification (same as DD).

```python
def build_protein_protein_graph(
    fasta_list: list[str],
    k: int = 3,
    top_k: int = 10,
) -> Data:
    """
    Build Protein-Protein similarity graph using k-mer frequency + cosine similarity.

    Args:
        fasta_list: list of amino acid sequences (ordered by target_index)
        k: k-mer length (3 recommended — 8000 dims, good balance)
        top_k: keep top-k most similar neighbors per node

    Returns:
        PyG Data with x=(n_proteins, 20^k), edge_index=(2, E)
    """
    from sklearn.metrics.pairwise import cosine_similarity

    AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
    kmers = ["".join(p) for p in itertools.product(AMINO_ACIDS, repeat=k)]
    kmer_idx = {km: i for i, km in enumerate(kmers)}
    dim = len(kmers)  # 8000 for k=3

    def seq_to_kmer_vec(seq: str) -> np.ndarray:
        vec = np.zeros(dim, dtype=np.float32)
        for i in range(len(seq) - k + 1):
            km = seq[i:i+k]
            if km in kmer_idx:
                vec[kmer_idx[km]] += 1
        total = vec.sum()
        return vec / total if total > 0 else vec

    vecs = np.stack([seq_to_kmer_vec(s) for s in fasta_list])  # (n, dim)
    x = torch.from_numpy(vecs)

    sim_matrix = cosine_similarity(vecs).astype(np.float32)  # (n, n)
    n = len(fasta_list)

    edge_index = []
    for i in range(n):
        row = sim_matrix[i].copy()
        row[i] = -1.0
        top_k_idx = np.argsort(row)[-top_k:]
        for j in top_k_idx:
            if row[j] > 0:
                edge_index.append([i, j])
                edge_index.append([j, i])

    edge_index = list({tuple(e) for e in edge_index})
    if edge_index:
        ei = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    else:
        ei = torch.zeros((2, 0), dtype=torch.long)

    return Data(x=x, edge_index=ei, num_nodes=n)
```

---

## 3. Caching & Loading

```python
GRAPH_CACHE_PATH = "data/cache/similarity_graphs.pt"

def build_and_cache_graphs(smiles_list, fasta_list, cache_path=GRAPH_CACHE_PATH):
    """Build DD/PP graphs and save to disk. Skip if cache exists."""
    import os
    if os.path.exists(cache_path):
        print(f"[graph_builder] Loading graphs from cache: {cache_path}")
        return torch.load(cache_path)

    print("[graph_builder] Building DD graph...")
    dd_graph = build_drug_drug_graph(smiles_list)

    print("[graph_builder] Building PP graph...")
    pp_graph = build_protein_protein_graph(fasta_list)

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    torch.save({"dd": dd_graph, "pp": pp_graph}, cache_path)
    print(f"[graph_builder] Saved to {cache_path}")
    return {"dd": dd_graph, "pp": pp_graph}


def load_graphs(cache_path=GRAPH_CACHE_PATH):
    graphs = torch.load(cache_path)
    return graphs["dd"], graphs["pp"]
```

---

## 4. Index Alignment (Critical)

`drug_index` and `target_index` in the batch are MD5-hashed IDs modulo 100003.
The graphs must be built with nodes ordered in the **same order** as the hash mapping.

When building graphs from `TDCCachingDataset`, extract the ordered lists:
```python
# In TDCCachingDataset or a separate build script:
drug_smiles_ordered = [smiles_map[idx] for idx in sorted(smiles_map.keys())]
protein_fasta_ordered = [fasta_map[idx] for idx in sorted(fasta_map.keys())]
```

If index alignment is wrong, Teacher will look up wrong node embeddings silently.
Always verify: `assert dd_graph.num_nodes == len(unique_drugs)`.

---

## 5. Graph Statistics to Log

After building, log these to WandB for debugging:
```python
n_drug_edges = dd_graph.edge_index.shape[1] // 2
n_prot_edges = pp_graph.edge_index.shape[1] // 2
avg_drug_degree = n_drug_edges / dd_graph.num_nodes
avg_prot_degree = n_prot_edges / pp_graph.num_nodes
```

---

## 6. Graph Stability Controls (Phase 11.3)

For dynamic graphs that rebuild during training:

```yaml
# configs/trainer/default_trainer.yaml
graph:
  warmup_epochs: 5      # freeze graph topology for first N epochs
  rebuild_every: 10     # rebuild kNN edges every N epochs
  ema_decay: 0.99       # EMA smoothing for node feature updates
```

```python
# EMA update for node features after each epoch
feat_ema = ema_decay * feat_ema + (1 - ema_decay) * new_feat

# Edge churn logging
old_edges = set(map(tuple, old_edge_index.t().tolist()))
new_edges = set(map(tuple, new_edge_index.t().tolist()))
churn = len(old_edges.symmetric_difference(new_edges)) / max(len(old_edges), 1)
wandb.log({"graph/edge_churn": churn})
```
