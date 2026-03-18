# Naming Conventions

## 1. Purpose

This document defines mandatory naming rules for the kit.

Names must be deterministic.
Names must encode role.
Names must support machine parsing.
Names must remain stable across skills, workflows, templates, and state.

## 2. General Rules

Mandatory rules:

- use lowercase letters for identifiers unless file format requires otherwise
- use kebab-case for skill names, workflow names, and template names
- use snake_case for structured data keys
- use PascalCase only for language-level types when required by the target language
- avoid abbreviations unless they are domain standard
- keep names semantically specific

Forbidden patterns:

- mixedCase for skill names
- vague nouns such as `thing`, `data`, `process`, `manager`
- synonyms for the same concept in different files
- unstable suffixes such as `-new`, `-final`, `-latest`

## 3. Skill Names

Skill names MUST use verb-object form.

Valid examples:

- `validate-dti-dataset`
- `extract-protein-features`
- `train-dti-model`
- `evaluate-biosequence-encoder`
- `export-experiment-report`

Invalid examples:

- `dti`
- `data-processing`
- `model`
- `do-training`
- `helper-skill`

Skill naming rules:

- the verb MUST describe the primary action
- the object MUST describe the primary artifact or task target
- one skill name MUST map to one responsibility

## 4. Workflow Names

Workflow names MUST encode domain, task, and pipeline type.

Pattern:

- `<domain>-<task>-pipeline`

Valid examples:

- `dti-benchmark-training-pipeline`
- `biosequence-feature-generation-pipeline`
- `drug-repurposing-ranking-pipeline`

Invalid examples:

- `main-workflow`
- `pipeline-v2`
- `training`

## 5. Template Names

Template names MUST encode output purpose.

Pattern:

- `<task>-<artifact>-template`
- `<task>-<artifact>-output`
- `<task>-<artifact>-prompt`

Valid examples:

- `dti-evaluation-output`
- `protein-validation-prompt`
- `experiment-summary-template`

Invalid examples:

- `output-template`
- `prompt1`
- `default-schema`

## 6. State Keys

State keys MUST use snake_case.
State keys MUST represent stable concepts.

Valid examples:

- `schema_version`
- `active_workflow`
- `dataset_manifest`
- `primary_metric_value`
- `retry_index`

Invalid examples:

- `activeWorkflow`
- `DatasetManifest`
- `temp`
- `misc_data`

## 7. Run Identifiers

Run identifiers MUST be deterministic.
Run identifiers MUST include task, model, dataset, and seed when applicable.

Pattern:

- `<task>-<model>-<dataset>-seed-<seed>`

Valid examples:

- `dti-graphdta-bindingdb-seed-42`
- `protein-bert-uniprot-seed-7`

Invalid examples:

- `run1`
- `latest-run`
- `test-run-final`

## 8. File Names

File names MUST be stable and predictable.

Required file names:

- `SKILL.md`
- `metrics.json`
- `predictions.csv`
- `run_manifest.json`
- `summary.md`
- `state.json`

Rules:

- use singular canonical names for standard artifacts
- avoid timestamp-only filenames for primary outputs
- include run directory instead of dynamic file suffixes

## 9. Directory Names

Directory names MUST describe content type.

Required directory patterns:

- `skills/<skill-name>/`
- `workflows/<workflow-name>/`
- `templates/<template-name>/`
- `runs/<run-id>/`
- `artifacts/<run-id>/`
- `reports/<run-id>/`

Invalid directory names:

- `misc/`
- `tmp-final/`
- `stuff/`

## 10. Domain Naming Rules

Use standard domain abbreviations only when the abbreviation is canonical.

Allowed canonical abbreviations:

- `dti`
- `gnn`
- `cnn`
- `rnn`
- `esm`
- `pdb`
- `smiles`

Rules:

- if an abbreviation is not canonical, spell the term out
- do not mix expanded and abbreviated forms for the same concept within the same kit version

## 11. Version Naming

Version names MUST use semantic versioning.

Pattern:

- `<major>.<minor>.<patch>`

Examples:

- `1.0.0`
- `1.2.3`

Invalid examples:

- `v1`
- `latest`
- `2026-final`

## 12. Anti-Patterns

The following naming patterns are prohibited:

- names that hide responsibility
- names that require reading implementation to understand meaning
- names that differ only by punctuation
- names that encode temporary context
- names that use inconsistent abbreviations

## 13. Review Checklist

A naming scheme is acceptable only if all checks pass:

- skill names use verb-object form
- workflow names use domain-task-pipeline form
- state keys use snake_case
- run ids are deterministic
- file names are canonical
- examples include valid and invalid names
