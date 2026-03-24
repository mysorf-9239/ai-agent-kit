# DTI Evaluation Metrics

## 1. Classification Metrics (Binary DTI)

When evaluating models predicting binary interaction (1=interacts, 0=no interaction):

| Metric | Formula | Range | Interpretation |
|---|---|---|---|
| **AUROC** | Area under ROC curve | [0.5, 1.0] | Separability across all thresholds |
| **AUPRC** | Area under Precision-Recall | [0, 1] | **Preferred metric** for imbalanced DTI data |
| **F1 Score** | 2·P·R / (P+R) | [0, 1] | Balance between precision and recall |
| **Accuracy** | (TP+TN)/(Total) | [0, 1] | Very misleading on sparse DTI data |

### Why AUPRC > AUROC for DTI?
The vast majority of drug-protein pairs do not interact (the class prior is extremely skewed towards 0).
- AUROC remains high even if the model makes many false positive errors on the negative class.
- AUPRC heavily penalizes false positives among the top-ranked predictions, which perfectly aligns with the real-world goal: finding candidates worth spending money on for lab validation.

---

## 2. Regression Metrics (Binding Affinity)

When evaluating models predicting binding affinity (Kd, Ki, IC50):

| Metric | Description | Goal |
|---|---|---|
| **CI (Concordance Index)** | P(correct ranking of two random pairs) | Maximize (max 1.0, random 0.5) |
| **MSE** | Mean Squared Error | Minimize |
| **Pearson r** | Linear correlation | Maximize |

### Concordance Index (CI) computation
```python
from scipy.stats import kendalltau

def concordance_index(y_true, y_pred):
    """Compute CI using Kendall tau relationship for DTI regression."""
    tau, _ = kendalltau(y_true, y_pred)
    return (tau + 1) / 2  # scale from [-1, 1] to [0, 1]
```

---

## 3. Thresholds for Binarizing Regression Data

If treating a regression dataset (like DAVIS) as a classification problem:
- **DAVIS threshold**: Typically `Kd < 30nM` (nanomolar) is treated as a positive interaction.
- **pKd transformation**: `-log10(Kd / 1e9)`. A Kd of 30nM equals a pKd of `~7.52`. Values greater than 7.52 are positive.
- **KIBA threshold**: Typically `KIBA score < 12.1` is treated as a positive interaction.
