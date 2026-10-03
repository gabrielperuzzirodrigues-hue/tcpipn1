#!/usr/bin/env python3
"""Converte o DOCX final em PDF imprimível usando Chromium já instalado."""

import base64
import html
import re
import shutil
import subprocess
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
import pymupdf


BASE = Path(__file__).resolve().parent
DOCX_PATH = BASE / "relatorio_payload_http11.docx"
HTML_PATH = BASE / "relatorio_payload_http11.html"
PDF_PATH = BASE / "relatorio_payload_http11.pdf"
RAW_PDF_PATH = BASE / "relatorio_payload_http11_sem_paginacao.pdf"


def paragraph_image_html(paragraph, document):
    elements = []
    for image in paragraph._p.xpath(".//a:blip"):
        relationship_id = image.get(qn("r:embed"))
        part = document.part.related_parts[relationship_id]
        content_type = part.content_type
        encoded = base64.b64encode(part.blob).decode("ascii")
        elements.append(
            f'<figure class="image"><img src="data:{content_type};base64,{encoded}"></figure>'
        )
    return "".join(elements)


def render_paragraph(paragraph, document):
    text = paragraph.text.strip()
    images = paragraph_image_html(paragraph, document)
    if not text:
        return images

    escaped = html.escape(text)
    style_name = paragraph.style.name
    style_class = re.sub(r"([a-z])([A-Z])", r"\1-\2", style_name).lower()

    if style_name.startswith("Cover"):
        return f"<p class='cover {style_class}'>{escaped}</p>"
    if style_name.startswith("TitlePage"):
        return f"<p class='title-page {style_class}'>{escaped}</p>"
    if style_name == "AbstractBody":
        return f"<p class='abstract-body'>{escaped}</p>"
    if style_name == "AbstractKeywords":
        return f"<p class='abstract-keywords'>{escaped}</p>"
    if style_name == "ReferenceEntry":
        return f"<p class='reference-entry'>{escaped}</p>"
    if style_name in {"TocEntry", "FigureListEntry"}:
        label, page = text.split("\t", 1)
        level = "subentry" if (paragraph.paragraph_format.left_indent.cm or 0) > 0 else "entry"
        entry_type = "figure-list" if style_name == "FigureListEntry" else "toc"
        return (
            f"<p class='{entry_type}-{level}'>"
            f"<span class='toc-label'>{html.escape(label)}</span>"
            "<span class='toc-leader'></span>"
            f"<span class='toc-page'>{html.escape(page)}</span></p>"
        )
    if any(run.font.name == "Consolas" for run in paragraph.runs):
        return f"{images}<pre class='code'>{escaped}</pre>"

    if text == "REFERÊNCIAS":
        return f"{images}<h2 class='references'>{escaped}</h2>"
    if text in {"RESUMO", "ABSTRACT", "LISTA DE ILUSTRAÇÕES", "SUMÁRIO"}:
        return f"{images}<h2 class='pretext-heading'>{escaped}</h2>"
    if re.match(r"^\d+\s+[A-Z]", text):
        return f"{images}<h2 class='section-primary'>{escaped}</h2>"
    if re.match(r"^\d+\.\d+\s", text):
        return f"{images}<h3 class='section-secondary'>{escaped}</h3>"
    if text.startswith("Figura "):
        return f"{images}<p class='caption'>{escaped}</p>"
    if text.startswith("Fonte:"):
        return f"{images}<p class='source'>{escaped}</p>"
    return f"{images}<p class='body'>{escaped}</p>"


def main():
    document = Document(DOCX_PATH)
    blocks = []
    for paragraph in document.paragraphs:
        blocks.append(render_paragraph(paragraph, document))

    html_document = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Payload em HTTP/1.1 — Gabriel Peruzzi Rodrigues</title>
<style>
  @page {{
    size: A4;
    margin: 30mm 20mm 20mm 30mm;
  }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: "Times New Roman", serif; font-size: 12pt; color: #111;
          margin: 0; }}
  p.body {{ text-align: justify; text-indent: 1.25cm; line-height: 1.5;
            margin: 0; orphans: 2; widows: 2; }}
  p.cover, p.title-page {{ text-align: center; text-indent: 0; line-height: 1.5;
                           margin: 0; }}
  p.cover-institution {{ font-weight: bold; margin-bottom: 4pt; line-height: 1; }}
  p.cover-course, p.cover-discipline, p.cover-registration,
  p.cover-year, p.title-page-registration, p.title-page-year {{ line-height: 1; }}
  p.cover-author {{ margin-top: 115pt; line-height: 1; }}
  p.cover-title {{ margin-top: 150pt; font-weight: bold; line-height: 1.5; }}
  p.cover-place {{ margin-top: 215pt; line-height: 1; }}
  p.title-page-author {{ break-before: page; page-break-before: always; line-height: 1; }}
  p.title-page-title {{ margin-top: 75pt; font-weight: bold; line-height: 1.5; }}
  p.title-page-nature {{ width: 9cm; margin: 140pt 0 0 auto; text-align: justify;
                         line-height: 1; }}
  p.title-page-place {{ margin-top: 175pt; line-height: 1; }}
  p.abstract-body {{ text-align: justify; text-indent: 0; line-height: 1;
                     margin: 0; }}
  p.abstract-keywords {{ text-align: left; text-indent: 0; line-height: 1;
                         margin: 8pt 0 0; }}
  p.reference-entry {{ text-align: left; text-indent: 0; line-height: 1;
                       margin: 0 0 12pt; }}
  h2 {{ font-size: 12pt; font-weight: bold; line-height: 1.5;
        break-after: avoid; }}
  h2.pretext-heading {{ text-align: center; break-before: page;
                        page-break-before: always; margin: 0 0 18pt; }}
  h2.section-primary {{ text-align: left; break-before: page;
                        page-break-before: always; margin: 0 0 18pt; }}
  h3.section-secondary {{ font-size: 12pt; font-weight: bold; text-align: left;
                          line-height: 1.5; margin: 18pt 0; break-after: avoid; }}
  h2.references {{ text-align: center; break-before: page;
                   page-break-before: always; margin: 0 0 18pt; }}
  p.toc-entry, p.toc-subentry, p.figure-list-entry {{
      display:flex; align-items:baseline; gap:4pt; line-height:1.2; margin:0 0 5pt;
      text-indent:0; }}
  p.toc-subentry {{ margin-left: 0.75cm; }}
  .toc-label {{ white-space:nowrap; }}
  .toc-leader {{ flex:1; border-bottom:1px dotted #111; min-width:12pt; }}
  .toc-page {{ text-align:right; min-width:1.2em; }}
  pre.code {{ white-space: pre-wrap; overflow-wrap: anywhere;
              font: 10pt/1.15 "DejaVu Sans Mono", monospace;
              margin: 3pt 0 3pt 1cm; break-inside: avoid; }}
  figure.image {{ margin: 5pt auto 3pt; text-align: center;
                  break-inside: avoid; page-break-inside: avoid; }}
  figure.image img {{ width: 100%; max-width: 6in; height: auto; }}
  p.caption {{ text-align: center; text-indent: 0; font-size: 10pt;
               line-height: 1; margin: 4pt 0 2pt; }}
  p.source {{ text-align: left; text-indent: 0; font-size: 10pt;
              line-height: 1; margin: 0 0 8pt; }}
</style>
</head>
<body>
{''.join(blocks)}
</body>
</html>"""
    HTML_PATH.write_text(html_document, encoding="utf-8")

    browser = next(
        (
            shutil.which(name)
            for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable")
            if shutil.which(name)
        ),
        None,
    )
    if browser is None and Path("/repl/tools/bin/chromium").exists():
        browser = "/repl/tools/bin/chromium"
    if browser is None:
        raise RuntimeError(
            "Chromium não encontrado. Instale Chromium ou adicione-o ao PATH para exportar o PDF."
        )
    result = subprocess.run(
        [
            browser,
            "--headless",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--no-first-run",
            "--no-pdf-header-footer",
            f"--print-to-pdf={RAW_PDF_PATH}",
            HTML_PATH.as_uri(),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0 or not RAW_PDF_PATH.exists():
        raise RuntimeError(f"Falha ao criar o PDF: {result.stderr}")

    pdf = pymupdf.open(RAW_PDF_PATH)
    text_page = next(
        (
            index
            for index, page in enumerate(pdf)
            if "O Hypertext Transfer Protocol" in page.get_text()
        ),
        None,
    )
    if text_page is None:
        raise RuntimeError("Não encontrei a primeira página textual para inserir a paginação.")

    font = pymupdf.Font("tiro")
    page_edge = 56.7  # 2 cm da borda direita
    baseline = 66.7   # 2 cm da borda superior, contando a altura do algarismo
    for page_index in range(text_page, len(pdf)):
        page = pdf[page_index]
        label = str(page_index)  # a capa não é contada; a folha de rosto vale 1
        width = font.text_length(label, fontsize=10)
        page.insert_text(
            (page.rect.width - page_edge - width, baseline),
            label,
            fontname="tiro",
            fontsize=10,
            color=(0, 0, 0),
        )

    metadata = pdf.metadata
    metadata.update(
        {
            "title": "Payload em HTTP/1.1: formato, delimitação e processamento do corpo da mensagem",
            "author": "Gabriel Peruzzi Rodrigues",
            "subject": "Trabalho acadêmico de Arquitetura TCP/IP",
        }
    )
    pdf.set_metadata(metadata)
    numbered_path = PDF_PATH.with_suffix(".tmp.pdf")
    pdf.save(numbered_path, garbage=4, deflate=True)
    pdf.close()
    numbered_path.replace(PDF_PATH)
    RAW_PDF_PATH.unlink(missing_ok=True)
    print(f"PDF gerado: {PDF_PATH}")


if __name__ == "__main__":
    main()