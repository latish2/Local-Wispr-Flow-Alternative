"""Render the Jarvis logo (assets/jarvis.png + jarvis.ico) with Pillow. Run: python tools/make_icon.py"""
from pathlib import Path

from PIL import Image, ImageDraw

S = 1024
ASSETS = Path(__file__).resolve().parents[1] / "assets"
TOP_LEFT, BOTTOM_RIGHT = (124, 92, 255), (34, 211, 238)  # violet -> cyan
BARS = [0.30, 0.58, 0.92, 0.70, 0.42]


def gradient(size: int) -> Image.Image:
    img = Image.new("RGB", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * (size - 1))
            px[x, y] = tuple(round(a + (b - a) * t) for a, b in zip(TOP_LEFT, BOTTOM_RIGHT))
    return img


def render() -> Image.Image:
    small = 256  # gradient is smooth; render small and upscale for speed
    bg = gradient(small).resize((S, S), Image.BICUBIC)
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((40, 40, S - 40, S - 40), radius=230, fill=255)
    icon = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    icon.paste(bg, (0, 0), mask)

    d = ImageDraw.Draw(icon)
    bar_w, gap = 92, 54
    total = len(BARS) * bar_w + (len(BARS) - 1) * gap
    x = (S - total) // 2
    for h in BARS:
        hh = int(h * 560)
        top = (S - hh) // 2
        d.rounded_rectangle((x, top, x + bar_w, top + hh), radius=bar_w // 2, fill=(255, 255, 255, 255))
        x += bar_w + gap
    return icon


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    icon = render()
    icon.resize((256, 256), Image.LANCZOS).save(ASSETS / "jarvis.png")
    icon.resize((512, 512), Image.LANCZOS).save(ASSETS / "jarvis-512.png")
    icon.save(ASSETS / "jarvis.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("wrote", ASSETS)


if __name__ == "__main__":
    main()
