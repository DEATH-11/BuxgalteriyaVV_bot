import subprocess
from pathlib import Path


def convert_to_pdf(docx_path: Path) -> Path | None:
    output_dir = docx_path.parent
    try:
        subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(output_dir),
                str(docx_path),
            ],
            check=True,
            timeout=60,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception:
        return None

    pdf_path = output_dir / (docx_path.stem + ".pdf")
    if pdf_path.exists():
        return pdf_path
    return None
