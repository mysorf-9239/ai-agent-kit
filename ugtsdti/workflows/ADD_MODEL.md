# Workflow: Thêm Model mới

Dùng khi: implement một encoder, fusion module, hoặc bất kỳ `nn.Module` nào mới.

---

## Checklist

- [ ] 1. Tạo Python file với `@MODELS.register`
- [ ] 2. Import vào `ugtsdti/models/__init__.py`
- [ ] 3. Tạo YAML config trong `configs/model/`
- [ ] 4. Viết unit test trong `tests/test_models.py`
- [ ] 5. Cập nhật `CONTEXT.md` — thêm model mới vào bảng "Registered components" nếu cần

---

## Bước 1: Python file

Copy từ `.agent/templates/model_plugin.py.template` và điều chỉnh.

**Quy tắc bắt buộc:**
- Decorator `@MODELS.register("snake_case_name")`
- `forward()` phải trả về `{"logits": tensor}` tối thiểu
- Hybrid model có thể trả thêm `"student_logits"`, `"teacher_logits"`

**Batch dict keys có sẵn:**

| Key | Type | Dùng bởi |
|-----|------|----------|
| `batch["drug"]` | PyG Data | Student drug branch |
| `batch["target_ids"]` | LongTensor [seq_len] | Student protein branch |
| `batch["target_mask"]` | LongTensor [seq_len] | Student protein branch |
| `batch["drug_index"]` | LongTensor [1] | Teacher transductive lookup |
| `batch["target_index"]` | LongTensor [1] | Teacher transductive lookup |
| `batch["label"]` | FloatTensor [1] | Trainer (loss) |

**Ví dụ — Student encoder:**
```python
# ugtsdti/models/student/my_encoder.py
from ugtsdti.core.registry import MODELS
import torch.nn as nn

@MODELS.register("my_encoder")
class MyEncoder(nn.Module):
    def __init__(self, hidden_dim: int, dropout: float = 0.1):
        super().__init__()
        self.net = nn.Linear(7, hidden_dim)  # 7 = OGB atom features
        self.dropout = nn.Dropout(dropout)

    def forward(self, batch):
        drug_graph = batch["drug"]
        x = self.dropout(self.net(drug_graph.x))
        # ... pooling
        return {"logits": logits}
```

**Ví dụ — Teacher encoder (transductive):**
```python
# ugtsdti/models/teacher/my_gnn.py
@MODELS.register("my_gnn_teacher")
class MyGNNTeacher(nn.Module):
    def __init__(self, num_nodes: int, hidden_dim: int, dropout: float = 0.1):
        super().__init__()
        # PHẢI có dropout để MC-Dropout hoạt động
        self.dropout = nn.Dropout(dropout)
        # ...

    def forward(self, batch):
        drug_idx = batch["drug_index"].squeeze(-1)
        target_idx = batch["target_index"].squeeze(-1)
        # lookup trong global graph
        return {"logits": logits}
```

---

## Bước 2: Import

```python
# ugtsdti/models/__init__.py — thêm dòng:
from .student.my_encoder import MyEncoder
# hoặc
from .teacher.my_gnn import MyGNNTeacher
```

Import phải có để decorator `@MODELS.register` được trigger khi package load.

---

## Bước 3: YAML config

```yaml
# configs/model/student/my_encoder.yaml
name: my_encoder
params:
  hidden_dim: 128
  dropout: 0.1
```

Để dùng trong hybrid:
```yaml
# configs/model/hybrid_my.yaml
name: hybrid_dti
params:
  student_cfg:
    name: my_encoder
    params:
      hidden_dim: 128
  teacher_cfg:
    name: baseline_teacher
    params:
      hidden_dim: 128
  fusion_cfg:
    name: pairgate_fusion
    params:
      input_dim: 128
      gate_hidden: 64
      mc_samples: 5
```

---

## Bước 4: Unit test

```python
# tests/test_models.py
def test_my_encoder(mock_batch):
    from ugtsdti.models.student.my_encoder import MyEncoder
    model = MyEncoder(hidden_dim=64)
    out = model(mock_batch)
    assert "logits" in out
    assert out["logits"].shape == (BATCH_SIZE,)
```

---

## Bước 5: Cập nhật docs

Nếu model mới là một component quan trọng (encoder mới, fusion mới), cập nhật bảng "Registered components" trong `CONTEXT.md` Section 3 (Current State).
