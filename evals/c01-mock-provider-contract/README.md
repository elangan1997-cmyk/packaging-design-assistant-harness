# c01-mock-provider-contract

- Module: C
- Input: completed artwork with explicit Mock opt-in
- Expected route: `mockup_render`
- Expected tools: `VisionProvider`, `ImageGenerationProvider`, `visual QA`
- Expected outputs: `cmf-plan.json`, `generation-record.json`, `mockup.png`, `retry-record.json`, `review-checklist.md`, `visual-qa.json`
- Expected warnings: `MOCK_OUTPUT_NOT_A_REAL_CMF_RENDER`
- Pass condition: six outputs are produced and Mock never reports a real render
