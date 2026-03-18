# DeepDTA Reference

Model family:
- `deepdta`

Expected input forms:
- drug representation: `smiles`
- target representation: `sequence`

Required config fields:
- `model.family`
- `model.drug_encoder`
- `model.target_encoder`
- `training.seed`

Validation rules:
- drug encoder must support tokenized SMILES
- target encoder must support sequence input
- seed must be fixed

Failure triggers:
- incompatible SMILES encoder
- missing seed
- unsupported target encoder
