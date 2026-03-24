# GPU Memory Optimization for T4/P100

## Memory Budget (T4, 16 GB VRAM)

| Component | VRAM Usage |
|-----------|-----------|
| ESM-2 t6 (8M, frozen) | ~0.5 GB |
| ESM-2 t12 (35M, frozen) | ~0.7 GB |
| ESM-2 t30 (150M, frozen) | ~1.5 GB |
| ESM-2 t33 (650M, frozen) | ~5.0 GB |
| ESM-2 t33 (650M, LoRA) | ~3.0 GB |
| GATv2 Teacher (128-dim, 3 layers) | ~0.3 GB |
| GIN Drug Encoder (128-dim, 3 layers) | ~0.1 GB |
| PairGate Fusion | ~0.05 GB |
| Batch (B=32, seq_len=512) | ~1.5 GB |
| Optimizer states (Adam) | ~2× model params |
| **Total (ESM-2 t6 + GATv2 + B=32)** | **~4 GB** ✅ |
| **Total (ESM-2 t33 + GATv2 + B=32)** | **~12 GB** ⚠️ tight |

**Safe configs for T4:**
- ESM-2 t6 + GATv2 + batch_size=64: ~6 GB ✅
- ESM-2 t12 + GATv2 + batch_size=32: ~5 GB ✅
- ESM-2 t33 + GATv2 + batch_size=16 + AMP: ~10 GB ✅
- ESM-2 t33 + GATv2 + batch_size=32 + AMP + grad_ckpt: ~12 GB ⚠️

---

## 1. Automatic Mixed Precision (AMP)

AMP uses FP16 for forward pass, FP32 for optimizer. Cuts VRAM ~40%, speeds
up T4 by ~2×.

```python
# In training loop (if modifying Trainer):
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

for batch in dataloader:
    optimizer.zero_grad()
    
    with autocast():  # FP16 forward pass
        outputs = model(batch)
        loss = criterion(outputs, batch["labels"])
    
    scaler.scale(loss).backward()
    scaler.unscale_(optimizer)
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    scaler.step(optimizer)
    scaler.update()
```

**Hydra config override to enable AMP:**
```python
"trainer.params.use_amp=true"
```

(Requires Trainer to support `use_amp` flag — check `core/trainer.py`.)

---

## 2. Gradient Checkpointing

Trades compute for memory: recomputes activations during backward pass instead
of storing them. Reduces VRAM by ~50% at cost of ~30% slower training.

```python
# For ESM-2:
from transformers import EsmModel

esm = EsmModel.from_pretrained("facebook/esm2_t33_650M_UR50D")
esm.gradient_checkpointing_enable()  # built-in HuggingFace support

# For custom GNN (PyG):
# PyG doesn't have built-in gradient checkpointing for GNN layers.
# Use torch.utils.checkpoint manually:
from torch.utils.checkpoint import checkpoint

class GATv2TeacherWithCheckpoint(nn.Module):
    def forward(self, x, edge_index):
        # Checkpoint each GNN layer
        x = checkpoint(self.conv1, x, edge_index)
        x = checkpoint(self.conv2, x, edge_index)
        return x
```

---

## 3. Frozen Backbone (Most Effective for ESM-2)

Freeze ESM-2 entirely — only train the projection head and downstream layers.
Cuts VRAM by ~60% for ESM-2 t33.

```python
# Freeze all ESM-2 parameters
for param in esm_model.parameters():
    param.requires_grad = False

# Only train projection layer
projection = nn.Linear(esm_hidden_dim, 128)  # trainable
```

**Hydra config:**
```yaml
model:
  params:
    student_cfg:
      name: esm_gin_student
      params:
        freeze_esm: true  # freeze ESM-2 backbone
        esm_model: "facebook/esm2_t6_8M_UR50D"
```

---

## 4. LoRA for ESM-2 (Best of Both Worlds)

LoRA adds small trainable rank-decomposition matrices to attention layers.
Trains only ~1% of parameters while adapting the full model.

```python
from peft import get_peft_model, LoraConfig, TaskType

lora_config = LoraConfig(
    task_type=TaskType.FEATURE_EXTRACTION,
    r=8,                    # rank — lower = less VRAM
    lora_alpha=16,
    target_modules=["query", "value"],  # ESM-2 attention layers
    lora_dropout=0.1,
    bias="none",
)

esm_model = get_peft_model(esm_model, lora_config)
esm_model.print_trainable_parameters()
# Output: trainable params: 294,912 || all params: 8,095,744 || trainable%: 3.64
```

**VRAM savings vs full fine-tuning:**
| Model | Full FT | LoRA r=8 |
|-------|---------|----------|
| ESM-2 t6 | 0.5 GB | 0.3 GB |
| ESM-2 t33 | 5.0 GB | 2.5 GB |

---

## 5. Batch Size Tuning

Find the maximum safe batch size without OOM:

```python
def find_max_batch_size(model, sample_batch_fn, device="cuda", start=128):
    """Binary search for max batch size."""
    lo, hi = 1, start
    best = 1
    
    while lo <= hi:
        mid = (lo + hi) // 2
        try:
            torch.cuda.empty_cache()
            batch = sample_batch_fn(mid)
            with torch.no_grad():
                _ = model(batch)
            best = mid
            lo = mid + 1
        except torch.cuda.OutOfMemoryError:
            hi = mid - 1
    
    print(f"Max safe batch size: {best}")
    return best
```

**Recommended starting points for T4:**
```python
# ESM-2 t6 + GATv2
"trainer.params.batch_size=64"

# ESM-2 t12 + GATv2
"trainer.params.batch_size=32"

# ESM-2 t33 + GATv2 + AMP
"trainer.params.batch_size=16"

# ESM-2 t33 + GATv2 + AMP + grad_ckpt
"trainer.params.batch_size=32"
```

---

## 6. Memory Monitoring

```python
def print_gpu_memory(label=""):
    allocated = torch.cuda.memory_allocated() / 1e9
    reserved = torch.cuda.memory_reserved() / 1e9
    total = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"[{label}] GPU: {allocated:.2f}/{total:.1f} GB allocated, {reserved:.2f} GB reserved")

# Use at key points:
print_gpu_memory("before model load")
model = model.to("cuda")
print_gpu_memory("after model load")
# ... training ...
print_gpu_memory("after first batch")
```

---

## 7. OOM Recovery

```python
def safe_forward(model, batch, device="cuda"):
    """Forward pass with OOM recovery via batch size halving."""
    try:
        return model(batch)
    except torch.cuda.OutOfMemoryError:
        torch.cuda.empty_cache()
        print("OOM! Trying with smaller batch...")
        # Split batch in half and run separately
        half = len(batch["labels"]) // 2
        out1 = model({k: v[:half] for k, v in batch.items()})
        out2 = model({k: v[half:] for k, v in batch.items()})
        return {k: torch.cat([out1[k], out2[k]]) for k in out1}
```

---

## 8. P100 vs T4 Differences

| Feature | T4 | P100 |
|---------|-----|------|
| VRAM | 16 GB | 16 GB |
| FP16 (AMP) | ✅ Fast (Tensor Cores) | ⚠️ Slower (no Tensor Cores) |
| BF16 | ❌ Not supported | ❌ Not supported |
| FP32 | Normal | ✅ Faster than T4 |
| Best for | ESM-2 + AMP | GNN-heavy workloads |

**P100 recommendation:** Disable AMP (`use_amp=false`) — P100 FP16 is not
accelerated by Tensor Cores, so AMP gives no speedup and may cause instability.
