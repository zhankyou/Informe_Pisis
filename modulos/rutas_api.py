# -*- coding: utf-8 -*-
import os
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
                return jsonify({"status": "error", "message": "Error de esquema."}), 500

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
        return jsonify({"status": "error", "message": "Petición bloqueada."}), 403

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
            f"🔑 *Perfil:* {form_data.get('perfil_profesional', 'N/A')}\n"
            f"📱 *Celular:* {form_data.get('celular', 'N/A')}\n"
            f"📧 *Correo:* {correo}"
        )
        notificar_nuevo_registro("Formulario de Acceso a Plataforma", detalles)
        return jsonify({"status": "success", "message": "Solicitud registrada exitosamente."})
    else:
        return jsonify({"status": "error", "message": "Error al guardar la solicitud."}), 500

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
            headers={'Content-Disposition': f"attachment;filename=Solicitud_Acceso_{datos.get('numero_documento', '000')}.pdf"}
        )
    except Exception as e:
        return jsonify({"status": "error", "message": "Error generando PDF."}), 500

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
        return jsonify({"status": "error", "message": "Error consultando datos"}), 500

@api_bp.route('/api/eliminar_acceso/<int:registro_id>', methods=['DELETE'])
@limiter.limit("20 per minute")
def api_eliminar_acceso(registro_id):
    query = text("DELETE FROM solicitudes_acceso WHERE id = :id")
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"id": registro_id})
            conn.commit()
            if result.rowcount == 0:
                return jsonify({"status": "error", "message": "Registro no encontrado"}), 404
        return jsonify({"status": "success", "message": "Registro eliminado exitosamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "Error al eliminar datos"}), 500


# ==============================================================================
# MÓDULO INDICADORES COBERTURA
# ==============================================================================

@api_bp.route('/api/indicadores_cobertura/auth', methods=['POST'])
@limiter.limit("10 per minute")
def auth_indicadores_cobertura():
    data = request.json
    territorio = str(data.get('territorio', '')).strip().upper()
    codigo = str(data.get('codigo', '')).strip()

    if not territorio or not codigo:
        return jsonify({"status": "error", "message": "Territorio y código requeridos."}), 400

    try:
        with engine.connect() as conn:
            query = text("SELECT * FROM territorios_cobertura WHERE territorio = :terr")
            row = conn.execute(query, {"terr": territorio}).mappings().fetchone()

            if not row:
                return jsonify({"status": "error", "message": "Territorio no existe."}), 404

            if row['bloqueado']:
                return jsonify({"status": "error", "message": "Territorio bloqueado por múltiples intentos fallidos. Comunicarse con el Administrador."}), 403

            if row['codigo_ingreso'] == codigo:
                conn.execute(text("UPDATE territorios_cobertura SET intentos_fallidos = 0 WHERE territorio = :terr"), {"terr": territorio})
                conn.commit()
                token = secrets.token_hex(16)
                return jsonify({"status": "success", "token_sesion": token, "territorio": territorio})
            else:
                intentos = row['intentos_fallidos'] + 1
                if intentos >= 3:
                    conn.execute(text("UPDATE territorios_cobertura SET intentos_fallidos = :int, bloqueado = TRUE WHERE territorio = :terr"), {"int": intentos, "terr": territorio})
                    conn.commit()
                    detalles_alerta = f"⚠️ *ALERTA DE SEGURIDAD*\nEl código del territorio *{territorio}* ha sido bloqueado tras 3 intentos de acceso fallidos al módulo de Indicadores de Cobertura."
                    notificar_nuevo_registro("SEGURIDAD PISIS", detalles_alerta)
                    return jsonify({"status": "error", "message": "Código bloqueado por múltiples intentos. Comunicarse con el Administrador."}), 403
                else:
                    conn.execute(text("UPDATE territorios_cobertura SET intentos_fallidos = :int WHERE territorio = :terr"), {"int": intentos, "terr": territorio})
                    conn.commit()
                    return jsonify({"status": "error", "message": f"Código incorrecto. Intentos restantes: {3 - intentos}"}), 401
    except Exception as e:
        logging.error(f"Error auth cobertura: {e}")
        return jsonify({"status": "error", "message": "Falla de servidor."}), 500

@api_bp.route('/api/indicadores_cobertura/desbloquear', methods=['POST'])
@limiter.limit("10 per minute")
def desbloquear_territorio_cobertura():
    data = request.json
    territorio = str(data.get('territorio', '')).strip().upper()
    username = str(data.get('username', '')).strip()
    password = str(data.get('password', '')).strip()

    if not territorio or not username or not password:
        return jsonify({"status": "error", "message": "Faltan parámetros de seguridad."}), 400

    query_user = text("SELECT * FROM usuarios WHERE username = :username")

    try:
        with engine.connect() as conn:
            usuario = conn.execute(query_user, {"username": username}).mappings().fetchone()
            if not usuario: return jsonify({"status": "error", "message": "Usuario no autorizado."}), 403

            rol = str(usuario.get('rol', '')).lower()
            if 'admin' not in rol and 'coordinador' not in rol:
                return jsonify({"status": "error", "message": "Privilegios insuficientes para desbloquear."}), 403

            db_pass = usuario.get('password_hash') or usuario.get('password') or usuario.get('clave')
            is_valid = False
            if str(db_pass).startswith('pbkdf2:') or str(db_pass).startswith('scrypt:'):
                is_valid = check_password_hash(str(db_pass), password)
            else:
                is_valid = (str(db_pass) == password)

            if not is_valid: return jsonify({"status": "error", "message": "Contraseña incorrecta."}), 403

            conn.execute(text("UPDATE territorios_cobertura SET intentos_fallidos = 0, bloqueado = FALSE WHERE territorio = :terr"), {"terr": territorio})
            conn.commit()

        return jsonify({"status": "success", "message": f"Territorio {territorio} desbloqueado exitosamente."})
    except Exception as e:
        logging.error(f"Error desbloqueo: {e}")
        return jsonify({"status": "error", "message": "Falla de servidor al desbloquear."}), 500

@api_bp.route('/api/indicadores_cobertura/datos', methods=['GET'])
def get_datos_cobertura():
    territorio = request.args.get('territorio', '').strip().upper()
    mes = request.args.get('mes', '').strip()
    if not territorio or not mes: return jsonify({"status": "error", "message": "Faltan parámetros"}), 400

    query = text("SELECT id_indicador, numerador, denominador, porcentaje, observaciones FROM indicadores_cobertura WHERE territorio = :terr AND mes = :mes")
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"terr": territorio, "mes": mes}).mappings().fetchall()
            return jsonify({"status": "success", "data": [dict(r) for r in result]})
    except Exception as e:
        return jsonify({"status": "error", "message": "Falla de servidor."}), 500

@api_bp.route('/api/indicadores_cobertura/guardar', methods=['POST'])
def guardar_datos_cobertura():
    data = request.json
    territorio = data.get('territorio', '').strip().upper()
    mes = data.get('mes', '').strip()
    indicadores = data.get('indicadores', [])

    if not territorio or not mes or not indicadores:
        return jsonify({"status": "error", "message": "Datos incompletos."}), 400

    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM indicadores_cobertura WHERE territorio = :terr AND mes = :mes"), {"terr": territorio, "mes": mes})
            insert_query = text("""
                INSERT INTO indicadores_cobertura (territorio, mes, id_indicador, numerador, denominador, porcentaje, observaciones)
                VALUES (:terr, :mes, :id_ind, :num, :den, :porc, :obs)
            """)
            for ind in indicadores:
                conn.execute(insert_query, {
                    "terr": territorio, "mes": mes, "id_ind": ind['id'],
                    "num": ind.get('num'), "den": ind.get('den'), "porc": ind.get('porc'), "obs": ind.get('obs')
                })
            conn.commit()
        return jsonify({"status": "success", "message": "Datos guardados exitosamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "Falla al guardar en base de datos."}), 500


# ==============================================================================
# MÓDULO INDICADORES COMPONENTES
# ==============================================================================

@api_bp.route('/api/indicadores_componentes/datos', methods=['GET'])
def get_datos_componentes():
    mes = request.args.get('mes', '').strip()
    if not mes: return jsonify({"status": "error", "message": "Faltan parámetros"}), 400

    query = text("SELECT id_indicador, numerador, denominador, porcentaje, observaciones FROM indicadores_componentes WHERE mes = :mes")
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"mes": mes}).mappings().fetchall()
            return jsonify({"status": "success", "data": [dict(r) for r in result]})
    except Exception as e:
        return jsonify({"status": "error", "message": "Falla de servidor."}), 500

@api_bp.route('/api/indicadores_componentes/guardar', methods=['POST'])
def guardar_datos_componentes():
    data = request.json
    mes = data.get('mes', '').strip()
    indicadores = data.get('indicadores', [])

    if not mes or not indicadores:
        return jsonify({"status": "error", "message": "Datos incompletos."}), 400

    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM indicadores_componentes WHERE mes = :mes"), {"mes": mes})
            insert_query = text("""
                INSERT INTO indicadores_componentes (mes, id_indicador, numerador, denominador, porcentaje, observaciones)
                VALUES (:mes, :id_ind, :num, :den, :porc, :obs)
            """)
            for ind in indicadores:
                conn.execute(insert_query, {
                    "mes": mes, "id_ind": ind['id'],
                    "num": ind.get('num'), "den": ind.get('den'), "porc": ind.get('porc'), "obs": ind.get('obs')
                })
            conn.commit()
        return jsonify({"status": "success", "message": "Datos guardados exitosamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "Falla al guardar en base de datos."}), 500
