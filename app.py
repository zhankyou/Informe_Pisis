# -*- coding: utf-8 -*-
import os
import logging
import secrets
from flask import Flask, send_from_directory, redirect, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import text
from werkzeug.security import check_password_hash

from modulos.db_config import engine
from modulos.Resolucion_2026 import registrar_modulos_2026
from modulos.informe_entidades import informe_bp
from modulos.acceso_db import procesar_y_guardar_solicitud
from modulos.matriz_ponderacion import ponderacion_bp

load_dotenv()
os.environ["PGCLIENTENCODING"] = "utf-8"
logging.basicConfig(level=logging.INFO, format='%(asctime)s | [%(levelname)s] | %(message)s')

DIR_BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
CORS(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["10000 per day", "1000 per hour"],
    storage_uri="memory://"
)

registrar_modulos_2026(app)
app.register_blueprint(informe_bp)
app.register_blueprint(ponderacion_bp)


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


@app.route("/ponderacion")
def vista_ponderacion():
    return send_from_directory(DIR_BASE, "ponderacion.html")


@app.route("/poblacional")
def vista_poblacional():
    return send_from_directory(DIR_BASE, "poblacional.html")


@app.route("/cronograma")
def vista_cronograma():
    return send_from_directory(DIR_BASE, "cronograma.html")


@app.route("/informe")
def vista_informe():
    return send_from_directory(DIR_BASE, "informe_entidades.html")


@app.route('/formulario_acceso')
def formulario_acceso():
    return send_from_directory(DIR_BASE, "formulario_acceso.html")


@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("20 per minute")
def api_login():
    data = request.json
    username = str(data.get('username', '')).strip()
    password = str(data.get('password', '')).strip()

    if not username or not password:
        return jsonify({"status": "error", "message": "Credenciales incompletas"}), 400

    query = text("SELECT * FROM usuarios WHERE username = :username")

    try:
        with engine.connect() as conn:
            usuario = conn.execute(query, {"username": username}).mappings().fetchone()

        if usuario:
            db_pass = usuario.get('password_hash') or usuario.get('password') or usuario.get('clave')

            if not db_pass:
                return jsonify({"status": "error", "message": "Error de esquema: No se encontró columna de contraseña."}), 500

            is_valid = False
            if str(db_pass).startswith('pbkdf2:') or str(db_pass).startswith('scrypt:'):
                is_valid = check_password_hash(str(db_pass), password)
            else:
                is_valid = (str(db_pass) == password)

            if is_valid:
                token = secrets.token_hex(32)
                return jsonify({
                    "status": "success",
                    "token": token,
                    "rol": usuario.get('rol', 'publico'),
                    "username": usuario.get('username', username)
                })

        return jsonify({"status": "error", "message": "Usuario o contraseña inválidos."}), 401
    except Exception as e:
        logging.error(f"Error en login: {e}")
        return jsonify({"status": "error", "message": f"Error interno: {str(e)}"}), 500


@app.route('/api/guardar_acceso', methods=['POST'])
@limiter.limit("10 per hour")
def api_guardar_acceso():
    form_data = request.form.to_dict()

    if form_data.get('validacion_bot_oculta', '') != '':
        return jsonify({"status": "error", "message": "Petición bloqueada por políticas de seguridad automatizada."}), 403

    file_obj = request.files.get('seguridad_social')
    correo = str(form_data.get('correo', '')).lower().strip()

    if not correo:
        return jsonify({"status": "error", "message": "El correo electrónico es obligatorio."}), 400

    exito = procesar_y_guardar_solicitud(form_data, file_obj)

    if exito:
        return jsonify({"status": "success", "message": "Solicitud registrada exitosamente."})
    else:
        return jsonify({"status": "error", "message": "Error interno al guardar la solicitud."}), 500


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"status": "error", "message": "Límite de solicitudes excedido. Error 429."}), 429


@app.route("/static/img/<path:filename>")
def serve_img(filename):
    return send_from_directory(os.path.join(DIR_BASE, "static", "img"), filename)


if __name__ == "__main__":
    port = int(os.getenv("PORT_INFORMES", 5050))
    logging.info(f"Iniciado en http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)