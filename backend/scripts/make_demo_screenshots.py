"""Generate synthetic demo screenshots (fictional content) + sibling .txt transcription fixtures.

Run:  python scripts/make_demo_screenshots.py     (requires Pillow)
Output: app/demo_assets/<scenario-id>.png and .txt
"""
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.scenarios import SCENARIOS  # noqa: E402

OUT = ROOT / "app" / "demo_assets"
OUT.mkdir(parents=True, exist_ok=True)
FONT_PATHS = [
    "C:/Windows/Fonts/segoeui.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def font(size):
    for p in FONT_PATHS:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render(sc):
    W, pad = 720, 36
    f, fs, fb = font(26), font(20), font(24)
    body = sc["text"]
    lines = []
    for para in body.split("\n"):
        lines += textwrap.wrap(para, 42) or [""]
    h = 150 + len(lines) * 36 + 120
    img = Image.new("RGB", (W, h), "#f2f2f7")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 96], fill="#ffffff")
    d.text((W // 2, 34), sc["channel"], fill="#111111", font=fb, anchor="mm")
    d.text((W // 2, 66), "Today 9:41 AM", fill="#8e8e93", font=fs, anchor="mm")
    bh = len(lines) * 36 + 36
    d.rounded_rectangle([pad, 130, W - pad, 130 + bh], radius=28, fill="#e5e5ea")
    y = 148
    for ln in lines:
        d.text((pad + 24, y), ln, fill="#111111", font=f)
        y += 36
    return img


for sc in SCENARIOS:
    render(sc).save(OUT / f"{sc['id']}.png", optimize=False)
    (OUT / f"{sc['id']}.txt").write_text(sc["text"], encoding="utf-8")
    print("wrote", sc["id"])
