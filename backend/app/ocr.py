"""Screenshot → text. Order: bundled demo fixture (hash match) → vision LLM → local Tesseract → clear failure."""
from __future__ import annotations

import io
from pathlib import Path

from .providers.base import LLMProvider, ProviderError
from .security.sanitize import sha256_hex

DEMO_DIR = Path(__file__).resolve().parent / "demo_assets"


class OCRUnavailable(Exception):
    pass


def demo_fixture_for(data: bytes) -> str | None:
    """Deterministic fixture so the demo never depends on external services.

    A bundled demo screenshot (demo_assets/<id>.png) has a sibling <id>.txt transcription.
    Only byte-identical bundled files match.
    """
    if not DEMO_DIR.exists():
        return None
    h = sha256_hex(data)
    for png in DEMO_DIR.glob("*.png"):
        try:
            if sha256_hex(png.read_bytes()) == h:
                txt = png.with_suffix(".txt")
                if txt.exists():
                    return txt.read_text(encoding="utf-8")
        except OSError:
            continue
    return None


def _tesseract(data: bytes) -> str:
    try:
        from PIL import Image  # type: ignore
        import pytesseract  # type: ignore
    except Exception as e:  # pragma: no cover
        raise OCRUnavailable("local OCR (Pillow + pytesseract) is not installed") from e
    import os
    import shutil

    cmd = os.getenv("TESSERACT_CMD", "").strip()
    if not cmd and not shutil.which("tesseract"):
        for p in (r"C:\Program Files\Tesseract-OCR\tesseract.exe", r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"):
            if os.path.exists(p):
                cmd = p
                break
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
        if img.width * img.height > 40_000_000:
            raise OCRUnavailable("image dimensions too large")
        # preprocess: small UI/email text OCRs far better when grayscale and upscaled
        from PIL import ImageOps  # type: ignore
        img = ImageOps.exif_transpose(img).convert("L")
        if img.width < 2400:
            scale = min(3.0, 2400 / img.width)
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
        img = ImageOps.autocontrast(img)
        return pytesseract.image_to_string(img, config="--oem 3 --psm 6")
    except OCRUnavailable:
        raise
    except Exception as e:
        raise OCRUnavailable("local OCR failed") from e


async def image_to_text(data: bytes, mime: str, provider: LLMProvider) -> tuple[str, str, str | None]:
    """Returns (text, method, note)."""
    fx = demo_fixture_for(data)
    if fx is not None:
        return fx, "demo_fixture", "Bundled demo screenshot: transcription is a pre-recorded fixture, not live OCR."
    if provider.supports_vision:
        try:
            txt = await provider.transcribe_image(data, mime)
            if txt.strip():
                return txt, f"vision:{provider.name}", None
        except ProviderError:
            pass
        except Exception:
            pass
    try:
        txt = _tesseract(data)
        if txt.strip():
            return txt, "tesseract", None
        raise OCRUnavailable("no text could be read from the image")
    except OCRUnavailable as e:
        raise OCRUnavailable(
            f"Could not read text from this screenshot ({e}). Configure a vision-capable model key or install Tesseract, "
            "or paste the message text instead."
        ) from e
