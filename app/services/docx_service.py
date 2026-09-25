from datetime import datetime
from pathlib import Path

from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docxtpl import DocxTemplate

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
OUTPUT_DIR = Path("/tmp/hujjat_bot")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _safe(name: str) -> str:
    return "".join(c for c in str(name) if c.isalnum() or c in "-_") or "x"


def _fmt_int(num) -> str:
    """10.0 -> '10', 10.5 -> '10.5', 5124000 -> '5 124 000'"""
    try:
        f = float(num)
        if f.is_integer():
            n = int(f)
        else:
            n = f
        if isinstance(n, int):
            return f"{n:,}".replace(",", " ")
        return str(n)
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

    context = {
        "spek_raqami": data.get("spek_raqami", ""),
        "table": "",
        "jami_summa": _fmt_int(jami),
    }
    doc.render(context)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"spetsifikatsiya_{_safe(data.get('spek_raqami'))}_{ts}.docx"
    output_path = OUTPUT_DIR / filename
    doc.save(str(output_path))

    _insert_table_in_place(str(output_path), items, jami)

    return output_path


def _insert_table_in_place(docx_path: str, items: list, jami) -> None:
    doc = Document(docx_path)

    # "{{ table }}" paragrafini topamiz
    target_paragraph = None
    for para in doc.paragraphs:
        if "table" in para.text.lower() or "{{" in para.text and "table" in para.text:
            target_paragraph = para
            break

    if target_paragraph is None:
        # Topilmasa, oxiriga qo‘shamiz
        target_paragraph = doc.add_paragraph()

    # Jadval yaratamiz
    rows_count = 1 + len(items) + 1
    table = doc.add_table(rows=rows_count, cols=5)
    table.style = "Table Grid"

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

    for idx, item in enumerate(items, start=1):
        row = table.rows[idx]
        row.cells[0].text = str(item.get("dori_nomi", ""))
        row.cells[1].text = "упак"
        row.cells[2].text = _fmt_int(item.get("miqdori", 0))
        row.cells[3].text = _fmt_int(item.get("narxi", 0))
        row.cells[4].text = _fmt_int(item.get("umumiy_narxi", 0))

        for cell in row.cells:
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.size = Pt(10)

    total_row = table.rows[-1]
    total_row.cells[0].text = "ИТОГО"
    total_row.cells[4].text = _fmt_int(jami)
    for cell in total_row.cells:
        for para in cell.paragraphs:
            for run in para.runs:
                run.bold = True
                run.font.size = Pt(10)

    # Jadvalni "{{ table }}" paragrafining OLDIGA joylashtiramiz
    target_paragraph._p.addprevious(table._tbl)

    # "{{ table }}" matnini o‘chirib tashlaymiz
    target_paragraph.text = ""

    doc.save(docx_path)
