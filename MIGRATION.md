# Migration Guide

## What remains compatible

- Existing material, finish, prompt, selection, output, and structure recommendation references remain under `references/`.
- Requests for packaging CMF advice still trigger the Skill and route to Module C.
- Complete artwork may enter Module C directly; Module A and B are not mandatory prerequisites.

## What changed

- `SKILL.md` is now an orchestration entrypoint instead of a complete domain encyclopedia.
- Executable requests use `scripts/skill_entry.py` and a stable JSON contract.
- Every task receives an isolated Job Workspace and manifest.
- Capability status is machine-readable. Documentation is no longer treated as an implemented tool.
- Module B now writes sourced fields and explicit placeholders into `LAYER_ARTWORK`; it does not modify structural layers or claim automatic legal compliance.
- Module C now uses explicit Host/OpenAI-compatible/Custom REST/Mock Provider adapters. External calls require opt-in, and API keys are resolved only from environment variables.
- Mock CMF output is a deterministic test fixture, always marked `manual_review`; it is never represented as a real render.

## Removed or moved

- No web application existed in the baseline repository, so no web code was removed or migrated.
- Detailed CMF knowledge remains in `references/` rather than being duplicated in `SKILL.md`.

## Legacy dielines

The external/local dieline generator is represented by an explicit adapter boundary. It is not silently invoked and no user-specific path is embedded. Model-specific deterministic implementations replace that adapter only after original-output comparison tests pass.
