# GNN Architecture Catalogue for Teacher Branch

## Architecture Comparison

| Model | Attention | Inductive | Best for | Weakness |
|-------|-----------|-----------|----------|----------|
| GCN | No (degree-norm) | No | Dense, homogeneous graphs | All neighbors equal weight |
| GAT | Yes (additive) | No | Heterogeneous neighbor importance | Static attention (query-independent) |
| GATv2 | Yes (dynamic) | No | Complex neighbor relationships | Heavier than GAT |
| GIN | No (sum-agg) | Yes | Graph isomorphism, expressive | No attention, noisy on sparse graphs |
| GraphSAGE | No (mean/max) | Yes | Large graphs, inductive | Less expressive than GIN |

**Recommendation for UGTS-DTI Teacher:**
- Start with **GCN** (fast, simple baseline)
- Upgrade to **GATv2** for best performance (dynamic attention handles varying drug similarity well)
- Use **GraphSAGE** if graph is large (>10k nodes) or needs inductive generalization

---

## 1. GCN Teacher

Simplest baseline. Symmetric normalization: `H' = σ(D̂^{-1/2} Â D̂^{-1/2} H W)`.

```python
# ugtsdti/models/teacher/gcn_teacher.py
import torch
import torch.nn as nn
from torch_geometric.nn import GCNConv
from ugtsdti.core.registry import MODELS


@MODELS.register("gcn_teacher")
class GCNTeacher(nn.Module):
    def __init__(
        self,
        drug_feat_dim: int = 2048,
        protein_feat_dim: int = 8000,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        self.drug_convs = nn.ModuleList([
            GCNConv(drug_feat_dim if i == 0 else hidden_dim, hidden_dim)
            for i in range(num_layers)
        ])
        self.protein_convs = nn.ModuleList([
            GCNConv(protein_feat_dim if i == 0 else hidden_dim, hidden_dim)
            for i in range(num_layers)
        ])
        self.predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

        self.dd_graph = None
        self.pp_graph = None

    def set_graphs(self, dd_graph, pp_graph):
        self.dd_graph = dd_graph
        self.pp_graph = pp_graph

    def _encode_drugs(self):
        x = self.dd_graph.x
        ei = self.dd_graph.edge_index
        for conv in self.drug_convs:
            x = self.dropout(conv(x, ei).relu())
        return x  # (n_drugs, hidden_dim)

    def _encode_proteins(self):
        x = self.pp_graph.x
        ei = self.pp_graph.edge_index
        for conv in self.protein_convs:
            x = self.dropout(conv(x, ei).relu())
        return x  # (n_proteins, hidden_dim)

    def forward(self, batch: dict) -> dict:
        drug_idx = batch["drug_index"].squeeze(-1)
        target_idx = batch["target_index"].squeeze(-1)

        drug_emb = self._encode_drugs()[drug_idx]       # (B, hidden_dim)
        protein_emb = self._encode_proteins()[target_idx]  # (B, hidden_dim)

        pair = torch.cat([drug_emb, protein_emb], dim=-1)
        logits = self.predictor(pair).squeeze(-1)
        return {"logits": logits}
```

**Config:**
```yaml
# configs/model/teacher/gcn.yaml
name: gcn_teacher
params:
  drug_feat_dim: 2048
  protein_feat_dim: 8000
  hidden_dim: 128
  num_layers: 2
  dropout: 0.3
```

---

## 2. GAT Teacher

Additive attention: each neighbor gets a learned scalar weight.
Better than GCN when neighbor importance varies (e.g., some drugs are more
structurally similar and should contribute more).

```python
# ugtsdti/models/teacher/gat_teacher.py
from torch_geometric.nn import GATConv
from ugtsdti.core.registry import MODELS
import torch, torch.nn as nn


@MODELS.register("gat_teacher")
class GATTeacher(nn.Module):
    def __init__(
        self,
        drug_feat_dim: int = 2048,
        protein_feat_dim: int = 8000,
        hidden_dim: int = 64,
        heads: int = 4,
        num_layers: int = 2,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.dropout = nn.Dropout(dropout)
        out_dim = hidden_dim  # after concat heads → project back

        self.drug_convs = nn.ModuleList()
        self.protein_convs = nn.ModuleList()
        for i in range(num_layers):
            in_d = drug_feat_dim if i == 0 else hidden_dim
            in_p = protein_feat_dim if i == 0 else hidden_dim
            # concat=False → average heads → output dim = hidden_dim
            self.drug_convs.append(GATConv(in_d, hidden_dim, heads=heads, concat=False, dropout=dropout))
            self.protein_convs.append(GATConv(in_p, hidden_dim, heads=heads, concat=False, dropout=dropout))

        self.predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )
        self.dd_graph = None
        self.pp_graph = None

    def set_graphs(self, dd_graph, pp_graph):
        self.dd_graph = dd_graph
        self.pp_graph = pp_graph

    def forward(self, batch: dict) -> dict:
        drug_idx = batch["drug_index"].squeeze(-1)
        target_idx = batch["target_index"].squeeze(-1)

        x_d = self.dd_graph.x
        for conv in self.drug_convs:
            x_d = self.dropout(conv(x_d, self.dd_graph.edge_index).relu())

        x_p = self.pp_graph.x
        for conv in self.protein_convs:
            x_p = self.dropout(conv(x_p, self.pp_graph.edge_index).relu())

        pair = torch.cat([x_d[drug_idx], x_p[target_idx]], dim=-1)
        return {"logits": self.predictor(pair).squeeze(-1)}
```

**Config:**
```yaml
# configs/model/teacher/gat.yaml
name: gat_teacher
params:
  drug_feat_dim: 2048
  protein_feat_dim: 8000
  hidden_dim: 64
  heads: 4
  num_layers: 2
  dropout: 0.3
```

---

## 3. GATv2 Teacher (Recommended)

Fixes GAT's static attention problem. In GAT, attention is computed as
`a(Wh_i, Wh_j)` — the transformation happens before the attention, making it
query-independent. GATv2 computes `a(W[h_i || h_j])` — truly dynamic.

```python
# ugtsdti/models/teacher/gatv2_teacher.py
from torch_geometric.nn import GATv2Conv
from ugtsdti.core.registry import MODELS
import torch, torch.nn as nn


@MODELS.register("gatv2_teacher")
class GATv2Teacher(nn.Module):
    def __init__(
        self,
        drug_feat_dim: int = 2048,
        protein_feat_dim: int = 8000,
        hidden_dim: int = 64,
        heads: int = 4,
        num_layers: int = 2,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        self.drug_convs = nn.ModuleList()
        self.protein_convs = nn.ModuleList()
        for i in range(num_layers):
            in_d = drug_feat_dim if i == 0 else hidden_dim
            in_p = protein_feat_dim if i == 0 else hidden_dim
            self.drug_convs.append(GATv2Conv(in_d, hidden_dim, heads=heads, concat=False, dropout=dropout))
            self.protein_convs.append(GATv2Conv(in_p, hidden_dim, heads=heads, concat=False, dropout=dropout))

        self.predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )
        self.dd_graph = None
        self.pp_graph = None

    def set_graphs(self, dd_graph, pp_graph):
        self.dd_graph = dd_graph
        self.pp_graph = pp_graph

    def forward(self, batch: dict) -> dict:
        drug_idx = batch["drug_index"].squeeze(-1)
        target_idx = batch["target_index"].squeeze(-1)

        x_d = self.dd_graph.x
        for conv in self.drug_convs:
            x_d = self.dropout(conv(x_d, self.dd_graph.edge_index).relu())

        x_p = self.pp_graph.x
        for conv in self.protein_convs:
            x_p = self.dropout(conv(x_p, self.pp_graph.edge_index).relu())

        pair = torch.cat([x_d[drug_idx], x_p[target_idx]], dim=-1)
        return {"logits": self.predictor(pair).squeeze(-1)}
```

**Config:**
```yaml
# configs/model/teacher/gatv2.yaml
name: gatv2_teacher
params:
  drug_feat_dim: 2048
  protein_feat_dim: 8000
  hidden_dim: 64
  heads: 4
  num_layers: 2
  dropout: 0.3
```

---

## 4. GIN Teacher

Graph Isomorphism Network — most expressive (Weisfeiler-Leman equivalent).
Uses sum aggregation + MLP. Good when structural patterns matter more than
neighbor weighting.

```python
# ugtsdti/models/teacher/gin_teacher.py
from torch_geometric.nn import GINConv
from ugtsdti.core.registry import MODELS
import torch, torch.nn as nn


def _mlp(in_dim, out_dim):
    return nn.Sequential(nn.Linear(in_dim, out_dim), nn.ReLU(), nn.Linear(out_dim, out_dim))


@MODELS.register("gin_teacher")
class GINTeacher(nn.Module):
    def __init__(
        self,
        drug_feat_dim: int = 2048,
        protein_feat_dim: int = 8000,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        self.drug_convs = nn.ModuleList([
            GINConv(_mlp(drug_feat_dim if i == 0 else hidden_dim, hidden_dim))
            for i in range(num_layers)
        ])
        self.protein_convs = nn.ModuleList([
            GINConv(_mlp(protein_feat_dim if i == 0 else hidden_dim, hidden_dim))
            for i in range(num_layers)
        ])
        self.predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )
        self.dd_graph = None
        self.pp_graph = None

    def set_graphs(self, dd_graph, pp_graph):
        self.dd_graph = dd_graph
        self.pp_graph = pp_graph

    def forward(self, batch: dict) -> dict:
        drug_idx = batch["drug_index"].squeeze(-1)
        target_idx = batch["target_index"].squeeze(-1)

        x_d = self.dd_graph.x
        for conv in self.drug_convs:
            x_d = self.dropout(conv(x_d, self.dd_graph.edge_index).relu())

        x_p = self.pp_graph.x
        for conv in self.protein_convs:
            x_p = self.dropout(conv(x_p, self.pp_graph.edge_index).relu())

        pair = torch.cat([x_d[drug_idx], x_p[target_idx]], dim=-1)
        return {"logits": self.predictor(pair).squeeze(-1)}
```

---

## 5. GraphSAGE Teacher

Inductive — learns an aggregation function rather than per-node embeddings.
Useful if the graph is large or you want to generalize to new nodes at test time.

```python
# ugtsdti/models/teacher/sage_teacher.py
from torch_geometric.nn import SAGEConv
from ugtsdti.core.registry import MODELS
import torch, torch.nn as nn


@MODELS.register("sage_teacher")
class SAGETeacher(nn.Module):
    def __init__(
        self,
        drug_feat_dim: int = 2048,
        protein_feat_dim: int = 8000,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        self.drug_convs = nn.ModuleList([
            SAGEConv(drug_feat_dim if i == 0 else hidden_dim, hidden_dim)
            for i in range(num_layers)
        ])
        self.protein_convs = nn.ModuleList([
            SAGEConv(protein_feat_dim if i == 0 else hidden_dim, hidden_dim)
            for i in range(num_layers)
        ])
        self.predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )
        self.dd_graph = None
        self.pp_graph = None

    def set_graphs(self, dd_graph, pp_graph):
        self.dd_graph = dd_graph
        self.pp_graph = pp_graph

    def forward(self, batch: dict) -> dict:
        drug_idx = batch["drug_index"].squeeze(-1)
        target_idx = batch["target_index"].squeeze(-1)

        x_d = self.dd_graph.x
        for conv in self.drug_convs:
            x_d = self.dropout(conv(x_d, self.dd_graph.edge_index).relu())

        x_p = self.pp_graph.x
        for conv in self.protein_convs:
            x_p = self.dropout(conv(x_p, self.pp_graph.edge_index).relu())

        pair = torch.cat([x_d[drug_idx], x_p[target_idx]], dim=-1)
        return {"logits": self.predictor(pair).squeeze(-1)}
```

---

## 6. Multi-View Teacher (MIDTI-inspired)

Combines DD + PP + DP (bipartite) views. More expressive but heavier.
Implement after single-view Teachers are validated.

```python
# Concept — implement after GCN/GAT baseline works:
# 1. Run GCN on DD graph → drug_emb_dd
# 2. Run GCN on PP graph → protein_emb_pp
# 3. Run GCN on DP bipartite graph → drug_emb_dp, protein_emb_dp
# 4. Concatenate views: drug_final = cat(drug_emb_dd, drug_emb_dp)
# 5. Predict from cat(drug_final, protein_final)
```

---

## 7. Hyperparameter Tuning Guide

| Param | Range | Notes |
|-------|-------|-------|
| `hidden_dim` | 64–256 | Start 128, increase if underfitting |
| `num_layers` | 1–3 | >3 layers → over-smoothing on small graphs |
| `dropout` | 0.2–0.5 | Must be ≥0.2 for MC-Dropout to work |
| `heads` (GAT) | 2–8 | 4 is a good default |
| `top_k` (graph) | 5–20 | Higher k → denser graph → more context but slower |
| `radius` (Morgan) | 2–3 | radius=2 (ECFP4) standard; radius=3 for more detail |

**Over-smoothing warning:** With DAVIS (68 drugs), a 3-layer GCN will average
over most of the graph. Keep `num_layers ≤ 2` for small datasets.
