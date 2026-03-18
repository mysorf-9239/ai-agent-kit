# Agent Skill Kit Guidelines

## 1. Scope

This directory defines the execution standards for a production-grade Agent Skill Kit.

The standards apply to:
- skills
- workflows
- orchestrators
- templates
- state
- artifacts
- failure handling
- execution safety
- compatibility across agent runtimes

These standards target AI coding agents.
These standards do not target casual human reading.

Supported domains:
- machine learning
- deep learning
- bioinformatics
- drug-target interaction

## 2. Core Execution Rules

The kit MUST satisfy these rules:
- every skill is executable
- every skill has explicit activation conditions
- every workflow is deterministic
- every template is structured
- every state transition is explicit
- every failure is typed
- every decision is testable
- every output is machine-checkable
- every side effect is bounded

The kit MUST NOT rely on:
- hidden context
- ambiguous wording
- free-form branch logic
- silent fallback behavior
- untyped errors
- undocumented network access
- unbounded filesystem writes

## 3. Architecture Layers

The kit is organized into five layers:

1. Skills
2. Workflows
3. Orchestrator
4. Templates
5. State

Layer rules:
- skills perform bounded actions
- workflows chain skills
- orchestrator chooses execution path
- templates standardize exchange format
- state tracks execution facts

## 4. Reading Order

Read these files in order:

1. `authoring-principles.md`
2. `project-conventions.md`
3. `skill-format.md`
4. `workflow-composition.md`
5. `templates-and-prompts.md`
6. `state-and-artifacts.md`
7. `execution-safety.md`
8. `review-checklist.md`
9. `agent-compatibility.md`
10. `naming-conventions.md`

## 5. Production Requirements

A kit is production-ready only if:
- all contracts are explicit
- all examples are deterministic
- all anti-patterns are blocked
- all artifacts are named canonically
- all retries are bounded
- all fallbacks are documented
- all state writes are validated
- all side effects are documented
- all compatibility assumptions are documented

## 6. Reference Design Patterns

This guideline set aligns with recurring patterns used in major agent ecosystems:
- executable `SKILL.md` contracts
- scoped project rules and persistent memory files
- progressive disclosure through `references/`, `assets/`, and `scripts/`
- template-driven outputs
- stateful orchestration
- bounded retries and explicit fallbacks

This guideline set is stricter than descriptive documentation.
This guideline set assumes autonomous execution by coding agents.

## 7. Operating Model

Deterministic DTI training flow:

1. Validate dataset manifest.
2. Select representation branch.
3. Build model from fixed configuration.
4. Train with fixed seed.
5. Evaluate with fixed metrics schema.
6. Export report and state patch.

Invalid operating model:
- start training before dataset validation
- infer missing configuration values
- overwrite prior run artifacts
- return prose instead of structured outputs

## 8. Acceptance Criteria

A new skill, workflow, or template is acceptable only if:
- it can be executed without clarifying questions
- it defines typed inputs and typed outputs
- it defines preconditions and postconditions
- it defines failure behavior
- it defines validation steps
- it conforms to naming rules
- it declares side effects
- it declares compatibility assumptions

## 9. File Inventory

Primary files:
- `README.md`
- `authoring-principles.md`
- `skill-format.md`
- `project-conventions.md`
- `execution-safety.md`
- `state-and-artifacts.md`
- `templates-and-prompts.md`
- `workflow-composition.md`
- `review-checklist.md`
- `agent-compatibility.md`
- `naming-conventions.md`

## 10. Anti-Patterns

The following kit-level patterns are prohibited:
- treating skills as knowledge articles
- mixing orchestration logic into skill instructions
- storing state only in conversation memory
- generating outputs without schema definitions
- allowing silent success on partial failure
- placing all standards in one monolithic file
- writing long `SKILL.md` files that duplicate reference documents

## 11. Review Rule

This guideline set is acceptable only if:
- every core runtime concern has a dedicated file
- every file contains strict rules
- every file contains examples
- every file contains anti-patterns
- no file uses ambiguous execution language
