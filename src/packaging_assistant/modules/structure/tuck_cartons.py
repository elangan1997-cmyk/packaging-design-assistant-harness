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


def _rect(element_id: str, *values: float) -> Primitive:
    return Primitive("rect", element_id, tuple(values))


def _body(spec: StructureSpec) -> tuple[float, ...]:
    length = spec.dimensions.length
    width = spec.dimensions.width
    height = spec.dimensions.height
    shrink = spec.shrink
    return (0.0, length, length + width, 2 * length + width, 2 * length + 2 * width - shrink, -height)


def _panels(spec: StructureSpec) -> tuple[Panel, ...]:
    x0, x1, x2, x3, x4, top = _body(spec)
    glue = spec.glue_width
    glue_angle = glue * tan(radians(15))
    return (
        Panel("panel-front", "正面", x0, top, x1 - x0, -top),
        Panel("panel-left", "侧面 A", x1, top, x2 - x1, -top),
        Panel("panel-back", "背面", x2, top, x3 - x2, -top),
        Panel("panel-right", "侧面 B", x3, top, x4 - x3, -top),
        Panel("panel-glue", "糊口", -glue, top + glue_angle, glue, -top - 2 * glue_angle),
    )


def _glue_tab(spec: StructureSpec, top: float) -> Primitive:
    glue = spec.glue_width
    angle = glue * tan(radians(15))
    return _poly("CUT_GLUE_TAB", 0, top, -glue, top + angle, -glue, -angle, 0, 0)


def _top_tuck_arch(element_id: str, x: float, top: float, length: float, width: float, tuck: float, shrink: float, extra: float = 0.0) -> Primitive:
    return _path(
        element_id,
        ("M", "S", "h", "c"),
        x + shrink, top - width - shrink,
        x + shrink, top - width - shrink - tuck,
        x + shrink + tuck + extra, top - width - shrink - tuck,
        length - 2 * tuck - 2 * shrink - extra,
        tuck, 0, tuck, tuck, tuck, tuck,
    )


def _bottom_tuck_arch_relative(element_id: str, right_x: float, length: float, width: float, tuck: float, shrink: float, extra: float = 0.0) -> Primitive:
    return _path(
        element_id,
        ("M", "s", "h", "c"),
        right_x - shrink, width + shrink,
        0, tuck, -(tuck + extra), tuck,
        -(length - 2 * tuck - 2 * shrink - extra),
        -tuck, 0, -tuck, -tuck, -tuck, -tuck,
    )


def _top_dust_left(element_id: str, x1: float, x2: float, top: float, depth: float) -> Primitive:
    return _poly(
        element_id,
        x1, top,
        x1 + 3, top - 3,
        x1 + 6, top - depth,
        x2 - 7.5, top - depth,
        x2 - 2.5, top - 7,
        x2 - 0.5, top - 5,
        x2 - 0.5, top,
    )


def _top_dust_right(element_id: str, x3: float, x4: float, top: float, depth: float, shrink: float) -> Primitive:
    return _poly(
        element_id,
        x3 + shrink, top,
        x3 + shrink, top - 5,
        x3 + 2 + shrink, top - 7,
        x3 + 7 + shrink, top - depth,
        x4 - 6, top - depth,
        x4 - 3, top - 3,
        x4, top,
    )


def _shifted_top_dust_left(element_id: str, x1: float, x2: float, top: float, depth: float, shrink: float) -> Primitive:
    return _poly(
        element_id,
        x1 + shrink, top,
        x1 + shrink, top - 5,
        x1 + 3.5, top - 8,
        x1 + 8, top - depth,
        x2 - 6, top - depth,
        x2 - 3, top - 3,
        x2, top,
    )


def _shifted_top_dust_right(element_id: str, x3: float, x4: float, top: float, depth: float) -> Primitive:
    return _poly(
        element_id,
        x3, top,
        x3 + 3, top - 3,
        x3 + 6, top - depth,
        x4 - 7.5, top - depth,
        x4 - 3, top - 8,
        x4, top - 5,
        x4, top,
    )


def _bottom_dust_left(element_id: str, x1: float, x2: float, depth: float, shrink: float = 0.0) -> Primitive:
    return _poly(
        element_id,
        x2, 0,
        x2 - 3, 3,
        x2 - 6, depth,
        x1 + 7.5, depth,
        x1 + 2.5, 7,
        x1 + 0.5, 5,
        x1 + 0.5, 0,
    )


def _bottom_dust_right(element_id: str, x3: float, x4: float, depth: float) -> Primitive:
    return _poly(
        element_id,
        x3, 0,
        x3 + 3, 3,
        x3 + 6, depth,
        x4 - 7, depth,
        x4 - 2, 7,
        x4, 5,
        x4, 0,
    )


def _bottom_dust_forward_left(element_id: str, x1: float, x2: float, depth: float) -> Primitive:
    return _poly(
        element_id,
        x1, 0,
        x1 + 3, 3,
        x1 + 6, depth,
        x2 - 7.5, depth,
        x2 - 2.5, 7,
        x2 - 0.5, 5,
        x2 - 0.5, 0,
    )


def _bottom_dust_forward_right(element_id: str, x3: float, x4: float, depth: float, shrink: float) -> Primitive:
    return _poly(
        element_id,
        x3 + shrink, 0,
        x3 + shrink, 5,
        x3 + 2.5, 7,
        x3 + 7.5, depth,
        x4 - 6, depth,
        x4 - 3, 3,
        x4, 0,
    )


def _shifted_bottom_dust_left(element_id: str, x1: float, x2: float, depth: float, shrink: float) -> Primitive:
    return _poly(
        element_id,
        x1 + shrink, 0,
        x1 + shrink, 5,
        x1 + 3.5, 8,
        x1 + 7.5, depth,
        x2 - 6, depth,
        x2 - 3, 3,
        x2, 0,
    )


def _shifted_bottom_dust_right(element_id: str, x3: float, x4: float, depth: float) -> Primitive:
    return _poly(
        element_id,
        x3, 0,
        x3 + 3.5, 3,
        x3 + 6, depth,
        x4 - 7.5, depth,
        x4 - 3, 8,
        x4, 5,
        x4, 0,
    )


def build_straight(spec: StructureSpec) -> StructureGeometry:
    """Box 2.0 reverse-tuck straight carton, measured from the supplied Illustrator output."""
    length, width, shrink, tuck = spec.dimensions.length, spec.dimensions.width, spec.shrink, spec.tuck_height
    x0, x1, x2, x3, x4, top = _body(spec)
    depth = (width + tuck + shrink) / 2
    crease = (
        _line("CREASE_LEFT_VERTICAL", x0, 0, x0, top),
        _poly("CREASE_PANEL_2", x1, top, x1, 0, x2, 0, x2, top, x1, top),
        _line("CREASE_PANEL_3_BOTTOM", x2, shrink, x3, shrink),
        _poly("CREASE_PANEL_4", x4, top, x3, top, x3, 0, x4, 0),
        _line("CREASE_TOP_TUCK", 7, top - width, length - 7, top - width),
        _line("CREASE_BOTTOM_TUCK", x2 + 7, width, x3 - 7, width),
        _line("CREASE_PANEL_1_TOP", x0, top - shrink, x1, top - shrink),
    )
    cut = (
        _top_tuck_arch("CUT_TOP_TUCK_ARCH", x0, top, length, width, tuck, shrink),
        _bottom_tuck_arch_relative("CUT_BOTTOM_TUCK_ARCH", x3, length, width, tuck, shrink),
        _poly("CUT_TOP_LEFT_OUTER", x0, top, x0, top - width - shrink, 7, top - width - shrink, 7, top - width + 2 * shrink),
        _poly("CUT_BOTTOM_RIGHT_OUTER", x3, 0, x3, width + shrink, x3 - 7, width + shrink, x3 - 7, width - 2 * shrink),
        _top_dust_left("CUT_TOP_DUST_LEFT", x1, x2, top, depth),
        _bottom_dust_left("CUT_BOTTOM_DUST_LEFT", x1, x2, depth),
        _poly("CUT_TOP_RIGHT_OUTER", x1, top, x1, top - width - shrink, x1 - 7, top - width - shrink, x1 - 7, top - width + 2 * shrink),
        _poly("CUT_BOTTOM_LEFT_OUTER", x2, 0, x2, width + shrink, x2 + 7, width + shrink, x2 + 7, width - 2 * shrink),
        _top_dust_right("CUT_TOP_DUST_RIGHT", x3, x4, top, depth, shrink),
        _bottom_dust_right("CUT_BOTTOM_DUST_RIGHT", x3, x4, depth),
        _poly("CUT_GLUE_TAB", 0, top, -spec.glue_width, top + spec.glue_width * tan(radians(15)), -spec.glue_width, -spec.glue_width * tan(radians(15)), 0, 0, x1, 0),
        _line("CUT_TOP_MAIN", x2 - shrink, top, x3 + shrink, top),
        _line("CUT_RIGHT_VERTICAL", x4, 0, x4, top),
    )
    return StructureGeometry(cut=cut, crease=crease, panels=_panels(spec), bounds=(-spec.glue_width, top - width - shrink - tuck, x4, width + shrink + tuck))


def build_top_cover(spec: StructureSpec) -> StructureGeometry:
    """Box 2.0 top-cover carton, using the independently labelled 100×60×50 sample."""
    length, width, shrink, tuck = spec.dimensions.length, spec.dimensions.width, spec.shrink, spec.tuck_height
    x0, x1, x2, x3, x4, top = _body(spec)
    depth = (width + tuck + shrink) / 2
    crease = (
        _line("CREASE_LEFT_VERTICAL", x0, 0, x0, top),
        _poly("CREASE_PANEL_2", x1, top, x1, 0, x2, 0, x2, top, x1, top),
        _line("CREASE_PANEL_1_BOTTOM", x0, shrink, x1, shrink),
        _poly("CREASE_PANEL_4", x4, top, x3, top, x3, 0, x4, 0),
        _line("CREASE_PANEL_1_TOP", x0, top - shrink, x1, top - shrink),
        _line("CREASE_TOP_TUCK", 7, top - width, length - 7, top - width),
        _line("CREASE_BOTTOM_TUCK", 7, width, length - 7, width),
    )
    bottom_arch = _path(
        "CUT_BOTTOM_TUCK_ARCH", ("M", "s", "H", "c"),
        x1 - shrink, width + shrink,
        0, tuck, -tuck, tuck,
        tuck + shrink,
        -tuck, 0, -tuck, -tuck, -tuck, -tuck,
    )
    cut = (
        _top_tuck_arch("CUT_TOP_TUCK_ARCH", x0, top, length, width, tuck, shrink),
        bottom_arch,
        _poly("CUT_TOP_LEFT_OUTER", x0, top, x0, top - width - shrink, 7, top - width - shrink, 7, top - width + 2 * shrink),
        _poly("CUT_BOTTOM_RIGHT_OUTER", x1, 0, x1, width + shrink, x1 - 7, width + shrink, x1 - 7, width - 2 * shrink),
        _top_dust_left("CUT_TOP_DUST_LEFT", x1, x2, top, depth),
        _poly("CUT_TOP_RIGHT_OUTER", x1, top, x1, top - width - shrink, x1 - 7, top - width - shrink, x1 - 7, top - width + 2 * shrink),
        _poly("CUT_BOTTOM_LEFT_OUTER", x0, 0, x0, width + shrink, 7, width + shrink, 7, width - 2 * shrink),
        _top_dust_right("CUT_TOP_DUST_RIGHT", x3, x4, top, depth, shrink),
        _bottom_dust_forward_left("CUT_BOTTOM_DUST_LEFT", x1, x2, depth),
        _bottom_dust_forward_right("CUT_BOTTOM_DUST_RIGHT", x3, x4, depth, shrink),
        _glue_tab(spec, top),
        _line("CUT_BOTTOM_MAIN", x2 - shrink, 0, x3 + shrink, 0),
        _line("CUT_TOP_MAIN", x2 - shrink, top, x3 + shrink, top),
        _line("CUT_RIGHT_VERTICAL", x4, 0, x4, top),
    )
    return StructureGeometry(cut=cut, crease=crease, panels=_panels(spec), bounds=(-spec.glue_width, top - width - shrink - tuck, x4, width + shrink + tuck))


def build_same_direction_tuck(spec: StructureSpec) -> StructureGeometry:
    """Box 2.0 same-direction tuck carton."""
    length, width, shrink, tuck = spec.dimensions.length, spec.dimensions.width, spec.shrink, spec.tuck_height
    x0, x1, x2, x3, x4, top = _body(spec)
    depth = (width + tuck + shrink) / 2
    crease = (
        _line("CREASE_LEFT_VERTICAL", x0, 0, x0, top),
        _poly("CREASE_PANEL_2", x1, top, x1, 0, x2, 0, x2, top, x1, top),
        _line("CREASE_PANEL_3_BOTTOM", x2, shrink, x3, shrink),
        _poly("CREASE_PANEL_4", x4, top, x3, top, x3, 0, x4, 0),
        _line("CREASE_PANEL_3_TOP", x2, top - shrink, x3, top - shrink),
        _line("CREASE_TOP_TUCK", x2 + 7, top - width, x3 - 7, top - width),
        _line("CREASE_BOTTOM_TUCK", x2 + 7, width, x3 - 7, width),
    )
    cut = (
        _top_tuck_arch("CUT_TOP_TUCK_ARCH", x2, top, length, width, tuck, shrink, shrink),
        _bottom_tuck_arch_relative("CUT_BOTTOM_TUCK_ARCH", x3, length, width, tuck, shrink, shrink),
        _poly("CUT_TOP_LEFT_OUTER", x2, top, x2, top - width - shrink, x2 + 7, top - width - shrink, x2 + 7, top - width + 2 * shrink),
        _poly("CUT_BOTTOM_RIGHT_OUTER", x3, 0, x3, width + shrink, x3 - 7, width + shrink, x3 - 7, width - 2 * shrink),
        _shifted_top_dust_left("CUT_TOP_DUST_LEFT", x1, x2, top, depth, shrink),
        _poly("CUT_TOP_RIGHT_OUTER", x3, top, x3, top - width - shrink, x3 - 7, top - width - shrink, x3 - 7, top - width + 2 * shrink),
        _poly("CUT_BOTTOM_LEFT_OUTER", x2, 0, x2, width + shrink, x2 + 7, width + shrink, x2 + 7, width - 2 * shrink),
        _shifted_top_dust_right("CUT_TOP_DUST_RIGHT", x3, x4, top, depth),
        _shifted_bottom_dust_left("CUT_BOTTOM_DUST_LEFT", x1, x2, depth, shrink),
        _shifted_bottom_dust_right("CUT_BOTTOM_DUST_RIGHT", x3, x4, depth),
        _poly("CUT_GLUE_TAB", 0, top, -spec.glue_width, top + spec.glue_width * tan(radians(15)), -spec.glue_width, -spec.glue_width * tan(radians(15)), 0, 0, x1 + shrink, 0),
        _line("CUT_TOP_PANEL_1", x0, top, x1 + shrink, top),
        _line("CUT_RIGHT_VERTICAL", x4, 0, x4, top),
    )
    return StructureGeometry(cut=cut, crease=crease, panels=_panels(spec), bounds=(-spec.glue_width, top - width - shrink - tuck, x4, width + shrink + tuck))


def build_glue_bottom(spec: StructureSpec) -> StructureGeometry:
    """Box 2.0 glue-bottom carton."""
    length, width, shrink, tuck = spec.dimensions.length, spec.dimensions.width, spec.shrink, spec.tuck_height
    x0, x1, x2, x3, x4, top = _body(spec)
    depth = (width + tuck + shrink) / 2
    crease = (
        _line("CREASE_LEFT_VERTICAL", x0, 0, x0, top),
        _poly("CREASE_PANEL_2", x1, top, x1, 0, x2, 0, x2, top, x1, top),
        _line("CREASE_PANEL_3_BOTTOM", x2 + shrink, shrink, x3 - shrink, shrink),
        _poly("CREASE_PANEL_4", x4, top, x3, top, x3, 0, x4, 0),
        _line("CREASE_PANEL_3_TOP", x2, top - shrink, x3, top - shrink),
        _line("CREASE_TOP_TUCK", x2 + 7, top - width, x3 - 7, top - width),
        _line("CREASE_PANEL_1_BOTTOM", x0 + shrink, shrink, x1 - shrink, shrink),
    )
    cut = (
        _top_tuck_arch("CUT_TOP_TUCK_ARCH", x2, top, length, width, tuck, shrink, shrink),
        _poly("CUT_TOP_LEFT_OUTER", x2, top, x2, top - width - shrink, x2 + 7, top - width - shrink, x2 + 7, top - width + 2 * shrink),
        _shifted_top_dust_left("CUT_TOP_DUST_LEFT", x1, x2, top, depth, shrink),
        _poly("CUT_TOP_RIGHT_OUTER", x3, top, x3, top - width - shrink, x3 - 7, top - width - shrink, x3 - 7, top - width + 2 * shrink),
        _shifted_top_dust_right("CUT_TOP_DUST_RIGHT", x3, x4, top, depth),
        _poly("CUT_BOTTOM_PANEL_1", x0, 0, x0 + 3, 3, x0 + 6, width - 3, x1 - 6, width - 3, x1 - 3, 3, x1, 0),
        _poly("CUT_BOTTOM_PANEL_2", x1, 0, x1 + 3, 3, x1 + 6, depth, x2 - 6, depth, x2 - 3, 3, x2, 0),
        _poly("CUT_BOTTOM_PANEL_3", x2, 0, x2 + 1, 1, x2 + 1.5, width - shrink, x3 - 1.5, width - shrink, x3 - 1, 1, x3, 0),
        _poly("CUT_BOTTOM_PANEL_4", x3, 0, x3 + 3.5, 3, x3 + 6, depth, x4 - 6, depth, x4 - 3, 3, x4, 0),
        _glue_tab(spec, top),
        _line("CUT_TOP_PANEL_1", x0, top, x1 + shrink, top),
        _line("CUT_RIGHT_VERTICAL", x4, 0, x4, top),
    )
    return StructureGeometry(cut=cut, crease=crease, panels=_panels(spec), bounds=(-spec.glue_width, top - width - shrink - tuck, x4, width - shrink))


def build_hang_tab(spec: StructureSpec) -> StructureGeometry:
    """Box 2.0 hang-tab carton, including the rounded hanging aperture."""
    length, width, shrink, tuck = spec.dimensions.length, spec.dimensions.width, spec.shrink, spec.tuck_height
    x0, x1, x2, x3, x4, top = _body(spec)
    depth = (width + tuck + shrink) / 2
    slot_width, slot_height = 56.0, 16.0
    slot_x = x0 + (length - slot_width) / 2
    slot_y = top - width + 66.6667
    crease = (
        _line("CREASE_LEFT_VERTICAL", x0, 0, x0, top),
        _poly("CREASE_PANEL_2", x1, top, x1, 0, x2, 0, x2, top, x1, top),
        _line("CREASE_PANEL_3_BOTTOM", x2 + shrink, shrink, x3 - shrink, shrink),
        _poly("CREASE_PANEL_4", x4, top, x3, top, x3, 0, x4, 0),
        _line("CREASE_PANEL_3_TOP", x2, top - shrink, x3, top - shrink),
        _line("CREASE_TOP_TUCK", x2 + 8, top - width, x3 - 8, top - width),
        _line("CREASE_PANEL_1_BOTTOM", x0 + shrink, shrink, x1 - shrink, shrink),
    )
    cut = (
        _rect("CUT_HANGER_SLOT", slot_x, slot_y, slot_width, slot_height, slot_height / 2, slot_height / 2),
        _path(
            "CUT_TOP_TUCK_ARCH", ("M", "s", "h", "c"),
            x2 + shrink, top - width - shrink,
            0, -tuck, tuck + shrink, -tuck,
            length - 2 * tuck - 3 * shrink,
            tuck, 0, tuck, tuck, tuck, tuck,
        ),
        _poly("CUT_TOP_LEFT_OUTER", x2, top, x2, top - width - shrink, x2 + 8, top - width - shrink, x2 + 8, top - width + 2 * shrink),
        _poly("CUT_TOP_DUST_LEFT", x1 + shrink, top, x1 + shrink, top - 6, x1 + 6.5, top - 12, x1 + 15.5, top - depth, x2 - 12, top - depth, x2 - 6, top - 6, x2, top),
        _poly("CUT_TOP_RIGHT_OUTER", x3, top, x3, top - width - shrink, x3 - 8, top - width - shrink, x3 - 8, top - width + 2 * shrink),
        _poly("CUT_TOP_DUST_RIGHT", x3, top, x3 + 6, top - 6, x3 + 12, top - depth, x4 - 15, top - depth, x4 - 6, top - 12, x4, top - 6, x4, top),
        _poly("CUT_BOTTOM_PANEL_1", x0, 0, x0 + 6, 6, x0 + 12, width - 3, x1 - 12, width - 3, x1 - 6, 6, x1, 0),
        _poly("CUT_BOTTOM_PANEL_2", x1, 0, x1 + 6, 6, x1 + 12, depth, x2 - 12, depth, x2 - 6, 6, x2, 0),
        _poly("CUT_BOTTOM_PANEL_3", x2, 0, x2 + 2, 2, x2 + 3, width - shrink, x3 - 3, width - shrink, x3 - 2, 2, x3, 0),
        _poly("CUT_BOTTOM_PANEL_4", x3, 0, x3 + 6.5, 6, x3 + 12, depth, x4 - 12, depth, x4 - 6, 6, x4, 0),
        _poly("CUT_HANGER_PANEL", x0, top, x0, top - width, x1, top - width, x1, top),
        _glue_tab(spec, top),
        _line("CUT_TOP_JOIN", x1, top, x1 + shrink, top),
        _line("CUT_RIGHT_VERTICAL", x4, 0, x4, top),
    )
    return StructureGeometry(cut=cut, crease=crease, panels=_panels(spec), bounds=(-spec.glue_width, top - width - tuck, x4, width - shrink))
