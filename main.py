"""Entrypoint for the news-image-20261125 entry.

Running `python3 main.py` redraws the front page from news.json and writes
image.png next to this file. When the grading harness sets MAKEFUN_OUTPUT_DIR,
the same image is also written there as entry.png, which is what the gate
reads. The render is deterministic: same input, same bytes, every run.
"""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)

import build_image


def main():
    news_path = os.path.join(HERE, "news.json")
    image_path = os.path.join(HERE, "image.png")
    build_image.render(news_path, image_path)

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        shutil.copyfile(image_path, os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
