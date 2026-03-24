# Graph Neural Networks (GNN) Architectures

## 1. Why Graphs for DTI?

- Drugs = molecular graphs (atoms + bonds)
- Proteins = can be represented as residue contact graphs
- DTI relationships = bipartite graph (drug ↔ protein)
- Similarity networks = DD, PP, DP adjacency matrices

**Message passing intuition:**
Nodes aggregate features from their neighbors. After `k` layers, a node encodes its `k-hop` neighborhood. For drugs, this captures the local chemical environment.

---

## 2. GCN (Graph Convolutional Network)

**Math:**
`H^(l+1) = σ(D̂^(-1/2) Â D̂^(-1/2) H^(l) W^(l))`
(where `Â = A + I` for self-loops)

**PyG implementation:**
```python
from torch_geometric.nn import GCNConv
import torch.nn as nn

class SimpleGCN(nn.Module):
    def __init__(self, in_dim, hidden_dim, out_dim):
        super().__init__()
        self.conv1 = GCNConv(in_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, out_dim)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        x = self.conv2(x, edge_index)
        return x
```

---

## 3. GAT (Graph Attention Network)

Adds learned attention weights to neighbor aggregation instead of static degree-based weights.

```python
from torch_geometric.nn import GATConv

# Attention mechanism allows the model to learn which neighbors are more important
conv = GATConv(in_channels=64, out_channels=32, heads=4, concat=True)
# output dim = out_channels * heads = 128
```

---

## 4. MPNN (Message Passing Neural Network)

General framework that encompasses GCN, GAT, etc., used in the UGTS-DTI Student branch for drug representation from SMILES.

---

## 5. Converting Similarity Matrix to PyG Graph

```python
import numpy as np
import torch
from torch_geometric.data import Data

def similarity_to_graph(sim_matrix: np.ndarray, threshold: float = 0.6) -> Data:
    """Convert a dense similarity matrix to a sparse PyG graph format."""
    n = sim_matrix.shape[0]
    # Node features = rows of similarity matrix (or other feature vectors)
    x = torch.tensor(sim_matrix, dtype=torch.float)

    edge_index = []
    for i in range(n):
        for j in range(n):
            if i != j and sim_matrix[i, j] >= threshold:
                edge_index.append([i, j])

    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    return Data(x=x, edge_index=edge_index)
```
