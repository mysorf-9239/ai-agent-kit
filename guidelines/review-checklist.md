# Review Checklist

## 1. Purpose

This document defines the mandatory review gate for new skills, workflows, templates, and support files.

## 2. Skill Review Gate

A skill passes only if:
- `SKILL.md` has valid frontmatter
- activation rules are explicit
- workflow is numbered
- best practices contain runtime constraints
- examples are realistic
- required details are split into `references/` or `assets/` when needed

## 3. Workflow Review Gate

A workflow passes only if:
- creation is justified
- branch predicates are explicit
- state hand-offs are explicit
- failure paths are explicit
- completion criteria are testable

## 4. Template Review Gate

A template passes only if:
- schema version exists
- field names are stable
- required fields are explicit
- output is machine-checkable

## 5. Safety Review Gate

A file set passes only if:
- side effects are declared
- filesystem writes are bounded
- network assumptions are explicit
- secret handling is safe

## 6. Compatibility Review Gate

A file set passes only if:
- runtime assumptions are declared
- agent-specific mappings are documented when needed
- no critical behavior depends on one vendor-specific feature unless declared

## 7. Anti-Patterns

The following review failures are terminal:
- missing activation criteria
- missing workflow
- missing output schema
- hidden required dependency
- unsafe side effects

## 8. Review Outcome

Allowed outcomes:
- accept
- accept with bounded follow-up
- reject

Reject when any terminal review failure exists.
