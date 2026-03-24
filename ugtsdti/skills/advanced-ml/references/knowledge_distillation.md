# Teacher-Student & Knowledge Distillation (KD)

## 1. The Teacher-Student Paradigm

In DTI, we often face a dilemma:
- **Graph models (Teacher)**: Highly accurate because they see the whole graph (DD, PP, DP), but cannot predict well on completely new drugs (Cold-start S2/S4) because the graph is missing edges.
- **Sequence models (Student)**: Less accurate overall, but highly robust to novel drugs/proteins because they only rely on the SMILES/FASTA string.

**Solution:** Train the Student to mimic the Teacher's representations. The Student gets the robustness of sequence models but inherits the rich structural knowledge of the graph model.

---

## 2. Knowledge Distillation Theory

Introduced by Hinton et al., KD transfers knowledge by training the Student to match the "soft probabilities" of the Teacher, rather than just the hard (0/1) binary labels.

### Temperature ($T$)
We soften the logits using a Temperature scaling factor:
`q_i = exp(z_i / T) / sum(exp(z_j / T))`
- $T = 1$: Standard Softmax.
- $T > 1$: Softer distribution, revealing the "dark knowledge" (e.g., the Teacher thinks a drug has a 0.1% chance of binding—this relative scoring holds valuable structural information).

---

## 3. Loss Formulation

The full loss for the Student is typically a combination of **Supervised Loss** (against true labels) and **KD Loss** (against Teacher):

`L_Total = L_BCE(y_student, y_true) + α * L_KL(p_student_soft, p_teacher_soft)`

Where $L_{KL}$ is the Kullback-Leibler (KL) Divergence.

---

## 4. PyTorch Implementation

```python
import torch
import torch.nn.functional as F

def get_kd_loss(student_logits, teacher_logits, temperature: float = 4.0):
    """
    Computes KL Divergence loss for Knowledge Distillation.
    Note: PyTorch's kl_div expects log-probabilities for the input (student)
    and standard probabilities for the target (teacher).
    """
    # 1. Soften the probabilities
    student_log_probs = F.log_softmax(student_logits / temperature, dim=-1)
    teacher_probs = F.softmax(teacher_logits / temperature, dim=-1)
    
    # 2. Compute KL Divergence
    # reduction='batchmean' is mathematically correct for KL Div in PyTorch
    loss_kl = F.kl_div(student_log_probs, teacher_probs, reduction='batchmean')
    
    # 3. Scale by T^2 to match the scale of the standard cross entropy loss
    # Since the gradients are scaled by 1/T^2 during soft softmax
    loss_kd = loss_kl * (temperature ** 2)
    
    return loss_kd

# Usage in training loop:
# alpha is a hyperparameter balancing the two losses (e.g., 0.5)
# loss_bce = F.binary_cross_entropy_with_logits(student_logits, labels)
# loss = loss_bce + alpha * get_kd_loss(student_logits, teacher_logits)
```

## 5. Offline vs Online Distillation
- **Offline KD**: Teacher is fully pre-trained and its weights are frozen. Student learns from Teacher's outputs. (Standard approach).
- **Online (Mutual) KD**: Both Teacher and Student train simultaneously and learn from each other. (More complex, but sometimes used in bi-path hybrid models).
