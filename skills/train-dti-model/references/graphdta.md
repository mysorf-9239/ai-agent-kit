# GraphDTA Reference

Model family:
- `graphdta`

Expected input forms:
- drug representation: `graph`
- target representation: `sequence`

Required config fields:
- `model.family`
- `model.drug_encoder`
- `model.target_encoder`
- `model.hidden_dim`
- `training.seed`

Validation rules:
- graph encoder must be compatible with graph drug representation
- target encoder must be compatible with sequence target representation
- hidden dimension must be explicit

Failure triggers:
- unsupported graph encoder
- missing hidden dimension
- inconsistent representation mapping
