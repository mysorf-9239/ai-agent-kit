# Project Conventions

## 1. Purpose

This document defines project-wide conventions shared by all skills and workflows.

## 2. Directory Model

Recommended root layout:

    guidelines/
    skills/
    workflows/
    templates/
    state/
    artifacts/
    reports/

Rules:
- `guidelines/` stores cross-cutting rules.
- `skills/` stores executable units.
- `workflows/` stores multi-skill pipelines.
- `templates/` stores canonical schemas and prompt templates.
- `state/` stores persisted runtime state.
- `artifacts/` stores generated outputs.
- `reports/` stores human-readable summaries derived from structured outputs.

## 3. Naming

Naming MUST follow `naming-conventions.md`.
No local override is allowed unless the kit version changes.

## 4. File Ownership

Each file category has one primary responsibility:
- `guidelines/` defines rules
- `skills/` defines execution units
- `workflows/` defines sequencing logic
- `templates/` defines structured output forms
- `state/` defines runtime facts

## 5. Artifact Layout

Artifacts MUST be grouped by `run_id`.

Example:
- `artifacts/dti-graphdta-bindingdb-seed-42/model.pt`
- `reports/dti-graphdta-bindingdb-seed-42/summary.md`
- `state/state.json`

## 6. Reference Usage

References MUST be read-only support material.
References MUST NOT contain hidden mandatory steps that are absent from `SKILL.md`.

## 7. Asset Usage

Assets MUST be canonical.
Assets MUST be reusable.
Assets MUST NOT be per-run outputs.

## 8. Anti-Patterns

The following project patterns are prohibited:
- mixing generated artifacts into `skills/`
- placing mutable runtime state in `guidelines/`
- duplicating the same template in multiple skills
- relying on unnamed scratch files

## 9. Review Checklist

Project conventions are acceptable only if:
- directory responsibilities are clear
- artifact placement is deterministic
- references and assets are not misused
