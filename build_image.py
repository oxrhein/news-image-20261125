"""Draw the one-page newspaper for Wednesday 25 November 2026.

Layout, from top to bottom: a centred serif masthead with the date and the
story/region count, a dark hero band carrying the day's biggest story, then a
dense three-column grid of the remaining stories (region tag, headline, short
summary), and a thin footer line. Everything is drawn with Pillow only, from
the stories in news.json, so the output is fully deterministic.

This file is the build-time renderer only. It is never imported by main.py:
the graded entrypoint copies the shipped image.png with the standard library
alone, so the grading sandbox needs no Pillow at all.
"""

import json
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = "/usr/share/fonts/truetype/dejavu"

PAGE_W = 1024
PAGE_H = 1024
MARGIN = 24
PAPER = (253, 253, 248)
INK = (18, 18, 18)
RULE = (120, 120, 120)
HERO_BG = (16, 16, 16)
HERO_INK = (250, 250, 245)
MUTED = (90, 90, 90)

# One ink colour per region tag so the eye can scan the grid by beat.
TAG_COLOURS = {
    "EUROPE": (26, 77, 143),
    "MIDDLE EAST": (143, 26, 26),
    "ASIA-PACIFIC": (15, 107, 74),
    "AMERICAS": (107, 63, 160),
    "AFRICA": (176, 106, 0),
    "MARKETS": (51, 51, 51),
    "TECH": (14, 116, 144),
    "SCIENCE": (77, 124, 15),
    "SPORT": (190, 24, 93),
}


def _font(name, size):
    """Load a DejaVu face; fall back to Pillow's built-in bitmap font."""
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, name), size)
    except OSError:
        return ImageFont.load_default()


SERIF_BOLD = lambda s: _font("DejaVuSerif-Bold.ttf", s)
SANS_BOLD = lambda s: _font("DejaVuSans-Bold.ttf", s)
SANS = lambda s: _font("DejaVuSans.ttf", s)


def load_stories(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def wrap_text(draw, text, font, max_width, max_lines):
    """Greedy word wrap, capped at max_lines; an overlong tail gets '...'."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
        if len(lines) == max_lines:
            break
    if len(lines) < max_lines and current:
        lines.append(current)
    if len(lines) == max_lines and current and lines[-1] != current:
        # The tail did not fit: mark the last visible line as cut off.
        last = lines[-1]
        while last and draw.textlength(last + "...", font=font) > max_width:
            last = last.rsplit(" ", 1)[0] if " " in last else ""
        lines[-1] = (last + "...") if last else "..."
    return lines


def draw_masthead(draw, data):
    """Title, date and count banner at the top of the page."""
    title_font = SERIF_BOLD(42)
    date_font = SANS_BOLD(16)
    count_font = SANS_BOLD(13)

    title = data["title"]
    tw = draw.textlength(title, font=title_font)
    draw.text(((PAGE_W - tw) / 2, 18), title, font=title_font, fill=INK)

    date_line = data["day"].upper()
    dw = draw.textlength(date_line, font=date_font)
    draw.text(((PAGE_W - dw) / 2, 70), date_line, font=date_font, fill=INK)

    stories = data["stories"]
    regions = sorted({s["region"] for s in stories})
    count_line = "%d STORIES  •  %d REGIONS" % (len(stories), len(regions))
    cw = draw.textlength(count_line, font=count_font)
    draw.text(((PAGE_W - cw) / 2, 92), count_line, font=count_font, fill=MUTED)

    draw.line([(MARGIN, 112), (PAGE_W - MARGIN, 112)], fill=INK, width=3)
    draw.line([(MARGIN, 116), (PAGE_W - MARGIN, 116)], fill=INK, width=1)


def draw_hero(draw, hero):
    """Dark band with the biggest story of the day."""
    top = 124
    height = 74
    draw.rectangle([MARGIN, top, PAGE_W - MARGIN, top + height], fill=HERO_BG)

    tag_font = SANS_BOLD(10)
    head_font = SANS_BOLD(23)
    body_font = SANS(13)
    inner = PAGE_W - 2 * MARGIN - 28

    tag = "TOP STORY  —  " + hero["region"]
    draw.text((MARGIN + 14, top + 6), tag, font=tag_font, fill=(255, 190, 60))

    head_lines = wrap_text(draw, hero["headline"], head_font, inner, 1)
    draw.text((MARGIN + 14, top + 20), head_lines[0], font=head_font, fill=HERO_INK)

    body_lines = wrap_text(draw, hero["summary"], body_font, inner, 1)
    if body_lines:
        draw.text((MARGIN + 14, top + 49), body_lines[0], font=body_font, fill=(210, 210, 205))

    return top + height


def draw_cell(draw, story, x, y, width, height):
    """One grid cell: coloured region tag, bold headline, short summary."""
    tag_font = SANS_BOLD(9)
    head_font = SANS_BOLD(12)
    body_font = SANS(10)

    colour = TAG_COLOURS.get(story["region"], INK)
    draw.text((x, y), story["region"], font=tag_font, fill=colour)

    head_lines = wrap_text(draw, story["headline"], head_font, width, 2)
    hy = y + 11
    for line in head_lines:
        draw.text((x, hy), line, font=head_font, fill=INK)
        hy += 13

    body_lines = wrap_text(draw, story["summary"], body_font, width, 2)
    by = hy
    for line in body_lines:
        draw.text((x, by), line, font=body_font, fill=(60, 60, 60))
        by += 11


def draw_grid(draw, stories, top):
    """Three columns, twelve rows, hairline rules between rows."""
    cols = 3
    rows = 12
    gutter = 14
    grid_w = PAGE_W - 2 * MARGIN
    cell_w = (grid_w - (cols - 1) * gutter) // cols
    grid_bottom = 996
    row_h = (grid_bottom - top) // rows

    for idx, story in enumerate(stories):
        col = idx % cols
        row = idx // cols
        x = MARGIN + col * (cell_w + gutter)
        y = top + row * row_h + 3
        draw_cell(draw, story, x, y, cell_w, row_h - 8)
        if row < rows - 1:
            ry = top + (row + 1) * row_h
            draw.line([(MARGIN, ry), (PAGE_W - MARGIN, ry)], fill=(215, 215, 205), width=1)
        if col < cols - 1:
            vx = x + cell_w + gutter // 2
            draw.line([(vx, top + 2), (vx, grid_bottom)], fill=(225, 225, 215), width=1)


def draw_footer(draw, data):
    foot_font = SANS(10)
    line = "All stories first reported 24–25 November 2026  •  Compiled %s" % data["day"]
    fw = draw.textlength(line, font=foot_font)
    draw.text(((PAGE_W - fw) / 2, 1002), line, font=foot_font, fill=MUTED)


def render(news_path, out_path):
    data = load_stories(news_path)
    stories = data["stories"]
    hero = next(s for s in stories if s.get("hero"))
    rest = [s for s in stories if not s.get("hero")]

    page = Image.new("RGB", (PAGE_W, PAGE_H), PAPER)
    draw = ImageDraw.Draw(page)

    draw_masthead(draw, data)
    grid_top = draw_hero(draw, hero) + 8
    draw_grid(draw, rest, grid_top)
    draw_footer(draw, data)

    page.save(out_path, format="PNG")


if __name__ == "__main__":
    render(os.path.join(HERE, "news.json"), os.path.join(HERE, "image.png"))
