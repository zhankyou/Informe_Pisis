# -*- coding: utf-8 -*-
import logging
import secrets
from flask import Blueprint, request, jsonify, Response
from sqlalchemy import text
from werkzeug.security import check_password_hash

from modulos.db_config import engine
from modulos.acceso_db import procesar_y_guardar_solicitud
from modulos.notificaciones import notificar_nuevo_registro
from modulos.pdf_acceso import generar_documento_pdf
from modulos.limitador import limiter

api_bp = Blueprint('api', __name__)


@api_bp.route('/api/auth/login', methods=['POST'])
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
                return jsonify(
                    {"status": "error", "message": "Error de esquema: No se encontró columna de contraseña."}), 500

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


@api_bp.route('/api/guardar_acceso', methods=['POST'])
@limiter.limit("10 per hour")
def api_guardar_acceso():
    form_data = request.form.to_dict()

    if form_data.get('validacion_bot_oculta', '') != '':
        return jsonify(
            {"status": "error", "message": "Petición bloqueada por políticas de seguridad automatizada."}), 403

    file_obj = request.files.get('seguridad_social')
    correo = str(form_data.get('correo', '')).lower().strip()

    if not correo:
        return jsonify({"status": "error", "message": "El correo electrónico es obligatorio."}), 400

    exito = procesar_y_guardar_solicitud(form_data, file_obj)

    if exito:
        nombre_completo = form_data.get('nombre_completo', '').strip()
        if not nombre_completo:
            nombre_completo = f"{form_data.get('primer_nombre', '')} {form_data.get('primer_apellido', '')}".strip()

        detalles = (
            f"👤 *Nuevo Registro procesado por {nombre_completo}*\n"
            f"📄 *Documento:* {form_data.get('numero_documento', 'N/A')}\n"
            f"🔑 *Perfil Profesional:* {form_data.get('perfil_profesional', 'N/A')}\n"
            f"📱 *Celular:* {form_data.get('celular', 'N/A')}\n"
            f"📧 *Correo:* {correo}"
        )
        notificar_nuevo_registro("Formulario de Acceso a Plataforma", detalles)
        return jsonify({"status": "success", "message": "Solicitud registrada exitosamente."})
    else:
        return jsonify({"status": "error", "message": "Error interno al guardar la solicitud."}), 500


@api_bp.route('/api/descargar_pdf_acceso', methods=['POST'])
@limiter.limit("20 per hour")
def api_descargar_pdf_acceso():
    datos = request.json
    if not datos:
        return jsonify({"status": "error", "message": "Datos no proporcionados."}), 400

    try:
        pdf_bytes = generar_documento_pdf(datos)
        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f"attachment;filename=Solicitud_Acceso_{datos.get('numero_documento', '000')}.pdf"}
        )
    except Exception as e:
        logging.error(f"Falla al generar PDF: {e}")
        return jsonify({"status": "error", "message": "Error interno generando PDF."}), 500


@api_bp.route('/api/listar_accesos', methods=['GET'])
@limiter.limit("60 per minute")
def api_listar_accesos():
    query = text("SELECT * FROM solicitudes_acceso ORDER BY id DESC")
    try:
        with engine.connect() as conn:
            result = conn.execute(query).mappings().fetchall()

            datos = []
            for row in result:
                dic_row = dict(row)
                if 'fecha_nacimiento' in dic_row and dic_row['fecha_nacimiento']:
                    dic_row['fecha_nacimiento'] = str(dic_row['fecha_nacimiento'])
                if 'fecha_solicitud' in dic_row and dic_row['fecha_solicitud']:
                    dic_row['fecha_solicitud'] = str(dic_row['fecha_solicitud'])
                if 'fecha_contrato' in dic_row and dic_row['fecha_contrato']:
                    dic_row['fecha_contrato'] = str(dic_row['fecha_contrato'])
                if 'fecha_finalizacion_contrato' in dic_row and dic_row['fecha_finalizacion_contrato']:
                    dic_row['fecha_finalizacion_contrato'] = str(dic_row['fecha_finalizacion_contrato'])
                datos.append(dic_row)

        return jsonify({"status": "success", "data": datos})
    except Exception as e:
        logging.error(f"Error consultando solicitudes de acceso: {e}")
        return jsonify({"status": "error", "message": "Error interno consultando datos"}), 500


@api_bp.route('/api/eliminar_acceso/<int:registro_id>', methods=['DELETE'])
@limiter.limit("20 per minute")
def api_eliminar_acceso(registro_id):
    query = text("DELETE FROM solicitudes_acceso WHERE id = :id")
    try:
        with engine.begin() as conn:
            result = conn.execute(query, {"id": registro_id})
            if result.rowcount == 0:
                return jsonify({"status": "error", "message": "Registro no encontrado"}), 404
        return jsonify({"status": "success", "message": "Registro eliminado exitosamente."})
    except Exception as e:
        logging.error(f"Error eliminando solicitud de acceso: {e}")
        return jsonify({"status": "error", "message": "Error interno al eliminar datos"}), 500
