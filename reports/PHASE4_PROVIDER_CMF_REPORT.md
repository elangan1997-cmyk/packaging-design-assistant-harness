# Phase 4 — Provider-based CMF and Visual QA

## Implemented

- Expanded model capability detection for text, vision, image generation, search, tool calling, structured output, and file reading.
- Added typed Provider configuration and interfaces for LLM, Vision, Image Generation, and Search.
- Added Host, OpenAI-compatible JSON, Custom REST, and deterministic Mock adapters.
- Added ordered provider execution with explicit unavailable/failure results, sanitized timeout/HTTP errors, finite retries, and fallback.
- Added environment-only credential lookup. API key values are not serialized into records, attempts, errors, examples, or logs.
- Added Module C artwork inspection, physical-dimension blocker, material requirement, original-artwork protection contract, CMF plan, image-provider call, independent visual QA, maximum two QA retries, and manual-review routing.
- Added flexible-packaging/heat-seal and bottle/label protection rules.
- Added six outputs: `mockup.png`, `cmf-plan.json`, `generation-record.json`, `visual-qa.json`, `retry-record.json`, and `review-checklist.md`.

## Safety boundary

No Pillow, OpenCV, ImageMagick, FFmpeg, numpy blending, local filter, foil, UV, embossing, reflection, or texture compositing is used. Local code only reads, validates, hashes, routes, records, and writes bytes returned by a Provider. The Mock PNG is a fixed provider-contract fixture, requires explicit opt-in, carries `MOCK_OUTPUT_NOT_A_REAL_CMF_RENDER`, and always enters `manual_review`.

External providers are disabled by default and require `allow_external_api=true`. Their endpoints, models, and environment-variable names are user configuration; no endpoint or secret is hard-coded.

## Verification

- `bash install.sh`: passed; installed version `0.5.0` and health check passed.
- Unit/integration/CLI/provider suite: 38 tests passed.
- Mock CLI end-to-end: six outputs written to an isolated job; status `manual_review`; no external API call.
- Provider tests cover no-vision/no-search availability, timeout sanitization, finite retry, fallback order, dry run, API-key redaction, and reproducible Mock output.

## Not claimed

- No real paid/provider image generation was executed in this phase because no user-approved Provider credential and endpoint were supplied.
- Mock output is not a visual quality sample and is not a real CMF effect image.
- Module A still has only two implemented Box 2.0 models.
- Formal 12-case evals and the complete workflow demo remain Phase 5.
