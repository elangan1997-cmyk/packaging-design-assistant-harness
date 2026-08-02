# Box 2.0 Supplied SVG Fixture Audit

## Conclusion

The supplied folder contains eight parseable SVG files, but they do not represent eight trustworthy independent models. Six files are accepted as new regression fixtures, one is a lock-bottom output where an airplane/mailer fixture was expected, and one duplicates the straight-carton geometry exactly.

Default parameters used for accepted samples: shrink `0.5 mm`, tuck height `12 mm`, glue width `11 mm`.

## Per-file disposition

| Supplied file | Observed structure | Disposition |
|---|---|---|
| `01-直线盒t-100x60x160.svg` | reverse-tuck straight carton | accepted as `carton.box_v2.straight` |
| `02-锁底盒-220x160x60.svg` | lock-bottom folding carton | rejected as airplane evidence; this geometry is not a mailer |
| `03-top-cover-100x60x50.svg` | top-cover/tuck folding carton | accepted as `carton.box_v2.top_cover` |
| `04-上盖盒-100x60x160.svg` | coordinate-identical to file 01 | rejected as an independent fixture |
| `05-同向盖-100x60x160.svg` | same-direction tuck carton | accepted as `carton.box_v2.same_direction_tuck` |
| `06-粘底盒-100x60x160.svg` | glue-bottom carton | accepted as `carton.box_v2.glue_bottom` |
| `07-挂耳盒-300x200x150.svg` | hang-tab carton with rounded slot | accepted as `carton.box_v2.hang_tab` |
| `08-纸箱-60x50x80.svg` | regular slotted shipping carton | accepted as `carton.box_v2.shipping_carton` |

## Defects found in the original-script output set

1. The airplane/mailer candidate has the characteristic lock-bottom panel layout and bottom locking flaps. Reproducing it would make the Harness generate the wrong box type.
2. Files 01 and 04 have the same normalized primitive hash, `d192b9961e9873c9`. File 04 cannot prove a separate model.
3. Files 04–07 render every primitive black, but their nested Illustrator group order still separates crease and cut geometry. The Harness restores explicit `LAYER_CREASE` and `LAYER_CUT` semantics.
4. “其它” has no fixed parameterized geometry in the supplied set and remains a clarification-required custom mode.

## Harness result

Eight fixed models are now available: straight, lock-bottom, top-cover, same-direction tuck, glue-bottom, hang-tab, carry-handle, and shipping carton. Each has one active regression fixture and its own builder. Airplane/mailer and custom return `NOT_IMPLEMENTED`; neither silently falls back to another structure.

The full suite passes 52 tests with `PYTHONPATH=src python3 -m unittest discover -s tests -v`.
