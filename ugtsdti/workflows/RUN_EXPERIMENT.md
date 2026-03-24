# Workflow: Chạy Experiment

Dùng khi: chạy ablation, sweep hyperparameters, hoặc so sánh models.

---

## Configs hiện có

| Config | Model | Dataset | Loss |
|--------|-------|---------|------|
| `model=only_student data=tdc_davis` | BaselineStudent | DAVIS random_split | BCE |
| `model=only_teacher data=tdc_davis` | BaselineTeacher (dummy) | DAVIS random_split | BCE |
| `model=hybrid_baseline data=tdc_davis` | Student + Teacher + PairGate | DAVIS random_split | BCE |
| `model=hybrid_baseline data=tdc_davis trainer.loss.name=kd_dual_loss` | Hybrid | DAVIS random_split | KDDualLoss |

---

## Chạy single run

```bash
python -m ugtsdti.main \
    model=only_student \
    data=tdc_davis \
    trainer.params.epochs=50 \
    trainer.params.lr=0.001 \
    run_name="student_baseline_v1"
```

---

## Chạy ablation suite (4 modes)

```bash
bash scripts/run_baselines.sh
# WandB disabled, epochs=2, dùng để validate pipeline
```

---

## Chạy với WandB

```bash
# Đảm bảo đã login: wandb login
python -m ugtsdti.main \
    model=hybrid_baseline \
    data=tdc_davis \
    logging.wandb_enabled=true \
    run_name="hybrid_pairgate_v1"
```

---

## Hyperparameter sweep với Hydra Optuna

```bash
python -m ugtsdti.main \
    --multirun \
    model=hybrid_baseline \
    data=tdc_davis \
    trainer.params.lr=0.001,0.0001,0.00001 \
    trainer.loss.alpha=0.3,0.5,0.7
```

---

## Cold-start evaluation (S4)

```yaml
# configs/data/tdc_davis_s4.yaml
name: tdc_caching_dataset
params:
  name: DAVIS
  split: train
  split_type: cold_split   # cold_split = S4
  column_name: Drug        # cold on Drug axis
  cache_dir: ./data/cache
  seed: 42
```

```bash
python -m ugtsdti.main model=hybrid_baseline data=tdc_davis_s4
```

---

## Đọc kết quả

Outputs lưu tại `outputs/YYYY-MM-DD/HH-MM-SS/`:
- `.hydra/config.yaml` — full resolved config
- `train.log` — Loguru logs
- WandB run URL in logs nếu enabled

---

## Trước khi tin vào metrics

Xem `task.md` Phase 10.2 — negative sampling audit chưa hoàn thành. Metrics hiện tại có thể bị inflate nếu negative sampling xảy ra sau split (data leakage).
