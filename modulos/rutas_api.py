# -*- coding: utf-8 -*-
import os
import io
import csv
import logging
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, Response, send_from_directory
from sqlalchemy import text
from werkzeug.security import check_password_hash
from flask_caching import Cache

from modulos.db_config import engine
from modulos.acceso_db import procesar_y_guardar_solicitud
from modulos.notificaciones import notificar_nuevo_registro
from modulos.pdf_acceso import generar_documento_pdf
from modulos.limitador import limiter
from modulos.email_service import enviar_correo_aval

api_bp = Blueprint('api', __name__)
DIR_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ==============================================================================
# CONFIGURACIÓN DE SEGURIDAD (JWT) Y CACHÉ
# ==============================================================================
SECRET_KEY = os.environ.get('SECRET_KEY', 'PISIS_SECURE_KEY_2026_COMPLEX_0987654321')
cache = Cache(config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 60})

def generar_token_jwt(username, rol):
    payload = {
        'exp': datetime.utcnow() + timedelta(hours=12),
        'iat': datetime.utcnow(),
        'sub': username,
        'rol': rol
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def token_requerido(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            partes = request.headers['Authorization'].split()
            if len(partes) == 2 and partes[0] == 'Bearer':
                token = partes[1]
        
        if not token:
            return jsonify({'status': 'error', 'message': 'Acceso denegado. Token faltante.'}), 401
        
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            usuario_actual = data['sub']
            rol_actual = data['rol']
        except jwt.ExpiredSignatureError:
            return jsonify({'status': 'error', 'message': 'Token expirado. Inicie sesión nuevamente.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'status': 'error', 'message': 'Token manipulado o inválido.'}), 401
            
        return f(usuario_actual, rol_actual, *args, **kwargs)
    return decorador

def normalizar_cadena(texto):
    if not texto: return ""
    t = str(texto).lower().strip()
    reemplazos = (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ä", "a"), ("ë", "e"), ("ï", "i"), ("ö", "o"), ("ü", "u"))
    for a, b in reemplazos:
        t = t.replace(a, b)
    return t

# ==============================================================================
# MÓDULO AUTENTICACIÓN Y ACCESOS
# ==============================================================================

@api_bp.route('/api/auth/login', methods=['POST'])
@limiter.limit("20 per minute")
def api_login():
    data = request.json
    raw_username = str(data.get('username', '')).strip()
    password = str(data.get('password', '')).strip()

    if not raw_username or not password:
        return jsonify({"status": "error", "message": "Credenciales incompletas"}), 400

    username_norm = normalizar_cadena(raw_username)

    query = text("""
        SELECT * FROM usuarios 
        WHERE LOWER(TRANSLATE(username, 'áéíóúäëïöüÁÉÍÓÚÄËÏÖÜ', 'aeiouaeiouAEIOUAEIOU')) = :username_norm
    """)

    try:
        with engine.connect() as conn:
            usuario = conn.execute(query, {"username_norm": username_norm}).mappings().fetchone()

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
                rol = usuario.get('rol', 'publico')
                token = generar_token_jwt(raw_username, rol)
                return jsonify({
                    "status": "success",
                    "token": token,
                    "rol": rol,
                    "username": usuario.get('username', raw_username)
                })

        return jsonify({"status": "error", "message": "Usuario o contraseña inválidos."}), 401
    except Exception as e:
        logging.error(f"Error en login: {e}")
        return jsonify({"status": "error", "message": "Falla interna del servidor."}), 500


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
@token_requerido
@limiter.limit("20 per hour")
def api_descargar_pdf_acceso(usuario_actual, rol_actual):
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
@token_requerido
@limiter.limit("60 per minute")
def api_listar_accesos(usuario_actual, rol_actual):
    # OPTIMIZACIÓN CRÍTICA: Se excluye la columna archivo_base64 para evitar OOM (Out Of Memory) en Render
    query = text("""
        SELECT id, sistema, programa, territorio, microterritorio, tipo_documento, 
               numero_documento, nombre_completo, primer_nombre, segundo_nombre, 
               primer_apellido, segundo_apellido, fecha_nacimiento, nacionalidad, 
               sexo, celular, correo, regimen, eapb, perfil_profesional, 
               numero_contrato, objeto_contrato, fecha_contrato, 
               fecha_finalizacion_contrato, valor_contrato, seguridad_social_url, 
               datos_adicionales, fecha_solicitud 
        FROM solicitudes_acceso 
        ORDER BY id DESC
    """)
    try:
        with engine.connect() as conn:
            result = conn.execute(query).mappings().fetchall()
            datos = []
            for row in result:
                dic_row = dict(row)
                if 'fecha_nacimiento' in dic_row and dic_row['fecha_nacimiento']: dic_row['fecha_nacimiento'] = str(dic_row['fecha_nacimiento'])
                if 'fecha_solicitud' in dic_row and dic_row['fecha_solicitud']: dic_row['fecha_solicitud'] = str(dic_row['fecha_solicitud'])
                if 'fecha_contrato' in dic_row and dic_row['fecha_contrato']: dic_row['fecha_contrato'] = str(dic_row['fecha_contrato'])
                if 'fecha_finalizacion_contrato' in dic_row and dic_row['fecha_finalizacion_contrato']: dic_row['fecha_finalizacion_contrato'] = str(dic_row['fecha_finalizacion_contrato'])
                
                if 'datos_adicionales' in dic_row and dic_row['datos_adicionales']:
                    if isinstance(dic_row['datos_adicionales'], str):
                        import json
                        try:
                            extras = json.loads(dic_row['datos_adicionales'])
                            dic_row.update(extras)
                        except: pass
                    elif isinstance(dic_row['datos_adicionales'], dict):
                        dic_row.update(dic_row['datos_adicionales'])
                        
                datos.append(dic_row)
        return jsonify({"status": "success", "data": datos})
    except Exception as e:
        logging.error(f"Error consultando accesos: {e}")
        return jsonify({"status": "error", "message": "Error consultando datos"}), 500


@api_bp.route('/api/eliminar_acceso/<int:registro_id>', methods=['DELETE'])
@token_requerido
@limiter.limit("20 per minute")
def api_eliminar_acceso(usuario_actual, rol_actual, registro_id):
    if 'admin' not in rol_actual:
        return jsonify({"status": "error", "message": "Privilegios insuficientes."}), 403

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


@api_bp.route('/api/enviar_aval/<int:registro_id>', methods=['POST'])
@token_requerido
@limiter.limit("30 per hour")
def api_enviar_aval(usuario_actual, rol_actual, registro_id):
    if 'admin' not in rol_actual and 'coordinador' not in rol_actual:
        return jsonify({"status": "error", "message": "Privilegios insuficientes."}), 403

    query = text("SELECT correo, nombre_completo, primer_nombre, primer_apellido FROM solicitudes_acceso WHERE id = :id")
    try:
        with engine.connect() as conn:
            usuario = conn.execute(query, {"id": registro_id}).mappings().fetchone()
            
        if not usuario or not usuario['correo']:
            return jsonify({"status": "error", "message": "Registro no encontrado o no posee correo."}), 404

        nombre_destino = usuario['nombre_completo'] or f"{usuario.get('primer_nombre','')} {usuario.get('primer_apellido','')}".strip()
        
        if enviar_correo_aval(usuario['correo'], nombre_destino):
            return jsonify({"status": "success", "message": f"Correo de aval enviado exitosamente a {usuario['correo']}."}), 200
        else:
            return jsonify({"status": "error", "message": "Falla al enviar correo. Verifique configuración SMTP."}), 500
    except Exception as e:
        logging.error(f"Error en API enviar_aval: {e}")
        return jsonify({"status": "error", "message": "Error interno del servidor."}), 500

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
                return jsonify({"status": "error", "message": "Territorio bloqueado por múltiples intentos fallidos."}), 403

            if row['codigo_ingreso'] == codigo:
                conn.execute(text("UPDATE territorios_cobertura SET intentos_fallidos = 0 WHERE territorio = :terr"), {"terr": territorio})
                conn.commit()
                token = generar_token_jwt(territorio, 'territorio')
                return jsonify({"status": "success", "token_sesion": token, "territorio": territorio})
            else:
                intentos = row['intentos_fallidos'] + 1
                if intentos >= 3:
                    conn.execute(text("UPDATE territorios_cobertura SET intentos_fallidos = :int, bloqueado = TRUE WHERE territorio = :terr"), {"int": intentos, "terr": territorio})
                    conn.commit()
                    notificar_nuevo_registro("SEGURIDAD PISIS", f"⚠️ *ALERTA*\nCódigo de territorio *{territorio}* bloqueado.")
                    return jsonify({"status": "error", "message": "Código bloqueado por múltiples intentos."}), 403
                else:
                    conn.execute(text("UPDATE territorios_cobertura SET intentos_fallidos = :int WHERE territorio = :terr"), {"int": intentos, "terr": territorio})
                    conn.commit()
                    return jsonify({"status": "error", "message": f"Código incorrecto. Intentos restantes: {3 - intentos}"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": "Falla de servidor."}), 500


@api_bp.route('/api/indicadores_cobertura/desbloquear', methods=['POST'])
@token_requerido
@limiter.limit("10 per minute")
def desbloquear_territorio_cobertura(usuario_actual, rol_actual):
    if 'admin' not in rol_actual and 'coordinador' not in rol_actual:
        return jsonify({"status": "error", "message": "Privilegios insuficientes."}), 403

    data = request.json
    territorio = str(data.get('territorio', '')).strip().upper()

    try:
        with engine.connect() as conn:
            conn.execute(text("UPDATE territorios_cobertura SET intentos_fallidos = 0, bloqueado = FALSE WHERE territorio = :terr"), {"terr": territorio})
            conn.commit()
        return jsonify({"status": "success", "message": f"Territorio {territorio} desbloqueado exitosamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": "Falla de servidor al desbloquear."}), 500


@api_bp.route('/api/indicadores_cobertura/datos', methods=['GET'])
@cache.cached(timeout=60, query_string=True)
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
@token_requerido
def guardar_datos_cobertura(usuario_actual, rol_actual):
    data = request.json
    territorio = data.get('territorio', '').strip().upper()
    mes = data.get('mes', '').strip()
    indicadores = data.get('indicadores', [])

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
@cache.cached(timeout=60, query_string=True)
def get_datos_componentes():
    mes = request.args.get('mes', '').strip()
    query = text("SELECT id_indicador, numerador, denominador, porcentaje, observaciones FROM indicadores_componentes WHERE mes = :mes")
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"mes": mes}).mappings().fetchall()
            return jsonify({"status": "success", "data": [dict(r) for r in result]})
    except Exception as e:
        return jsonify({"status": "error", "message": "Falla de servidor."}), 500


@api_bp.route('/api/indicadores_componentes/guardar', methods=['POST'])
@token_requerido
def guardar_datos_componentes(usuario_actual, rol_actual):
    if 'admin' not in rol_actual and 'coordinador' not in rol_actual:
        return jsonify({"status": "error", "message": "Privilegios insuficientes."}), 403

    data = request.json
    mes = data.get('mes', '').strip()
    indicadores = data.get('indicadores', [])

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


# ==============================================================================
# MÓDULO SEGUIMIENTO PAGOS (GESTIÓN HUMANA)
# ==============================================================================

def parse_float(val):
    try:
        if val is None or str(val).strip() == '': return 0.0
        return float(str(val).replace(',', '.'))
    except (ValueError, TypeError): return 0.0

def parse_int(val):
    try:
        if val is None or str(val).strip() == '': return 0
        return int(float(str(val).strip()))
    except (ValueError, TypeError): return 0


@api_bp.route('/seguimiento_pagos', methods=['GET'])
def vista_seguimiento_pagos():
    return send_from_directory(DIR_BASE, "seguimiento_pagos.html")


@api_bp.route('/api/pagos', methods=['GET'])
def get_pagos():
    try:
        with engine.connect() as conn:
            query = text("SELECT * FROM seguimientos_pagos ORDER BY id DESC")
            result = conn.execute(query).mappings().fetchall()
            return jsonify({"status": "success", "data": [dict(r) for r in result]}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Falla al consultar registros de pago."}), 500


@api_bp.route('/api/pagos', methods=['POST'])
@token_requerido
def crear_pago(usuario_actual, rol_actual):
    data = request.get_json(silent=True) or {}
    con_val = str(data.get('contrato', '')).strip().upper()[:50]
    cta_val = parse_int(data.get('cuenta'))

    if not con_val or cta_val <= 0:
        return jsonify({"status": "error", "message": "El Contrato y el Número de Cuenta válido son obligatorios."}), 400

    try:
        with engine.connect() as conn:
            check_query = text("SELECT id FROM seguimientos_pagos WHERE UPPER(contrato) = :con AND cuenta = :cta")
            existe = conn.execute(check_query, {"con": con_val, "cta": cta_val}).fetchone()

            if existe:
                return jsonify({"status": "error", "message": f"DUPLICADO: La cuenta N° {cta_val} ya se encuentra registrada para el contrato {con_val}."}), 400

            query = text("""
                INSERT INTO seguimientos_pagos 
                (nombre_completo, numero_documento, contrato, valor_contrato, numero_pagos, cuenta, 
                 pago_mensual, pago_real, egresos, adicion_contrato, observaciones)
                VALUES (:nc, :nd, :con, :vc, :np, :cta, :pm, :pr, :eg, :adc, :obs)
            """)
            conn.execute(query, {
                "nc": str(data.get('nombre_completo', '')).strip().upper()[:200],
                "nd": str(data.get('numero_documento', '')).strip()[:20],
                "con": con_val,
                "vc": parse_float(data.get('valor_contrato')),
                "np": parse_int(data.get('numero_pagos')),
                "cta": cta_val,
                "pm": parse_float(data.get('pago_mensual')),
                "pr": parse_float(data.get('pago_real')),
                "eg": parse_float(data.get('egresos')),
                "adc": parse_int(data.get('adicion_contrato')),
                "obs": str(data.get('observaciones', '')).strip().upper()[:500]
            })
            conn.commit()
        return jsonify({"status": "success", "message": "Registro de pago guardado exitosamente."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error interno en base de datos."}), 500


@api_bp.route('/api/pagos/<int:pago_id>', methods=['PUT'])
@token_requerido
def actualizar_pago(usuario_actual, rol_actual, pago_id):
    data = request.get_json(silent=True) or {}
    con_val = str(data.get('contrato', '')).strip().upper()[:50]
    cta_val = parse_int(data.get('cuenta'))

    try:
        with engine.connect() as conn:
            check_query = text("SELECT id FROM seguimientos_pagos WHERE UPPER(contrato) = :con AND cuenta = :cta AND id != :id")
            existe = conn.execute(check_query, {"con": con_val, "cta": cta_val, "id": pago_id}).fetchone()

            if existe:
                return jsonify({"status": "error", "message": f"DUPLICADO: La cuenta N° {cta_val} ya está registrada en otro reporte del contrato {con_val}."}), 400

            query = text("""
                UPDATE seguimientos_pagos 
                SET nombre_completo=:nc, numero_documento=:nd, contrato=:con, valor_contrato=:vc, 
                    numero_pagos=:np, cuenta=:cta, pago_mensual=:pm, pago_real=:pr, egresos=:eg, 
                    adicion_contrato=:adc, observaciones=:obs
                WHERE id = :id
            """)
            conn.execute(query, {
                "id": pago_id,
                "nc": str(data.get('nombre_completo', '')).strip().upper()[:200],
                "nd": str(data.get('numero_documento', '')).strip()[:20],
                "con": con_val,
                "vc": parse_float(data.get('valor_contrato')),
                "np": parse_int(data.get('numero_pagos')),
                "cta": cta_val,
                "pm": parse_float(data.get('pago_mensual')),
                "pr": parse_float(data.get('pago_real')),
                "eg": parse_float(data.get('egresos')),
                "adc": parse_int(data.get('adicion_contrato')),
                "obs": str(data.get('observaciones', '')).strip().upper()[:500]
            })
            conn.commit()
        return jsonify({"status": "success", "message": "Registro actualizado exitosamente."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Error al actualizar el registro."}), 500


@api_bp.route('/api/pagos/<int:pago_id>', methods=['DELETE'])
@token_requerido
def eliminar_pago(usuario_actual, rol_actual, pago_id):
    if 'admin' not in rol_actual:
        return jsonify({"status": "error", "message": "Privilegios insuficientes."}), 403
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM seguimientos_pagos WHERE id = :id"), {"id": pago_id})
            conn.commit()
        return jsonify({"status": "success", "message": "Registro eliminado exitosamente."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Error al eliminar el registro."}), 500


@api_bp.route('/api/pagos/upload', methods=['POST'])
@token_requerido
@limiter.limit("10 per minute")
def upload_csv(usuario_actual, rol_actual):
    if 'admin' not in rol_actual:
        return jsonify({"status": "error", "message": "Privilegios insuficientes."}), 403

    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No se adjuntó ningún archivo CSV."}), 400

    file = request.files['file']
    if not file.filename.lower().endswith('.csv'):
        return jsonify({"status": "error", "message": "El formato de archivo debe ser .csv"}), 400

    try:
        stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline=None)
        csv_input = csv.DictReader(stream, delimiter=';')

        insert_query = text("""
            INSERT INTO seguimientos_pagos 
            (nombre_completo, numero_documento, contrato, valor_contrato, numero_pagos, cuenta, 
             pago_mensual, pago_real, egresos, adicion_contrato, observaciones)
            VALUES (:nc, :nd, :con, :vc, :np, :cta, :pm, :pr, :eg, :adc, :obs)
        """)

        count = 0
        with engine.connect() as conn:
            existing_records = {(str(r.contrato).strip().upper(), parse_int(r.cuenta)) for r in conn.execute(text("SELECT contrato, cuenta FROM seguimientos_pagos")).fetchall()}

            for idx, row in enumerate(csv_input, start=1):
                con_val = str(row.get('contrato', '')).strip().upper()[:50]
                cta_val = parse_int(row.get('cuenta'))

                if (con_val, cta_val) in existing_records:
                    conn.rollback()
                    return jsonify({"status": "error", "message": f"ERROR FILA {idx}: La cuenta N° {cta_val} para el contrato {con_val} ya existe en BD o duplicado en archivo. Operación cancelada."}), 400

                existing_records.add((con_val, cta_val))

                conn.execute(insert_query, {
                    "nc": str(row.get('nombre_completo', '')).strip().upper()[:200],
                    "nd": str(row.get('numero_documento', '')).strip()[:20],
                    "con": con_val,
                    "vc": parse_float(row.get('valor_contrato')),
                    "np": parse_int(row.get('numero_pagos')),
                    "cta": cta_val,
                    "pm": parse_float(row.get('pago_mensual')),
                    "pr": parse_float(row.get('pago_real')),
                    "eg": parse_float(row.get('egresos')),
                    "adc": parse_int(row.get('adicion_contrato')),
                    "obs": str(row.get('observaciones', '')).strip().upper()[:500]
                })
                count += 1
            conn.commit()
        return jsonify({"status": "success", "message": f"Carga masiva completada: {count} registros importados."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Falla al procesar estructura CSV: {str(e)}"}), 500
