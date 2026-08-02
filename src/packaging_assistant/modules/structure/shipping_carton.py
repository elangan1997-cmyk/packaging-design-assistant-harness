from __future__ import annotations

from packaging_assistant.modules.structure.models import Panel, Primitive, StructureGeometry, StructureSpec


def _line(element_id: str, *values: float) -> Primitive:
    return Primitive("line", element_id, tuple(values))


def _poly(element_id: str, *values: float) -> Primitive:
    return Primitive("polyline", element_id, tuple(values))


def build_shipping_carton(spec: StructureSpec) -> StructureGeometry:
    """Box 2.0 regular slotted shipping carton measured from the supplied fixture."""
    length = spec.dimensions.length
    width = spec.dimensions.width
    height = spec.dimensions.height
    shrink = spec.shrink
    glue = spec.glue_width
    x0 = 0.0
    x1 = length
    x2 = length + width
    x3 = 2 * length + width
    x4 = 2 * length + 2 * width - shrink
    top = -height
    flap = width / 2

    crease = (
        _poly("CREASE_PANEL_1", x0, 0, x0, top, x0, top - shrink, x1, top - shrink),
        _poly("CREASE_PANEL_2", x1, top, x1, 0, x2, 0, x2, top, x1, top),
        _line("CREASE_PANEL_3_BOTTOM", x2, shrink, x3, shrink),
        _poly("CREASE_PANEL_4", x4, top, x3, top, x3, 0, x4, 0),
        _line("CREASE_PANEL_3_TOP", x2, top - shrink, x3, top - shrink),
        _line("CREASE_PANEL_1_BOTTOM", x0, shrink, x1, shrink),
    )
    cut = (
        _poly("CUT_TOP_PANEL_3", x2, top, x2, top - flap, x3, top - flap, x3, top),
        _poly("CUT_BOTTOM_PANEL_3", x3, 0, x3, flap, x2, flap, x2, 0),
        _poly("CUT_BOTTOM_PANEL_1", x1, 0, x1, flap, x0, flap, x0, 0),
        _poly("CUT_TOP_PANEL_2", x1, top, x1 + 1.5, top - 1.5, x1 + 1.5, top - flap, x2 - 1.5, top - flap, x2 - 1.5, top - 1.5, x2, top),
        _poly("CUT_BOTTOM_PANEL_2", x2, 0, x2 - 1.5, 1.5, x2 - 1.5, flap, x1 + 1.5, flap, x1 + 1.5, 1.5, x1, 0),
        _poly("CUT_TOP_PANEL_4", x3, top, x3 + 1.5, top - 1.5, x3 + 1.5, top - flap, x4 - 1.5, top - flap, x4 - 1.5, top - 1.5, x4, top),
        _poly("CUT_BOTTOM_PANEL_4", x4, 0, x4 - 1.5, 1.5, x4 - 1.5, flap, x3 + 1.5, flap, x3 + 1.5, 1.5, x3, 0),
        _poly("CUT_TOP_PANEL_1", x0, top, x0, top - flap, x1, top - flap, x1, top),
        _poly("CUT_GLUE_TAB", x0, top, -glue, top + glue * 0.2679491924, -glue, -glue * 0.2679491924, x0, 0),
        _line("CUT_RIGHT_VERTICAL", x4, 0, x4, top),
    )
    panels = (
        Panel("panel-front", "正面", x0, top, length, height),
        Panel("panel-left", "侧面 A", x1, top, width, height),
        Panel("panel-back", "背面", x2, top, length, height),
        Panel("panel-right", "侧面 B", x3, top, width - shrink, height),
        Panel("panel-glue", "糊口", -glue, top + glue * 0.2679491924, glue, height - 2 * glue * 0.2679491924),
    )
    return StructureGeometry(cut=cut, crease=crease, panels=panels, bounds=(-glue, top - flap, x4, flap))
