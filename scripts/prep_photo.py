#!/usr/bin/env python3
"""
prep_photo.py — turn a normal photo into a high-contrast, background-free
grayscale image that converts cleanly into ASCII art.

Usage:
    python scripts/prep_photo.py source-photo.jpg
Writes:
    source-prepped.png
"""
import sys
import io
import numpy as np
import cv2
from PIL import Image
from rembg import remove


def prep(in_path: str, out_path: str = "source-prepped.png") -> None:
    with open(in_path, "rb") as f:
        raw = f.read()

    # 1. Remove the background so the subject is isolated on transparency.
    cutout_bytes = remove(raw)
    cutout = Image.open(io.BytesIO(cutout_bytes)).convert("RGBA")

    # 2. Composite onto pure white — this maps background to the blank
    #    end of the ASCII ramp (white -> space) instead of a dark blob.
    white_bg = Image.new("RGBA", cutout.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, cutout).convert("RGB")

    # 3. Boost local contrast with CLAHE so a flatly-lit face gets real
    #    highlights and shadows instead of converting to a dull gray mass.
    gray = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    boosted = clahe.apply(gray)

    Image.fromarray(boosted).save(out_path)
    print(f"wrote {out_path} ({boosted.shape[1]}x{boosted.shape[0]})")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "source-photo.jpg"
    prep(src)
