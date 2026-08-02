from __future__ import annotations

from math import radians, tan

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


def _horizontal_handle_slot(element_id: str, x: float, y: float, mirrored_close: bool) -> Primitive:
    close_command = "h" if mirrored_close else "H"
    close_value = -30.0 if mirrored_close else x + 5.0
    return _path(
        element_id,
        ("M", "L", "c", "h", "c", "v", "c", close_command, "C", "z"),
        x, y,
        x, y,
        0, -2.75, 2.25, -5, 5, -5,
        30,
        2.75, 0, 5, 2.25, 5, 5,
        0,
        0, 2.75, -2.25, 5, -5, 5,
        close_value,
        x + 2.25, y + 5, x, y + 2.75, x, y,
    )


def _vertical_handle_slot(element_id: str, x: float, y: float, slot_height: float) -> Primitive:
    return _path(
        element_id,
        ("M", "v", "c", "l", "c", "v", "c", "l", "C", "z"),
        x, y,
        -slot_height,
        0, -0.4125, 0.3375, -0.75, 0.75, -0.75,
        0, 0,
        0.4125, 0, 0.75, 0.3375, 0.75, 0.75,
        slot_height,
        0, 0.4125, -0.3375, 0.75, -0.75, 0.75,
        0, 0,
        x + 0.3375, y + 0.75, x, y + 0.4125, x, y,
    )


def build_carry_handle(spec: StructureSpec) -> StructureGeometry:
    """Reproduce the measured Box 2.0 carry-handle geometry in millimetres."""
    length = spec.dimensions.length
    width = spec.dimensions.width
    height = spec.dimensions.height
    shrink = spec.shrink
    glue = spec.glue_width
    tuck = spec.tuck_height

    x0 = 0.0
    x1 = length
    x2 = length + width
    x3 = 2 * length + width
    x4 = 2 * length + 2 * width - shrink
    top = -height
    half = width / 2
    quarter3 = 3 * width / 4
    dust_depth = (width + tuck - shrink) / 2
    glue_angle = glue * tan(radians(15))
    right_partial_x = x4 - (half - shrink)

    crease = (
        _poly("CREASE_PANEL_1", x0, 0, x0, top, x0, top - shrink, x1, top - shrink),
        _poly("CREASE_PANEL_2", x1, top, x1, 0, x2, 0, x2, top, x1, top),
        _line("CREASE_PANEL_3_BOTTOM", x2 + shrink, shrink, x3 - shrink, shrink),
        _poly("CREASE_PANEL_4", x4, top, x3, top, x3, 0, x4, 0),
        _line("CREASE_TOP_PANEL_3", x2, top - shrink, x3, top - shrink),
        _line("CREASE_HANDLE_BACK", x2, top - half, x3, top - half),
        _line("CREASE_HANDLE_FRONT", x0, top - half, x1, top - half),
        _line("CREASE_PANEL_1_BOTTOM", x0, shrink, x1, shrink),
    )

    cut = (
        _poly(
            "CUT_HANDLE_BACK_OUTER",
            x2, top, x2, top - width,
            x2 + 5, top - width,
            x2 + 10, top - width + 5,
            x2 + 15, top - width,
            x3 - 15, top - width,
            x3 - 10, top - width + 5,
            x3 - 5, top - width,
            x3, top - width,
            x3, top,
        ),
        _poly(
            "CUT_TOP_DUST_LEFT",
            x1, top,
            x1 + 3, top - 3,
            x1 + 6 + shrink, top - dust_depth,
            x2 - 6, top - dust_depth,
            x2 - 3, top - 3,
            x2, top,
        ),
        _poly(
            "CUT_TOP_DUST_RIGHT",
            x3, top,
            x3 + 3, top - 3,
            x3 + 6, top - dust_depth,
            x4 - 6, top - dust_depth,
            x4 - 3, top - 3,
            x4, top,
        ),
        _poly("CUT_BOTTOM_LOCK_CENTER", x2, 0, x2 + half, half, x2 + half, quarter3, x3 - half, quarter3, x3 - half, half, x3, 0),
        _poly(
            "CUT_HANDLE_FRONT_OUTER",
            x0, top, x0, top - width,
            x0 + 5, top - width,
            x0 + 10, top - width + 5,
            x0 + 15, top - width,
            x1 - 15, top - width,
            x1 - 10, top - width + 5,
            x1 - 5, top - width,
            x1, top - width,
            x1, top,
        ),
        _poly("CUT_BOTTOM_RIGHT_PARTIAL", x4, 0, right_partial_x, half, right_partial_x, quarter3 - 7),
        _poly("CUT_BOTTOM_LEFT_PARTIAL", x1, 0, x1 + half, half, x1 + half, quarter3 - 7),
        _poly("CUT_BOTTOM_PANEL_1", x0, 0, x0, quarter3, half, quarter3, half, half, length - half, half, length - half, quarter3, x1, quarter3, x1, 0),
        _poly("CUT_GLUE_TAB", x0, top, -glue, top + glue_angle, -glue, -glue_angle, x0, 0),
        _path("CUT_BOTTOM_LEFT_CURVE", ("M", "c"), x1 + half, quarter3 - 7, 0, 0, 0, 5, 5, 5),
        _path("CUT_BOTTOM_RIGHT_CURVE", ("M", "c"), right_partial_x - 5, quarter3 - 2, 0, 0, 5, 0, 5, -5),
        _poly("CUT_BOTTOM_RIGHT_INNER", right_partial_x - 5, quarter3 - 2, x3, quarter3 - 2, x3, 0),
        _poly("CUT_BOTTOM_LEFT_INNER", x1 + half + 5, quarter3 - 2, x2, quarter3 - 2, x2, 0),
        _line("CUT_RIGHT_VERTICAL", x4, 0, x4, top),
        _horizontal_handle_slot("CUT_HANDLE_SLOT_FRONT", length / 2 - 20, top - width + 15, False),
        _horizontal_handle_slot("CUT_HANDLE_SLOT_BACK", x2 + length / 2 - 19.95, top - width + 15.05, True),
        _vertical_handle_slot("CUT_HANDLE_SLOT_SIDE_LEFT", x1 + half - 0.75, top - 2.75, half - 1),
        _vertical_handle_slot("CUT_HANDLE_SLOT_SIDE_RIGHT", x3 + half - 0.45, top - 2.7, half - 1),
    )

    panels = (
        Panel("PANEL_FRONT", "正面", x0, top, length, height),
        Panel("PANEL_SIDE_LEFT", "侧面 A", x1, top, width, height),
        Panel("PANEL_BACK", "背面", x2, top, length, height),
        Panel("PANEL_SIDE_RIGHT", "侧面 B", x3, top, width - shrink, height),
        Panel("PANEL_GLUE", "糊口", -glue, top + glue_angle, glue, height - 2 * glue_angle),
    )
    min_y = top - width
    max_y = max(quarter3, quarter3 - 5 + 5)
    return StructureGeometry(cut=cut, crease=crease, panels=panels, bounds=(-glue, min_y, x4, max_y))
