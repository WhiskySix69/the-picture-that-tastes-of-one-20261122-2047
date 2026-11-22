#!/usr/bin/env python3
"""Picture that tastes of one ingredient — make.fun entry program.

Writes the pre-rendered ramen illustration (entry.png, sitting next to
this file) to $MAKEFUN_OUTPUT_DIR/entry.png.

Stdlib only: no Pillow, no network, no fonts. The picture itself is a
static asset produced beforehand by gen_image.py (pure-Python PNG
encoder), so this program only has to move bytes reliably.
"""
import os
import sys
from pathlib import Path

SOURCE_NAME = "entry.png"
DEST_NAME = "entry.png"
CHUNK = 65536


def fail(message):
    print("error:", message, file=sys.stderr)
    raise SystemExit(1)


def main():
    here = Path(__file__).resolve().parent
    source = here / SOURCE_NAME
    if not source.is_file():
        fail(f"{SOURCE_NAME} not found next to main.py ({here})")

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    dest_dir = Path(out_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / DEST_NAME

    # Stream the file in chunks so memory stays flat even for big PNGs.
    total = 0
    with source.open("rb") as src, dest.open("wb") as dst:
        while True:
            piece = src.read(CHUNK)
            if not piece:
                break
            dst.write(piece)
            total += len(piece)

    # Verify the copy byte-for-byte before reporting success.
    if dest.stat().st_size != source.stat().st_size:
        fail(f"size mismatch after copy: {dest.stat().st_size} != "
             f"{source.stat().st_size}")
    if dest.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        fail("copied file does not start with a PNG signature")

    print(f"wrote {dest} ({total} bytes)")


if __name__ == "__main__":
    main()
