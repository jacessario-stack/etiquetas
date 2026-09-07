"""
Conversion engine: MercadoLibre Full label PDF -> one 50x25mm label per page,
100% vectorial (no rasterization), ready to print on a thermal printer.

Extracted from the internal ml-etiquetas-full skill logic. Do not touch the
content stream — only mediabox/cropbox are modified, so print quality never
degrades.
"""
import copy
import io
import re
from collections import Counter

import pdfplumber
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

ML_CODE = re.compile(r'^[A-Z]{4}\d{5}$')
NORMAL_MB = RectangleObject([0, 0, 595.276, 841.89])


class ConversionError(Exception):
    """Raised when the uploaded PDF doesn't look like a MercadoLibre Full label sheet."""


def fix_mediabox(reader: PdfReader) -> io.BytesIO:
    """Corrige páginas con mediabox invertido (bug conocido en la página 1 del PDF de ML)."""
    writer = PdfWriter()
    for page in reader.pages:
        new_p = copy.copy(page)
        if float(page.mediabox.bottom) > float(page.mediabox.top):
            new_p.mediabox = NORMAL_MB
        writer.add_page(new_p)
    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf


def get_cells(plumb_page):
    """Detecta las celdas de etiquetas (tamaño fijo 142.3x71 pt) en la grilla 3x10."""
    rects = [
        r for r in plumb_page.rects
        if abs((r['x1'] - r['x0']) - 142.3) < 2
        and abs((r['bottom'] - r['top']) - 71.0) < 2
    ]
    seen, cells = set(), []
    for r in rects:
        key = (round(r['x0']), round(r['top']))
        if key not in seen:
            seen.add(key)
            cells.append(r)
    return sorted(cells, key=lambda r: (round(r['top']), r['x0']))


def get_ml_code(r, words):
    """Extrae el código ML (formato XXXX99999) dentro de la celda."""
    cx0, cx1, ctop, cbot = r['x0'], r['x1'], r['top'], r['bottom']
    cell_words = [
        w for w in words
        if cx0 - 3 <= w['x0'] and w['x1'] <= cx1 + 3
        and ctop - 3 <= w['top'] and w['bottom'] <= cbot + 3
    ]
    return next((w['text'] for w in cell_words if ML_CODE.match(w['text'])), None)


def convert(input_path: str, output_path: str) -> Counter:
    """
    Convierte el PDF de etiquetas de ML Full (grilla 3x10) en un PDF con
    una etiqueta por página, 50x25mm exactos, vectorial.

    Devuelve un Counter {codigo_ml: cantidad} para validar el conteo.
    Lanza ConversionError si no se detecta ninguna etiqueta (probablemente
    el PDF subido no es el formato esperado de MercadoLibre Full).
    """
    reader_orig = PdfReader(input_path)
    buf = fix_mediabox(reader_orig)
    reader = PdfReader(buf)
    writer = PdfWriter()
    counter: Counter = Counter()

    with pdfplumber.open(buf) as pdf:
        for plumb_page, pypdf_page in zip(pdf.pages, reader.pages):
            words = plumb_page.extract_words()
            cells = get_cells(plumb_page)
            page_h = float(pypdf_page.mediabox.top)

            for r in cells:
                ml_code = get_ml_code(r, words)
                if not ml_code:
                    continue  # celda vacía

                y_b = page_h - r['bottom']
                y_t = page_h - r['top']
                new_page = copy.copy(pypdf_page)
                box = RectangleObject([r['x0'], y_b, r['x1'], y_t])
                new_page.cropbox = box
                new_page.mediabox = box
                writer.add_page(new_page)
                counter[ml_code] += 1

    if not counter:
        raise ConversionError(
            "No se detectó ninguna etiqueta en el PDF. "
            "Verificá que sea un PDF de etiquetas de MercadoLibre Full sin modificar."
        )

    with open(output_path, 'wb') as f:
        writer.write(f)

    return counter
