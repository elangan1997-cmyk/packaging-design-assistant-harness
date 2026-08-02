from __future__ import annotations

from math import tan, radians

from packaging_assistant.modules.structure.models import (
    Panel,
    Primitive,
    StructureGeometry,
    StructureSpec,
)


def _line(element_id: str, *values: float) -> Primitive:
    return Primitive("line", element_id, tuple(values))


def _poly(element_id: str, *values: float) -> Primitive:
    return Primitive("polyline", element_id, tuple(values))


def _path(element_id: str, commands: tuple[str, ...], *values: float) -> Primitive:
    return Primitive("path", element_id, tuple(values), commands)


def build_lock_bottom(spec: StructureSpec) -> StructureGeometry:
    """Reproduce the measured Box 2.0 lock-bottom geometry in canonical millimetres."""
    length = spec.dimensions.length
    width = spec.dimensions.width
    height = spec.dimensions.height
    shrink = spec.shrink
    tuck = spec.tuck_height
    glue = spec.glue_width

    x0 = 0.0
    x1 = length
    x2 = length + width
    x3 = 2 * length + width
    x4 = 2 * length + 2 * width - shrink
    top = -height
    dust_depth = (width + tuck + shrink) / 2
    glue_angle = glue * tan(radians(15))
    quarter3 = 3 * width / 4
    half = width / 2
    right_partial_x = x4 - (half - shrink)

    crease = (
        _line("CREASE_LEFT_VERTICAL", x0, 0, x0, top),
        _poly("CREASE_PANEL_2", x1, top, x1, 0, x2, 0, x2, top, x1, top),
        _line("CREASE_PANEL_1_BOTTOM", x0, 0, x1, 0),
        _poly("CREASE_PANEL_4", x4, top, x3, top, x3, 0, x4, 0),
        _line("CREASE_TOP_PANEL_1", x0, top - shrink, x1, top - shrink),
        _line("CREASE_TUCK", 7, top - width, length - 7, top - width),
        _line("CREASE_PANEL_3_BOTTOM", x2, 0, x3, 0),
    )

    cut = (
        _path(
            "CUT_TOP_TUCK_ARCH",
            ("M", "c", "h", "c"),
            shrink,
            top - width - shrink,
            0,
            0,
            0,
            -tuck,
            tuck,
            -tuck,
            length - 2 * tuck - 2 * shrink,
            tuck,
            0,
            tuck,
            tuck,
            tuck,
            tuck,
        ),
        _poly("CUT_TOP_LEFT_OUTER", x0, top, x0, top - width - shrink, 7, top - width - shrink, 7, top - width + 2 * shrink),
        _poly(
            "CUT_TOP_DUST_LEFT",
            x1, top,
            x1 + 3, top - 3,
            x1 + 6, top - dust_depth,
            x2 - 7.5, top - dust_depth,
            x2 - shrink - 2, top - 7,
            x2 - shrink, top - 5,
            x2 - shrink, top,
        ),
        _poly("CUT_TOP_RIGHT_OUTER", x1, top, x1, top - width - shrink, x1 - 7, top - width - shrink, x1 - 7, top - width + 2 * shrink),
        _poly(
            "CUT_TOP_DUST_RIGHT",
            x3 + shrink, top,
            x3 + shrink, top - 5,
            x3 + shrink + 2, top - 7,
            x3 + 7.5, top - dust_depth,
            x4 - 6, top - dust_depth,
            x4 - 3, top - 3,
            x4, top,
        ),
        _poly("CUT_BOTTOM_LOCK_CENTER", x2, 0, x2 + half, half, x2 + half, quarter3, x3 - half, quarter3, x3 - half, half, x3, 0),
        _poly("CUT_BOTTOM_RIGHT_PARTIAL", x4, 0, right_partial_x, half, right_partial_x, quarter3 - 8),
        _poly("CUT_BOTTOM_LEFT_PARTIAL", x1, 0, x1 + half, half, x1 + half, quarter3 - 8),
        _poly("CUT_BOTTOM_PANEL_1", x0, 0, x0, quarter3, half, quarter3, half, half, length - half, half, length - half, quarter3, x1, quarter3, x1, 0),
        _poly("CUT_GLUE_TAB", x0, top, -glue, top + glue_angle, -glue, -glue_angle, x0, 0),
        _path("CUT_BOTTOM_LEFT_CURVE", ("M", "c"), x1 + half, quarter3 - 8, 0, 0, 0, 6, 6, 6),
        _path("CUT_BOTTOM_RIGHT_CURVE", ("M", "c"), right_partial_x - 6, quarter3 - 2, 0, 0, 6, 0, 6, -6),
        _poly("CUT_BOTTOM_RIGHT_INNER", right_partial_x - 6, quarter3 - 2, x3, quarter3 - 2, x3, 0),
        _poly("CUT_BOTTOM_LEFT_INNER", x1 + half + 6, quarter3 - 2, x2, quarter3 - 2, x2, 0),
        _line("CUT_TOP_MAIN", x2 - shrink, top, x3 + shrink, top),
        _line("CUT_RIGHT_VERTICAL", x4, 0, x4, top),
    )

    panels = (
        Panel("panel-front", "正面", x0, top, length, height),
        Panel("panel-left", "侧面 A", x1, top, width, height),
        Panel("panel-back", "背面", x2, top, length, height),
        Panel("panel-right", "侧面 B", x3, top, width - shrink, height),
        Panel("panel-glue", "糊口", -glue, top + glue_angle, glue, height - 2 * glue_angle),
    )
    min_x = -glue
    min_y = top - width - shrink - tuck
    max_x = x4
    max_y = max(quarter3, quarter3 - 2 + 6)
    return StructureGeometry(cut=cut, crease=crease, panels=panels, bounds=(min_x, min_y, max_x, max_y))
