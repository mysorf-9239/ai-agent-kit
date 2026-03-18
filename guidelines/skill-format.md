# Skill Format

## 1. Purpose

This document defines the canonical format for every skill directory and every `SKILL.md`.

## 2. Required Skill Directory

Each skill MUST use this layout:

    skills/<skill-name>/
      SKILL.md
      assets/
      references/
      scripts/

Rules:
- `SKILL.md` is mandatory.
- subdirectories are optional but recommended when needed.
- a skill directory MUST remain self-contained.

## 3. Required Frontmatter

Every `SKILL.md` MUST start with YAML frontmatter.

Required fields:
- `name`
- `description`

Recommended fields:
- `version`
- `inputs`
- `outputs`
- `side_effects`

Minimum valid example:

    ---
    name: validate-dti-dataset
    description: Validate a DTI dataset manifest and reject unsupported schemas or missing artifacts.
    ---

Extended example:

    ---
    name: train-dti-model
    description: Train a deterministic DTI model from a validated dataset manifest and fixed experiment configuration.
    version: 1.0.0
    inputs:
      - dataset_manifest
      - experiment_config
    outputs:
      - model_artifact
      - metrics_report
      - state_patch
    side_effects:
      - writes artifacts
      - updates state
    ---

## 4. Required Sections

Each `SKILL.md` MUST contain these sections:

1. `# <Skill Title>`
2. `## When to use this skill`
3. `## What this skill does`
4. `## Workflow`
5. `## Best Practices`
6. `## Examples`

Recommended additional sections:
- `## Inputs`
- `## Outputs`
- `## Failure Handling`
- `## Validation`
- `## Dependencies`

## 5. Activation Rules

The `When to use this skill` section MUST define:
- exact task triggers
- valid user intents
- activation boundaries
- exclusion cases when the skill must not be used

Example:
- use when the request is to train one deterministic DTI model from known dataset artifacts
- do not use when the request is only to compare prior metrics

## 6. Workflow Rules

The `Workflow` section MUST:
- use numbered steps
- define action order
- define validation checkpoints
- define hand-off points to other skills if needed

Workflow steps MUST be short.
Workflow steps MUST be executable.
Workflow steps MUST NOT contain long theoretical explanation.

## 7. Best Practices Rules

The `Best Practices` section MUST contain execution-critical constraints only.

Valid content:
- fixed seed requirements
- artifact naming rules
- validation requirements
- isolation requirements

Invalid content:
- broad educational advice
- duplicated reference material
- long architecture essays

## 8. Examples Rules

The `Examples` section MUST include:
- one realistic trigger example
- one expected output example or reference to asset

Examples SHOULD point to `assets/` or `references/` when code would be too long.

## 9. Skill Size Rule

`SKILL.md` SHOULD remain concise.
Detailed reference content MUST move to `references/`.
Boilerplate artifacts MUST move to `assets/`.

If a `SKILL.md` exceeds the size needed for activation plus workflow, split the detail out.

## 10. Anti-Patterns

The following skill format patterns are prohibited:
- missing activation section
- missing workflow
- embedding all implementation details inline
- using `SKILL.md` as a full textbook
- hiding critical steps only in `assets/`

## 11. Review Checklist

A skill format is acceptable only if:
- frontmatter is valid
- required sections exist
- activation rules are explicit
- workflow is numbered
- detailed reference material is split out when needed
