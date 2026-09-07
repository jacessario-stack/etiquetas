"""Genera un PDF sintético que imita el layout de etiquetas de ML Full
(grilla 3x10, celdas 142.3x71pt) para poder probar el pipeline end-to-end
sin tener un PDF real de MercadoLibre a mano."""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

PAGE_W, PAGE_H = 595.276, 841.89
CELL_W, CELL_H = 142.3, 71.0
COLS, ROWS = 3, 10

c = canvas.Canvas("test_labels.pdf", pagesize=(PAGE_W, PAGE_H))

codes = []
n = 1
for page in range(2):
    for row in range(ROWS):
        for col in range(COLS):
            x0 = col * CELL_W
            top = row * CELL_H  # distancia desde arriba
            y1 = PAGE_H - top          # borde superior en coords PDF (origen abajo)
            y0 = y1 - CELL_H            # borde inferior
            code = f"ABCD{10000 + n:05d}"[:9]
            codes.append(code)
            c.rect(x0, y0, CELL_W, CELL_H, stroke=1, fill=0)
            c.setFont("Helvetica", 8)
            c.drawString(x0 + 10, y0 + CELL_H / 2, code)
            c.drawString(x0 + 10, y0 + CELL_H / 2 - 12, "Datos de envio ficticios")
            n += 1
    c.showPage()

c.save()
print(f"Generadas {n - 1} celdas de prueba en test_labels.pdf")
