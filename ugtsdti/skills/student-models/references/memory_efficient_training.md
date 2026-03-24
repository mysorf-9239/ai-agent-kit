# Memory-Efficient Training for Student Models

## Why This Matters

ESM-2 models are large. On Kaggle T4 (16GB VRAM):
- `esm2_t12_35M` frozen: fine — fits easily
- `esm2_t30_150M` frozen: fine — ~1.1GB training
- `esm2_t33_650M` full fine-tune: OOM — needs LoRA
- `esm2_t33_650M` + LoRA: fits — only ~4M extra params trained

---

## 1. Frozen Backbone (Default Strategy)

Freeze all ESM-2 weights, only train the projection head and predictor.
Fastest, lowest memory, good performance for most DTI tasks.

```python
# In model __init__:
if freeze_esm:
    for param in self.esm.parameters():
        param.requires_grad = False

# Verify only projection layers are trainable:
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
total = sum(p.numel() for p in model.parameters())
print(f"Trainable: {trainable:,} / {total:,} ({100*trainable/total:.1f}%)")
```

---

## 2. LoRA Fine-Tuning (When Frozen is Not Enough)

LoRA (Low-Rank Adaptation) adds small trainable matrices to frozen attention
layers. Reduces trainable params by ~90% vs full fine-tuning.

**Install:** `pip install peft`

```python
# ugtsdti/models/student/esm_lora_student.py
import torch
import torch.nn as nn
from transformers import EsmModel
from peft import get_peft_model, LoraConfig, TaskType
from ugtsdti.core.registry import MODELS
from torch_geometric.nn import GINConv, global_mean_pool


def _gin_mlp(in_dim, out_dim):
    return nn.Sequential(
        nn.Linear(in_dim, out_dim), nn.BatchNorm1d(out_dim),
        nn.ReLU(), nn.Linear(out_dim, out_dim),
    )


@MODELS.register("esm_lora_student")
class ESMLoRAStudent(nn.Module):
    """
    ESM-2 with LoRA fine-tuning + GIN drug encoder.
    Use when frozen ESM-2 underfits and you need better protein representations.
    """
    def __init__(
        self,
        esm_model_name: str = "facebook/esm2_t33_650M_UR50D",
        atom_feat_dim: int = 7,
        hidden_dim: int = 128,
        gin_layers: int = 3,
        dropout: float = 0.3,
        lora_r: int = 8,
        lora_alpha: int = 16,
        lora_dropout: float = 0.1,
        lora_target_modules: list = None,
    ):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        # Load ESM-2 and apply LoRA
        base_esm = EsmModel.from_pretrained(esm_model_name)
        lora_config = LoraConfig(
            r=lora_r,                    # rank — lower = fewer params
            lora_alpha=lora_alpha,       # scaling factor
            lora_dropout=lora_dropout,
            # Target the query and value projection matrices in attention
            target_modules=lora_target_modules or ["query", "value"],
            bias="none",
        )
        self.esm = get_peft_model(base_esm, lora_config)
        esm_hidden = base_esm.config.hidden_size

        # GIN drug encoder
        self.drug_convs = nn.ModuleList([
            GINConv(_gin_mlp(atom_feat_dim if i == 0 else hidden_dim, hidden_dim))
            for i in range(gin_layers)
        ])

        self.protein_proj = nn.Sequential(
            nn.Linear(esm_hidden, hidden_dim), nn.ReLU(), nn.Dropout(dropout),
        )
        self.predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim), nn.ReLU(),
            nn.Dropout(dropout), nn.Linear(hidden_dim, 1),
        )

    def forward(self, batch: dict) -> dict:
        # Drug
        drug = batch["drug"]
        x = drug.x.float()
        for conv in self.drug_convs:
            x = self.dropout(conv(x, drug.edge_index).relu())
        drug_emb = global_mean_pool(x, drug.batch)

        # Protein with LoRA
        esm_out = self.esm(
            input_ids=batch["target_ids"],
            attention_mask=batch["target_mask"],
        )
        mask = batch["target_mask"].unsqueeze(-1).float()
        prot_emb = (esm_out.last_hidden_state * mask).sum(1) / mask.sum(1).clamp(min=1)
        prot_emb = self.protein_proj(prot_emb)

        pair = torch.cat([drug_emb, prot_emb], dim=-1)
        return {"logits": self.predictor(pair).squeeze(-1)}
```

**Config:**
```yaml
# configs/model/student/esm_lora.yaml
name: esm_lora_student
params:
  esm_model_name: "facebook/esm2_t33_650M_UR50D"
  hidden_dim: 128
  gin_layers: 3
  dropout: 0.3
  lora_r: 8
  lora_alpha: 16
  lora_dropout: 0.1
```

**LoRA param guide:**
| `lora_r` | Extra params | Memory | Quality |
|----------|-------------|--------|---------|
| 4 | ~2M | Minimal | Good |
| 8 | ~4M | Low | Better |
| 16 | ~8M | Medium | Best |
| 32 | ~16M | High | Diminishing returns |

---

## 3. Gradient Checkpointing

Trades compute for memory: recomputes activations during backward pass instead
of storing them. Reduces memory by ~40-60% at cost of ~20% slower training.

```python
# Enable in model __init__ after loading ESM-2:
self.esm.gradient_checkpointing_enable()

# Or via HuggingFace config:
self.esm = EsmModel.from_pretrained(
    esm_model_name,
    use_cache=False,  # must disable KV cache when using gradient checkpointing
)
self.esm.gradient_checkpointing_enable()
```

**Important:** `use_cache=False` is required — gradient checkpointing and KV
cache are incompatible.

---

## 4. Mixed Precision (AMP)

Use `torch.cuda.amp` to train in float16. Halves memory, ~2x faster on modern GPUs.

```python
# In Trainer (ugtsdti/core/trainer.py) — add AMP support:
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

# Training loop:
with autocast():
    outputs = model(batch)
    loss = criterion(outputs, batch["label"])

scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()
```

**Note:** `core/trainer.py` is FROZEN. Add AMP via config flag if needed, or
implement in a custom trainer subclass.

---

## 5. Memory Budget Reference (Kaggle T4 = 16GB)

| Student Config | VRAM Usage | Fits T4? |
|----------------|------------|----------|
| baseline_student (current) | ~0.5 GB | ✅ |
| GIN + nn.Embedding protein | ~1 GB | ✅ |
| GIN + ESM-2 t6 frozen | ~1.5 GB | ✅ |
| GIN + ESM-2 t12 frozen | ~2 GB | ✅ |
| GIN + ESM-2 t30 frozen | ~3 GB | ✅ |
| GIN + ESM-2 t33 frozen | ~6 GB | ✅ |
| GIN + ESM-2 t33 + LoRA r=8 | ~7 GB | ✅ |
| GIN + ESM-2 t33 full fine-tune | ~20 GB | ❌ OOM |
| Hybrid (Teacher GCN + Student ESM-t12) | ~4 GB | ✅ |
| Hybrid (Teacher GATv2 + Student ESM-t30) | ~6 GB | ✅ |

---

## 6. Recommended Training Strategy

```
Stage 1: Validate pipeline
  → baseline_student (current) — fast, no PLM

Stage 2: Better drug encoder
  → gin_student (GIN drug + nn.Embedding protein)
  → Verify AUROC improves over baseline

Stage 3: Better protein encoder
  → esm_gin_student (GIN drug + ESM-2 t12 frozen)
  → Verify cold-start (S4) improves significantly

Stage 4: Fine-tune protein encoder
  → esm_lora_student (GIN drug + ESM-2 t33 + LoRA)
  → Only if Stage 3 still underfits on S4
```
