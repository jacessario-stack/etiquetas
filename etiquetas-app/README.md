# Etiquetas ML Full → térmica 50x25mm (MVP de entrega automática)

Web app mínima: el cliente sube el PDF de etiquetas que le da MercadoLibre
Full, y le devuelve un PDF con una etiqueta por página, 50x25mm exactos,
vectorial, listo para imprimir. Cero intervención manual de tu parte —
esto es el paso "Deliver" para poder validar demanda antes de invertir en
más variantes (otros tamaños, otras conversiones).

## Probar en local

```bash
pip install -r requirements.txt
python app.py
# abrí http://localhost:5000
```

Si no tenés a mano un PDF real de MercadoLibre para probar, generá uno de
prueba con el layout correcto (grilla 3x10, 60 etiquetas falsas):

```bash
pip install reportlab
python make_test_pdf.py   # genera test_labels.pdf
```

Ya lo probé end-to-end con este PDF sintético: detecta las 60 etiquetas,
genera el PDF de salida con una página por etiqueta a 50.2mm x 25.0mm
(dentro del margen de error esperado). **Falta validarlo con un PDF real
de MercadoLibre** antes de mostrárselo a un cliente — el layout sintético
imita las medidas de celda conocidas, pero el PDF real puede tener detalles
que no estoy viendo (por eso el "falta ver variantes de tamaño" que dejaste
para después).

## Deployar (para que sea un link público, no algo que corrés vos)

La opción más simple y gratis para arrancar es **Render**:

1. Subí esta carpeta a un repo de GitHub (puede ser privado).
2. En [render.com](https://render.com) → New → Web Service → conectá el repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Plan Free alcanza para validar demanda (se duerme si no hay tráfico,
   tarda unos segundos en despertar — aceptable para un MVP).

Alternativas equivalentes: Railway, Fly.io. Todas leen el `Procfile` /
start command de la misma forma.

Variable de entorno opcional: `SECRET_KEY` (cualquier string random, para
que las cookies de sesión de Flask no usen el valor por default).

## Qué falta antes de mostrarlo a un cliente real

- [ ] Probar con un PDF real de MercadoLibre Full (no el sintético).
- [ ] Decidir dominio/nombre.
- [ ] Decidir cobro (pago único / por lote) — ver charla con Claude sobre
      Whop vs Mercado Pago según a quién le vendas.
- [ ] Nada de esto necesita esperar a las variantes de otros tamaños de
      etiqueta — eso es explícitamente para después.

## Estructura

```
app.py            servidor Flask (rutas: /, /convert, /download/<id>)
converter.py       la lógica de conversión (misma que la skill de Claude)
make_test_pdf.py   genera un PDF de prueba con el layout de ML Full
templates/         HTML (subida + resultado)
static/style.css    estilos
requirements.txt
Procfile           para Render/Railway (gunicorn)
```
