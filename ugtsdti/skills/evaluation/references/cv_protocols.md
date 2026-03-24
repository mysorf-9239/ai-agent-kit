# Cross-Validation and Cold Start Protocols

## 1. The 4 Cold-Start Scenarios (S1 - S4)

Evaluating a model on completely randomly split data (S1) is unrealistic. In practice, researchers want to know if the model can predict targets for a completely novel drug, or drugs for a completely novel target.

| Scenario | Target | Train Drugs | Test Drugs | Train Proteins | Test Proteins | Difficulty |
|---|---|---|---|---|---|---|
| **S1** (Warm Start) | Random pairs | Seen | Seen | Seen | Seen | Easiest |
| **S2** (New Drug) | Drug discovery | Seen | **Unseen** | Seen | Seen | Hard |
| **S3** (New Target)| Target discovery | Seen | Seen | Seen | **Unseen** | Hard |
| **S4** (Novel Pair) | True novelty | Seen | **Unseen** | Seen | **Unseen** | Hardest |

### S1: Random Pair Split
- Pool all DTI pairs. Randomly partition 80% train / 20% test.
- The network has seen the test drugs (in other pairs) and the test proteins (in other pairs).

### S2: Unseen Drug Split
- Partition the **set of all drugs** into 80% train / 20% test.
- All pairs containing a test drug go to the test set.
- The model must generalize zero-shot to a new molecular structure.

### S3: Unseen Protein Split
- Partition the **set of all proteins** into 80% train / 20% test.
- All pairs containing a test protein go to the test set.

### S4: Unseen Drug AND Unseen Protein Split
- The hardest setting. Partition drugs 80/20 AND proteins 80/20.
- Test set consists ONLY of pairs where BOTH the drug and the protein were totally absent from the training set.

---

## 2. Standard Benchmark Datasets

| Dataset | Metric | Total Drugs | Total Proteins | Total Pairs | Density |
|---|---|---|---|---|---|
| **DAVIS** | Kd | 68 | 442 | 30,056 | 100% (Dense) |
| **KIBA** | Score | 2,068 | 229 | 118,254 | ~25% (Sparse) |
| **DrugBank** | Binary | ~10,000 | ~5,000 | ~6,000 | <0.1% (Very Sparse)|
