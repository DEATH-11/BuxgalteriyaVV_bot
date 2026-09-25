from datetime import datetime
from pathlib import Path

from docxtpl import DocxTemplate

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
OUTPUT_DIR = Path("/tmp/hujjat_bot")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _safe(name: str) -> str:
    return "".join(c for c in str(name) if c.isalnum() or c in "-_") or "x"


def render_shartnoma(data: dict) -> Path:
    template_path = TEMPLATES_DIR / "shartnoma.docx"
    doc = DocxTemplate(str(template_path))
    doc.render(data)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"shartnoma_{_safe(data.get('shartnoma_raqami'))}_{ts}.docx"
    output_path = OUTPUT_DIR / filename
    doc.save(str(output_path))
    return output_path


def render_spetsifikatsiya(data: dict) -> Path:
    template_path = TEMPLATES_DIR / "spetsifikatsiya.docx"
    doc = DocxTemplate(str(template_path))
    doc.render(data)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"spetsifikatsiya_{_safe(data.get('spek_raqami'))}_{ts}.docx"
    output_path = OUTPUT_DIR / filename
    doc.save(str(output_path))
    return output_path
