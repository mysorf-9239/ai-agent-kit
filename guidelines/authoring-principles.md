# Authoring Principles

## 1. Purpose

This document defines the mandatory principles for authoring skills, workflows, references, templates, and support assets.

These principles apply before any file-specific format rules.

## 2. Core Principles

Every authored unit MUST be:
- executable
- deterministic
- scoped
- structured
- testable
- composable

Every authored unit MUST NOT be:
- a knowledge dump
- a vague best-practice memo
- an unbounded multi-purpose instruction set
- dependent on hidden conversational context

## 3. Progressive Disclosure

The kit MUST use progressive disclosure.

Rules:
- `SKILL.md` contains activation criteria, execution workflow, and direct operational guidance.
- `references/` contains detailed standards, protocol notes, or technical background.
- `assets/` contains reusable templates, code snippets, fixtures, and canonical examples.
- `scripts/` contains executable helpers only.

A skill MUST NOT duplicate long reference material inside `SKILL.md`.

## 4. Scope Discipline

Each authored unit MUST have one clear scope.

Valid scopes:
- validate dataset
- train model
- evaluate model
- export report
- select workflow branch

Invalid scopes:
- handle all ML tasks
- build and deploy everything
- general bioinformatics knowledge

## 5. Deterministic Language

Use deterministic language only.

Allowed language:
- MUST
- MUST NOT
- IF
- THEN
- ELSE
- STOP
- RETURN
- VALIDATE

Disallowed language:
- usually
- maybe
- try to
- prefer if possible
- generally
- optionally infer

## 6. Execution First

The kit is for agent execution.
The writing style MUST prioritize runtime behavior over explanation.

Rules:
- define inputs before actions
- define validation before side effects
- define failure behavior before fallback behavior
- define outputs as artifacts or schemas

## 7. Domain Grounding

Domain-specific content MUST be anchored to concrete ML and bioinformatics tasks.

Required domain examples:
- dataset validation
- feature extraction
- model training
- model evaluation
- benchmark reporting
- DTI-specific branching

## 8. Anti-Patterns

The following authoring patterns are prohibited:
- writing skills as tutorials
- placing critical instructions only in examples
- mixing global rules with one skill's local logic
- writing files that require human interpretation before execution

## 9. Review Checklist

An authored unit is acceptable only if:
- scope is single-purpose
- language is deterministic
- progressive disclosure is respected
- runtime behavior is clearer than prose explanation
