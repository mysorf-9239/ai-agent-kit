# DTI Model Family Rules

Supported model families:
- `graphdta`
- `deepdta`

Rules:
- `graphdta` requires `drug_encoder` compatible with graph input.
- `deepdta` requires `drug_encoder` compatible with sequence or tokenized SMILES input.
- unsupported families MUST fail immediately.

Determinism rules:
- seed is mandatory
- output directory must be fixed
- one run id maps to one family and one dataset
