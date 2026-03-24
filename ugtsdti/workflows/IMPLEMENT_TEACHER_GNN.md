# Workflow: Implement Teacher GNN (Phase 11)

Đây là task ưu tiên cao nhất hiện tại. Teacher hiện tại (`baseline_teacher`) chỉ là `nn.Embedding` lookup — không có signal thực. PairGate và KD không có ý nghĩa cho đến khi Teacher thật được implement.

---

## Tại sao Teacher GNN quan trọng

```
Với dummy Teacher:
  - var_t ≈ random noise → gate α không học được gì có nghĩa
  - logit_t ≈ random → KDDualLoss distillation term vô nghĩa
  - Kết quả: hybrid ≈ student-only về mặt thực chất

Với Teacher GNN thật:
  - S1: Teacher confident (low var_t) → α → 1 → Teacher dominates ✓
  - S4: Teacher uncertain (high var_t) → α → 0 → Student dominates ✓
  - KD: Student học được graph structure từ Teacher ✓
```

---

## Kế hoạch implement (Phase 11.1 → 11.2 → 11.3)

### Phase 11.1: Feature-based Graph Initialization

**File:** `ugtsdti/data/graph_builder.py`

```python
# Tạo DD (Drug-Drug) similarity graph từ Morgan fingerprints
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs
from torch_geometric.data import Data
import torch

def build_drug_drug_graph(smiles_list: list[str], threshold: float = 0.6, radius: int = 2, nbits: int = 2048):
    """
    Tanimoto similarity graph trên Morgan fingerprints.
    Edge nếu Tanimoto(fp_i, fp_j) >= threshold.
    """
    fps = []
    for smi in smiles_list:
        mol = Chem.MolFromSmiles(smi)
        if mol:
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=nbits)
            fps.append(fp)
        else:
            fps.append(None)

    n = len(fps)
    edge_index = []
    for i in range(n):
        for j in range(i+1, n):
            if fps[i] and fps[j]:
                sim = DataStructs.TanimotoSimilarity(fps[i], fps[j])
                if sim >= threshold:
                    edge_index.extend([[i, j], [j, i]])  # undirected

    # Node features: fingerprint vectors
    x = torch.zeros(n, nbits)
    for i, fp in enumerate(fps):
        if fp:
            arr = np.zeros(nbits)
            DataStructs.ConvertToNumpyArray(fp, arr)
            x[i] = torch.from_numpy(arr).float()

    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous() if edge_index else torch.zeros(2, 0, dtype=torch.long)
    return Data(x=x, edge_index=edge_index)


def build_protein_protein_graph(fasta_list: list[str], k: int = 3, threshold: float = 0.5):
    """
    Cosine similarity graph trên k-mer frequency vectors.
    """
    from sklearn.metrics.pairwise import cosine_similarity
    amino_acids = "ACDEFGHIKLMNPQRSTVWY"
    kmers = ["".join(p) for p in itertools.product(amino_acids, repeat=k)]
    kmer_idx = {km: i for i, km in enumerate(kmers)}

    def fasta_to_kmer(seq):
        vec = np.zeros(len(kmers))
        for i in range(len(seq) - k + 1):
            km = seq[i:i+k]
            if km in kmer_idx:
                vec[kmer_idx[km]] += 1
        norm = vec.sum()
        return vec / norm if norm > 0 else vec

    vecs = np.array([fasta_to_kmer(f) for f in fasta_list])
    sim_matrix = cosine_similarity(vecs)

    edge_index = []
    for i in range(len(fasta_list)):
        for j in range(i+1, len(fasta_list)):
            if sim_matrix[i, j] >= threshold:
                edge_index.extend([[i, j], [j, i]])

    x = torch.from_numpy(vecs).float()
    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous() if edge_index else torch.zeros(2, 0, dtype=torch.long)
    return Data(x=x, edge_index=edge_index)
```

Cache graphs:
```python
# Lưu vào disk để tránh recompute
torch.save({"dd_graph": dd_graph, "pp_graph": pp_graph}, "data/cache/similarity_graphs.pt")
```

---

### Phase 11.2: GNN Teacher Model

**File:** `ugtsdti/models/teacher/gcn_teacher.py`

```python
from torch_geometric.nn import GCNConv, GATConv, global_mean_pool
from ugtsdti.core.registry import MODELS
import torch.nn as nn

@MODELS.register("gcn_teacher")
class GCNTeacher(nn.Module):
    def __init__(self, drug_feat_dim: int, protein_feat_dim: int,
                 hidden_dim: int, num_layers: int = 2, dropout: float = 0.3):
        super().__init__()
        # PHẢI có dropout để MC-Dropout hoạt động
        self.dropout = nn.Dropout(dropout)

        # Drug GCN
        self.drug_convs = nn.ModuleList([
            GCNConv(drug_feat_dim if i == 0 else hidden_dim, hidden_dim)
            for i in range(num_layers)
        ])

        # Protein GCN
        self.protein_convs = nn.ModuleList([
            GCNConv(protein_feat_dim if i == 0 else hidden_dim, hidden_dim)
            for i in range(num_layers)
        ])

        self.predictor = nn.Linear(hidden_dim * 2, 1)

        # Global graphs — set sau khi build
        self.dd_graph = None  # PyG Data
        self.pp_graph = None  # PyG Data

    def set_graphs(self, dd_graph, pp_graph):
        """Gọi sau khi load graphs từ cache."""
        self.dd_graph = dd_graph
        self.pp_graph = pp_graph

    def forward(self, batch):
        drug_idx = batch["drug_index"].squeeze(-1)
        target_idx = batch["target_index"].squeeze(-1)

        # Drug embedding từ DD graph
        x_d = self.dd_graph.x
        for conv in self.drug_convs:
            x_d = self.dropout(conv(x_d, self.dd_graph.edge_index).relu())
        drug_emb = x_d[drug_idx]  # [B, hidden_dim]

        # Protein embedding từ PP graph
        x_p = self.pp_graph.x
        for conv in self.protein_convs:
            x_p = self.dropout(conv(x_p, self.pp_graph.edge_index).relu())
        protein_emb = x_p[target_idx]  # [B, hidden_dim]

        # Predict
        pair = torch.cat([drug_emb, protein_emb], dim=-1)
        logits = self.predictor(pair).squeeze(-1)
        return {"logits": logits}
```

**Config:**
```yaml
# configs/model/teacher/gcn.yaml
name: gcn_teacher
params:
  drug_feat_dim: 2048    # Morgan fingerprint bits
  protein_feat_dim: 8000 # 3-mer frequency (20^3)
  hidden_dim: 128
  num_layers: 2
  dropout: 0.3
```

---

### Phase 11.3: Graph Stability Controls

Khi Teacher GNN đã chạy được, thêm:

```yaml
# configs/trainer/default_trainer.yaml — thêm:
graph:
  warmup_epochs: 5      # freeze graph trong N epochs đầu
  rebuild_every: 10     # rebuild kNN graph mỗi N epochs
  ema_decay: 0.99       # EMA cho node embeddings
```

Log edge churn vào WandB:
```python
edge_churn = (new_edges != old_edges).float().mean()
wandb.log({"graph/edge_churn": edge_churn})
```

---

## Thứ tự implement

1. `ugtsdti/data/graph_builder.py` — build DD/PP graphs
2. Tích hợp graph building vào `TDCCachingDataset` hoặc tạo separate script
3. `ugtsdti/models/teacher/gcn_teacher.py` — GCN Teacher
4. Config `configs/model/teacher/gcn.yaml`
5. Import vào `ugtsdti/models/__init__.py`
6. Unit test
7. Chạy `model=only_teacher` với GCN Teacher, verify AUROC > 0.5 ở S1
8. Chạy hybrid, verify gate behavior (α cao ở S1, thấp ở S4)
