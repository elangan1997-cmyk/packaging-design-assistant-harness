# Changelog

## Unreleased

### Renamed

- Display name updated to `包装设计助理 Harness 2.0`; the Skill invocation name `packaging-design-assistant` remains unchanged for compatibility.

### Added

- Local-first Packaging Design Assistant Harness foundation.
- Unified Skill entrypoint, CLI, Python API, Packaging IR, isolated job workspaces, routing, asset inspection, validation, capability discovery, and Mock Provider.
- Machine-readable `not_implemented` responses for unfinished modules.
- JSON Schemas, examples, health check, installation scripts, and standard-library tests.
- Ten independent Box 2.0 structure model registrations.
- Deterministic `carton.box_v2.lock_bottom` SVG generator with stable Illustrator layers and IDs.
- Deterministic `carton.box_v2.carry_handle` generator, including two handle apertures and two side slots.
- One active original-Illustrator regression sample per implemented box model, compared at 0.001 mm precision.
- Conversational box-model choices when `model_code` is missing, with availability status and `needs_input` routing.
- Model-specific structure capability discovery and three-file structure job output.
- Module B deterministic content fields with sources, statuses, placeholders, semantic panel assignment, and safe SVG artwork-layer writing.
- Five-file content-layout output, content schemas, aquarium-product example, and structure-layer integrity checks.
- Module C Provider orchestration for Host, OpenAI-compatible, Custom REST, and deterministic Mock adapters.
- Environment-only credential resolution, explicit paid-call and Mock opt-ins, timeout handling, finite retry, and ordered fallback.
- CMF plan, generation record, independent visual QA, retry record, review checklist, and six-file mockup output.
- Soft-packaging heat-seal and bottle/label protection rules, with blank-dieline and missing-dimension blockers.
- Provider, CMF-plan, and visual-QA schemas plus Module C contract tests.
- Evidence-backed route inference for structure, content, mockup, multi-stage, and clarification outcomes.
- Eight-case routing acceptance matrix, 12 runnable Evals (four per module), and a complete A -> B -> Mock C workflow demo.
- Expanded health check for CLI, schemas, examples, writable output, and minimum structure generation.

### Changed

- Refocused the Skill from CMF-only advice to three-module packaging orchestration while preserving all CMF references.
- Lowered the core runtime floor to Python 3.9 for the active macOS environment.
