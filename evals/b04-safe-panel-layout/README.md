# b04-safe-panel-layout

- Module: B
- Input: content placement across semantic non-glue panels
- Expected route: `content_layout`
- Expected tools: `SVG parser`, `field generator`, `safe-area layout`, `structure fingerprint`
- Expected outputs: `content-layout.svg`, `content-spec.json`, `missing-fields.md`, `review-checklist.md`, `source-report.md`
- Expected warnings: `REQUIRES_COMPLIANCE_REVIEW`
- Pass condition: sources/statuses are present and protected structure layers remain unchanged
