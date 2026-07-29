# -*- coding: utf-8 -*-
import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Importación de extensiones de Seguridad, Limite y Caché
from modulos.limitador import limiter
from modulos.seguridad import cache

# Importación de Módulos Locales
from modulos.db_config import engine
from modulos.Resolucion_2026 import registrar_modulos_2026
from modulos.informe_entidades import informe_bp
from modulos.matriz_ponderacion import ponderacion_bp

# Importación de Rutas Refactorizadas
from modulos.rutas_vistas import vistas_bp
from modulos.rutas_api import api_bp

load_dotenv()
os.environ["PGCLIENTENCODING"] = "utf-8"
logging.basicConfig(level=logging.INFO, format='%(asctime)s | [%(levelname)s] | %(message)s')

# Inicialización de Flask
app = Flask(__name__)

# Configuración estricta de CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# Inicialización de extensiones
limiter.init_app(app)
cache.init_app(app)


# Inyección Global de Cabeceras de Seguridad Estrictas
@app.after_request
def aplicar_cabeceras_seguridad(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


# Registro de Blueprints y Módulos
registrar_modulos_2026(app)
app.register_blueprint(informe_bp)
app.register_blueprint(ponderacion_bp)
app.register_blueprint(vistas_bp)
app.register_blueprint(api_bp)


# Manejador Global de Límite de Peticiones
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"status": "error", "message": "Límite de solicitudes excedido. Error 429."}), 429


if __name__ == "__main__":
    port = int(os.getenv("PORT_INFORMES", 5050))
    # Control de debug mediante variable de entorno para evitar exposición en producción
    modo_debug = os.getenv("FLASK_ENV", "production") == "development"

    logging.info(f"Iniciado en http://0.0.0.0:{port} | Modo Debug: {modo_debug}")
    app.run(host="0.0.0.0", port=port, debug=modo_debug)
