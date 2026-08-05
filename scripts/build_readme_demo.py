#!/usr/bin/env python3
"""Build the short terminal-style showcase GIF used by the public README."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 1280, 720
BACKGROUND = (12, 18, 28)
PANEL = (22, 31, 45)
TEXT = (232, 239, 247)
MUTED = (142, 157, 176)
GREEN = (90, 214, 145)
CYAN = (89, 196, 235)
AMBER = (245, 191, 82)
RED = (247, 117, 117)


def _font(size: int, *, mono: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        ("/System/Library/Fonts/Menlo.ttc" if mono else "/System/Library/Fonts/SFNS.ttf"),
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for path in candidates:
        if Path(path).is_file():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


TITLE_FONT = _font(34)
SUBTITLE_FONT = _font(21)
MONO = _font(22, mono=True)
SMALL_MONO = _font(17, mono=True)


SCENES = [
    (
        "One conversation. Three packaging stages.",
        "Packaging Design Assistant Harness 2.0",
        [
            ("CMD", CYAN), ("$ packaging-assistant run --job lock-bottom.json", TEXT),
            ("ROUTE", MUTED), ("structure_template", GREEN),
            ("NEXT", MUTED), ("content_layout -> mockup_render", CYAN),
        ],
        CYAN,
    ),
    (
        "Start with a plain-language request.",
        "The agent keeps the dimensions and asks for a box model when needed.",
        [
            ("USER", AMBER), ("  Make a lock-bottom box, 80 x 40 x 120 mm.", TEXT),
            ("INPUT", MUTED), ("  model=lock-bottom  dimensions=80x40x120 mm", TEXT),
            ("GUARD", MUTED), ("  unknown model -> choice_prompt (no guessing)", GREEN),
        ],
        AMBER,
    ),
    (
        "Module A: deterministic structure SVG.",
        "No Illustrator script installation. No browser bridge.",
        [
            ("MODEL", MUTED), ("  carton.box_v2.lock_bottom", CYAN),
            ("OUTPUT", MUTED), ("  template.svg", GREEN),
            ("LAYERS", MUTED), ("  CUT / CREASE / BLEED / SAFE / ARTWORK", TEXT),
            ("STATUS", MUTED), ("  DESIGN_TEMPLATE  |  Illustrator-compatible", GREEN),
        ],
        GREEN,
    ),
    (
        "Module B: content layout without touching the knife lines.",
        "Facts, sources, placeholders, and review items stay auditable.",
        [
            ("INPUT", MUTED), ("  template.svg + product-brief.json", TEXT),
            ("WRITE", MUTED), ("  LAYER_ARTWORK only", GREEN),
            ("OUTPUT", MUTED), ("  content-layout.svg  content-spec.json", CYAN),
            ("GUARD", MUTED), ("  missing facts -> explicit placeholder", AMBER),
        ],
        CYAN,
    ),
    (
        "Module C: keep the original CMF workflow.",
        "Completed artwork stays protected; finishes are mapped to regions.",
        [
            ("PROTECT", MUTED), ("  structure / logo / text / layout / color", GREEN),
            ("PLAN", MUTED), ("  material + finish + target region", CYAN),
            ("PROVIDER", MUTED), ("  host | openai-compatible | custom REST | mock", TEXT),
            ("BOUNDARY", MUTED), ("  blank dieline is not completed artwork", AMBER),
        ],
        GREEN,
    ),
    (
        "Provider contract first. Real generation is opt-in.",
        "The demo uses Mock Provider to prove orchestration, not to fake a CMF render.",
        [
            ("MOCK", MUTED), ("  generation-record.json", CYAN),
            ("QA", MUTED), ("  visual-qa.json", GREEN),
            ("RESULT", MUTED), ("  manual_review", AMBER),
            ("NOTE", MUTED), ("  real Provider requires explicit approval + config", TEXT),
        ],
        AMBER,
    ),
    (
        "One job workspace. Readable outputs.",
        "Every stage leaves an artifact that a designer or reviewer can inspect.",
        [
            ("01", GREEN), (" template.svg", TEXT),
            ("02", CYAN), (" content-layout.svg + source-report.md", TEXT),
            ("03", AMBER), (" cmf-plan.json + visual-qa.json", TEXT),
            ("DONE", GREEN), ("  53 tests | 12 evals | audit trail", TEXT),
        ],
        CYAN,
    ),
    (
        "Packaging structure + content + CMF in one harness.",
        "Try it from Codex, Claude Code, or the local CLI.",
        [
            ("NEXT", GREEN), ("  ./install.sh", TEXT),
            ("THEN", CYAN), ("  say: Make a carry-handle box, 100 x 60 x 160 mm.", TEXT),
            ("READ", AMBER), ("  README.md  ->  Quick start", TEXT),
        ],
        GREEN,
    ),
]


def _draw_scene(index: int, tick: int) -> Image.Image:
    title, subtitle, lines, accent = SCENES[index]
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)

    # A quiet top band makes the GIF read like a product demo rather than raw logs.
    draw.rectangle((0, 0, WIDTH, 11), fill=accent)
    draw.text((74, 54), "PACKAGING DESIGN ASSISTANT / HARNESS 2.0", font=SMALL_MONO, fill=MUTED)
    draw.text((74, 102), title, font=TITLE_FONT, fill=TEXT)
    draw.text((74, 150), subtitle, font=SUBTITLE_FONT, fill=MUTED)

    left, top, right, bottom = 74, 222, WIDTH - 74, HEIGHT - 79
    draw.rounded_rectangle((left, top, right, bottom), radius=18, fill=PANEL, outline=(47, 64, 85), width=2)
    draw.ellipse((left + 24, top + 23, left + 36, top + 35), fill=RED)
    draw.ellipse((left + 46, top + 23, left + 58, top + 35), fill=AMBER)
    draw.ellipse((left + 68, top + 23, left + 80, top + 35), fill=GREEN)
    draw.text((left + 112, top + 17), "harness-demo", font=SMALL_MONO, fill=MUTED)

    y = top + 93
    for index in range(0, len(lines), 2):
        label, label_color = lines[index]
        value, value_color = lines[index + 1]
        draw.text((left + 36, y), f"{label:<10}", font=MONO, fill=label_color)
        draw.text((left + 210, y), value, font=MONO, fill=value_color)
        y += 48

    if tick % 2 == 0:
        draw.rectangle((left + 36, bottom - 40, left + 50, bottom - 16), fill=accent)
    draw.text((left, HEIGHT - 50), "deterministic demo  •  Mock Provider  •  manual review boundary shown", font=SMALL_MONO, fill=MUTED)
    return image


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/assets/packaging-assistant-demo.gif")
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    frames = []
    durations = []
    for index in range(len(SCENES)):
        for tick in range(4):
            frames.append(_draw_scene(index, tick))
            durations.append(1000)

    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    print(f"Wrote {output} ({len(frames)} frames, {sum(durations) / 1000:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
