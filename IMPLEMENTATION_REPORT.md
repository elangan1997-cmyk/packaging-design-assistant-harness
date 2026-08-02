# Implementation Report

## Current release

Version `0.4.0` implements the local-first Harness foundation, two Box 2.0 structure models, and the first complete Module B content-layout workflow. No browser, web server, DOM, Node.js, or npm dependency is used by the core.

## Files and architecture

- `scripts/skill_entry.py`, CLI, Python API, request validation, routing, capability discovery, isolated job workspaces, and machine-readable results are active.
- `src/packaging_assistant/modules/structure/` contains repository-owned deterministic geometry and SVG serialization.
- `src/packaging_assistant/modules/content/` contains field rules, source/status models, panel layout, protected-layer validation, reports, and output writers.
- `src/packaging_assistant/modules/mockup/` preserves the legacy CMF advisory boundary.
- No web application existed in the audited baseline; no web code was moved or deleted.

## Compatibility retained

- Original `packaging-cmf-finishes` advisory references and trigger vocabulary remain available.
- Original-artwork, Chinese text, Logo, structure, soft-packaging, bottle, and no-local-CMF-compositing rules remain in the preserved references/Skill.
- Codex and Claude Code installation remains a local Skill workflow.

## Interface status

- Natural-language Skill: available through `SKILL.md` and `scripts/skill_entry.py`.
- Python API: available for structure generation, content layout, asset inspection, and unified request execution.
- CLI: `inspect`, `route`, `structure`, `content`, `mockup`, `run`, `validate`, and `health-check` commands exist; unavailable modules report honestly.

## Module status

### Module A

Implemented models:

- `carton.box_v2.lock_bottom`
- `carton.box_v2.carry_handle`

Each has one active raw Illustrator regression sample at 0.001 mm coordinate precision. The other eight Box 2.0 models remain registered but not implemented. Outputs remain `DESIGN_TEMPLATE` with manufacturer review required.

### Module B

Implemented:

- product brief parsing;
- stable field IDs;
- source and status tracking;
- non-fabricating placeholders;
- semantic panel assignment;
- safe-area fit checks;
- editable SVG text in `LAYER_ARTWORK`;
- protected structure-layer comparison;
- source, missing-field, and review reports.

Not implemented:

- automatic government/standards research;
- category-specific legal determination;
- final commercial typography or visual design;
- barcode generation.

### Module C

CMF knowledge and legacy advisory compatibility are retained. Real Vision, Image Generation, Search Providers, visual QA, and retry orchestration are not implemented. The only executable Provider is deterministic `MockProvider`; no paid API is called by default.

## Tests and evals

The release includes 26 passing unit, integration, CLI, routing, SVG geometry, content-safety, job-workspace, and Mock Provider tests. Formal eval count is currently 0; the required 12-case `evals/` suite is not yet implemented and remains Phase 5 work.

## Known limitations and next steps

1. Implement the remaining Box 2.0 models one original sample per model.
2. Add official-source research interfaces and jurisdiction/category profiles for Module B.
3. Implement Host/OpenAI-compatible/Custom REST Providers without storing secrets.
4. Implement Module C visual QA and a maximum two-retry policy.
5. Add the required 12 eval cases and full multi-stage workflow after Modules B/C stabilize.
