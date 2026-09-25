from datetime import datetime
from pathlib import Path

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docxtpl import DocxTemplate

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
OUTPUT_DIR = Path("/tmp/hujjat_bot")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _safe(name: str) -> str:
    return "".join(c for c in str(name) if c.isalnum() or c in "-_") or "x"


def _fmt(num) -> str:
    """Raqamni chiroyli formatda chiqaradi: 5124000 -> 5 124 000"""
    try:
        return f"{int(round(float(num))):,}".replace(",", " ")
    except Exception:
        return str(num)


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

    items = data.get("items", [])
    jami = data.get("jami_summa", 0)

    # Shablonga oddiy matn sifatida yozamiz, keyin jadvalni qo‘shamiz
    context = {
        "spek_raqami": data.get("spek_raqami", ""),
        "table": "",  # bo‘sh — jadvalni keyin qo‘shamiz
        "jami_summa": _fmt(jami),
    }
    doc.render(context)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"spetsifikatsiya_{_safe(data.get('spek_raqami'))}_{ts}.docx"
    output_path = OUTPUT_DIR / filename
    doc.save(str(output_path))

    # Endi jadvalni qo‘shamiz
    _insert_table(str(output_path), items, jami)

    return output_path


def _insert_table(docx_path: str, items: list, jami) -> None:
    """DOCX faylga jadval qo‘shadi."""
    doc = Document(docx_path)

    # "{{ table }}" qatorini topamiz
    target_paragraph = None
    for para in doc.paragraphs:
        if "{{ table }}" in para.text or "table" in para.text.lower():
            target_paragraph = para
            break

    if target_paragraph is None:
        # Topilmasa — hujjat oxiriga qo‘shamiz
        target_paragraph = doc.add_paragraph()

    # Jadval yaratamiz: 1 sarlavha + N ma'lumot + 1 ИТОГО
    rows_count = 1 + len(items) + 1
    table = doc.add_table(rows=rows_count, cols=5)
    table.style = "Table Grid"

    # Sarlavha
    headers = [
        "Наименование товаров",
        "Ед. изм.",
        "Количество",
        "Цена с НДС",
        "Стоимость поставки с учетом НДС",
    ]
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for para in cell.paragraphs:
            for run in para.runs:
                run.bold = True
                run.font.size = Pt(10)

    # Ma’lumot qatorlari
    for idx, item in enumerate(items, start=1):
        row = table.rows[idx]
        row.cells[0].text = str(item.get("dori_nomi", ""))
        row.cells[1].text = "упак"
        row.cells[2].text = str(item.get("miqdori", ""))
        row.cells[3].text = _fmt(item.get("narxi", 0))
        row.cells[4].text = _fmt(item.get("umumiy_narxi", 0))

        for cell in row.cells:
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.size = Pt(10)

    # ИТОГО
    total_row = table.rows[-1]
    total_row.cells[0].text = "ИТОГО"
    total_row.cells[4].text = _fmt(jami)
    for cell in total_row.cells:
        for para in cell.paragraphs:
            for run in para.runs:
                run.bold = True
                run.font.size = Pt(10)

    # "{{ table }}" matnini o‘chirib tashlaymiz
    target_paragraph.text = ""

    doc.save(docx_path)
