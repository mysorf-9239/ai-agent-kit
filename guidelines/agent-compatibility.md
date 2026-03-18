# Agent Compatibility

## 1. Purpose

This document defines compatibility rules across major coding agent runtimes.

Target runtimes:
- Codex
- Claude Code
- Cursor
- Continue

## 2. Shared Compatibility Baseline

The kit MUST assume only these shared capabilities:
- markdown file reading
- directory traversal
- local file generation
- structured prompt following
- reference file loading

The kit MUST NOT assume:
- one specific memory file mechanism
- one specific slash command model
- one specific UI integration

## 3. Codex Mapping

Codex-compatible behavior:
- use `guidelines/` as repo-level instruction source
- use `skills/<skill>/SKILL.md` as executable contract
- use support files through progressive disclosure

Rules:
- avoid vendor-specific slash command assumptions
- keep execution contracts file-based

## 4. Claude Code Mapping

Claude Code supports project memory and nested `CLAUDE.md` behavior.

Rules:
- project-wide conventions MAY be mirrored into `CLAUDE.md`
- nested guidance MAY be scoped by directory
- critical execution contracts MUST still exist in `SKILL.md`

## 5. Cursor Mapping

Cursor supports project rules and scoped rule files.

Rules:
- global rules MAY be mirrored into Cursor rules
- skill execution logic MUST remain in portable markdown files
- do not rely on Cursor-only rule syntax for critical behavior

## 6. Continue Mapping

Continue supports custom agents, prompts, and rules.

Rules:
- prompt fragments MAY be reused from `templates/`
- workflow behavior MUST remain readable without Continue-specific UI features

## 7. Portability Rules

A portable skill kit MUST:
- keep core contracts in plain markdown and YAML
- keep schemas in vendor-neutral formats
- avoid hidden IDE-only dependencies
- avoid mandatory UI-only setup steps

## 8. Anti-Patterns

The following compatibility patterns are prohibited:
- placing critical workflow logic only in one vendor config file
- assuming one runtime's memory file is always loaded
- requiring a proprietary prompt editor to understand the kit

## 9. Review Checklist

Compatibility is acceptable only if:
- core behavior is portable
- vendor-specific optimizations are optional
- critical logic remains file-based
