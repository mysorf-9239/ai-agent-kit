# DTI Dataset Manifest Spec

Supported schema versions:
- `1.0.0`

Required top-level keys:
- `schema_version`
- `dataset_id`
- `task_type`
- `drug_representation`
- `target_representation`
- `split_strategy`
- `splits`

Supported `task_type`:
- `drug-target-interaction`

Supported `drug_representation`:
- `graph`
- `smiles`

Supported `target_representation`:
- `sequence`

Required split keys:
- `train`
- `validation`
- `test`

Each split object MUST contain:
- `path`
- `record_count`

Invalid examples:
- missing `schema_version`
- `task_type: dti`
- `drug_representation: fingerprint`
- split object without `path`
