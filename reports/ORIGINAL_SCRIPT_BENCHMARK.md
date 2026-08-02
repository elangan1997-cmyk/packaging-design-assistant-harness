# Original Illustrator Script Benchmark

## Scope

The user authorised local execution of `AI脚本插件146合集-146版.jsx`. The original `盒型2.0` ScriptUI was run in Adobe Illustrator as a black-box reference. Its output was exported to SVG and retained under `tests/fixtures/original-script/`.

The Harness does not require Illustrator, the JSX, a browser, or baoxiaohe.com at runtime.

## Box 2.0 model inventory

The original dialog exposes ten distinct radio-button models. They are represented by ten separate model IDs in the Harness:

| Original name | Harness model ID | Status |
|---|---|---|
| 直线盒 | `carton.box_v2.straight` | implemented and regression-tested |
| 锁底盒 | `carton.box_v2.lock_bottom` | implemented and regression-tested |
| 飞机盒 | `carton.box_v2.mailer` | registered, not implemented |
| 上盖盒 | `carton.box_v2.top_cover` | implemented and regression-tested |
| 同向盖 | `carton.box_v2.same_direction_tuck` | implemented and regression-tested |
| 粘底盒 | `carton.box_v2.glue_bottom` | implemented and regression-tested |
| 挂耳盒 | `carton.box_v2.hang_tab` | implemented and regression-tested |
| 手提盒 | `carton.box_v2.carry_handle` | implemented and regression-tested |
| 纸箱 | `carton.box_v2.shipping_carton` | implemented and regression-tested |
| 其它 | `carton.box_v2.custom` | registered, not implemented |

This separation is deliberate: an unimplemented model returns `NOT_IMPLEMENTED`; it is never routed to the lock-bottom generator as a visual approximation.

## Original inputs observed

All models share these visible fields in the original dialog:

- 长度: default 60 mm
- 宽度: default 50 mm
- 高度: default 80 mm
- 缩位: default 0.5 mm
- 插舌高度: default 12 mm
- 粘口宽度: default 11 mm
- 添加图层: enabled by default

The dialog identifies itself as version `2nd version`, dated `2012.5.1`, author `guise4543`.

## Active regression samples

The acceptance rule is one original Illustrator fixture per box model.

| Model | L × W × H | Shrink | Tuck | Glue | Original output |
|---|---|---:|---:|---:|---|
| 锁底盒 | 80 × 40 × 120 mm | 0.5 | 12 | 11 | raw Illustrator SVG fixture |
| 手提盒 | 100 × 60 × 160 mm | 0.5 | 12 | 11 | raw Illustrator SVG fixture |
| 直线盒 | 100 × 60 × 160 mm | 0.5 | 12 | 11 | compact Illustrator SVG fixture |
| 上盖盒 | 100 × 60 × 50 mm | 0.5 | 12 | 11 | compact Illustrator SVG fixture |
| 同向盖 | 100 × 60 × 160 mm | 0.5 | 12 | 11 | compact Illustrator SVG fixture |
| 粘底盒 | 100 × 60 × 160 mm | 0.5 | 12 | 11 | compact Illustrator SVG fixture |
| 挂耳盒 | 300 × 200 × 150 mm | 0.5 | 12 | 11 | compact Illustrator SVG fixture |
| 纸箱 | 60 × 50 × 80 mm | 0.5 | 12 | 11 | compact Illustrator SVG fixture |

The previously captured 100 × 55 × 160 mm lock-bottom SVG remains historical evidence but is not part of the active one-sample-per-model matrix.

## Comparison method and result

The test parser:

1. selects the documented result group and normalizes artboard translation where needed;
2. separates the original red crease group and black cut group;
3. removes only empty Illustrator placeholder paths;
4. converts Illustrator points using `72 / 25.4` points per millimetre;
5. compares element kind, path command topology, element sequence, value count, and every coordinate against the newly generated SVG.

The original two fixtures pass at `0.001 mm` coordinate precision. The six compact exports pass with the same primitive topology and a maximum accepted coordinate delta of `0.05 mm`, covering Illustrator's compact-export rounding and intentional sub-0.05 mm offsets:

- 锁底盒: 7 non-empty crease primitives and 16 cut primitives match;
- 手提盒: 8 non-empty crease primitives and 18 cut primitives match;
- 直线盒: 7 crease primitives and 13 cut primitives match;
- 上盖盒: 7 crease primitives and 14 cut primitives match;
- 同向盖: 7 crease primitives and 13 cut primitives match;
- 粘底盒: 7 crease primitives and 12 cut primitives match;
- 挂耳盒: 7 crease primitives and 14 cut primitives match, including the rounded hanger aperture;
- 纸箱: 6 crease primitives and 10 cut primitives match;
- hand apertures, side slots, dust flaps, bottom locking tabs, and 15-degree glue tabs are included.

The supplied plane-box candidate is not an airplane/mailer geometry: its panel and flap topology is a lock-bottom carton. It is excluded from the regression matrix, and the Harness intentionally returns `NOT_IMPLEMENTED` for `carton.box_v2.mailer` instead of reproducing that defect. The duplicated `04-上盖盒-100x60x160.svg` is also excluded because its geometry hash is identical to the supplied straight-carton sample.

This is a geometry regression claim for the tested samples, not a production-readiness claim. Every generated file remains `DESIGN_TEMPLATE` and carries `REQUIRES_MANUFACTURER_REVIEW`.
