# KD Loss Variants & Training Schedule

## Overview

Knowledge Distillation (KD) loss trains the Student to mimic the Teacher's
output distribution, not just the hard labels. This transfers the Teacher's
"dark knowledge" — its confidence patterns across all classes.

Current implementation: `KDDualLoss` in `ugtsdti/losses/distillation.py`
uses MSE distillation. This file covers alternatives and training schedules.

---

## 1. Loss Variants

### 1.1 MSE Distillation (Current)

```
L = (1-β) * BCE(logits, y_true) + β * MSE(student_logits, teacher_logits)
```

Simple, stable. Works well when Teacher and Student logits are on similar scales.

```python
# Already in ugtsdti/losses/distillation.py
# KDDualLoss with alpha parameter
```

**When to use:** Default. Start here.

---

### 1.2 KL-Divergence with Temperature Scaling

```
L = (1-β) * BCE(logits, y_true) + β * T² * KL(softmax(s/T) || softmax(t/T))
```

Temperature T > 1 softens the distributions, revealing "dark knowledge" —
the relative confidence patterns the Teacher has learned.

```python
# ugtsdti/losses/kd_kl_loss.py
import torch
import torch.nn as nn
import torch.nn.functional as F
from ugtsdti.core.registry import LOSSES


@LOSSES.register("kd_kl_loss")
class KDKLLoss(nn.Module):
    """
    KD loss using KL-divergence with temperature scaling.
    Better than MSE when Teacher logits carry meaningful soft probabilities.
    
    Args:
        alpha: weight for KD loss (1-alpha for task loss)
        temperature: softening temperature T (higher = softer distributions)
    """

    def __init__(self, alpha: float = 0.5, temperature: float = 4.0):
        super().__init__()
        self.alpha = alpha
        self.T = temperature
        self.bce = nn.BCEWithLogitsLoss()

    def forward(self, model_outputs: dict, y_true: torch.Tensor) -> torch.Tensor:
        logits = model_outputs["logits"]
        student_logits = model_outputs.get("student_logits")
        teacher_logits = model_outputs.get("teacher_logits")

        # Task loss
        task_loss = self.bce(logits, y_true.float())

        if student_logits is None or teacher_logits is None:
            return task_loss

        # KL divergence with temperature
        # For binary DTI: treat as 2-class problem [p_neg, p_pos]
        s_logits_2 = torch.stack([-student_logits, student_logits], dim=-1)
        t_logits_2 = torch.stack([-teacher_logits, teacher_logits], dim=-1)

        student_log_probs = F.log_softmax(s_logits_2 / self.T, dim=-1)
        teacher_probs = F.softmax(t_logits_2 / self.T, dim=-1)

        # T² scaling to match gradient magnitude of task loss
        kd_loss = F.kl_div(student_log_probs, teacher_probs, reduction="batchmean") * (self.T ** 2)

        return (1 - self.alpha) * task_loss + self.alpha * kd_loss
```

**Config:**
```yaml
# In trainer config:
trainer:
  loss:
    name: kd_kl_loss
    params:
      alpha: 0.5
      temperature: 4.0
```

**Temperature guide:**
| T | Effect |
|---|--------|
| 1.0 | Standard softmax — no softening |
| 2.0 | Mild softening |
| 4.0 | Recommended default |
| 8.0 | Heavy softening — use when Teacher is very confident |

---

### 1.3 Adaptive Alpha (Dynamic KD Weight)

Instead of fixed α, anneal it during training. Start with high KD weight
(Student learns from Teacher), then shift to task loss (Student learns from labels).

```python
# ugtsdti/losses/kd_adaptive_loss.py
import torch
import torch.nn as nn
import torch.nn.functional as F
from ugtsdti.core.registry import LOSSES


@LOSSES.register("kd_adaptive_loss")
class KDAdaptiveLoss(nn.Module):
    """
    KD loss with linearly decaying alpha.
    alpha starts at alpha_start, decays to alpha_end over total_epochs.
    
    Call loss.step_epoch() at the end of each epoch to update alpha.
    """

    def __init__(
        self,
        alpha_start: float = 0.8,
        alpha_end: float = 0.2,
        total_epochs: int = 50,
        temperature: float = 4.0,
    ):
        super().__init__()
        self.alpha_start = alpha_start
        self.alpha_end = alpha_end
        self.total_epochs = total_epochs
        self.T = temperature
        self.current_epoch = 0
        self.bce = nn.BCEWithLogitsLoss()

    @property
    def alpha(self) -> float:
        progress = min(self.current_epoch / self.total_epochs, 1.0)
        return self.alpha_start + progress * (self.alpha_end - self.alpha_start)

    def step_epoch(self):
        self.current_epoch += 1

    def forward(self, model_outputs: dict, y_true: torch.Tensor) -> torch.Tensor:
        logits = model_outputs["logits"]
        student_logits = model_outputs.get("student_logits")
        teacher_logits = model_outputs.get("teacher_logits")

        task_loss = self.bce(logits, y_true.float())

        if student_logits is None or teacher_logits is None:
            return task_loss

        s_2 = torch.stack([-student_logits, student_logits], dim=-1)
        t_2 = torch.stack([-teacher_logits, teacher_logits], dim=-1)
        kd_loss = F.kl_div(
            F.log_softmax(s_2 / self.T, dim=-1),
            F.softmax(t_2 / self.T, dim=-1),
            reduction="batchmean",
        ) * (self.T ** 2)

        return (1 - self.alpha) * task_loss + self.alpha * kd_loss
```

---

### 1.4 Gate Regularizer Loss

Penalizes the gate from collapsing to always 0 or always 1. Encourages the
gate to actually use both branches.

```python
# Add to any KD loss as an extra term:
def gate_entropy_regularizer(gate_weights: torch.Tensor, reg_weight: float = 0.01) -> torch.Tensor:
    """
    Entropy regularizer: maximize entropy of gate distribution.
    Prevents gate from collapsing to always trust one branch.
    
    gate_weights: (B,) tensor of α values from PairGate, in (0,1)
    """
    # Clamp to avoid log(0)
    alpha = gate_weights.clamp(1e-6, 1 - 1e-6)
    # Binary entropy: -α*log(α) - (1-α)*log(1-α)
    entropy = -(alpha * alpha.log() + (1 - alpha) * (1 - alpha).log())
    return -reg_weight * entropy.mean()  # negative because we maximize entropy
```

---

## 2. Training Schedule (Phase 12.3)

Staged training prevents the gate from learning on random Teacher signals.

### Stage 1: Teacher Pretrain (Epochs 1–N₁)

Train Teacher only. Goal: Teacher learns meaningful graph representations.
Gate and Student are frozen.

```yaml
# configs/model/only_teacher_gcn.yaml
name: hybrid_dti
params:
  student_cfg: null
  teacher_cfg:
    name: gcn_teacher
    params: {hidden_dim: 128, dropout: 0.3}
  fusion_cfg: null
```

```bash
python -m ugtsdti.main model=only_teacher_gcn data=tdc_davis \
    trainer.params.epochs=20
# Save checkpoint: outputs/teacher_pretrained.pt
```

**Stop criterion:** Teacher AUROC on S1 validation > 0.7

---

### Stage 2: Student Pretrain (Epochs 1–N₂)

Train Student only. Goal: Student learns sequence representations independently.

```bash
python -m ugtsdti.main model=only_student_esm_gin data=tdc_davis \
    trainer.params.epochs=20
# Save checkpoint: outputs/student_pretrained.pt
```

**Stop criterion:** Student AUROC on S4 validation > 0.65

---

### Stage 3: Joint Training with KD + Gate (Epochs 1–N₃)

Load pretrained Teacher and Student, train fusion + KD loss together.

```yaml
# configs/model/hybrid_staged.yaml
name: hybrid_dti
params:
  student_cfg:
    name: esm_gin_student
    params: {hidden_dim: 128, freeze_esm: true}
  teacher_cfg:
    name: gcn_teacher
    params: {hidden_dim: 128, dropout: 0.3}
  fusion_cfg:
    name: pairgate_fusion
    params: {gate_hidden: 64, mc_samples: 10}
```

```bash
python -m ugtsdti.main model=hybrid_staged data=tdc_davis \
    trainer.loss.name=kd_kl_loss \
    trainer.loss.alpha=0.5 \
    trainer.loss.temperature=4.0
```

---

### Stage Schedule Summary

```
Epoch 1–20:   Teacher only (only_teacher_gcn)
              → Verify AUROC_S1 > 0.7

Epoch 1–20:   Student only (only_student_esm_gin)  [can run in parallel]
              → Verify AUROC_S4 > 0.65

Epoch 1–50:   Joint hybrid (hybrid_staged) with KD loss
              → Load pretrained weights from Stage 1 & 2
              → Monitor gate α distribution (should vary between S1 and S4)
              → Monitor KD loss convergence
```

---

## 3. Loss Monitoring in WandB

Log these metrics every epoch to diagnose training:

```python
# In Trainer or custom callback:
wandb.log({
    "loss/task": task_loss.item(),
    "loss/kd": kd_loss.item(),
    "loss/total": total_loss.item(),
    "gate/alpha_mean": gate_weights.mean().item(),
    "gate/alpha_std": gate_weights.std().item(),
    "gate/alpha_hist": wandb.Histogram(gate_weights.detach().cpu()),
    "uncertainty/student_var_mean": student_var.mean().item(),
    "uncertainty/teacher_var_mean": teacher_var.mean().item(),
    "kd/alpha": loss_fn.alpha,  # for adaptive loss
})
```

**Healthy training signals:**
- `gate/alpha_mean` on S1 batches: should trend toward 1.0 (trust Teacher)
- `gate/alpha_mean` on S4 batches: should trend toward 0.0 (trust Student)
- `uncertainty/teacher_var_mean` on S4: should be higher than on S1
- `loss/kd` should decrease as Student learns from Teacher

**Warning signs:**
- `gate/alpha_std` ≈ 0: gate collapsed → add gate entropy regularizer
- `loss/kd` not decreasing: Teacher logits not informative → check Teacher training
- `uncertainty/teacher_var_mean` same on S1 and S4: MC-Dropout not working → check dropout rate
