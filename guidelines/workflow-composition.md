# Workflow Composition

## 1. Purpose

This document defines when to create workflows, how to compose skills, and how to model branch logic.

## 2. When To Create A Workflow

Create a workflow when:
- more than one skill is required
- branch selection is required
- state transitions must be coordinated
- retries and fallbacks span multiple skills

Do not create a workflow when:
- one atomic skill is sufficient
- there is no branch logic
- there is no cross-step state dependency

## 3. Composition Rules

Workflow composition MUST be based on:
- input and output compatibility
- explicit preconditions
- explicit branch predicates
- explicit completion criteria

## 4. Branching Rules

Branching MUST use validated state or validated outputs only.
Each branch set MUST include a terminal else branch.

## 5. Hand-Off Rules

One skill may hand off to another only if:
- the next skill is named
- the next skill's required inputs are satisfied
- the hand-off is visible in workflow logic

## 6. Completion Rules

A workflow is complete only if:
- all mandatory skills succeeded
- all mandatory artifacts exist
- final state patch is valid

## 7. Anti-Patterns

The following workflow composition patterns are prohibited:
- hidden branch decisions in script internals
- workflow graphs that depend on conversational memory
- optional core validation steps
- silent degraded completion

## 8. Review Checklist

Workflow composition is acceptable only if:
- workflow creation criteria are met
- branches are explicit
- hand-offs are visible
- completion is testable
