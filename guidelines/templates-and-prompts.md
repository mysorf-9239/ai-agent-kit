# Templates And Prompts

## 1. Purpose

This document defines canonical rules for templates and prompts used by the kit.

## 2. Template Types

Supported template types:
- output schemas
- prompt templates
- experiment configuration templates
- report templates
- state patch templates

## 3. Prompt Rules

Prompts MUST define:
- role
- task
- inputs
- constraints
- execution steps
- output schema
- failure response

Prompts MUST NOT:
- request chain-of-thought output
- request hidden reasoning
- mix more than one output schema in one prompt

## 4. Output Rules

Every output template MUST include:
- `schema_version`
- `template_name`
- `status`
- `run_id`
- `artifacts`
- `errors`

## 5. Experiment Rules

Every experiment template MUST include:
- dataset identity
- model identity
- training hyperparameters
- seed
- evaluation metrics
- output directory

## 6. Report Rules

Reports MAY be markdown.
Reports MUST be derived from structured outputs.
Reports MUST NOT introduce facts not present in validated state or artifacts.

## 7. Anti-Patterns

The following patterns are prohibited:
- prompt templates without explicit constraints
- output schemas without version
- reports as primary machine interface
- experiment templates without seed

## 8. Review Checklist

Templates and prompts are acceptable only if:
- prompt contract is explicit
- output schema is stable
- experiment template is reproducible
- reports are derived, not primary
