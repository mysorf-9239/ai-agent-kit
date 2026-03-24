# Architecture Decisions

Ghi lại các quyết định thiết kế quan trọng, lý do chọn, và alternatives đã bỏ.
Format: `[DATE] Decision — Rationale — Alternatives considered`

---

## Core Architecture

### [2026-03] Hybrid Teacher-Student thay vì single encoder
**Decision:** Dùng hai nhánh encoder (graph + sequence) kết hợp qua gate.
**Rationale:** Single encoder không giải quyết được cả S1 lẫn S4 cùng lúc. Graph encoder mạnh ở S1 (có context toàn graph) nhưng fail ở S4 (node mới không có trong graph). Sequence encoder ngược lại.
**Alternatives:** ESM-only (tốt cho cold-start nhưng bỏ qua graph structure), GNN-only (MIDTI approach, fail ở S4).

### [2026-03] MC-Dropout cho uncertainty thay vì Deep Ensembles
**Decision:** Dùng MC-Dropout (N forward passes với dropout active) để ước lượng epistemic uncertainty.
**Rationale:** Deep Ensembles chính xác hơn nhưng tốn gấp N lần memory và compute. MC-Dropout là approximation đủ tốt cho mục đích gating, không cần calibration hoàn hảo.
**Alternatives:** Deep Ensembles (quá tốn), Bayesian Neural Networks (quá phức tạp để implement), Conformal Prediction (không phù hợp cho gating real-time).

### [2026-03] Soft gate (α ∈ (0,1)) thay vì hard switch
**Decision:** PairGate output là scalar weight α, fused = α·logit_t + (1−α)·logit_s.
**Rationale:** Hard switch (chọn một trong hai) không differentiable và không tận dụng được thông tin từ cả hai nhánh. Soft gate cho phép gradient flow qua cả hai nhánh.
**Alternatives:** Hard argmax gate (không differentiable), Mixture of Experts (phức tạp hơn cần thiết).

### [2026-03] MSE distillation thay vì KL-divergence
**Decision:** KDDualLoss dùng MSE(logit_s, logit_t) thay vì KL(softmax(logit_s/T) || softmax(logit_t/T)).
**Rationale:** DTI là binary classification với logits không nhất thiết calibrated. MSE đơn giản hơn, không cần temperature scaling, phù hợp cho regression-style alignment.
**Alternatives:** KL-divergence với temperature (chuẩn hơn cho classification KD, sẽ thêm sau khi Teacher thật có logits có nghĩa).
**Status:** Sẽ revisit khi Teacher GNN thật được implement (Phase 12.2).

---

## Data Pipeline

### [2026-03] PyTDC thay vì custom data loader
**Decision:** Dùng `tdc.multi_pred.DTI` để fetch data và split S1-S4.
**Rationale:** PyTDC cung cấp standardized benchmarks, S1-S4 splits chuẩn, negative sampling built-in. Tránh reinvent the wheel và đảm bảo reproducibility với community.
**Alternatives:** Custom CSV loader (đã có `dti_standard_dataset` nhưng là scaffold rỗng, bỏ).

### [2026-03] Disk cache `.pt` thay vì on-the-fly processing
**Decision:** Preprocess SMILES→PyG graph và FASTA→ESM tokens một lần, lưu vào `data/cache/*.pt`.
**Rationale:** RDKit và ESM tokenizer tốn thời gian. Cache tránh recompute mỗi epoch. Đặc biệt quan trọng khi chạy nhiều ablation runs.
**Alternatives:** On-the-fly (chậm), HDF5 (phức tạp hơn cần thiết).

### [2026-03] MD5 hash cho drug_index/target_index
**Decision:** `drug_index = MD5(SMILES) % 100003` để tạo deterministic node ID cho Teacher transductive lookup.
**Rationale:** Teacher cần integer index để lookup trong global embedding table. MD5 modulo large prime cho collision rate thấp (~0.01% với DAVIS ~68k pairs).
**Alternatives:** Sequential integer ID (cần global mapping table, phức tạp hơn), UUID (không phải integer).
**Known issue:** Collision có thể xảy ra. Cần audit khi Teacher GNN thật được implement.

---

## Engineering

### [2026-03] Hydra + Registry pattern thay vì argparse
**Decision:** Dùng Hydra cho config management, Registry pattern cho plugin system.
**Rationale:** Hydra cho phép compose configs, override từ CLI, multirun sweeps. Registry pattern cho phép thêm model/dataset/loss mà không sửa core code.
**Alternatives:** argparse (không composable), gin-config (ít phổ biến hơn trong ML community).

### [2026-03] WandB thay vì TensorBoard
**Decision:** WandB cho experiment tracking.
**Rationale:** WandB có UI tốt hơn, hỗ trợ sweep natively, dễ share runs với collaborators.
**Alternatives:** TensorBoard (local only, UI kém hơn), MLflow (self-hosted, phức tạp hơn).

### [2026-03] MC-Dropout consistency fix — `_mc_forward()` thay thế `_estimate_epistemic_uncertainty()`
**Decision:** Thay hàm `_estimate_epistemic_uncertainty()` (chỉ trả về variance) bằng `_mc_forward()` (trả về cả mean logit lẫn epistemic variance từ cùng một tập `mc_logits`).
**Rationale:** Code cũ lấy logit từ một deterministic pass (dropout OFF) riêng biệt, sau đó chạy N stochastic passes riêng để lấy variance. Hai giá trị đến từ hai distribution khác nhau — gate weight `α` không có ý nghĩa toán học. Fix đảm bảo `mean_logit = mc_logits.mean(dim=-1)` và `epistemic_var = mc_logits.var(dim=-1)` từ cùng tensor, đúng theo Gal & Ghahramani (2016).
**Behavior change:** Ở eval mode với `mc_samples > 0`, prediction logit là mean của N stochastic passes (không còn là deterministic pass). Ở training mode, chỉ 1 forward pass bình thường — không chạy MC passes thừa.
**Alternatives:** Giữ deterministic logit + stochastic uncertainty (sai về mặt lý thuyết), dùng deterministic gate features như `|logit_s - logit_t|` (bỏ mất novelty uncertainty gate).

### [2026-03] Giữ `cnn1d_student` và `esm_student` dù chưa tích hợp
**Decision:** Không xóa các model chưa hoàn chỉnh, comment rõ trạng thái.
**Rationale:** Giữ làm baseline reference cho audit. `cnn1d_student` là sequence baseline đơn giản nhất, `esm_student` là PLM baseline. Cả hai cần thiết cho ablation study đầy đủ.
**Status:** Cần fix trước Phase 13 (Experiments).

---

## Agent Skills System (2026-03-24)

### [2026-03-24] Skill set curated — 9 skills → 9 skills (5 new, 5 deleted, 4 kept)
**Decision:** Xóa 5 skills cũ (`midti-project`, `biology-foundation`, `deep-learning`, `knowledge-graphs`, `engineering`, `ugts-dti-project`), giữ 4 skills nền (`advanced-ml`, `graph-networks`, `cheminformatics`, `evaluation`), tạo 5 skills mới chuyên biệt.
**Rationale:** Skills cũ quá generic hoặc duplicate nhau. Skills mới được tổ chức theo task cụ thể của project (implement Teacher, implement Student, fusion, train on Kaggle, tune hyperparams) — dễ trigger đúng skill hơn.
**New skills:** `teacher-models`, `student-models`, `fusion-strategies`, `kaggle-gpu-training`, `hyperparameter-tuning`.

### [2026-03-24] Kaggle GPU training — session limit và filesystem behavior
**Decision:** Ghi nhận đúng các thông số Kaggle sau khi research từ official docs.
**Corrections made:**
- Session limit: **9 giờ** (không phải 12h như ban đầu viết)
- `/kaggle/working/` là **ephemeral** — mất sau session nếu không bật "Persistence: Variables and Files" trong Settings
- WandB Secrets: cần bật **Internet ON** trước, sau đó vào Add-ons → Secrets
- Offline pip install: dùng `--no-index --find-links <wheel_dir>` (không phải `--offline`)
**Source:** kaggle.com/docs, WandB documentation.

### [2026-03-24] Hyperparameter tuning — Hydra-Optuna và WandB Sweeps syntax
**Decision:** Ghi nhận đúng syntax sau khi research từ official docs.
**Corrections made:**
- Hydra-Optuna: distribution syntax là `tag(log, interval(1e-4, 1e-1))` (không phải `log_uniform(...)`)
- WandB Sweeps: distribution name là `log_uniform_values` (không phải `log_uniform`)
- Multi-objective Optuna: dùng `study.best_trials` để lấy Pareto front (không phải `study.best_trial`)
- Sweep init: `wandb sweep config.yaml` → trả về sweep ID, sau đó `wandb agent <sweep_id>`
**Source:** hydra.cc, optuna.readthedocs.io, docs.wandb.ai.

### [2026-03-24] `.agent/` structure — giữ nguyên, không refactor
**Decision:** Giữ cấu trúc `.agent/` hiện tại (AGENT.md, CONTEXT.md, task.md, roadmap.md, DECISIONS.md, workflows/, skills/).
**Rationale:** Cấu trúc đủ rõ ràng. AGENT.md làm entry point với reading order và skill trigger table. Tách task.md (current) vs roadmap.md (history) đúng. workflows/ vs skills/ phân biệt rõ "làm gì" vs "biết gì". Không có vấn đề navigation thực sự.
**Alternatives considered:** Đổi tên `.agent/` → `agent/` (không cần thiết), gộp workflows vào skills (làm mờ ranh giới).
