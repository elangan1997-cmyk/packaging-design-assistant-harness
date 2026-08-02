# Architecture Audit

Audit date: 2026-08-02

Baseline revision: `d13abac` (`main`, tracking `origin/main`)

## Executive summary

The repository is currently a documentation-only packaging CMF advisory Skill. It contains useful material, finish, structure-selection, prompt, and output guidance, but it has no executable harness and cannot generate deterministic dielines or SVG files. The requested Packaging Design Assistant Harness therefore requires a new code architecture rather than an incremental extension of an existing application.

The current Skill must remain useful during the migration. Existing CMF guidance will be retained as Module C reference material while executable capabilities are introduced behind explicit capability declarations. Features that are not implemented must return `not_implemented`; the harness must not imply that documentation alone is executable behavior.

## Repository inventory

| Path | Role | Executable | Migration disposition |
|---|---|---:|---|
| `SKILL.md` | Main CMF workflow and routing instructions | No | Rewrite as the harness entrypoint while retaining links to CMF references |
| `README.md` | User-facing overview | No | Replace with installation, chat, CLI, Python API, and safety documentation |
| `agents/openai.yaml` | Agent display metadata | No | Update for the expanded harness |
| `references/finish-taxonomy.md` | Finish vocabulary | No | Retain for Module C |
| `references/material-compatibility.md` | Material/process compatibility | No | Retain for Modules B/C |
| `references/output-format.md` | CMF response template | No | Retain and adapt to structured Module C output |
| `references/prompt-templates.md` | Rendering prompt fragments | No | Retain for Module C provider adapters |
| `references/selection-questions.md` | Intake questions | No | Split into common intake plus module-specific schemas |
| `references/structure-recommendations.md` | General packaging structure guidance | No | Retain for Module B; do not treat as dieline geometry |
| `.gitignore` | Minimal ignore rules | No | Extend for Python/test/generated artifacts |

No `src/`, `scripts/`, `tests/`, examples, package metadata, lockfile, CLI, Python API, SVG fixtures, geometry engine, provider abstraction, or capability manifest exists at baseline.

## Baseline test result

- `python3 -m unittest discover -v`: exit 0, **0 tests run**.
- `python3 -m pytest -q`: unavailable in the active system Python (`No module named pytest`).
- There is no project dependency declaration from which a test environment could be reproduced.

These results are the pre-refactor baseline, not evidence that the repository is functionally correct.

## Current strengths

1. Material and finish terminology is already organized into focused references.
2. The Skill clearly separates visual proposals from production-ready print files.
3. Existing guidance already calls out critical prepress concerns: cut/fold separation, bleed, safety margins, white ink, and dedicated finishing layers.
4. Physical-dimension confirmation and uncertainty reporting are established workflow principles that should remain global harness guards.

## Gaps against the requested harness

### Runtime and interface

- No single request/response contract.
- No conversational dispatcher, CLI, or importable Python API.
- No deterministic serialization or machine-readable errors.
- No capability discovery or honest `not_implemented` behavior.

### Module A: dielines

- No packaging-type registry or subtype separation.
- No parameter schemas, dimensional validation, geometry formulas, intermediate representation, layer model, stable element IDs, metadata, or SVG exporter.
- No distinction between cut, crease, perforation, bleed, safe area, glue area, annotation, and artwork regions.
- No original-script comparison fixtures or tolerance-based geometric tests.
- Existing prose about structures is advisory only and cannot be used as production geometry.

### Module B: packaging content and standards

- No structured content schema, panel assignment, regulatory profile, locale handling, or validation report.
- No connection between dieline panels and content placement.

### Module C: CMF and rendering

- Good prose references exist, but there is no provider interface, prompt compiler, render job model, result manifest, or visual QA pipeline.

### Engineering and governance

- No packaging metadata or install process.
- No tests, snapshots, linting, typing, CI, examples, changelog, or migration guide.
- No license file is present; provenance of formulas and any reconstructed behavior must be documented.

## Key risks and controls

| Risk | Required control |
|---|---|
| Calling a visually plausible net “standard” | Label generated outputs `DESIGN_TEMPLATE`; validate dimensions and disclose production limitations |
| Treating “盒型 2.0” as one generic box | Enumerate each original subtype and give it a distinct registry ID, schema, generator, fixtures, and tests |
| Copying opaque JSXBIN implementation | Use the user-authorized original only as a black-box behavioral oracle; implement independently from observed inputs/outputs |
| Matching one sample by accident | Capture multiple dimension sets, normalize SVG geometry, compare topology and coordinates within declared tolerances |
| Nondeterministic SVG output | Stable ordering, numeric formatting, IDs, metadata, and snapshot tests |
| Hidden provider/network dependency | Keep Module A standard-library-only and local; isolate optional providers behind adapters |
| Breaking the existing CMF Skill | Preserve reference documents and expose legacy CMF guidance while executable Module C evolves |

## Target architecture

```text
scripts/skill_entry.py             conversational/JSON entrypoint
src/packaging_harness/
  api.py                           public Python API
  cli.py                           command-line interface
  dispatcher.py                    request validation and module routing
  capabilities.py                  implemented/not_implemented manifest
  errors.py                        stable machine-readable errors
  models.py                        shared request/result models
  dielines/                        Module A registry, schemas, geometry, SVG
  content/                         Module B schemas and validators
  cmf/                             Module C advisory/provider adapters
tests/                             unit, snapshot, contract, comparison tests
examples/                          copyable requests and generated SVG examples
reports/                           benchmark and migration reports
```

The geometry layer will use millimetres as its canonical unit. A typed intermediate representation will be the only source for SVG serialization and geometry tests. Exporters will not infer structure from rendered pixels.

## Phased implementation plan

1. **Foundation:** package metadata, request/result contract, dispatcher, capability manifest, CLI, Python API, JSON Skill entrypoint, deterministic errors, smoke tests.
2. **Original-script benchmark:** run the supplied Illustrator JSX in a disposable document, enumerate each Packaging Box 2.0 subtype and parameter field, export complex reference cases, and record provenance.
3. **Module A:** implement separately identified models, geometry IR, Illustrator-compatible SVG layers/IDs/metadata, validation, snapshots, and tolerance-based comparisons.
4. **Module B:** implement structured content, standards profiles, panel mapping, and validation without claiming legal certification.
5. **Module C:** wrap retained CMF expertise in structured results and optional provider adapters with explicit QA state.
6. **Release:** complete documentation, examples, migration notes, acceptance report, and versioned commits.

Each phase will be committed separately. Generated comparison evidence will be reproducible and will not overwrite user documents.

## Baseline acceptance boundary

At this revision the only implemented capability is advisory documentation. All executable module capabilities are absent. The next commit may add harness foundations, but no dieline subtype will be advertised as implemented until its schema, generator, SVG output, and tests are present.
