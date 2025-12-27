#!/usr/bin/env python3
"""
hc_curve.py

High-contrast "curves" style boost:
- Darker darks + brighter brights as strength increases
- Tries to preserve color hue by scaling RGB using Value (max channel)

Output: <prefix>-hc.<ext>
"""

import argparse
import os
import sys
import math

import numpy as np
from PIL import Image


def out_path(input_path: str) -> str:
    base = os.path.basename(input_path)
    root, ext = os.path.splitext(base)
    if not ext:
        ext = ".png"
    return os.path.join(os.path.dirname(input_path), f"{root}-hc{ext}")


def sigmoid_norm(x: np.ndarray, k: float) -> np.ndarray:
    """
    Normalized sigmoid S-curve centered at 0.5:
        s(x) = 1/(1+exp(-k*(x-0.5)))
    Then normalized so that f(0)=0 and f(1)=1 (approximately).
    Larger k => stronger contrast: darker shadows, brighter highlights.
    """
    if k <= 0:
        return x

    # Compute endpoints for normalization
    s0 = 1.0 / (1.0 + math.exp(-k * (0.0 - 0.5)))
    s1 = 1.0 / (1.0 + math.exp(-k * (1.0 - 0.5)))
    scale = 1.0 / (s1 - s0)

    s = 1.0 / (1.0 + np.exp(-k * (x - 0.5)))
    y = (s - s0) * scale
    return np.clip(y, 0.0, 1.0)


def process(img: Image.Image, strength: float, pivot: float) -> Image.Image:
    """
    strength: >=0, controls curve steepness
    pivot: in (0,1), where contrast pivots (default 0.5)
    """
    if strength <= 0:
        return img

    # Convert to RGBA for consistent handling
    rgba = img.convert("RGBA")
    arr = np.asarray(rgba).astype(np.float32) / 255.0  # HxWx4 in [0,1]
    rgb = arr[..., :3]
    a = arr[..., 3:4]

    # Value/brightness proxy
    v = np.max(rgb, axis=2, keepdims=True)  # HxWx1

    # Map strength to sigmoid steepness k.
    # 0 -> no change; 1 -> moderate; 2+ -> strong.
    # Feel free to tweak these numbers to taste.
    k = 6.0 * strength

    # Apply curve around pivot: shift so pivot behaves like 0.5, curve, shift back.
    # This lets you adjust where the "bend" happens.
    # We remap [0,1] with pivot p:
    #   x' = (x - p) + 0.5
    # then curve on x', then inverse shift.
    p = float(pivot)
    xprime = np.clip(v - p + 0.5, 0.0, 1.0)
    v2prime = sigmoid_norm(xprime, k)
    v2 = np.clip(v2prime + p - 0.5, 0.0, 1.0)

    # Scale RGB to match new value, preserving hue/chroma approximately.
    eps = 1e-6
    scale = v2 / (v + eps)
    rgb2 = np.clip(rgb * scale, 0.0, 1.0)

    out = np.concatenate([rgb2, a], axis=2)
    out8 = (out * 255.0 + 0.5).astype(np.uint8)
    return Image.fromarray(out8, mode="RGBA")


def main():
    ap = argparse.ArgumentParser(description="Increase contrast with an S-curve so shadows darken and highlights brighten.")
    ap.add_argument("image", help="Input image filename")
    ap.add_argument("--strength", type=float, default=1.0,
                    help="Contrast strength (>=0). 1.0 default; 2.0 strong; 0 disables.")
    ap.add_argument("--pivot", type=float, default=0.5,
                    help="Pivot point in [0,1]. Lower pivots emphasize darkening shadows more.")
    args = ap.parse_args()

    if args.strength < 0:
        print("Error: --strength must be >= 0", file=sys.stderr)
        sys.exit(2)
    if not (0.0 <= args.pivot <= 1.0):
        print("Error: --pivot must be in [0,1]", file=sys.stderr)
        sys.exit(2)

    img = Image.open(args.image)
    result = process(img, args.strength, args.pivot)

    out = out_path(args.image)
    result.save(out)
    print(out)


if __name__ == "__main__":
    main()

