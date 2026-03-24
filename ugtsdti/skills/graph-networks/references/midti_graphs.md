# MIDTI Multi-View Graph Implementations

## 1. MIDTI Custom GCN Base
MIDTI does not use PyTorch Geometric `GCNConv`. It relies on custom dense matrix multiplications:

```python
class GraphConvolution(nn.Module):
    """Base GCN layer: H' = ReLU(A * H * W)"""
    def forward(self, adj, input):
        support = torch.matmul(input, self.weight)   # H * W
        output  = torch.matmul(adj, support)          # A * (H*W)
        return output + self.bias
```

Note: MIDTI's inputs are **pre-normalized dense adjacency matrices**.

---

## 2. Three GCN Variants in MIDTI

MIDTI processes 4 graphs using 3 GCN variants:

### Homogeneous (GCN_homo)
- **Used for**: DD graph (Drugs isolated) and PP graph (Proteins isolated).
- A 3-layer stack returning embeddings at each hop.

### Bipartite (GCN_bi)
- **Used for**: DP graph (Drug-Protein interactions).
- Treats the concatenation of drug and protein features as the input node feature matrix.
- `adj_dp` shape is `(n_d+n_p, n_d+n_p)`.

### Heterogeneous (GCN_hete)
- **Used for**: DDPP graph (Combined).
- The adjacency is a block matrix `[DD, DP; DP^T, PP]`.

---

## 3. Multi-view Embedding Assembly

The embeddings from all layers and all graph views are stacked. Since there are 3 hops and 3 types (homo, bi, hete), this yields **9 views total**.

```python
# Output stacking code concept from MIDTI:
# x_d_dr shape: (n_drugs, 9_views, dim)
# y_p_pro shape: (n_proteins, 9_views, dim)
```

---

## 4. Deep Interactive Attention (DIA)

The core innovation is capturing cross-attention between the drug and the protein representations.

```python
class Deep_inter_att(nn.Module):
    def forward(self, drug_vector, protein_vector):
        # Step 1: Self-attention (capture self-context)
        drug_vector    = self.sda(drug_vector, None)     
        protein_vector = self.sta(protein_vector, None)  

        # Step 2: Cross-attention (drug focuses on protein, protein on drug)
        drug_covector    = self.dta(drug_vector, protein_vector)  
        protein_covector = self.tda(protein_vector, drug_vector)  
        
        return drug_covector, protein_covector
```

These DIA blocks are repeated (parameter `layer_IA`), and their outputs at each step are concatenated together and passed through a final MLP.
