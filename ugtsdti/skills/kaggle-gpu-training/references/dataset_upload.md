# Uploading to Kaggle Datasets

## Overview

Kaggle Datasets are the mechanism for getting files into `/kaggle/input/`.
Datasets are accessible from notebooks **even with internet OFF** — this is
the key mechanism for offline package installs and pre-built data.

You need separate datasets for:
1. **Code** — the `ugtsdti` package source
2. **Data** — TDC cache, pre-built DD/PP graphs
3. **Weights** — ESM-2 model files, pretrained checkpoints
4. **Wheels** — pre-downloaded pip wheels (for offline install)

---

## 1. Kaggle CLI Setup

```bash
pip install kaggle

# Download kaggle.json from kaggle.com → Account → API → Create New API Token
mkdir -p ~/.kaggle
cp ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

---

## 2. Create a Dataset (Correct Workflow)

The correct workflow uses `kaggle datasets init` to generate metadata, then
`kaggle datasets create` to upload.

```bash
# Step 1: Create folder with files to upload
mkdir kaggle_upload_code
cp -r ugtsdti/ kaggle_upload_code/
cp setup.py pyproject.toml requirements.txt kaggle_upload_code/

# Step 2: Generate metadata file (creates datapackage.json)
kaggle datasets init -p kaggle_upload_code/

# Step 3: Edit datapackage.json — set id to your username/dataset-name
# {
#   "title": "ugtsdti-code",
#   "id": "<your-username>/ugtsdti-code",
#   "licenses": [{"name": "other"}]
# }

# Step 4: Create dataset (first time only)
kaggle datasets create -p kaggle_upload_code/

# Step 5: Update dataset (subsequent times)
kaggle datasets version -p kaggle_upload_code/ -m "Phase 11: GATv2 teacher"
```

Source: [Kaggle Setup Guide](https://isaac-flath.github.io/fastblog/kaggle/getting%20started/2021/03/25/KaggleSetupGuide.html)

---

## 3. Attach Dataset to Notebook

In notebook editor: right panel → **Input** → **Add Data** → **Your Datasets** → select dataset.

Appears at: `/kaggle/input/<dataset-name>/`

---

## 4. Upload Data Dataset (TDC Cache + Graphs)

Pre-build the TDC cache and DD/PP graphs locally, then upload to avoid
recomputing on Kaggle (~10 min saved per session).

```bash
# Local: build cache by running once
python -m ugtsdti.main data=tdc_davis trainer.params.epochs=0

# Collect cache files
mkdir kaggle_upload_data
cp -r ~/.cache/ugtsdti/tdc/ kaggle_upload_data/tdc_cache/
# If DD/PP graphs are pre-built:
cp -r data/graphs/ kaggle_upload_data/graphs/

kaggle datasets init -p kaggle_upload_data/
# Edit datapackage.json: id = "<username>/ugtsdti-data"
kaggle datasets create -p kaggle_upload_data/
```

In notebook:
```python
os.environ["UGTSDTI_CACHE_DIR"] = "/kaggle/input/ugtsdti-data/tdc_cache"
```

---

## 5. Upload Model Weights (ESM-2)

```python
# Local: download ESM-2 weights from HuggingFace
from transformers import EsmModel, EsmTokenizer

for model_name in ["facebook/esm2_t6_8M_UR50D", "facebook/esm2_t12_35M_UR50D"]:
    short = model_name.split("/")[1]
    model = EsmModel.from_pretrained(model_name)
    tokenizer = EsmTokenizer.from_pretrained(model_name)
    model.save_pretrained(f"./kaggle_upload_weights/{short}/")
    tokenizer.save_pretrained(f"./kaggle_upload_weights/{short}/")
```

```bash
kaggle datasets init -p kaggle_upload_weights/
# Edit datapackage.json: id = "<username>/ugtsdti-weights"
kaggle datasets create -p kaggle_upload_weights/
```

In notebook (internet OFF):
```python
os.environ["TRANSFORMERS_CACHE"] = "/kaggle/input/ugtsdti-weights"
os.environ["HF_DATASETS_OFFLINE"] = "1"

from transformers import EsmModel
esm = EsmModel.from_pretrained(
    "/kaggle/input/ugtsdti-weights/esm2_t6_8M_UR50D/"
)
```

---

## 6. Upload Pip Wheels (for offline install)

```bash
# Local: download wheels for the target platform
pip download torch-geometric torch-scatter torch-sparse rdkit PyTDC \
    wandb hydra-core hydra-optuna-sweeper omegaconf loguru peft optuna \
    -d ./kaggle_upload_wheels/ \
    --platform manylinux2014_x86_64 \
    --python-version 3.10

kaggle datasets init -p kaggle_upload_wheels/
# Edit datapackage.json: id = "<username>/ugtsdti-wheels"
kaggle datasets create -p kaggle_upload_wheels/
```

In notebook:
```python
subprocess.run([
    "pip", "install", "-q", "--no-index",
    "--find-links=/kaggle/input/ugtsdti-wheels/",
    "torch-geometric", "rdkit", "PyTDC", "wandb",
    "hydra-core", "hydra-optuna-sweeper", "peft", "optuna"
], check=True)
```

---

## 7. Dataset Size Limits

| Limit | Value |
|-------|-------|
| Total storage per account | 100 GB |
| Single dataset | 100 GB |
| Single file | 20 GB |

ESM-2 t6 ≈ 32 MB, ESM-2 t33 ≈ 2.5 GB, DD/PP graphs for DAVIS ≈ 5–50 MB — all fine.

---

## 8. Versioning

```bash
# After each significant change:
kaggle datasets version -p kaggle_upload_code/ -m "Phase 11: GATv2 teacher"
kaggle datasets version -p kaggle_upload_weights/ -m "Teacher pretrained epoch 20"
```

In notebook, pin to a specific version via the Input panel version dropdown.
