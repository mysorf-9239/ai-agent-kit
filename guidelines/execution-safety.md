# Execution Safety

## 1. Purpose

This document defines execution boundaries and safety rules for autonomous agents using the kit.

## 2. Side Effect Boundaries

Every skill and workflow MUST declare side effects.

Allowed side effects:
- read workspace files
- write bounded artifact paths
- update persisted state
- invoke declared local scripts

Restricted side effects:
- network access
- package installation
- secret access
- deletion of non-generated files

## 3. Filesystem Rules

Filesystem writes MUST be bounded to declared output directories.

Allowed write targets:
- `artifacts/`
- `reports/`
- `state/`
- declared generated paths inside the workspace

Forbidden write targets:
- parent directories outside workspace
- user home directories unless explicitly declared
- source directories unless the skill is a code-generation skill

## 4. Network Rules

Network access MUST be explicit.
Network access MUST be declared in skill or workflow preconditions.

Default rule:
- no network access

Allowed exceptions:
- documented model download
- documented dataset fetch
- documented remote inference call

## 5. Secret Rules

Secrets MUST NEVER be embedded in:
- `SKILL.md`
- templates
- references
- examples
- state
- reports

Secrets MAY be referenced through environment variable names only.

## 6. Retry Safety

Retries MUST be idempotent when possible.
Retries MUST NOT duplicate irreversible side effects.

If a step is not idempotent:
- it MUST declare compensation logic
- or it MUST be marked non-retryable

## 7. Quarantine Safety

Corrupt or partial outputs MUST be quarantined before any downstream step consumes them.

## 8. Agent Prompting Safety

Prompts MUST NOT instruct the agent to:
- infer missing secrets
- guess missing file paths
- continue after validation failure
- ignore conflicting state

## 9. Anti-Patterns

The following safety violations are prohibited:
- undeclared network calls
- writing outside bounded paths
- storing raw secrets in output
- retrying destructive actions without compensation

## 10. Review Checklist

Execution safety is acceptable only if:
- side effects are declared
- filesystem scope is bounded
- network policy is explicit
- secret handling is safe
