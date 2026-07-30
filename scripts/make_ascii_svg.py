#!/usr/bin/env python3
"""Convert source-prepped.png into a self-typing monochrome ASCII SVG.

Each pixel of a ~100x53 character grid picks a glyph from a density
ramp. Every row is wrapped in a horizontal clip that wipes left-to-right
(with a block cursor riding the wipe edge), staggered top to bottom.
The portrait prints once and freezes - no looping. SMIL only, so GitHub
plays it inside an <img>.

Run:  python scripts/make_ascii_svg.py   # writes adi-ascii.svg
"""
from PIL import Image

SRC = "source-prepped.png"
OUT = "adi-ascii.svg"

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense)
#        ^ leading space clears the background to nothing

COLS, ROWS = 100, 53
CHAR_W, LINE_H = 6.0, 11.0
FONT_SIZE = 10
PAD_X, PAD_Y = 14, 12
BAR_H = 28

INK = "#c9d1d9"        # one light-gray fill: monochrome, not confetti
BG = "#0d1117"
BORDER = "#30363d"
FONT = "ui-monospace,SFMono-Regular,'Cascadia Code',Menlo,Consolas,monospace"

T0 = 0.2               # s before the first row starts printing
STAGGER = 0.05         # s between row starts
WIPE = 0.9             # s for one row's left-to-right wipe


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> None:
    img = Image.open(SRC).convert("L")

    # crop to the subject so the portrait fills the frame
    bbox = img.point(lambda v: 255 if v < 250 else 0).getbbox()
    if bbox:
        m = int(min(img.size) * 0.03)
        img = img.crop((max(bbox[0] - m, 0), max(bbox[1] - m, 0),
                        min(bbox[2] + m, img.width), min(bbox[3] + m, img.height)))

    # push midtones darker so faces print with real density
    img = img.point(lambda v: int(255 * (v / 255) ** 1.35))

    img = img.resize((COLS, ROWS), Image.LANCZOS)
    px = img.load()

    rows = []
    for r in range(ROWS):
        line = "".join(
            RAMP[min(int((255 - px[c, r]) / 256 * len(RAMP)), len(RAMP) - 1)]
            for c in range(COLS)
        ).rstrip()
        rows.append(line)

    grid_w = COLS * CHAR_W
    width = int(2 * PAD_X + grid_w)
    height = int(BAR_H + PAD_Y + ROWS * LINE_H + PAD_Y)

    out = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{FONT}" font-size="{FONT_SIZE}">'
    )
    # terminal window chrome
    out.append(f'<rect width="{width}" height="{height}" rx="8" fill="{BG}" stroke="{BORDER}"/>')
    out.append(f'<line x1="1" y1="{BAR_H}" x2="{width - 1}" y2="{BAR_H}" stroke="{BORDER}"/>')
    for i, dot in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        out.append(f'<circle cx="{16 + i * 18}" cy="{BAR_H // 2}" r="5" fill="{dot}"/>')
    out.append(
        f'<text x="{width // 2}" y="{BAR_H // 2 + 4}" text-anchor="middle" '
        f'fill="#8b949e">adi@github: ~/adi.jpg</text>'
    )

    out.append("<defs>")
    for r, line in enumerate(rows):
        if not line:
            continue
        begin = T0 + r * STAGGER
        out.append(
            f'<clipPath id="c{r}"><rect x="{PAD_X}" y="0" width="0" height="{height}">'
            f'<animate attributeName="width" from="0" to="{grid_w:g}" '
            f'begin="{begin:.2f}s" dur="{WIPE}s" fill="freeze"/></rect></clipPath>'
        )
    out.append("</defs>")

    for r, line in enumerate(rows):
        if not line:
            continue
        begin = T0 + r * STAGGER
        end = begin + WIPE
        y = BAR_H + PAD_Y + (r + 1) * LINE_H - 3
        out.append(
            f'<g clip-path="url(#c{r})"><text x="{PAD_X}" y="{y:g}" xml:space="preserve" '
            f'fill="{INK}" textLength="{len(line) * CHAR_W:g}" '
            f'lengthAdjust="spacing">{esc(line)}</text></g>'
        )
        # block cursor riding the wipe edge, gone when the row is done
        out.append(
            f'<rect x="{PAD_X}" y="{y - FONT_SIZE + 1:g}" width="{CHAR_W:g}" '
            f'height="{FONT_SIZE + 1}" fill="{INK}" opacity="0">'
            f'<set attributeName="opacity" to="0.85" begin="{begin:.2f}s"/>'
            f'<animate attributeName="x" from="{PAD_X}" to="{PAD_X + grid_w:g}" '
            f'begin="{begin:.2f}s" dur="{WIPE}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{end:.2f}s"/></rect>'
        )

    out.append("</svg>")
    svg = "\n".join(out)
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT} ({width}x{height}, {len(svg) // 1024} KiB)")


if __name__ == "__main__":
    main()
