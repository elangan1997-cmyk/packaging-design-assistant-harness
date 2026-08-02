# Original Illustrator Script Benchmark

## Scope

The user authorised local execution of `AI脚本插件146合集-146版.jsx`. The original `盒型2.0` ScriptUI was run in Adobe Illustrator as a black-box reference. Its output was exported to SVG and retained under `tests/fixtures/original-script/`.

The Harness does not require Illustrator, the JSX, a browser, or baoxiaohe.com at runtime.

## Box 2.0 model inventory

The original dialog exposes ten distinct radio-button models. They are represented by ten separate model IDs in the Harness:

| Original name | Harness model ID | Status |
|---|---|---|
| 直线盒 | `carton.box_v2.straight` | registered, not implemented |
| 锁底盒 | `carton.box_v2.lock_bottom` | implemented and regression-tested |
| 飞机盒 | `carton.box_v2.mailer` | registered, not implemented |
| 上盖盒 | `carton.box_v2.top_cover` | registered, not implemented |
| 同向盖 | `carton.box_v2.same_direction_tuck` | registered, not implemented |
| 粘底盒 | `carton.box_v2.glue_bottom` | registered, not implemented |
| 挂耳盒 | `carton.box_v2.hang_tab` | registered, not implemented |
| 手提盒 | `carton.box_v2.carry_handle` | registered, not implemented |
| 纸箱 | `carton.box_v2.shipping_carton` | registered, not implemented |
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

## Regression samples

| Sample | L × W × H | Shrink | Tuck | Glue | Original output |
|---|---|---:|---:|---:|---|
| A | 80 × 40 × 120 mm | 0.5 | 12 | 11 | raw Illustrator SVG fixture |
| B | 100 × 55 × 160 mm | 0.7 | 15 | 14 | raw Illustrator SVG fixture |

Sample B intentionally changes every dimensional parameter and uses a taller, wider structure to catch hard-coded coordinates.

## Comparison method and result

The test parser:

1. selects the documented top-level result group from each raw Illustrator SVG;
2. separates the original red crease group and black cut group;
3. removes only empty Illustrator placeholder paths;
4. converts Illustrator points using `72 / 25.4` points per millimetre;
5. compares element kind, path command topology, element sequence, value count, and every coordinate against the newly generated SVG.

Both samples pass at `0.001 mm` coordinate precision:

- 7 non-empty crease primitives match;
- 16 non-empty cut primitives match;
- all three curved path command sequences match;
- variable tuck arch, dust flaps, bottom locking tabs, and 15-degree glue tab all match.

This is a geometry regression claim for the two tested samples, not a production-readiness claim. Every generated file remains `DESIGN_TEMPLATE` and carries `REQUIRES_MANUFACTURER_REVIEW`.

