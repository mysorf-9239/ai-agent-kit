# Wiring a Teacher Model into UGTS-DTI

## Step-by-Step Checklist

- [ ] 1. Create Python file in `ugtsdti/models/teacher/`
- [ ] 2. Register with `@MODELS.register("name")`
- [ ] 3. Implement `set_graphs(dd_graph, pp_graph)` method
- [ ] 4. `forward(batch)` reads `batch["drug_index"]` and `batch["target_index"]`
- [ ] 5. Return `{"logits": tensor}` minimum
- [ ] 6. Import in `ugtsdti/models/__init__.py`
- [ ] 7. Create `configs/model/teacher/<name>.yaml`
- [ ] 8. Wire graph loading in training entry point
- [ ] 9. Write unit test in `tests/test_models.py`
- [ ] 10. Verify AUROC > 0.5 on S1 with `model=only_teacher`

---

## 1. File Structure

```
ugtsdti/models/teacher/
├── baseline.py       # existing dummy (nn.Embedding only)
├── gcn_teacher.py    # GCN
├── gat_teacher.py    # GAT
├── gatv2_teacher.py  # GATv2 (recommended)
├── gin_teacher.py    # GIN
└── sage_teacher.py   # GraphSAGE
```

---

## 2. Import in `__init__.py`

```python
# ugtsdti/models/__init__.py — add lines:
from .teacher.gcn_teacher import GCNTeacher
from .teacher.gat_teacher import GATTeacher
from .teacher.gatv2_teacher import GATv2Teacher
from .teacher.gin_teacher import GINTeacher
from .teacher.sage_teacher import SAGETeacher
```

Import must exist for `@MODELS.register` decorator to trigger at package load.

---

## 3. YAML Configs

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

```yaml
# configs/model/only_teacher_gcn.yaml
name: hybrid_dti
params:
  student_cfg: null
  teacher_cfg:
    name: gcn_teacher
    params:
      drug_feat_dim: 2048
      protein_feat_dim: 8000
      hidden_dim: 128
      num_layers: 2
      dropout: 0.3
  fusion_cfg: null
```

```yaml
# configs/model/hybrid_gcn_teacher.yaml
name: hybrid_dti
params:
  student_cfg:
    name: baseline_student
    params:
      hidden_dim: 128
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

## 4. Graph Loading in Training Entry Point

The Teacher needs graphs loaded before `trainer.fit()`. Add to `ugtsdti/main.py`:

```python
# ugtsdti/main.py — inside @hydra.main
from ugtsdti.data.graph_builder import build_and_cache_graphs, load_graphs

# Build/load graphs if teacher is present
if cfg.model.params.get("teacher_cfg") is not None:
    graphs = build_and_cache_graphs(
        smiles_list=dataset.get_drug_smiles(),   # ordered list
        fasta_list=dataset.get_protein_fasta(),  # ordered list
    )
    teacher = model.teacher  # access via HybridDTIModel
    if hasattr(teacher, "set_graphs"):
        dd = graphs["dd"].to(device)
        pp = graphs["pp"].to(device)
        teacher.set_graphs(dd, pp)
```

**Important:** Move graphs to the same device as the model before `set_graphs`.

---

## 5. Unit Test Template

```python
# tests/test_models.py
import torch
from torch_geometric.data import Data

def _make_mock_graphs(n_drugs=10, n_proteins=15, drug_feat=2048, prot_feat=8000):
    dd = Data(
        x=torch.randn(n_drugs, drug_feat),
        edge_index=torch.randint(0, n_drugs, (2, 20)),
        num_nodes=n_drugs,
    )
    pp = Data(
        x=torch.randn(n_proteins, prot_feat),
        edge_index=torch.randint(0, n_proteins, (2, 30)),
        num_nodes=n_proteins,
    )
    return dd, pp

def test_gcn_teacher():
    from ugtsdti.models.teacher.gcn_teacher import GCNTeacher
    model = GCNTeacher(drug_feat_dim=2048, protein_feat_dim=8000, hidden_dim=64)
    dd, pp = _make_mock_graphs()
    model.set_graphs(dd, pp)

    batch = {
        "drug_index": torch.randint(0, 10, (4, 1)),
        "target_index": torch.randint(0, 15, (4, 1)),
    }
    out = model(batch)
    assert "logits" in out
    assert out["logits"].shape == (4,)

def test_mc_dropout_variance():
    """Teacher must produce non-zero variance under MC-Dropout."""
    from ugtsdti.models.teacher.gcn_teacher import GCNTeacher
    model = GCNTeacher(dropout=0.3)
    dd, pp = _make_mock_graphs()
    model.set_graphs(dd, pp)
    model.train()  # activate dropout

    batch = {"drug_index": torch.zeros(4, 1, dtype=torch.long),
             "target_index": torch.zeros(4, 1, dtype=torch.long)}

    logits = torch.stack([model(batch)["logits"] for _ in range(20)])
    variance = logits.var(dim=0)
    assert (variance > 0).all(), "MC-Dropout must produce non-zero variance"
```

---

## 6. Validation Checklist After Implementation

Run these checks before using Teacher in hybrid:

```bash
# 1. Teacher-only baseline — should beat random (AUROC > 0.5) on S1
python -m ugtsdti.main model=only_teacher_gcn data=tdc_davis

# 2. Check gate behavior on S1 vs S4
# Expected: alpha (gate weight) higher on S1, lower on S4
python -m ugtsdti.main model=hybrid_gcn_teacher data=tdc_davis
python -m ugtsdti.main model=hybrid_gcn_teacher data=tdc_davis_s4

# 3. Verify uncertainty is higher on S4 than S1
# Check WandB logs: teacher_uncertainty mean should be higher on S4
```

---

## 7. Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `AttributeError: 'NoneType' has no attribute 'x'` | `set_graphs()` not called | Call `set_graphs` before `trainer.fit()` |
| `IndexError: index out of bounds` | Index alignment mismatch | Verify `dd_graph.num_nodes == len(unique_drugs)` |
| `RuntimeError: size mismatch` | Wrong `drug_feat_dim` in config | Match config to actual fingerprint dim |
| Variance ≈ 0 in MC-Dropout | Dropout rate too low or model in eval mode | Use `dropout ≥ 0.2`, force `model.train()` in `_mc_forward` |
| AUROC ≈ 0.5 on S1 | Graph not built from meaningful features | Check fingerprints are non-zero, graph has edges |
