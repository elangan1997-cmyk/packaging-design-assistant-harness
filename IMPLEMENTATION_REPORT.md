# Implementation Report

## Current release

Version `0.5.0` implements the local-first Harness foundation, two Box 2.0 structure models, Module B content layout, and Module C Provider/visual-QA orchestration. No browser, web server, DOM, Node.js, or npm dependency is used by the core.

## Files and architecture

- `scripts/skill_entry.py`, CLI, Python API, request validation, routing, capability discovery, isolated job workspaces, and machine-readable results are active.
- `src/packaging_assistant/modules/structure/` contains repository-owned deterministic geometry and SVG serialization.
- `src/packaging_assistant/modules/content/` contains field rules, source/status models, panel layout, protected-layer validation, reports, and output writers.
- `src/packaging_assistant/modules/mockup/` implements the Provider-only CMF flow and retains the legacy advisory boundary.
- `src/packaging_assistant/providers/` contains typed capabilities, configuration, Host/OpenAI-compatible/Custom REST/Mock adapters, and finite retry/fallback execution.
- No web application existed in the audited baseline; no web code was moved or deleted.

## Compatibility retained

- Original `packaging-cmf-finishes` advisory references and trigger vocabulary remain available.
- Original-artwork, Chinese text, Logo, structure, soft-packaging, bottle, and no-local-CMF-compositing rules remain in the preserved references/Skill.
- Codex and Claude Code installation remains a local Skill workflow.

## Interface status

- Natural-language Skill: available through `SKILL.md` and `scripts/skill_entry.py`.
- Python API: available for structure generation, content layout, Provider-based mockup orchestration, asset inspection, and unified request execution.
- CLI: `inspect`, `route`, `structure`, `content`, `mockup`, `run`, `validate`, and `health-check` commands are available. Unimplemented box models still report honestly.

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

Implemented:

- Host adapter boundary for agent-native capabilities;
- configurable OpenAI-compatible and Custom REST adapters;
- deterministic Mock Provider for contract tests;
- vision inspection, image generation, independent visual QA, and maximum two QA retries;
- ordered fallback, timeout/error sanitization, environment-only credentials, and explicit external-call/Mock opt-in;
- original artwork, Logo, Chinese text, structure, panel mapping, soft-packaging heat-seal, bottle, and label protection instructions;
- physical-dimension and blank-dieline blockers;
- six isolated outputs and manual-review state.

No real external Provider was executed because no user-approved endpoint/credential was supplied. Host is an adapter boundary and needs a runtime callback. OpenAI-compatible and Custom REST are generic configured integrations, not vendor-specific certified connectors. Mock emits a fixed test PNG, not a real CMF render. Search capability is available only when a configured Provider advertises it; otherwise it fails explicitly.

## Tests and evals

The release includes 38 passing unit, integration, CLI, routing, SVG geometry, content-safety, job-workspace, Provider, and Module C tests. Formal eval count is currently 0; the required 12-case `evals/` suite remains Phase 5 work.

## Known limitations and next steps

1. Implement the remaining Box 2.0 models one original sample per model.
2. Add official-source research interfaces and jurisdiction/category profiles for Module B.
3. Add vendor-specific request/response normalizers only for Providers selected and authorized by the user.
4. Add the required 12 eval cases and full multi-stage workflow demo.
5. Execute one approved real-Provider CMF test when endpoint, model, budget consent, and local credential are available.
