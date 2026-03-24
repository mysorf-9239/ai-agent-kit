# Fusion Module Wiring Guide

## Step-by-Step Checklist

Follow this checklist every time you add a new fusion module to UGTS-DTI.

### Step 1 — Create the module file

```
ugtsdti/models/fusion/<name>_fusion.py
```

Minimum required structure:

```python
import torch.nn as nn
from ugtsdti.core.registry import MODELS


@MODELS.register("<name>_fusion")
class <Name>Fusion(nn.Module):
    """One-line description."""

    def __init__(self, **kwargs):
        super().__init__()
        # ... layers ...

    def forward(self, student_logits, teacher_logits, student_var=None, teacher_var=None):
        # Must return a (B,) tensor — NOT a dict
        ...
```

**Signature contract:**
- `student_logits`: `(B,)` float tensor
- `teacher_logits`: `(B,)` float tensor
- `student_var`: `(B,)` float tensor or `None` (MC-Dropout variance)
- `teacher_var`: `(B,)` float tensor or `None`
- Return: `(B,)` float tensor (fused logit, not probability)

Always handle `student_var is None` gracefully — fall back to simple average.

---

### Step 2 — Register in `__init__.py`

Open `ugtsdti/models/__init__.py` and add the import:

```python
from ugtsdti.models.fusion.<name>_fusion import <Name>Fusion  # noqa: F401
```

The `# noqa: F401` suppresses "imported but unused" warnings — the import
is needed to trigger the `@MODELS.register(...)` decorator.

---

### Step 3 — Create YAML config

```
configs/model/fusion/<name>.yaml
```

```yaml
# configs/model/fusion/<name>.yaml
name: <name>_fusion
params:
  # list all __init__ kwargs with their defaults
  hidden_dim: 64
  dropout: 0.1
```

---

### Step 4 — Wire into a hybrid config

Create or update a hybrid model config that references the new fusion:

```yaml
# configs/model/hybrid_<name>.yaml
name: hybrid_dti
params:
  student_cfg:
    name: baseline_student
    params: {}
  teacher_cfg:
    name: baseline_teacher
    params: {}
  fusion_cfg:
    name: <name>_fusion
    params:
      hidden_dim: 64
      dropout: 0.1
```

---

### Step 5 — Write a unit test

Add to `tests/test_models.py` (or `tests/test_models_extended.py`):

```python
import torch
import pytest
from ugtsdti.models.fusion.<name>_fusion import <Name>Fusion


def test_<name>_fusion_output_shape():
    B = 8
    model = <Name>Fusion(hidden_dim=32, dropout=0.0)
    s_logits = torch.randn(B)
    t_logits = torch.randn(B)
    s_var = torch.rand(B)
    t_var = torch.rand(B)

    out = model(s_logits, t_logits, s_var, t_var)
    assert out.shape == (B,), f"Expected ({B},), got {out.shape}"


def test_<name>_fusion_no_var_fallback():
    """Fusion must not crash when uncertainty is unavailable."""
    B = 8
    model = <Name>Fusion(hidden_dim=32, dropout=0.0)
    s_logits = torch.randn(B)
    t_logits = torch.randn(B)

    out = model(s_logits, t_logits)  # no var args
    assert out.shape == (B,)


def test_<name>_fusion_registry():
    from ugtsdti.core.registry import MODELS
    assert "<name>_fusion" in MODELS._registry
```

Run with:
```bash
pytest tests/test_models.py -k "<name>" -v
```

---

### Step 6 — Validate end-to-end

Run a quick smoke test with the new fusion config:

```bash
python -m ugtsdti.main \
    model=hybrid_<name> \
    data=tdc_davis \
    trainer.params.epochs=2 \
    trainer.params.batch_size=32
```

Expected: no crash, AUROC printed at end of epoch 2.

---

### Step 7 — Run ablation

Always compare against baselines before claiming improvement:

```bash
# Baselines
python -m ugtsdti.main model=only_student data=tdc_davis
python -m ugtsdti.main model=only_teacher data=tdc_davis

# New fusion
python -m ugtsdti.main model=hybrid_<name> data=tdc_davis

# Existing fusion (comparison)
python -m ugtsdti.main model=hybrid_baseline data=tdc_davis
```

---

## File Structure Reference

After adding a new fusion module, the directory should look like:

```
ugtsdti/models/fusion/
├── pairgate.py              # existing — uncertainty-gated (current default)
├── pairgate_v2.py           # existing — richer gate input
├── simple_avg_fusion.py     # existing — sanity check baseline
├── weighted_avg_fusion.py   # existing — learnable scalar gate
├── concat_mlp_fusion.py     # existing — non-uncertainty baseline
├── <name>_fusion.py         # NEW — your module here

configs/model/fusion/
├── pairgate.yaml
├── pairgate_v2.yaml
├── simple_avg.yaml
├── weighted_avg.yaml
├── concat_mlp.yaml
├── <name>.yaml              # NEW — your config here

configs/model/
├── hybrid_baseline.yaml     # existing
├── hybrid_<name>.yaml       # NEW — full hybrid config using your fusion
```

---

## HybridDTIModel Integration

`HybridDTIModel` in `ugtsdti/models/hybrid.py` calls fusion like this:

```python
# Inside HybridDTIModel.forward():
fused_logits = self.fusion(
    student_logits=student_out["logits"],
    teacher_logits=teacher_out["logits"],
    student_var=student_out.get("uncertainty"),
    teacher_var=teacher_out.get("uncertainty"),
)
```

Your fusion module receives scalar logits `(B,)` and optional variance `(B,)`.
If your fusion needs embeddings (e.g., Bilinear, CrossAttention), you must
also modify `HybridDTIModel` to expose `student_emb` and `teacher_emb` in
the branch outputs — see `fusion_catalogue.md` notes for those strategies.

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `KeyError: '<name>_fusion' not in registry` | Import not added to `__init__.py` | Add `from ugtsdti.models.fusion.<name>_fusion import <Name>Fusion` |
| `RuntimeError: shape mismatch` | Logits are `(B,1)` not `(B,)` | Add `.squeeze(-1)` before returning |
| `TypeError: forward() missing argument` | Caller passes positional args | Use keyword args in `HybridDTIModel` call |
| `NaN loss after epoch 1` | Gate output is 0 or 1 exactly | Add `.clamp(1e-6, 1-1e-6)` to gate sigmoid output |
| `gate/alpha_std ≈ 0` in WandB | Gate collapsed | Add gate entropy regularizer (see `kd_loss_and_schedule.md`) |
| `AttributeError: 'NoneType' object` | `student_var` is None but code doesn't guard | Add `if student_var is None: return fallback` |
| Fusion not improving over baselines | Fusion trains on random Teacher signal | Use staged training (see `kd_loss_and_schedule.md` Stage 1-3) |
