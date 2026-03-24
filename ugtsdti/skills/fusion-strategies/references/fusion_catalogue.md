# Fusion Module Catalogue

## Strategy Comparison

| Strategy | Uses uncertainty | Learnable | Cold-start adaptive | Complexity |
|----------|-----------------|-----------|---------------------|------------|
| Simple Average | No | No | No | Trivial |
| Weighted Average | No | Yes (fixed α) | No | Minimal |
| Concat + MLP | No | Yes | No | Low |
| Bilinear | No | Yes | No | Medium |
| PairGate (current) | Yes (MC-Dropout) | Yes | Yes | Medium |
| Cross-Attention | No | Yes | Partial | High |
| Stacking (meta-learner) | Optional | Yes | Optional | High |

**Recommendation order for ablation:**
1. Simple Average (sanity check baseline)
2. PairGate (current — uncertainty-aware)
3. Concat + MLP (strong non-uncertainty baseline)
4. Cross-Attention (if drug-protein interaction matters)
5. Stacking (if you have multiple Teacher/Student variants)

---

## 1. Simple Average (Baseline)

No parameters. Equal weight to both branches. Use as sanity check — fusion
should beat this.

```python
# ugtsdti/models/fusion/simple_avg_fusion.py
import torch.nn as nn
from ugtsdti.core.registry import MODELS


@MODELS.register("simple_avg_fusion")
class SimpleAvgFusion(nn.Module):
    """Equal-weight average of student and teacher logits. No parameters."""

    def forward(self, student_logits, teacher_logits, student_var=None, teacher_var=None):
        return 0.5 * student_logits + 0.5 * teacher_logits
```

**Config:**
```yaml
# configs/model/fusion/simple_avg.yaml
name: simple_avg_fusion
params: {}
```

---

## 2. Learnable Weighted Average

Single scalar α learned during training. Soft constraint: α ∈ (0,1) via sigmoid.
Simple but effective when one branch is consistently better.

```python
# ugtsdti/models/fusion/weighted_avg_fusion.py
import torch
import torch.nn as nn
from ugtsdti.core.registry import MODELS


@MODELS.register("weighted_avg_fusion")
class WeightedAvgFusion(nn.Module):
    """
    Learnable scalar gate α ∈ (0,1).
    output = α * teacher_logits + (1-α) * student_logits
    α is global (same for all samples in batch).
    """

    def __init__(self, init_alpha: float = 0.5):
        super().__init__()
        # Unconstrained parameter — sigmoid maps to (0,1)
        self.alpha_raw = nn.Parameter(torch.tensor(init_alpha).logit())

    @property
    def alpha(self) -> float:
        return torch.sigmoid(self.alpha_raw).item()

    def forward(self, student_logits, teacher_logits, student_var=None, teacher_var=None):
        alpha = torch.sigmoid(self.alpha_raw)
        return alpha * teacher_logits + (1 - alpha) * student_logits
```

**Config:**
```yaml
# configs/model/fusion/weighted_avg.yaml
name: weighted_avg_fusion
params:
  init_alpha: 0.5
```

---

## 3. Concat + MLP Fusion

Concatenate both logits → MLP → final prediction. No uncertainty needed.
Strong non-uncertainty baseline — if PairGate doesn't beat this, uncertainty
gating isn't helping.

```python
# ugtsdti/models/fusion/concat_mlp_fusion.py
import torch
import torch.nn as nn
from ugtsdti.core.registry import MODELS


@MODELS.register("concat_mlp_fusion")
class ConcatMLPFusion(nn.Module):
    """
    Concatenate [student_logits, teacher_logits] → MLP → fused logit.
    No uncertainty required. Strong non-uncertainty baseline.
    """

    def __init__(self, hidden_dim: int = 32, dropout: float = 0.1):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, student_logits, teacher_logits, student_var=None, teacher_var=None):
        # Ensure both are (B,) shaped
        s = student_logits.unsqueeze(-1) if student_logits.dim() == 1 else student_logits
        t = teacher_logits.unsqueeze(-1) if teacher_logits.dim() == 1 else teacher_logits
        combined = torch.cat([s, t], dim=-1)  # (B, 2)
        return self.mlp(combined).squeeze(-1)  # (B,)
```

**Config:**
```yaml
# configs/model/fusion/concat_mlp.yaml
name: concat_mlp_fusion
params:
  hidden_dim: 32
  dropout: 0.1
```

---

## 4. PairGate Fusion (Current — Uncertainty-Aware)

The existing implementation. Uses MC-Dropout variance from both branches as
gate input. Adaptive per-sample: high Teacher uncertainty → trust Student more.

```python
# Already implemented in ugtsdti/models/fusion/pairgate.py
# Signature:
# forward(student_logits, teacher_logits, student_var=None, teacher_var=None)
# Falls back to simple average if vars are None
```

**Extended PairGate with richer gate input:**

```python
# ugtsdti/models/fusion/pairgate_v2.py
import torch
import torch.nn as nn
from ugtsdti.core.registry import MODELS


@MODELS.register("pairgate_v2")
class PairGateV2(nn.Module):
    """
    Enhanced PairGate: gate input includes [var_s, var_t, logit_s, logit_t].
    Richer signal — gate can also use prediction confidence, not just uncertainty.
    """

    def __init__(self, gate_hidden: int = 64, dropout: float = 0.1):
        super().__init__()
        self.gate_mlp = nn.Sequential(
            nn.Linear(4, gate_hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(gate_hidden, 1),
            nn.Sigmoid(),
        )

    def forward(self, student_logits, teacher_logits, student_var=None, teacher_var=None):
        if student_var is None or teacher_var is None:
            return 0.5 * student_logits + 0.5 * teacher_logits

        s = student_logits if student_logits.dim() > 0 else student_logits.unsqueeze(-1)
        t = teacher_logits if teacher_logits.dim() > 0 else teacher_logits.unsqueeze(-1)
        sv = student_var if student_var.dim() > 0 else student_var.unsqueeze(-1)
        tv = teacher_var if teacher_var.dim() > 0 else teacher_var.unsqueeze(-1)

        gate_input = torch.stack([sv, tv, s, t], dim=-1)  # (B, 4)
        alpha = self.gate_mlp(gate_input).squeeze(-1)      # (B,)
        return alpha * teacher_logits + (1 - alpha) * student_logits
```

**Config:**
```yaml
# configs/model/fusion/pairgate_v2.yaml
name: pairgate_v2
params:
  gate_hidden: 64
  dropout: 0.1
```

---

## 5. Bilinear Fusion

Models multiplicative interactions between student and teacher embeddings.
Useful when the relationship between branches is non-linear.

```python
# ugtsdti/models/fusion/bilinear_fusion.py
import torch
import torch.nn as nn
from ugtsdti.core.registry import MODELS


@MODELS.register("bilinear_fusion")
class BilinearFusion(nn.Module):
    """
    Bilinear fusion: output = s^T W t + b
    Captures multiplicative interactions between branches.
    Requires hidden_dim embeddings, not just scalar logits.
    
    NOTE: This requires HybridDTIModel to pass embeddings, not just logits.
    Needs modification to HybridDTIModel.forward() to expose branch embeddings.
    Use ConcatMLPFusion as simpler alternative.
    """

    def __init__(self, input_dim: int = 128, dropout: float = 0.1):
        super().__init__()
        self.bilinear = nn.Bilinear(input_dim, input_dim, 1)
        self.dropout = nn.Dropout(dropout)

    def forward(self, student_emb, teacher_emb, student_var=None, teacher_var=None):
        # student_emb, teacher_emb: (B, input_dim)
        s = self.dropout(student_emb)
        t = self.dropout(teacher_emb)
        return self.bilinear(s, t).squeeze(-1)  # (B,)
```

**Note:** Bilinear fusion requires branch embeddings (not just scalar logits).
This needs a small change to `HybridDTIModel` to expose `student_emb` and
`teacher_emb`. Implement after simpler fusions are validated.

---

## 6. Cross-Attention Fusion

Drug and protein representations attend to each other before prediction.
Inspired by MIDTI's Deep Interactive Attention (DIA). Most expressive but
requires access to intermediate token-level representations.

```python
# ugtsdti/models/fusion/cross_attention_fusion.py
import torch
import torch.nn as nn
from ugtsdti.core.registry import MODELS


@MODELS.register("cross_attention_fusion")
class CrossAttentionFusion(nn.Module):
    """
    Cross-attention between student and teacher embeddings.
    Student embedding attends to Teacher embedding and vice versa.
    
    NOTE: Requires HybridDTIModel to pass branch embeddings (not just logits).
    """

    def __init__(self, hidden_dim: int = 128, num_heads: int = 4, dropout: float = 0.1):
        super().__init__()
        self.cross_attn = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True,
        )
        self.norm = nn.LayerNorm(hidden_dim)
        self.predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, student_emb, teacher_emb, student_var=None, teacher_var=None):
        # student_emb, teacher_emb: (B, hidden_dim)
        # Expand to sequence dim for attention: (B, 1, hidden_dim)
        s = student_emb.unsqueeze(1)
        t = teacher_emb.unsqueeze(1)

        # Student attends to Teacher
        s_attended, _ = self.cross_attn(query=s, key=t, value=t)
        s_attended = self.norm(s + s_attended).squeeze(1)  # (B, hidden_dim)

        combined = torch.cat([s_attended, teacher_emb], dim=-1)
        return self.predictor(combined).squeeze(-1)
```

---

## 7. Stacking (Meta-Learner)

Train multiple Student/Teacher variants, then train a meta-learner on their
predictions. Best for ensembling diverse models.

```python
# ugtsdti/models/fusion/stacking_fusion.py
import torch
import torch.nn as nn
from ugtsdti.core.registry import MODELS


@MODELS.register("stacking_fusion")
class StackingFusion(nn.Module):
    """
    Meta-learner that combines predictions from N models.
    Input: list of logits from N models → MLP → final prediction.
    
    Usage: pass all model logits as a stacked tensor.
    Requires custom HybridDTIModel variant that runs N branches.
    """

    def __init__(self, n_models: int = 3, hidden_dim: int = 32, dropout: float = 0.1):
        super().__init__()
        self.meta_mlp = nn.Sequential(
            nn.Linear(n_models, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, logits_list: list, **kwargs):
        # logits_list: list of (B,) tensors from N models
        stacked = torch.stack(logits_list, dim=-1)  # (B, N)
        return self.meta_mlp(stacked).squeeze(-1)   # (B,)
```

---

## 8. Ablation Experiment Design

Always run these 4 configs to isolate fusion contribution:

```bash
# Baseline: no fusion
python -m ugtsdti.main model=only_student data=tdc_davis
python -m ugtsdti.main model=only_teacher data=tdc_davis

# Fusion ablation
python -m ugtsdti.main model=hybrid_simple_avg data=tdc_davis    # sanity check
python -m ugtsdti.main model=hybrid_concat_mlp data=tdc_davis    # non-uncertainty baseline
python -m ugtsdti.main model=hybrid_pairgate data=tdc_davis      # uncertainty-aware

# Cold-start: where fusion matters most
python -m ugtsdti.main model=hybrid_pairgate data=tdc_davis_s4
python -m ugtsdti.main model=hybrid_concat_mlp data=tdc_davis_s4
```

**Expected pattern:**
- S1: Teacher ≈ Hybrid (Teacher already good, fusion adds little)
- S4: Student >> Teacher, Hybrid ≈ Student (gate correctly ignores Teacher)
- PairGate should beat ConcatMLP on S4 (uncertainty signal helps)
- If PairGate ≈ ConcatMLP on S4 → uncertainty signal not informative → Teacher not trained well enough
