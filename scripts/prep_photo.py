#!/usr/bin/env python3
"""Prep a photo for ASCII conversion: remove background, boost local
contrast (CLAHE), composite onto pure white so the background maps to
the blank end of the ASCII ramp.

Run once per photo:  python scripts/prep_photo.py source-photo.jpg
Writes: source-prepped.png (grayscale)
"""
import sys

import cv2
import numpy as np
from PIL import Image

OUT = "source-prepped.png"


def remove_background(img: Image.Image) -> Image.Image:
    try:
        from rembg import remove
        return remove(img.convert("RGB"))
    except Exception as exc:  # rembg not installed / model unavailable
        print(f"rembg unavailable ({exc}); falling back to GrabCut")
        bgr = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)
        mask = np.zeros(bgr.shape[:2], np.uint8)
        h, w = bgr.shape[:2]
        rect = (int(w * 0.06), int(h * 0.04), int(w * 0.88), int(h * 0.94))
        bgdModel = np.zeros((1, 65), np.float64)
        fgdModel = np.zeros((1, 65), np.float64)
        cv2.grabCut(bgr, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
        alpha = np.where((mask == 2) | (mask == 0), 0, 255).astype("uint8")
        rgba = np.dstack([cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), alpha])
        return Image.fromarray(rgba, "RGBA")


def clahe_contrast(gray: np.ndarray) -> np.ndarray:
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    return clahe.apply(gray)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/prep_photo.py <photo>")

    subject = remove_background(Image.open(sys.argv[1])).convert("RGBA")

    # local-contrast boost on the luminance of the subject only
    rgb = np.array(subject.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray = clahe_contrast(gray)

    # composite onto pure white: background -> blank end of the ramp
    alpha = np.array(subject.getchannel("A"), dtype=np.float32) / 255.0
    out = (gray.astype(np.float32) * alpha + 255.0 * (1.0 - alpha)).astype("uint8")

    Image.fromarray(out, "L").save(OUT)
    print(f"wrote {OUT} ({out.shape[1]}x{out.shape[0]})")


if __name__ == "__main__":
    main()
