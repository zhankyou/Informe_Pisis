# -*- coding: utf-8 -*-
import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Importación del Limitador centralizado
from modulos.limitador import limiter

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

app = Flask(__name__)
CORS(app)

# Inicialización de extensiones
limiter.init_app(app)

# Registro de Blueprints y Módulos
registrar_modulos_2026(app)
app.register_blueprint(informe_bp)
app.register_blueprint(ponderacion_bp)
app.register_blueprint(vistas_bp)
app.register_blueprint(api_bp)

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"status": "error", "message": "Límite de solicitudes excedido. Error 429."}), 429

if __name__ == "__main__":
    port = int(os.getenv("PORT_INFORMES", 5050))
    logging.info(f"Iniciado en http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
