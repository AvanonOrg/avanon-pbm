"""Noto Sans font loader for ReportLab with fallback chain."""
import logging
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

FONT_DIR = Path(__file__).parent / "fonts"

_NOTO_URLS = {
    "NotoSans-Regular": [
        "https://github.com/notofonts/latin-greek-cyrillic/raw/main/fonts/NotoSans/hinted/ttf/NotoSans-Regular.ttf",
        "https://github.com/notofonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf",
    ],
    "NotoSans-Bold": [
        "https://github.com/notofonts/latin-greek-cyrillic/raw/main/fonts/NotoSans/hinted/ttf/NotoSans-Bold.ttf",
        "https://github.com/notofonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Bold.ttf",
    ],
    "NotoSans-Italic": [
        "https://github.com/notofonts/latin-greek-cyrillic/raw/main/fonts/NotoSans/hinted/ttf/NotoSans-Italic.ttf",
        "https://github.com/notofonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Italic.ttf",
    ],
    "NotoSans-BoldItalic": [
        "https://github.com/notofonts/latin-greek-cyrillic/raw/main/fonts/NotoSans/hinted/ttf/NotoSans-BoldItalic.ttf",
        "https://github.com/notofonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-BoldItalic.ttf",
    ],
}

_FONTS_CACHE: dict | None = None


def _download(url: str, dest: Path) -> bool:
    import urllib.request
    try:
        urllib.request.urlretrieve(url, str(dest))
        return dest.exists() and dest.stat().st_size > 10_000
    except Exception:
        return False


def _register_noto() -> tuple | None:
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    registered = {}
    for name, urls in _NOTO_URLS.items():
        dest = FONT_DIR / f"{name}.ttf"
        if not (dest.exists() and dest.stat().st_size > 10_000):
            for url in urls:
                if _download(url, dest):
                    break
        if dest.exists() and dest.stat().st_size > 10_000:
            try:
                pdfmetrics.registerFont(TTFont(name, str(dest)))
                registered[name] = True
            except Exception as e:
                logger.warning("Could not register %s: %s", name, e)
                registered[name] = False
        else:
            registered[name] = False

    if all(registered.values()):
        registerFontFamily(
            "NotoSans",
            normal="NotoSans-Regular",
            bold="NotoSans-Bold",
            italic="NotoSans-Italic",
            boldItalic="NotoSans-BoldItalic",
        )
        logger.info("Loaded Noto Sans fonts")
        return "NotoSans-Regular", "NotoSans-Bold", "NotoSans-Italic", "NotoSans-BoldItalic"
    return None


def _register_dejavu() -> tuple | None:
    try:
        import matplotlib
        dejavu_dir = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
        variants = {
            "DejaVuSans":             dejavu_dir / "DejaVuSans.ttf",
            "DejaVuSans-Bold":        dejavu_dir / "DejaVuSans-Bold.ttf",
            "DejaVuSans-Oblique":     dejavu_dir / "DejaVuSans-Oblique.ttf",
            "DejaVuSans-BoldOblique": dejavu_dir / "DejaVuSans-BoldOblique.ttf",
        }
        for name, path in variants.items():
            if path.exists():
                pdfmetrics.registerFont(TTFont(name, str(path)))
        if (dejavu_dir / "DejaVuSans.ttf").exists():
            registerFontFamily(
                "DejaVuSans",
                normal="DejaVuSans",
                bold="DejaVuSans-Bold",
                italic="DejaVuSans-Oblique",
                boldItalic="DejaVuSans-BoldOblique",
            )
            logger.info("Loaded DejaVu Sans fonts (fallback)")
            return "DejaVuSans", "DejaVuSans-Bold", "DejaVuSans-Oblique", "DejaVuSans-BoldOblique"
    except Exception as e:
        logger.warning("DejaVu fallback failed: %s", e)
    return None


def load_report_fonts() -> dict:
    """Return font name dict, downloading Noto Sans if needed."""
    global _FONTS_CACHE
    if _FONTS_CACHE is not None:
        return _FONTS_CACHE

    result = _register_noto()
    if result is None:
        result = _register_dejavu()
    if result is None:
        result = ("Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique")
        logger.info("Using built-in Helvetica fonts")

    reg, bold, italic, bolditalic = result
    _FONTS_CACHE = {"regular": reg, "bold": bold, "italic": italic, "bolditalic": bolditalic}
    return _FONTS_CACHE
