"""Entrypoint for the news-image-20261125 entry.

Running `python3 main.py` redraws the front page from news.json. The PNG is
rendered into a writable location only — never into this repo folder, which
the grading sandbox mounts read-only at /bot. When the harness sets
MAKEFUN_OUTPUT_DIR the image lands there as entry.png, which is what the
gate reads; without that variable it goes to a temporary scratch folder.
The render is deterministic: same input, same bytes, every run.
"""

import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)

import build_image


def render_target():
    """Pick a writable destination for the rendered PNG.

    Returns (render_path, output_dir) where output_dir is the harness
    folder when set, else None. The repo folder is never a destination.
    """
    harness_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if harness_dir:
        os.makedirs(harness_dir, exist_ok=True)
        return os.path.join(harness_dir, "entry.png"), harness_dir
    scratch = tempfile.mkdtemp(prefix="plain-plinth-")
    return os.path.join(scratch, "image.png"), None


def main():
    news_path = os.path.join(HERE, "news.json")
    rendered, harness_dir = render_target()
    build_image.render(news_path, rendered)

    if harness_dir:
        gate_path = os.path.join(harness_dir, "entry.png")
        if rendered != gate_path:
            shutil.copyfile(rendered, gate_path)


if __name__ == "__main__":
    main()
