# Drug Encoders for Student Branch

## Overview

Drug input arrives as `batch["drug"]` — a PyG `Data` object built by
`smiles_to_graph()` in `ugtsdti/data/transforms/chemistry.py`.

Node features: 7-dim OGB atom features (atomic num, degree, formal charge,
num Hs, num radical electrons, hybridization, aromaticity).
Edge features: 3-dim bond features (bond type, conjugated, in-ring).

---

## Architecture Comparison

| Model | Aggregation | Edge features | Expressiveness | Best for |
|-------|-------------|---------------|----------------|----------|
| GCN | Degree-norm | No | Low | Fast baseline |
| GIN | Sum + MLP | No | High (WL-equiv) | Structural patterns |
| MPNN | Message passing | Yes | High | Bond-aware encoding |
| AttentiveFP | Attention | Yes | Very high | SOTA molecular property |

**Recommendation:** Start with **GIN** (fast, expressive). Upgrade to **AttentiveFP**
for best performance on molecular property tasks.

---

## 1. GIN Drug Encoder (Recommended Start)

Graph Isomorphism Network — most expressive standard GNN for molecular graphs.
Sum aggregation + MLP per layer.

```python
# ugtsdti/models/student/gin_drug_student.py
import torch
import torch.nn as nn
from torch_geometric.nn import GINConv, global_mean_pool, global_add_pool
from ugtsdti.core.registry import MODELS


def _mlp(in_dim: int, out_dim: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(in_dim, out_dim),
        nn.BatchNorm1d(out_dim),
        nn.ReLU(),
        nn.Linear(out_dim, out_dim),
    )


@MODELS.register("gin_student")
class GINStudent(nn.Module):
    """
    GIN drug encoder + simple protein embedding.
    Drug: GIN on PyG molecular graph (OGB atom features).
    Protein: nn.Embedding on tokenized sequence (mean pool).
    """
    def __init__(
        self,
        atom_feat_dim: int = 7,
        hidden_dim: int = 128,
        num_layers: int = 3,
        dropout: float = 0.3,
        protein_vocab_size: int = 26,
        protein_embed_dim: int = 128,
        max_protein_len: int = 1000,
    ):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        # Drug GIN layers
        self.drug_convs = nn.ModuleList([
            GINConv(_mlp(atom_feat_dim if i == 0 else hidden_dim, hidden_dim))
            for i in range(num_layers)
        ])

        # Protein embedding (simple baseline — replace with ESM-2 for better perf)
        self.protein_embed = nn.Embedding(protein_vocab_size, protein_embed_dim, padding_idx=0)
        self.protein_proj = nn.Linear(protein_embed_dim, hidden_dim)

        # Predictor
        self.predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, batch: dict) -> dict:
        # --- Drug encoding ---
        drug = batch["drug"]
        x = drug.x.float()
        for conv in self.drug_convs:
            x = self.dropout(conv(x, drug.edge_index).relu())
        drug_emb = global_mean_pool(x, drug.batch)  # (B, hidden_dim)

        # --- Protein encoding ---
        target_ids = batch["target_ids"]          # (B, seq_len)
        target_mask = batch["target_mask"]        # (B, seq_len)
        prot_emb = self.protein_embed(target_ids) # (B, seq_len, embed_dim)
        # Mean pool over non-padding tokens
        mask_expanded = target_mask.unsqueeze(-1).float()
        prot_emb = (prot_emb * mask_expanded).sum(1) / mask_expanded.sum(1).clamp(min=1)
        prot_emb = self.dropout(self.protein_proj(prot_emb))  # (B, hidden_dim)

        # --- Predict ---
        pair = torch.cat([drug_emb, prot_emb], dim=-1)
        logits = self.predictor(pair).squeeze(-1)
        return {"logits": logits}
```

**Config:**
```yaml
# configs/model/student/gin.yaml
name: gin_student
params:
  atom_feat_dim: 7
  hidden_dim: 128
  num_layers: 3
  dropout: 0.3
  protein_vocab_size: 26
  protein_embed_dim: 128
```

---

## 2. MPNN Drug Encoder

Message Passing Neural Network — uses edge features (bond type, conjugated, in-ring).
More expressive than GIN for bond-sensitive properties.

```python
# ugtsdti/models/student/mpnn_drug_student.py
import torch
import torch.nn as nn
from torch_geometric.nn import NNConv, global_mean_pool
from ugtsdti.core.registry import MODELS


@MODELS.register("mpnn_student")
class MPNNStudent(nn.Module):
    """
    MPNN drug encoder using edge features (bond type, conjugated, in-ring).
    """
    def __init__(
        self,
        atom_feat_dim: int = 7,
        edge_feat_dim: int = 3,
        hidden_dim: int = 128,
        num_layers: int = 3,
        dropout: float = 0.3,
        protein_vocab_size: int = 26,
        protein_embed_dim: int = 128,
    ):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        # NNConv: edge MLP maps edge features to weight matrix
        self.drug_convs = nn.ModuleList()
        for i in range(num_layers):
            in_d = atom_feat_dim if i == 0 else hidden_dim
            edge_nn = nn.Sequential(
                nn.Linear(edge_feat_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, in_d * hidden_dim),
            )
            self.drug_convs.append(NNConv(in_d, hidden_dim, edge_nn, aggr="mean"))

        self.protein_embed = nn.Embedding(protein_vocab_size, protein_embed_dim, padding_idx=0)
        self.protein_proj = nn.Linear(protein_embed_dim, hidden_dim)

        self.predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, batch: dict) -> dict:
        drug = batch["drug"]
        x = drug.x.float()
        edge_attr = drug.edge_attr.float()  # (E, 3)

        for conv in self.drug_convs:
            x = self.dropout(conv(x, drug.edge_index, edge_attr).relu())
        drug_emb = global_mean_pool(x, drug.batch)

        target_ids = batch["target_ids"]
        target_mask = batch["target_mask"]
        prot_emb = self.protein_embed(target_ids)
        mask_expanded = target_mask.unsqueeze(-1).float()
        prot_emb = (prot_emb * mask_expanded).sum(1) / mask_expanded.sum(1).clamp(min=1)
        prot_emb = self.dropout(self.protein_proj(prot_emb))

        pair = torch.cat([drug_emb, prot_emb], dim=-1)
        return {"logits": self.predictor(pair).squeeze(-1)}
```

**Config:**
```yaml
# configs/model/student/mpnn.yaml
name: mpnn_student
params:
  atom_feat_dim: 7
  edge_feat_dim: 3
  hidden_dim: 128
  num_layers: 3
  dropout: 0.3
```

---

## 3. AttentiveFP Drug Encoder (SOTA)

Attention-based molecular fingerprint. Uses graph attention on both atoms and
bonds. Best performance on molecular property prediction tasks.

```python
# ugtsdti/models/student/attentivefp_student.py
import torch
import torch.nn as nn
from torch_geometric.nn import AttentiveFP
from ugtsdti.core.registry import MODELS


@MODELS.register("attentivefp_student")
class AttentiveFPStudent(nn.Module):
    def __init__(
        self,
        atom_feat_dim: int = 7,
        edge_feat_dim: int = 3,
        hidden_dim: int = 128,
        num_layers: int = 2,
        num_timesteps: int = 2,
        dropout: float = 0.3,
        protein_vocab_size: int = 26,
        protein_embed_dim: int = 128,
    ):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        # AttentiveFP handles both atom and bond attention internally
        self.drug_encoder = AttentiveFP(
            in_channels=atom_feat_dim,
            hidden_channels=hidden_dim,
            out_channels=hidden_dim,
            edge_dim=edge_feat_dim,
            num_layers=num_layers,
            num_timesteps=num_timesteps,
            dropout=dropout,
        )

        self.protein_embed = nn.Embedding(protein_vocab_size, protein_embed_dim, padding_idx=0)
        self.protein_proj = nn.Linear(protein_embed_dim, hidden_dim)

        self.predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, batch: dict) -> dict:
        drug = batch["drug"]
        drug_emb = self.drug_encoder(
            drug.x.float(),
            drug.edge_index,
            drug.edge_attr.float(),
            drug.batch,
        )  # (B, hidden_dim)

        target_ids = batch["target_ids"]
        target_mask = batch["target_mask"]
        prot_emb = self.protein_embed(target_ids)
        mask_expanded = target_mask.unsqueeze(-1).float()
        prot_emb = (prot_emb * mask_expanded).sum(1) / mask_expanded.sum(1).clamp(min=1)
        prot_emb = self.dropout(self.protein_proj(prot_emb))

        pair = torch.cat([drug_emb, prot_emb], dim=-1)
        return {"logits": self.predictor(pair).squeeze(-1)}
```

---

## 4. Hyperparameter Guide (Drug Encoders)

| Param | Range | Notes |
|-------|-------|-------|
| `hidden_dim` | 64–256 | 128 is a good default |
| `num_layers` | 2–5 | GIN: 3–4 optimal; >5 → over-smoothing |
| `dropout` | 0.2–0.5 | Must be ≥0.2 for MC-Dropout |
| `num_timesteps` (AttentiveFP) | 2–4 | Higher = more global context |
