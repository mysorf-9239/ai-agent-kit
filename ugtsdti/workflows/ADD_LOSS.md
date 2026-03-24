# Workflow: Thêm Loss mới

Dùng khi: thêm loss function mới (focal loss, contrastive, KL-divergence KD, v.v.)

---

## Checklist

- [ ] 1. Tạo Python file với `@LOSSES.register`
- [ ] 2. Import vào `ugtsdti/losses/__init__.py`
- [ ] 3. Cập nhật YAML config nếu cần params mới
- [ ] 4. Viết unit test trong `tests/test_losses.py`

---

## Interface bắt buộc

```python
def forward(self, model_outputs: dict, y_true: torch.Tensor) -> torch.Tensor:
    ...
```

`model_outputs` luôn có:
- `model_outputs["logits"]` — fused output (hoặc student/teacher nếu single branch)
- `model_outputs["student_logits"]` — chỉ có khi hybrid mode
- `model_outputs["teacher_logits"]` — chỉ có khi hybrid mode

---

## Ví dụ: Focal Loss

```python
# ugtsdti/losses/focal.py
import torch
import torch.nn as nn
from ugtsdti.core.registry import LOSSES

@LOSSES.register("focal_loss")
class FocalLoss(nn.Module):
    def __init__(self, alpha: float = 0.25, gamma: float = 2.0):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, model_outputs: dict, y_true: torch.Tensor) -> torch.Tensor:
        logits = model_outputs["logits"]
        bce = nn.functional.binary_cross_entropy_with_logits(logits, y_true, reduction="none")
        pt = torch.exp(-bce)
        focal = self.alpha * (1 - pt) ** self.gamma * bce
        return focal.mean()
```

Import:
```python
# ugtsdti/losses/__init__.py
from .focal import FocalLoss
```

Dùng từ CLI:
```bash
python -m ugtsdti.main trainer.loss.name=focal_loss trainer.loss.alpha=0.25 trainer.loss.gamma=2.0
```

---

## Ví dụ: KL-Divergence KD (thay thế MSE trong KDDualLoss)

```python
@LOSSES.register("kd_kl_loss")
class KDKLLoss(nn.Module):
    """KD với KL-divergence và temperature scaling."""
    def __init__(self, alpha: float = 0.5, temperature: float = 4.0):
        super().__init__()
        self.alpha = alpha
        self.T = temperature
        self.task_loss = nn.BCEWithLogitsLoss()

    def forward(self, model_outputs: dict, y_true: torch.Tensor) -> torch.Tensor:
        main_loss = self.task_loss(model_outputs["logits"], y_true)
        if "student_logits" in model_outputs and "teacher_logits" in model_outputs:
            s = model_outputs["student_logits"] / self.T
            t = model_outputs["teacher_logits"] / self.T
            # KL(student || teacher)
            kl = nn.functional.kl_div(
                nn.functional.logsigmoid(s),
                torch.sigmoid(t),
                reduction="batchmean"
            )
            return (1 - self.alpha) * main_loss + self.alpha * (self.T ** 2) * kl
        return main_loss
```

**Lưu ý:** Không sửa `KDDualLoss` hiện có — thêm loss mới và register riêng.
