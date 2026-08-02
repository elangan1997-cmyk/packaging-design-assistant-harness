from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from packaging_assistant.modules.structure.models import Panel, Primitive, StructureGeometry, StructureSpec


PT_PER_MM = 72 / 25.4
REFERENCE_LENGTH = 300.0
REFERENCE_WIDTH = 200.0
REFERENCE_DEPTH = 60.0
REFERENCE_THICKNESS = 0.3
REFERENCE_PATH = Path(__file__).with_name("assets") / "box-v2-mailer-300x200x60.svg"
TOKEN_RE = re.compile(r"[A-Za-z]|[-+]?(?:\d*\.\d+|\d+)")
COMMAND_SIZES = {
    "M": 2, "L": 2, "C": 6, "S": 4, "H": 1, "V": 1, "Z": 0,
    "m": 2, "l": 2, "c": 6, "s": 4, "h": 1, "v": 1, "z": 0,
}


def _path_tokens(d: str) -> tuple[tuple[str, ...], tuple[float, ...]]:
    tokens = TOKEN_RE.findall(d)
    commands: list[str] = []
    values: list[float] = []
    index = 0
    command: str | None = None
    while index < len(tokens):
        if tokens[index].isalpha():
            command = tokens[index]
            index += 1
        if command not in COMMAND_SIZES:
            raise ValueError(f"Unsupported mailer path command: {tokens[index]}")
        commands.append(command)
        size = COMMAND_SIZES[command]
        values.extend(float(item) / PT_PER_MM for item in tokens[index:index + size])
        index += size
        if command in {"Z", "z"}:
            command = None
    return tuple(commands), tuple(values)


def _scaled_path(commands: tuple[str, ...], values: tuple[float, ...], sx: float, sy: float) -> tuple[float, ...]:
    result: list[float] = []
    index = 0
    for command in commands:
        size = COMMAND_SIZES[command]
        current = list(values[index:index + size])
        if command in {"M", "L", "C", "S", "m", "l", "c", "s"}:
            for pair_index in range(0, size, 2):
                current[pair_index] *= sx
                current[pair_index + 1] *= sy
        elif command in {"H", "h"}:
            current[0] *= sx
        elif command in {"V", "v"}:
            current[0] *= sy
        result.extend(current)
        index += size
    return tuple(result)


def _reference_primitives(spec: StructureSpec) -> tuple[tuple[Primitive, ...], tuple[Primitive, ...]]:
    root = ET.parse(REFERENCE_PATH).getroot()
    thickness = spec.board_thickness or REFERENCE_THICKNESS
    sx = (spec.dimensions.length + 3 * thickness) / (REFERENCE_LENGTH + 3 * REFERENCE_THICKNESS)
    sy = (spec.dimensions.width + 2 * thickness) / (REFERENCE_WIDTH + 2 * REFERENCE_THICKNESS)
    cut: list[Primitive] = []
    crease: list[Primitive] = []
    cut_index = 0
    crease_index = 0
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        class_name = element.attrib.get("class", "")
        if tag == "path" and class_name == "cls-3":
            commands, values = _path_tokens(element.attrib["d"])
            cut.append(Primitive("path", f"CUT_MAILER_OUTER_{cut_index + 1}", _scaled_path(commands, values, sx, sy), commands))
            cut_index += 1
        elif tag == "line" and class_name == "cls-2":
            values = tuple(float(element.attrib[key]) / PT_PER_MM for key in ("x1", "y1", "x2", "y2"))
            crease.append(Primitive("line", f"CREASE_MAILER_{crease_index + 1:02d}", (values[0] * sx, values[1] * sy, values[2] * sx, values[3] * sy)))
            crease_index += 1
    return tuple(cut), tuple(crease)


def _panel(spec: StructureSpec, panel_id: str, name: str, x: float, y: float, width: float, height: float, sx: float, sy: float) -> Panel:
    return Panel(panel_id, name, x * sx, y * sy, width * sx, height * sy)


def build_mailer(spec: StructureSpec) -> StructureGeometry:
    """Measured Box 2.0 crash-lock mailer, based on the supplied 300×200×60 mm SVG."""
    cut, crease = _reference_primitives(spec)
    thickness = spec.board_thickness or REFERENCE_THICKNESS
    sx = (spec.dimensions.length + 3 * thickness) / (REFERENCE_LENGTH + 3 * REFERENCE_THICKNESS)
    sy = (spec.dimensions.width + 2 * thickness) / (REFERENCE_WIDTH + 2 * REFERENCE_THICKNESS)
    panels = (
        _panel(spec, "panel-front", "正面 F", 364.24 / PT_PER_MM, 186.23 / PT_PER_MM, 852.94 / PT_PER_MM, 568.63 / PT_PER_MM, sx, sy),
        _panel(spec, "panel-front-left", "侧墙 FL", 190.48 / PT_PER_MM, 186.23 / PT_PER_MM, 173.76 / PT_PER_MM, 568.63 / PT_PER_MM, sx, sy),
        _panel(spec, "panel-front-right", "侧墙 FR", 1217.19 / PT_PER_MM, 186.23 / PT_PER_MM, 173.76 / PT_PER_MM, 568.63 / PT_PER_MM, sx, sy),
        _panel(spec, "panel-lid", "上盖 FT", 362.26 / PT_PER_MM, 16.72 / PT_PER_MM, 856.91 / PT_PER_MM, 169.51 / PT_PER_MM, sx, sy),
        _panel(spec, "panel-front-bottom", "前底 FB", 361.41 / PT_PER_MM, 754.86 / PT_PER_MM, 858.61 / PT_PER_MM, 170.93 / PT_PER_MM, sx, sy),
        _panel(spec, "panel-back", "背面 H", 361.41 / PT_PER_MM, 925.79 / PT_PER_MM, 858.61 / PT_PER_MM, 567.78 / PT_PER_MM, sx, sy),
        _panel(spec, "panel-back-left", "侧墙 HL", 190.48 / PT_PER_MM, 925.79 / PT_PER_MM, 170.93 / PT_PER_MM, 567.78 / PT_PER_MM, sx, sy),
        _panel(spec, "panel-back-right", "侧墙 HR", 1220.02 / PT_PER_MM, 925.79 / PT_PER_MM, 170.93 / PT_PER_MM, 567.78 / PT_PER_MM, sx, sy),
        _panel(spec, "panel-back-bottom", "后底 HB", 362.83 / PT_PER_MM, 1493.57 / PT_PER_MM, 855.78 / PT_PER_MM, 169.51 / PT_PER_MM, sx, sy),
    )
    bounds = (0.0, 0.0, 1581.43 / PT_PER_MM * sx, 1678.38 / PT_PER_MM * sy)
    return StructureGeometry(cut=cut, crease=crease, panels=panels, bounds=bounds)
