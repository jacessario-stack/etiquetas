"""
MVP de entrega automática: subís el PDF de etiquetas de MercadoLibre Full,
te devuelve el PDF listo para imprimir en térmica 50x25mm. Sin intervención
manual — esto es el paso "Deliver" del framework, para poder validar demanda
antes de invertir en más variantes (otros tamaños, otras conversiones).
"""
import os
import time
import uuid
import shutil
import tempfile

from flask import Flask, request, render_template, send_file, flash, redirect, url_for

from converter import convert, ConversionError

MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB, un PDF de etiquetas típico pesa poco
JOB_TTL_SECONDS = 60 * 60  # 1 hora: después de eso se borra el resultado

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# Carpeta de trabajo transitoria. No hay login ni persistencia de datos del
# cliente: se procesa y se sirve, no queda nada guardado del comprador.
WORKDIR = os.path.join(tempfile.gettempdir(), "etiquetas-app")
os.makedirs(WORKDIR, exist_ok=True)


def cleanup_old_jobs():
    """Housekeeping simple: no hay clientes ni base de datos que administrar,
    así que basta con barrer carpetas de trabajo viejas en cada request."""
    now = time.time()
    try:
        for name in os.listdir(WORKDIR):
            path = os.path.join(WORKDIR, name)
            if os.path.isdir(path) and (now - os.path.getmtime(path)) > JOB_TTL_SECONDS:
                shutil.rmtree(path, ignore_errors=True)
    except FileNotFoundError:
        pass


@app.route("/", methods=["GET"])
def index():
    cleanup_old_jobs()
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def do_convert():
    cleanup_old_jobs()
    uploaded = request.files.get("pdf")
    if not uploaded or uploaded.filename == "":
        flash("Subí un archivo PDF primero.")
        return redirect(url_for("index"))

    if not uploaded.filename.lower().endswith(".pdf"):
        flash("El archivo tiene que ser un PDF.")
        return redirect(url_for("index"))

    job_id = uuid.uuid4().hex
    job_dir = os.path.join(WORKDIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    input_path = os.path.join(job_dir, "input.pdf")
    output_path = os.path.join(job_dir, "etiquetas_50x25mm.pdf")
    uploaded.save(input_path)

    try:
        counter = convert(input_path, output_path)
    except ConversionError as e:
        shutil.rmtree(job_dir, ignore_errors=True)
        flash(str(e))
        return redirect(url_for("index"))
    except Exception:
        shutil.rmtree(job_dir, ignore_errors=True)
        flash("No se pudo procesar el PDF. Verificá que no esté dañado o protegido con contraseña.")
        return redirect(url_for("index"))

    total = sum(counter.values())
    return render_template(
        "result.html",
        job_id=job_id,
        total=total,
        codigos=len(counter),
        detalle=sorted(counter.items()),
    )


@app.route("/download/<job_id>")
def download(job_id):
    # job_id es un uuid hex generado por nosotros -> no hay path traversal posible
    if not job_id.isalnum():
        return "Not found", 404
    output_path = os.path.join(WORKDIR, job_id, "etiquetas_50x25mm.pdf")
    if not os.path.exists(output_path):
        return "El archivo ya no está disponible (los resultados se borran después de un rato). Volvé a subir el PDF.", 404
    return send_file(
        output_path,
        as_attachment=True,
        download_name="etiquetas_50x25mm.pdf",
        mimetype="application/pdf",
    )


if __name__ == "__main__":
    # Para producción: gunicorn app:app (ver README)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
