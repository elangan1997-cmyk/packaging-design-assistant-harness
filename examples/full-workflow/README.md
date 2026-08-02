# Full workflow demo

This runnable demo executes:

```text
Box model + dimensions
-> deterministic template.svg
-> sourced content-layout.svg
-> Provider contract call
-> visual-qa.json
```

Run:

```bash
.venv/bin/python examples/full-workflow/run_demo.py --output output/full-workflow-demo
```

The final Module C stage deliberately uses the deterministic Mock Provider. It verifies orchestration, output contracts, and manual-review handling only. `mockup.png` is not a real CMF render or visual-quality example. Replace the Mock configuration with a user-approved real Provider configuration for an actual render.
