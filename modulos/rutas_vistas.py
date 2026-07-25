# -*- coding: utf-8 -*-
import os
from flask import Blueprint, send_from_directory, redirect

vistas_bp = Blueprint('vistas', __name__)

# Resuelve el directorio raíz del proyecto dinámicamente
DIR_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@vistas_bp.route("/")
def aplicacion_principal(): return send_from_directory(DIR_BASE, "index.html")

@vistas_bp.route("/login")
def login(): return send_from_directory(DIR_BASE, "login.html")

@vistas_bp.route("/logout")
def logout(): return redirect("/")

@vistas_bp.route("/financiero")
def vista_financiero(): return send_from_directory(DIR_BASE, "financiero.html")

@vistas_bp.route("/consultas")
def vista_consultas(): return send_from_directory(DIR_BASE, "consultas.html")

@vistas_bp.route("/ponderacion")
def vista_ponderacion(): return send_from_directory(DIR_BASE, "ponderacion.html")

@vistas_bp.route("/poblacional")
def vista_poblacional(): return send_from_directory(DIR_BASE, "poblacional.html")

@vistas_bp.route("/cronograma")
def vista_cronograma(): return send_from_directory(DIR_BASE, "cronograma.html")

@vistas_bp.route("/informe")
def vista_informe(): return send_from_directory(DIR_BASE, "informe_entidades.html")

@vistas_bp.route('/formulario_acceso')
def formulario_acceso(): return send_from_directory(DIR_BASE, "formulario_acceso.html")

@vistas_bp.route('/consulta_acceso')
def consulta_acceso(): return send_from_directory(DIR_BASE, "consulta_acceso.html")

@vistas_bp.route("/static/img/<path:filename>")
def serve_img(filename):
    return send_from_directory(os.path.join(DIR_BASE, "static", "img"), filename)
