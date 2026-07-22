# -*- coding: utf-8 -*-
import os
from flask import Blueprint, request, jsonify, send_from_directory
from sqlalchemy import text
from modulos.db_config import engine

# Importación de submódulos
from modulos.mensual import registrar_rutas_mensual
from modulos.diario_vacunacion import registrar_rutas_diario

cronograma_bp = Blueprint('cronograma', __name__)
DIR_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@cronograma_bp.route('/cronograma')
def vista_cronograma():
    return send_from_directory(DIR_BASE, "cronograma.html")

# --- CATÁLOGO DE ACTIVIDADES ---
@cronograma_bp.route('/api/cronograma/actividades', methods=['GET'])
def get_actividades():
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT id, nombre FROM cro_actividades ORDER BY id ASC")).mappings().fetchall()
        return jsonify({"status": "success", "data": [dict(r) for r in rows]}), 200
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

@cronograma_bp.route('/api/cronograma/actividades', methods=['POST'])
def save_actividad():
    nombre = request.json.get('nombre', '').strip().upper()
    if not nombre:
        return jsonify({"status": "error", "msg": "El nombre de la actividad es obligatorio."}), 400
    try:
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO cro_actividades (nombre) VALUES (:n)"), {"n": nombre})
        return jsonify({"status": "success", "msg": "Actividad registrada exitosamente."}), 200
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

# Inyección de rutas delegadas
registrar_rutas_mensual(cronograma_bp)
registrar_rutas_diario(cronograma_bp)