# Drug Similarity Metrics

## 1. Tanimoto (Jaccard) Coefficient

Tanimoto is the standard metric used to calculate the similarity between two binary fingerprints.

```
Tanimoto(A, B) = |A ∩ B| / |A ∪ B|
              = count(bits both 1) / count(bits either 1)
Range: [0, 1], where 1 = identical structures.
```

### RDKit Implementation
```python
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit import DataStructs

def get_morgan_fp(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None: return None
    return AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)

def compute_tanimoto(smiles1, smiles2):
    fp1 = get_morgan_fp(smiles1)
    fp2 = get_morgan_fp(smiles2)
    return DataStructs.TanimotoSimilarity(fp1, fp2)
```

---

## 2. Similarity Matrices for Multi-view DTI Graphs

In models like MIDTI (Multi-view Graph Neural Networks), several adjacency matrices are built connecting the entities:

| Matrix | Dimensions | Content Metric |
|---|---|---|
| **DD** (Drug-Drug) | (n_drugs, n_drugs) | Tanimoto similarity on Morgan fingerprints |
| **PP** (Protein-Protein)| (n_proteins, n_proteins) | Sequence similarity (Smith-Waterman or BLAST score) |
| **DP** (Drug-Protein) | (n_drugs, n_proteins) | Known interaction labels (binary 0 or 1) |

### Building the Drug-Drug (DD) Matrix

```python
def build_dd_similarity_matrix(smiles_list):
    """Computes full NxN Tanimoto similarity matrix for a list of drugs."""
    fps = [get_morgan_fp(s) for s in smiles_list]
    n = len(fps)
    sim_matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(n):
            if fps[i] is None or fps[j] is None:
                sim_matrix[i][j] = 0.0
            else:
                sim_matrix[i][j] = DataStructs.TanimotoSimilarity(fps[i], fps[j])
                
    return sim_matrix
```

### Graph Sparsification (Thresholding / kNN)
Raw similarity matrices are dense. To use them in Graph Neural Networks efficiently, they are often sparsified:
1. **Thresholding**: Keep edges only if similarity > threshold (e.g., `0.6`).
2. **k-Nearest Neighbors (kNN)**: Keep edges only for the top-k most similar drugs (e.g., `k=5`), setting the rest to 0.
