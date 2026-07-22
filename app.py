# -*- coding: utf-8 -*-
import os
import logging
from flask import Flask, send_from_directory, redirect
from flask_cors import CORS
from dotenv import load_dotenv

from modulos.Resolucion_2026 import registrar_modulos_2026
from modulos.informe_entidades import informe_bp

load_dotenv()
os.environ["PGCLIENTENCODING"] = "utf-8"
logging.basicConfig(level=logging.INFO, format='%(asctime)s | [%(levelname)s] | %(message)s')

DIR_BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
CORS(app)

registrar_modulos_2026(app)
app.register_blueprint(informe_bp)

@app.route("/")
def aplicacion_principal():
    return send_from_directory(DIR_BASE, "index.html")

@app.route("/login")
def login():
    return send_from_directory(DIR_BASE, "login.html")

@app.route("/logout")
def logout():
    return redirect("/")

@app.route("/financiero")
def vista_financiero():
    return send_from_directory(DIR_BASE, "financiero.html")

@app.route("/consultas")
def vista_consultas():
    return send_from_directory(DIR_BASE, "consultas.html")

@app.route("/poblacional")
def vista_poblacional():
    return send_from_directory(DIR_BASE, "poblacional.html")

@app.route("/cronograma")
def vista_cronograma():
    return send_from_directory(DIR_BASE, "cronograma.html")

@app.route("/informe")
def vista_informe():
    return send_from_directory(DIR_BASE, "informe_entidades.html")

@app.route("/static/img/<path:filename>")
def serve_img(filename):
    return send_from_directory(os.path.join(DIR_BASE, "static", "img"), filename)

if __name__ == "__main__":
    port = int(os.getenv("PORT_INFORMES", 5050))
    logging.info(f"🚀 Iniciado en http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)