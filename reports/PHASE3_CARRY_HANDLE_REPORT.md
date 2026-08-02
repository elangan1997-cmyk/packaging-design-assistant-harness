# Phase 3 Carry-handle Structure Report

## Outcome

Module A now includes an independent deterministic generator for Box 2.0 `手提盒` (`carton.box_v2.carry_handle`). It does not call Illustrator, the original JSX, a website, Node.js, or an image model at runtime.

## Geometry covered

- Four body panels and one 15-degree glue tab.
- Two full-width reinforced carry flaps with notch geometry.
- Two rounded horizontal handle apertures.
- Two narrow side slots.
- Two top dust flaps and the complete interlocking bottom structure.
- Eight crease primitives and eighteen cut primitives with stable IDs.

## Original-script regression

The active fixture is the original Illustrator output for L100 × W60 × H160 mm, shrink 0.5 mm, tuck 12 mm, and glue 11 mm. The Illustrator artboard translation is normalized before comparison. Primitive type, sequence, path commands, value count, and every coordinate pass at 0.001 mm precision.

The project acceptance matrix uses one original fixture per box model. The older second lock-bottom fixture remains historical evidence but is not an active acceptance sample.

## Boundaries

This output is a `DESIGN_TEMPLATE` and always carries `REQUIRES_MANUFACTURER_REVIEW`. Board thickness, grain direction, tolerances, handle reinforcement, glue allowance, bleed, and a physical proof still require manufacturer confirmation. Box 2.0 `手提盒` is not the separate F5 `手提袋 Pro` paper-bag model.
