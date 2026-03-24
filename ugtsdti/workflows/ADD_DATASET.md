# Workflow: Thêm Dataset mới

Dùng khi: thêm dataset mới (KIBA, BindingDB, custom) hoặc split strategy mới.

---

## Checklist

- [ ] 1. Tạo Python file với `@DATASETS.register`
- [ ] 2. Import vào `ugtsdti/data/__init__.py`
- [ ] 3. Tạo YAML config trong `configs/data/`
- [ ] 4. Viết unit test trong `tests/test_data.py`

---

## Quy tắc bắt buộc

`__getitem__` phải trả về dict với đúng keys sau:

| Key | Type | Mô tả |
|-----|------|-------|
| `drug` | PyG Data | Molecular graph từ RDKit |
| `target_ids` | LongTensor [seq_len] | ESM token IDs |
| `target_mask` | LongTensor [seq_len] | ESM attention mask |
| `label` | FloatTensor [1] | Affinity value (raw hoặc binary) |
| `drug_index` | LongTensor [1] | MD5 hash của SMILES % 100003 |
| `target_index` | LongTensor [1] | MD5 hash của FASTA % 100003 |

Thiếu bất kỳ key nào sẽ làm vỡ Student hoặc Teacher branch.

---

## Cách nhanh nhất: Kế thừa TDCCachingDataset

Nếu dataset có trong PyTDC, chỉ cần tạo config YAML mới:

```yaml
# configs/data/tdc_kiba.yaml
name: tdc_caching_dataset
params:
  name: KIBA
  split: train
  split_type: random_split   # random_split = S1, cold_split = S4
  cache_dir: ./data/cache
  seed: 42
```

PyTDC dataset names: `DAVIS`, `KIBA`, `BindingDB_Kd`.
Split types: `random_split` (S1), `cold_split` (S4 — cold drug by default).

---

## Nếu cần dataset custom

```python
# ugtsdti/data/datasets/my_dataset.py
import hashlib
import torch
from torch.utils.data import Dataset
from ugtsdti.core.registry import DATASETS
from ugtsdti.data.transforms.chemistry import smiles_to_graph
from ugtsdti.data.transforms.sequence import ESMSequenceTokenizer

@DATASETS.register("my_dataset")
class MyDataset(Dataset):
    def __init__(self, csv_path: str, split: str = "train", cache_dir: str = "./data/cache"):
        super().__init__()
        # load, split, preprocess, cache
        self.data = self._load_or_cache(csv_path, split, cache_dir)

    def _load_or_cache(self, csv_path, split, cache_dir):
        cache_file = f"{cache_dir}/my_dataset_{split}.pt"
        if os.path.exists(cache_file):
            return torch.load(cache_file)
        # process...
        tokenizer = ESMSequenceTokenizer()
        processed = []
        for row in data:
            drug_graph = smiles_to_graph(row["smiles"])
            if drug_graph is None:
                continue
            tokens = tokenizer.encode(row["fasta"])
            d_hash = int(hashlib.md5(row["smiles"].encode()).hexdigest(), 16) % 100003
            t_hash = int(hashlib.md5(row["fasta"].encode()).hexdigest(), 16) % 100003
            processed.append({
                "drug": drug_graph,
                "target_ids": tokens["input_ids"],
                "target_mask": tokens["attention_mask"],
                "label": torch.tensor([row["y"]], dtype=torch.float32),
                "drug_index": torch.tensor([d_hash], dtype=torch.long),
                "target_index": torch.tensor([t_hash], dtype=torch.long),
            })
        torch.save(processed, cache_file)
        return processed

    def __len__(self): return len(self.data)
    def __getitem__(self, idx): return self.data[idx]
```

---

## Import

```python
# ugtsdti/data/__init__.py
from .datasets.my_dataset import MyDataset
```

---

## YAML config

```yaml
# configs/data/my_dataset.yaml
name: my_dataset
params:
  csv_path: ./data/my_data.csv
  split: train
  cache_dir: ./data/cache
```
