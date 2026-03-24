# Protein Encoders for Student Branch

## Overview

Protein input arrives as:
- `batch["target_ids"]`: LongTensor `(B, seq_len)` — tokenized amino acid sequence
- `batch["target_mask"]`: LongTensor `(B, seq_len)` — 1 for real tokens, 0 for padding

Tokenization is handled by `ESMSequenceTokenizer` in
`ugtsdti/data/transforms/sequence.py`.

---

## ESM-2 Model Size Guide

| Checkpoint | Layers | Params | VRAM (fp16 inference) | VRAM (Adam train) | Recommendation |
|------------|--------|--------|-----------------------|-------------------|----------------|
| `esm2_t6_8M_UR50D` | 6 | 8M | ~0.1 GB | ~0.3 GB | Dev/debug, fast iteration |
| `esm2_t12_35M_UR50D` | 12 | 35M | ~0.3 GB | ~1.1 GB | **Default for experiments** |
| `esm2_t30_150M_UR50D` | 30 | 150M | ~0.3 GB | ~1.1 GB | Better quality, still fits T4 |
| `esm2_t33_650M_UR50D` | 33 | 650M | ~1.3 GB | ~5.2 GB | Best quality, needs LoRA on T4 |
| `esm2_t36_3B_UR50D` | 36 | 3B | ~6 GB | OOM on T4 | Kaggle A100 only |

**For Kaggle T4 (16GB):** Use `esm2_t12_35M_UR50D` frozen + LoRA, or
`esm2_t30_150M_UR50D` frozen (no LoRA needed).

---

## 1. ESM-2 Protein Encoder (Recommended)

```python
# ugtsdti/models/student/esm_student.py
import torch
import torch.nn as nn
from transformers import EsmModel
from ugtsdti.core.registry import MODELS


@MODELS.register("esm_student")
class ESMProteinStudent(nn.Module):
    """
    ESM-2 protein encoder (frozen) + GIN/simple drug encoder.
    Protein: ESM-2 CLS token → projection → hidden_dim
    Drug: mean pool over atom features → projection → hidden_dim

    For drug encoding, pair with a dedicated drug encoder or use
    the simple linear projection below as a placeholder.
    """
    def __init__(
        self,
        esm_model_name: str = "facebook/esm2_t12_35M_UR50D",
        hidden_dim: int = 128,
        dropout: float = 0.3,
        freeze_esm: bool = True,
        atom_feat_dim: int = 7,
    ):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        # Load ESM-2
        self.esm = EsmModel.from_pretrained(esm_model_name)
        self.esm_hidden = self.esm.config.hidden_size  # 480 for t12, 640 for t30, 1280 for t33

        if freeze_esm:
            for param in self.esm.parameters():
                param.requires_grad = False

        # Project ESM output to hidden_dim
        self.protein_proj = nn.Sequential(
            nn.Linear(self.esm_hidden, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

        # Simple drug encoder (replace with GIN/MPNN for better performance)
        self.drug_proj = nn.Sequential(
            nn.Linear(atom_feat_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

        self.predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, batch: dict) -> dict:
        # --- Protein encoding via ESM-2 ---
        esm_out = self.esm(
            input_ids=batch["target_ids"],
            attention_mask=batch["target_mask"],
        )
        # Use mean pooling over non-padding tokens (more stable than CLS)
        token_emb = esm_out.last_hidden_state          # (B, seq_len, esm_hidden)
        mask = batch["target_mask"].unsqueeze(-1).float()
        prot_emb = (token_emb * mask).sum(1) / mask.sum(1).clamp(min=1)
        prot_emb = self.protein_proj(prot_emb)         # (B, hidden_dim)

        # --- Drug encoding (simple mean pool) ---
        drug = batch["drug"]
        # Mean pool atom features across all atoms in each graph
        from torch_geometric.nn import global_mean_pool
        drug_emb = global_mean_pool(drug.x.float(), drug.batch)  # (B, atom_feat_dim)
        drug_emb = self.drug_proj(drug_emb)                       # (B, hidden_dim)

        pair = torch.cat([drug_emb, prot_emb], dim=-1)
        return {"logits": self.predictor(pair).squeeze(-1)}
```

**Config:**
```yaml
# configs/model/student/esm_t12.yaml
name: esm_student
params:
  esm_model_name: "facebook/esm2_t12_35M_UR50D"
  hidden_dim: 128
  dropout: 0.3
  freeze_esm: true
  atom_feat_dim: 7
```

---

## 2. ESM-2 + GIN Combined Student (Best Student Architecture)

Combines the best drug encoder (GIN/AttentiveFP) with ESM-2 protein encoder.

```python
# ugtsdti/models/student/esm_gin_student.py
import torch
import torch.nn as nn
from torch_geometric.nn import GINConv, global_mean_pool
from transformers import EsmModel
from ugtsdti.core.registry import MODELS


def _gin_mlp(in_dim, out_dim):
    return nn.Sequential(
        nn.Linear(in_dim, out_dim),
        nn.BatchNorm1d(out_dim),
        nn.ReLU(),
        nn.Linear(out_dim, out_dim),
    )


@MODELS.register("esm_gin_student")
class ESMGINStudent(nn.Module):
    """
    Best Student: GIN drug encoder + ESM-2 protein encoder.
    """
    def __init__(
        self,
        esm_model_name: str = "facebook/esm2_t12_35M_UR50D",
        atom_feat_dim: int = 7,
        hidden_dim: int = 128,
        gin_layers: int = 3,
        dropout: float = 0.3,
        freeze_esm: bool = True,
    ):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        # GIN drug encoder
        self.drug_convs = nn.ModuleList([
            GINConv(_gin_mlp(atom_feat_dim if i == 0 else hidden_dim, hidden_dim))
            for i in range(gin_layers)
        ])

        # ESM-2 protein encoder
        self.esm = EsmModel.from_pretrained(esm_model_name)
        esm_hidden = self.esm.config.hidden_size
        if freeze_esm:
            for p in self.esm.parameters():
                p.requires_grad = False

        self.protein_proj = nn.Sequential(
            nn.Linear(esm_hidden, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

        self.predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, batch: dict) -> dict:
        # Drug
        drug = batch["drug"]
        x = drug.x.float()
        for conv in self.drug_convs:
            x = self.dropout(conv(x, drug.edge_index).relu())
        drug_emb = global_mean_pool(x, drug.batch)  # (B, hidden_dim)

        # Protein
        esm_out = self.esm(
            input_ids=batch["target_ids"],
            attention_mask=batch["target_mask"],
        )
        token_emb = esm_out.last_hidden_state
        mask = batch["target_mask"].unsqueeze(-1).float()
        prot_emb = (token_emb * mask).sum(1) / mask.sum(1).clamp(min=1)
        prot_emb = self.protein_proj(prot_emb)  # (B, hidden_dim)

        pair = torch.cat([drug_emb, prot_emb], dim=-1)
        return {"logits": self.predictor(pair).squeeze(-1)}
```

**Config:**
```yaml
# configs/model/student/esm_gin.yaml
name: esm_gin_student
params:
  esm_model_name: "facebook/esm2_t12_35M_UR50D"
  atom_feat_dim: 7
  hidden_dim: 128
  gin_layers: 3
  dropout: 0.3
  freeze_esm: true
```

---

## 3. CNN1D Student (Fixed — Multimodal Batch Compatible)

The existing `cnn1d_student` in the repo has a mock forward pass that doesn't
work with the real multimodal batch. This is the corrected version.

```python
# ugtsdti/models/student/cnn1d_student.py  (FIXED)
import torch
import torch.nn as nn
from torch_geometric.nn import global_mean_pool
from ugtsdti.core.registry import MODELS


@MODELS.register("cnn1d_student")
class CNN1DStudent(nn.Module):
    """
    CNN1D protein encoder + GIN drug encoder.
    Faster than ESM-2, no pretrained weights needed.
    """
    def __init__(
        self,
        atom_feat_dim: int = 7,
        hidden_dim: int = 128,
        protein_vocab_size: int = 26,
        protein_embed_dim: int = 128,
        cnn_filters: int = 128,
        cnn_kernel: int = 7,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        # Drug: simple linear projection (replace with GIN for better perf)
        self.drug_proj = nn.Sequential(
            nn.Linear(atom_feat_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

        # Protein: Embedding → Conv1D → GlobalMaxPool
        self.protein_embed = nn.Embedding(protein_vocab_size, protein_embed_dim, padding_idx=0)
        self.protein_conv = nn.Sequential(
            nn.Conv1d(protein_embed_dim, cnn_filters, kernel_size=cnn_kernel, padding=cnn_kernel // 2),
            nn.ReLU(),
            nn.Conv1d(cnn_filters, hidden_dim, kernel_size=cnn_kernel, padding=cnn_kernel // 2),
            nn.ReLU(),
        )
        self.protein_pool = nn.AdaptiveMaxPool1d(1)

        self.predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, batch: dict) -> dict:
        # Drug
        drug = batch["drug"]
        drug_emb = global_mean_pool(drug.x.float(), drug.batch)  # (B, atom_feat_dim)
        drug_emb = self.drug_proj(drug_emb)                       # (B, hidden_dim)

        # Protein — Conv1D expects (B, channels, length)
        target_ids = batch["target_ids"]                          # (B, seq_len)
        prot_emb = self.protein_embed(target_ids)                 # (B, seq_len, embed_dim)
        prot_emb = prot_emb.transpose(1, 2)                       # (B, embed_dim, seq_len)
        prot_emb = self.dropout(self.protein_conv(prot_emb))      # (B, hidden_dim, seq_len)
        prot_emb = self.protein_pool(prot_emb).squeeze(-1)        # (B, hidden_dim)

        pair = torch.cat([drug_emb, prot_emb], dim=-1)
        return {"logits": self.predictor(pair).squeeze(-1)}
```

---

## 4. ChemBERTa Drug Encoder (Optional — SMILES Transformer)

Uses a pretrained BERT-style model trained on SMILES strings. Alternative to
GIN when you want a pretrained drug representation.

```python
# ugtsdti/models/student/chemberta_student.py
import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
from ugtsdti.core.registry import MODELS


@MODELS.register("chemberta_student")
class ChemBERTaStudent(nn.Module):
    """
    ChemBERTa drug encoder + ESM-2 protein encoder.
    Note: requires separate SMILES tokenization — NOT compatible with
    current batch["drug"] PyG format. Needs custom dataset transform.
    Use only if you add a SMILES tokenizer to the data pipeline.
    """
    def __init__(
        self,
        chemberta_name: str = "seyonec/ChemBERTa-zinc-base-v1",
        esm_name: str = "facebook/esm2_t12_35M_UR50D",
        hidden_dim: int = 128,
        dropout: float = 0.3,
        freeze_chemberta: bool = True,
        freeze_esm: bool = True,
    ):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        self.drug_encoder = AutoModel.from_pretrained(chemberta_name)
        drug_hidden = self.drug_encoder.config.hidden_size  # 768
        if freeze_chemberta:
            for p in self.drug_encoder.parameters():
                p.requires_grad = False

        self.esm = AutoModel.from_pretrained(esm_name)
        prot_hidden = self.esm.config.hidden_size
        if freeze_esm:
            for p in self.esm.parameters():
                p.requires_grad = False

        self.drug_proj = nn.Linear(drug_hidden, hidden_dim)
        self.prot_proj = nn.Linear(prot_hidden, hidden_dim)

        self.predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, batch: dict) -> dict:
        # Requires batch["smiles_ids"] and batch["smiles_mask"] — custom keys
        drug_out = self.drug_encoder(
            input_ids=batch["smiles_ids"],
            attention_mask=batch["smiles_mask"],
        )
        drug_emb = drug_out.last_hidden_state[:, 0, :]  # CLS token
        drug_emb = self.drug_proj(drug_emb)

        esm_out = self.esm(
            input_ids=batch["target_ids"],
            attention_mask=batch["target_mask"],
        )
        mask = batch["target_mask"].unsqueeze(-1).float()
        prot_emb = (esm_out.last_hidden_state * mask).sum(1) / mask.sum(1).clamp(min=1)
        prot_emb = self.prot_proj(prot_emb)

        pair = torch.cat([drug_emb, prot_emb], dim=-1)
        return {"logits": self.predictor(pair).squeeze(-1)}
```

**Warning:** ChemBERTa requires adding `smiles_ids`/`smiles_mask` to the batch
dict. This needs a new transform in `ugtsdti/data/transforms/`. Only implement
after GIN + ESM-2 baseline is validated.

---

## 5. Protein Encoder Comparison

| Encoder | Params | Quality | Speed | Cold-start |
|---------|--------|---------|-------|------------|
| `nn.Embedding` (baseline) | ~3K | Low | Very fast | Poor |
| CNN1D | ~500K | Medium | Fast | Good |
| ESM-2 t6 (frozen) | 8M | Good | Fast | Excellent |
| ESM-2 t12 (frozen) | 35M | Very good | Medium | Excellent |
| ESM-2 t30 (frozen) | 150M | Best | Slow | Excellent |
| ESM-2 t33 + LoRA | 650M+4M | Best | Slow | Excellent |
