# Uncertainty Gating & MC Dropout

## 1. Uncertainty in Deep Learning

Deep neural networks are notoriously overconfident. In DTI prediction, we need to know *when* the model is guessing, especially for unknown drugs (Cold-start problem).

There are two main types of uncertainty:
1. **Aleatoric Uncertainty**: Inherent noise in the data (e.g., assay measurement errors). Can't be reduced by more data.
2. **Epistemic Uncertainty**: Model ignorance due to lack of training data. Can be reduced with more data. **MC Dropout measures this.**

---

## 2. Monte Carlo (MC) Dropout

Introduced by Yarin Gal (2016). Dropout is normally turned off during inference (`model.eval()`). MC Dropout keeps it **ON** during inference and runs the input multiple times.

- The network acts as an ensemble of slightly different sub-networks.
- **Mean of predictions**: Expected interaction.
- **Variance of predictions**: The Epistemic Uncertainty ($\sigma^2$).

### PyTorch Implementation

```python
import torch

def mc_dropout_predict(model, x, num_samples: int = 20):
    """
    Forward pass x through the model num_samples times with dropout active.
    Returns the mean prediction and the variance (uncertainty).
    """
    # CRITICAL: Force the model (or just dropout layers) to stay in train mode!
    model.train() 
    
    # Forward pass N times
    with torch.no_grad(): # Don't track gradients for inference
        preds = []
        for _ in range(num_samples):
            # Assumes model outputs logits. 
            logits = model(x)
            # Apply sigmoid to get probabilities before computing variance
            probs = torch.sigmoid(logits) 
            preds.append(probs)
            
    preds = torch.stack(preds, dim=0)  # Shape: (num_samples, batch_size, out_dim)
    
    # Calculate Mean and Variance across the samples
    mean_pred = preds.mean(dim=0)      # E[y]
    variance = preds.var(dim=0)        # σ^2 (Uncertainty)
    
    return mean_pred, variance
```

---

## 3. Uncertainty-Gated Fusion (PairGate)

When relying on two branches (e.g., Student sequence-model vs Teacher graph-model), we shouldn't use a static 50/50 average. We want to **trust the model that is most certain**.

The **PairGate** is a small network that takes the estimated uncertainties ($\sigma^2_S, \sigma^2_T$) and outputs an adaptive weight $w \in [0, 1]$.

### Formulation
$w = \sigma(W \cdot [\sigma^2_S, \sigma^2_T] + b)$
Final Output = $w \times \text{Student\_Pred} + (1 - w) \times \text{Teacher\_Pred}$

### PyTorch Implementation

```python
import torch
import torch.nn as nn

class PairGate(nn.Module):
    def __init__(self, uncertainty_dim: int = 2):
        super().__init__()
        # A simple linear layer mapping [var_S, var_T] -> 1 weight value
        self.gate = nn.Sequential(
            nn.Linear(uncertainty_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 1)
        )
        
    def forward(self, var_s, var_t):
        """
        var_s: Uncertainty variance from Student, shape (batch, 1)
        var_t: Uncertainty variance from Teacher, shape (batch, 1)
        Returns weight 'w' shape (batch, 1)
        """
        gate_input = torch.cat([var_s, var_t], dim=-1) # (batch, 2)
        w = torch.sigmoid(self.gate(gate_input))       # Bound between 0 and 1
        return w

# Fusion logic inside the main model forward pass:
# student_mean, var_s = mc_dropout_predict(student, x)
# teacher_mean, var_t = mc_dropout_predict(teacher, x)
# w = pair_gate(var_s, var_t)
# final_prediction = w * student_mean + (1 - w) * teacher_mean
```

**Behavior:**
- If the drug is missing from the graph (Cold Start), the Teacher's variance ($\sigma^2_T$) will spike.
- The PairGate learns that high $\sigma^2_T$ means the Teacher is guessing.
- It outputs $w \approx 1$ to heavily rely on the Student's prediction instead.
