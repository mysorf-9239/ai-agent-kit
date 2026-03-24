# Wiring a Student Model into UGTS-DTI

## Step-by-Step Checklist

- [ ] 1. Create Python file in `ugtsdti/models/student/`
- [ ] 2. Register with `@MODELS.register("name")`
- [ ] 3. `forward(batch)` reads `batch["drug"]`, `batch["target_ids"]`, `batch["target_mask"]`
- [ ] 4. Return `{"logits": tensor}` minimum
- [ ] 5. Must have `nn.Dropout` layers (MC-Dropout requirement)
- [ ] 6. Import in `ugtsdti/models/__init__.py`
- [ ] 7. Create `configs/model/student/<name>.yaml`
- [ ] 8. Write unit test in `tests/test_models.py`
- [ ] 9. Verify AUROC > baseline_student on S1 and S4

---

## 1. File Structure

```
ugtsdti/models/student/
├── baseline.py           # existing (GlobalMeanPool + Embedding) — working
├── cnn1d.py              # existing — BROKEN, needs fix from protein_encoders.md
├── plm.py                # existing ESMProteinStudent — partially working
├── gin_drug_student.py   # GIN drug + Embedding protein
├── mpnn_drug_student.py  # MPNN drug + Embedding protein
├── attentivefp_student.py # AttentiveFP drug + Embedding protein
├── esm_student.py        # simple drug + ESM-2 protein
├── esm_gin_student.py    # GIN drug + ESM-2 protein (BEST)
└── esm_lora_student.py   # GIN drug + ESM-2 + LoRA
```

---

## 2. Import in `__init__.py`

```python
# ugtsdti/models/__init__.py — add lines:
from .student.gin_drug_student import GINStudent
from .student.mpnn_drug_student import MPNNStudent
from .student.attentivefp_student import AttentiveFPStudent
from .student.esm_student import ESMProteinStudent
from .student.esm_gin_student import ESMGINStudent
from .student.esm_lora_student import ESMLoRAStudent
```

---

## 3. YAML Configs

```yaml
# configs/model/only_student_gin.yaml
name: hybrid_dti
params:
  student_cfg:
    name: gin_student
    params:
      hidden_dim: 128
      num_layers: 3
      dropout: 0.3
  teacher_cfg: null
  fusion_cfg: null
```

```yaml
# configs/model/hybrid_esm_gin_gcn.yaml
name: hybrid_dti
params:
  student_cfg:
    name: esm_gin_student
    params:
      esm_model_name: "facebook/esm2_t12_35M_UR50D"
      hidden_dim: 128
      gin_layers: 3
      dropout: 0.3
      freeze_esm: true
  teacher_cfg:
    name: gcn_teacher
    params:
      drug_feat_dim: 2048
      protein_feat_dim: 8000
      hidden_dim: 128
      num_layers: 2
      dropout: 0.3
  fusion_cfg:
    name: pairgate_fusion
    params:
      input_dim: 128
      gate_hidden: 64
      mc_samples: 10
```

---

## 4. Unit Test Template

```python
# tests/test_models.py
import torch
from torch_geometric.data import Data, Batch

BATCH_SIZE = 4
SEQ_LEN = 64
ATOM_FEAT = 7


def _make_mock_batch(batch_size=BATCH_SIZE, seq_len=SEQ_LEN):
    """Create a mock multimodal batch matching TDCCachingDataset format."""
    # Create individual PyG graphs and batch them
    graphs = []
    for _ in range(batch_size):
        n_atoms = torch.randint(5, 20, (1,)).item()
        g = Data(
            x=torch.randn(n_atoms, ATOM_FEAT),
            edge_index=torch.randint(0, n_atoms, (2, n_atoms * 2)),
            edge_attr=torch.randn(n_atoms * 2, 3),
        )
        graphs.append(g)
    drug_batch = Batch.from_data_list(graphs)

    return {
        "drug": drug_batch,
        "target_ids": torch.randint(1, 26, (batch_size, seq_len)),
        "target_mask": torch.ones(batch_size, seq_len, dtype=torch.long),
        "label": torch.randint(0, 2, (batch_size,)).float(),
        "drug_index": torch.randint(0, 68, (batch_size, 1)),
        "target_index": torch.randint(0, 442, (batch_size, 1)),
    }


def test_gin_student():
    from ugtsdti.models.student.gin_drug_student import GINStudent
    model = GINStudent(hidden_dim=64, num_layers=2)
    batch = _make_mock_batch()
    out = model(batch)
    assert "logits" in out
    assert out["logits"].shape == (BATCH_SIZE,)


def test_cnn1d_student():
    from ugtsdti.models.student.cnn1d import CNN1DStudent
    model = CNN1DStudent(hidden_dim=64)
    batch = _make_mock_batch()
    out = model(batch)
    assert "logits" in out
    assert out["logits"].shape == (BATCH_SIZE,)


def test_esm_gin_student():
    """Test ESM-GIN student with small ESM model."""
    from ugtsdti.models.student.esm_gin_student import ESMGINStudent
    model = ESMGINStudent(
        esm_model_name="facebook/esm2_t6_8M_UR50D",
        hidden_dim=64,
        gin_layers=2,
        freeze_esm=True,
    )
    batch = _make_mock_batch()
    out = model(batch)
    assert "logits" in out
    assert out["logits"].shape == (BATCH_SIZE,)


def test_student_mc_dropout_variance():
    """Student must produce non-zero variance under MC-Dropout."""
    from ugtsdti.models.student.gin_drug_student import GINStudent
    model = GINStudent(hidden_dim=64, dropout=0.3)
    model.train()
    batch = _make_mock_batch(batch_size=2)

    logits = torch.stack([model(batch)["logits"] for _ in range(20)])
    variance = logits.var(dim=0)
    assert (variance > 0).all(), "MC-Dropout must produce non-zero variance"
```

---

## 5. Validation Checklist After Implementation

```bash
# 1. Student-only baseline — should beat current baseline_student
python -m ugtsdti.main model=only_student_gin data=tdc_davis

# 2. Cold-start test — GIN+ESM should be much better than GIN+Embedding on S4
python -m ugtsdti.main model=only_student_gin data=tdc_davis_s4
python -m ugtsdti.main model=only_student_esm_gin data=tdc_davis_s4

# 3. Hybrid — verify gate behavior
python -m ugtsdti.main model=hybrid_esm_gin_gcn data=tdc_davis
```

Expected results:
- S1: Teacher ≥ Student (graph context helps)
- S4: Student >> Teacher (sequence generalizes, graph fails)
- Hybrid S4: ≈ Student (gate correctly trusts Student)
- Hybrid S1: ≈ Teacher or better (gate correctly trusts Teacher)

---

## 6. Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `AttributeError: 'Batch' has no attribute 'batch'` | Drug not batched via `Batch.from_data_list` | Check DataLoader collate_fn |
| `RuntimeError: Expected all tensors on same device` | ESM on CPU, drug graph on GPU | Move batch to device before forward |
| `CUDA OOM` with ESM-2 | Model too large or batch too big | Use frozen ESM-2 t12, reduce batch size, enable gradient checkpointing |
| `IndexError: index out of range in self` | `target_ids` has token > `vocab_size` | Check ESM tokenizer vocab size matches model |
| Variance ≈ 0 in MC-Dropout | Dropout disabled or rate too low | Ensure `model.train()` in `_mc_forward`, use `dropout ≥ 0.2` |
| ESM slow on first run | Downloading model weights | Pre-download: `from transformers import EsmModel; EsmModel.from_pretrained("facebook/esm2_t12_35M_UR50D")` |
