# -*- coding: utf-8 -*-
import os, io, csv, logging, jwt, json, re, unicodedata
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
from modulos.email_service import enviar_correo_aval, enviar_correo_denegacion

api_bp = Blueprint('api', __name__)
DIR_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = os.environ.get('SECRET_KEY', 'PISIS_SECURE_KEY_2026_COMPLEX_0987654321')
cache = Cache(config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 60})


# --- HELPERS ---
def generar_token_jwt(u, r): return jwt.encode(
    {'exp': datetime.utcnow() + timedelta(hours=12), 'iat': datetime.utcnow(), 'sub': u, 'rol': r}, SECRET_KEY,
    algorithm='HS256')


def normalizar_cadena(t): return ''.join(
    (c for c in str(t).lower().strip().translate(str.maketrans('áéíóúäëïöü', 'aeiouaeiou')) if c)) if t else ""


def limpiar_ansi(t): return re.sub(r'[^A-Za-z0-9 \-\.\,\;\:]', '', ''.join(
    c for c in unicodedata.normalize('NFD', str(t).replace('|', '')) if
    unicodedata.category(c) != 'Mn')).strip().upper() if t else ""


def p_num(v, t=float):
    try:
        return t(str(v).replace(',', '.')) if v and str(v).strip() else t(0)
    except:
        return t(0)


def p_dat(v): return str(v).strip() if v and str(v).strip() else None


def token_requerido(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        t = request.headers.get('Authorization', '').split()[1] if 'Bearer' in request.headers.get('Authorization',
                                                                                                   '') else None
        if not t: return jsonify({'status': 'error', 'message': 'Acceso denegado. Token faltante.'}), 401
        try:
            d = jwt.decode(t, SECRET_KEY, algorithms=['HS256'])
        except Exception:
            return jsonify({'status': 'error', 'message': 'Token manipulado o expirado.'}), 401
        return f(d['sub'], d['rol'], *args, **kwargs)

    return decorador


# --- AUTENTICACIÓN Y ACCESOS ---
@api_bp.route('/api/auth/login', methods=['POST'])
@limiter.limit("20 per minute")
def api_login():
    u, p = str(request.json.get('username', '')).strip(), str(request.json.get('password', '')).strip()
    if not u or not p: return jsonify({"status": "error", "message": "Credenciales incompletas"}), 400
    try:
        with engine.connect() as conn:
            us = conn.execute(
                text("SELECT * FROM usuarios WHERE LOWER(TRANSLATE(username, 'áéíóúÁÉÍÓÚ', 'aeiouAEIOU')) = :u"),
                {"u": normalizar_cadena(u)}).mappings().fetchone()
        if us and (check_password_hash(us.get('password_hash') or us.get('password', ''), p) if str(
                us.get('password_hash', '')).startswith(('pbkdf2:', 'scrypt:')) else (
                str(us.get('password') or us.get('clave')) == p)):
            return jsonify({"status": "success", "token": generar_token_jwt(u, us.get('rol', 'publico')),
                            "rol": us.get('rol', 'publico'), "username": us.get('username', u)})
        return jsonify({"status": "error", "message": "Credenciales inválidas."}), 401
    except Exception:
        return jsonify({"status": "error", "message": "Falla del servidor."}), 500


@api_bp.route('/api/guardar_acceso', methods=['POST'])
@limiter.limit("10 per hour")
def api_guardar_acceso():
    fd = request.form.to_dict()
    if fd.get('validacion_bot_oculta', '') or not str(fd.get('correo', '')).strip(): return jsonify(
        {"status": "error", "message": "Datos inválidos."}), 400
    if procesar_y_guardar_solicitud(fd, request.files.get('seguridad_social')):
        notificar_nuevo_registro("Formulario de Acceso",
                                 f"👤 *{fd.get('nombre_completo') or fd.get('numero_documento')}*\n📧 *{fd.get('correo')}*")
        return jsonify({"status": "success", "message": "Solicitud registrada."})
    return jsonify({"status": "error", "message": "Error al guardar."}), 500


@api_bp.route('/api/descargar_pdf_acceso', methods=['POST'])
@token_requerido
def api_descargar_pdf_acceso(u, r):
    try:
        return Response(generar_documento_pdf(request.json), mimetype='application/pdf', headers={
            'Content-Disposition': f"attachment;filename=Solicitud_{request.json.get('numero_documento', '000')}.pdf"})
    except:
        return jsonify({"status": "error", "message": "Error generando PDF."}), 500


@api_bp.route('/api/listar_accesos', methods=['GET'])
@token_requerido
def api_listar_accesos(u, r):
    try:
        with engine.connect() as conn:
            res = [dict(r) for r in conn.execute(text(
                "SELECT id, sistema, programa, territorio, microterritorio, tipo_documento, numero_documento, nombre_completo, primer_nombre, segundo_nombre, primer_apellido, segundo_apellido, fecha_nacimiento, nacionalidad, sexo, celular, correo, regimen, eapb, perfil_profesional, numero_contrato, objeto_contrato, fecha_contrato, fecha_finalizacion_contrato, valor_contrato, seguridad_social_url, datos_adicionales, fecha_solicitud FROM solicitudes_acceso ORDER BY id DESC")).mappings().fetchall()]
            for d in res:
                for f in ['fecha_nacimiento', 'fecha_solicitud', 'fecha_contrato', 'fecha_finalizacion_contrato']: d[
                    f] = str(d[f]) if d.get(f) else None
                if d.get('datos_adicionales'): d.update(
                    json.loads(d['datos_adicionales']) if isinstance(d['datos_adicionales'], str) else d[
                        'datos_adicionales'])
        return jsonify({"status": "success", "data": res})
    except:
        return jsonify({"status": "error", "message": "Falla DB."}), 500


@api_bp.route('/api/eliminar_acceso/<int:rid>', methods=['DELETE'])
@token_requerido
def api_eliminar_acceso(u, r, rid):
    if 'admin' not in r: return jsonify({"status": "error"}), 403
    with engine.begin() as conn: conn.execute(text("DELETE FROM solicitudes_acceso WHERE id = :id"), {"id": rid})
    return jsonify({"status": "success", "message": "Eliminado."})


@api_bp.route('/api/enviar_aval/<int:rid>', methods=['POST'])
@token_requerido
def api_enviar_aval(u, r, rid):
    if 'admin' not in r and 'coordinador' not in r: return jsonify({"status": "error"}), 403
    with engine.connect() as conn:
        us = conn.execute(text("SELECT correo, nombre_completo, primer_nombre FROM solicitudes_acceso WHERE id = :id"),
                          {"id": rid}).mappings().fetchone()
    if us and enviar_correo_aval(us['correo'], us['nombre_completo'] or us.get('primer_nombre', '')): return jsonify(
        {"status": "success", "message": "Aval enviado."})
    return jsonify({"status": "error", "message": "Error enviando correo."}), 500


@api_bp.route('/api/denegar_acceso/<int:rid>', methods=['POST'])
@token_requerido
def api_denegar_acceso(u, r, rid):
    if 'admin' not in r and 'coordinador' not in r: return jsonify({"status": "error"}), 403
    with engine.connect() as conn:
        us = conn.execute(text("SELECT correo, nombre_completo, primer_nombre FROM solicitudes_acceso WHERE id = :id"),
                          {"id": rid}).mappings().fetchone()
    if not us or not us['correo']: return jsonify(
        {"status": "error", "message": "Registro no encontrado o sin correo."}), 404

    nd = us['nombre_completo'] or us.get('primer_nombre', '')
    if enviar_correo_denegacion(us['correo'], nd):
        with engine.begin() as conn: conn.execute(text("DELETE FROM solicitudes_acceso WHERE id = :id"), {"id": rid})
        return jsonify(
            {"status": "success", "message": f"Acceso denegado. Correo enviado a {us['correo']} y registro eliminado."})
    return jsonify({"status": "error", "message": "Error enviando correo de denegación."}), 500


# --- INDICADORES ---
@api_bp.route('/api/indicadores_cobertura/auth', methods=['POST'])
def auth_ind_cob():
    t, c = str(request.json.get('territorio', '')).strip().upper(), str(request.json.get('codigo', '')).strip()
    with engine.connect() as conn:
        row = conn.execute(text("SELECT * FROM territorios_cobertura WHERE territorio = :t"),
                           {"t": t}).mappings().fetchone()
        if not row or row['bloqueado']: return jsonify(
            {"status": "error", "message": "Territorio bloqueado/inexistente."}), 403
        if row['codigo_ingreso'] == c:
            conn.execute(text("UPDATE territorios_cobertura SET intentos_fallidos = 0 WHERE territorio = :t"),
                         {"t": t});
            conn.commit()
            return jsonify({"status": "success", "token_sesion": generar_token_jwt(t, 'territorio'), "territorio": t})
        int_f = row['intentos_fallidos'] + 1
        conn.execute(
            text("UPDATE territorios_cobertura SET intentos_fallidos = :i, bloqueado = :b WHERE territorio = :t"),
            {"i": int_f, "b": int_f >= 3, "t": t});
        conn.commit()
        return jsonify({"status": "error", "message": "Código incorrecto."}), 401


@api_bp.route('/api/indicadores_<tipo>/datos', methods=['GET'])
@cache.cached(timeout=60, query_string=True)
def get_ind(tipo):
    t, m = request.args.get('territorio', '').upper(), request.args.get('mes', '')
    tb, p = ("indicadores_cobertura", {"terr": t, "mes": m}) if tipo == 'cobertura' else ("indicadores_componentes",
                                                                                          {"mes": m})
    wh = "WHERE territorio = :terr AND mes = :mes" if tipo == 'cobertura' else "WHERE mes = :mes"
    with engine.connect() as conn: return jsonify({"status": "success", "data": [dict(r) for r in conn.execute(
        text(f"SELECT * FROM {tb} {wh}"), p).mappings().fetchall()]})


@api_bp.route('/api/indicadores_<tipo>/guardar', methods=['POST'])
@token_requerido
def save_ind(u, r, tipo):
    d = request.json
    tb, p = ("indicadores_cobertura",
             {"terr": d.get('territorio', '').upper(), "mes": d.get('mes')}) if tipo == 'cobertura' else (
        "indicadores_componentes", {"mes": d.get('mes')})
    wh = "WHERE territorio = :terr AND mes = :mes" if tipo == 'cobertura' else "WHERE mes = :mes"
    ins = f"INSERT INTO {tb} (territorio, mes, id_indicador, numerador, denominador, porcentaje, observaciones) VALUES (:terr, :mes, :id_ind, :num, :den, :porc, :obs)" if tipo == 'cobertura' else f"INSERT INTO {tb} (mes, id_indicador, numerador, denominador, porcentaje, observaciones) VALUES (:mes, :id_ind, :num, :den, :porc, :obs)"
    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM {tb} {wh}"), p)
        for i in d.get('indicadores', []): conn.execute(text(ins), {**p, "id_ind": i['id'], "num": i.get('num'),
                                                                    "den": i.get('den'), "porc": i.get('porc'),
                                                                    "obs": i.get('obs')})
    return jsonify({"status": "success", "message": "Guardado."})


# --- PAGOS ---
def extrae_pago(d):
    return {
        "nc": str(d.get('nombre_completo', '')).upper()[:200], "nd": str(d.get('numero_documento', ''))[:20],
        "con": str(d.get('contrato', '')).upper()[:50], "fic": p_dat(d.get('fecha_inicio_contrato')),
        "ftc": p_dat(d.get('fecha_terminacion_contrato')), "ls": str(d.get('link_secop', '')).strip(),
        "vc": p_num(d.get('valor_contrato')), "np": str(d.get('numero_pagos', '')).strip()[:20],
        "cta": int(p_num(d.get('cuenta'))),
        "pm": p_num(d.get('pago_mensual')), "pr": p_num(d.get('pago_real')), "ne": str(d.get('numero_egreso', ''))[:50],
        "adc": int(p_num(d.get('adicion_contrato'))), "obs": str(d.get('observaciones', '')).upper()[:500],
        "cdp": str(d.get('numero_cdp', '')).strip()[:50], "rp": str(d.get('numero_rp', '')).strip()[:50],
        "nsup": str(d.get('nombre_supervisor', '')).upper()[:200],
        "csup": str(d.get('cedula_supervisor', '')).strip()[:20]
    }


@api_bp.route('/seguimiento_pagos', methods=['GET'])
def vista_pagos(): return send_from_directory(DIR_BASE, "seguimiento_pagos.html")


@api_bp.route('/api/pagos', methods=['GET'])
def get_pagos():
    with engine.connect() as conn: return jsonify({"status": "success", "data": [
        dict(r, fecha_inicio_contrato=str(r['fecha_inicio_contrato']) if r.get('fecha_inicio_contrato') else '',
             fecha_terminacion_contrato=str(r['fecha_terminacion_contrato']) if r.get(
                 'fecha_terminacion_contrato') else '') for r in
        conn.execute(text("SELECT * FROM seguimientos_pagos ORDER BY id DESC")).mappings().fetchall()]})


@api_bp.route('/api/pagos', methods=['POST'])
@token_requerido
def crear_pago(u, r):
    d = extrae_pago(request.get_json(silent=True) or {})
    if not all([d['con'], d['cta'], d['ne'], d['fic'], d['ftc'], d['ls'], d['cdp'], d['nsup']]): return jsonify(
        {"status": "error", "message": "Faltan campos obligatorios."}), 400
    with engine.begin() as conn:
        if conn.execute(text("SELECT 1 FROM seguimientos_pagos WHERE UPPER(contrato)=:con AND cuenta=:cta"),
                        d).fetchone(): return jsonify({"status": "error", "message": "Cuenta duplicada."}), 400
        conn.execute(text(
            "INSERT INTO seguimientos_pagos (nombre_completo, numero_documento, contrato, fecha_inicio_contrato, fecha_terminacion_contrato, link_secop, valor_contrato, numero_pagos, cuenta, pago_mensual, pago_real, numero_egreso, adicion_contrato, observaciones, numero_cdp, numero_rp, nombre_supervisor, cedula_supervisor) VALUES (:nc, :nd, :con, :fic, :ftc, :ls, :vc, :np, :cta, :pm, :pr, :ne, :adc, :obs, :cdp, :rp, :nsup, :csup)"),
                     d)
    return jsonify({"status": "success", "message": "Guardado."})


@api_bp.route('/api/pagos/<int:pid>', methods=['PUT'])
@token_requerido
def actualizar_pago(u, r, pid):
    d = {**extrae_pago(request.get_json(silent=True) or {}), "id": pid}
    if not all([d['con'], d['cta'], d['ne'], d['fic'], d['ftc'], d['ls']]): return jsonify(
        {"status": "error", "message": "Faltan campos."}), 400
    with engine.begin() as conn:
        if conn.execute(text("SELECT 1 FROM seguimientos_pagos WHERE UPPER(contrato)=:con AND cuenta=:cta AND id!=:id"),
                        d).fetchone(): return jsonify({"status": "error", "message": "Duplicado."}), 400
        conn.execute(text(
            "UPDATE seguimientos_pagos SET nombre_completo=:nc, numero_documento=:nd, contrato=:con, fecha_inicio_contrato=:fic, fecha_terminacion_contrato=:ftc, link_secop=:ls, valor_contrato=:vc, numero_pagos=:np, cuenta=:cta, pago_mensual=:pm, pago_real=:pr, numero_egreso=:ne, adicion_contrato=:adc, observaciones=:obs, numero_cdp=:cdp, numero_rp=:rp, nombre_supervisor=:nsup, cedula_supervisor=:csup WHERE id=:id"),
                     d)
    return jsonify({"status": "success", "message": "Actualizado."})


@api_bp.route('/api/pagos/<int:pid>', methods=['DELETE'])
@token_requerido
def eliminar_pago(u, r, pid):
    if 'admin' not in r: return jsonify({"status": "error"}), 403
    with engine.begin() as conn: conn.execute(text("DELETE FROM seguimientos_pagos WHERE id = :id"), {"id": pid})
    return jsonify({"status": "success", "message": "Eliminado."})


@api_bp.route('/api/pagos/upload', methods=['POST'])
@token_requerido
def upload_csv(u, r):
    if 'admin' not in r or 'file' not in request.files: return jsonify({"status": "error", "message": "Invalido."}), 400
    try:
        csv_in = csv.DictReader(io.StringIO(request.files['file'].stream.read().decode("utf-8-sig"), newline=None),
                                delimiter=';')
        with engine.begin() as conn:
            ext = {(str(r[0]).strip().upper(), int(r[1])) for r in
                   conn.execute(text("SELECT contrato, cuenta FROM seguimientos_pagos")).fetchall()}
            for row in csv_in:
                d = extrae_pago(row)
                if (d['con'], d['cta']) in ext: return jsonify(
                    {"status": "error", "message": f"Cuenta {d['cta']} duplicada en {d['con']}."}), 400
                ext.add((d['con'], d['cta']))
                conn.execute(text(
                    "INSERT INTO seguimientos_pagos (nombre_completo, numero_documento, contrato, fecha_inicio_contrato, fecha_terminacion_contrato, link_secop, valor_contrato, numero_pagos, cuenta, pago_mensual, pago_real, numero_egreso, adicion_contrato, observaciones, numero_cdp, numero_rp, nombre_supervisor, cedula_supervisor) VALUES (:nc, :nd, :con, :fic, :ftc, :ls, :vc, :np, :cta, :pm, :pr, :ne, :adc, :obs, :cdp, :rp, :nsup, :csup)"),
                             d)
        return jsonify({"status": "success", "message": "Carga masiva completada."})
    except Exception as e:
        return jsonify({"status": "error", "message": "Error procesando CSV."}), 500


# --- MOTOR ETL PISIS ---
@api_bp.route('/api/etl/pisis/<anexo>', methods=['GET'])
@token_requerido
def generar_pisis(u, r, anexo):
    if 'admin' not in r and 'coordinador' not in r: return jsonify({"status": "error"}), 403
    fc, nit, idr, out = request.args.get('fecha_corte', datetime.now().strftime('%Y-%m-%d')), request.args.get('nit',
                                                                                                               '892000146'), request.args.get(
        'id_recurso', 'ID0000000000'), io.StringIO()
    try:
        dt_c = datetime.strptime(fc, '%Y-%m-%d'); fcf, fim = dt_c.strftime('%Y%m%d'), dt_c.replace(day=1).strftime(
            '%Y-%m-%d')
    except:
        return jsonify({"status": "error"}), 400

    if anexo.upper() == 'SER124DREC':
        with engine.connect() as conn:
            pagos = conn.execute(
                text("SELECT * FROM seguimientos_pagos WHERE pago_real > 0 ORDER BY id ASC")).mappings().fetchall()
        out.write(f"1|NI|{nit}|{fim}|{fc}|{len(pagos) * 2}\n");
        cons = 1
        for p in pagos:
            fi, ft, o, cc, ne = p['fecha_inicio_contrato'] or '1900-01-01', p[
                'fecha_terminacion_contrato'] or '1900-01-01', limpiar_ansi(
                p['observaciones']) or 'PRESTACION DE SERVICIOS', limpiar_ansi(p['contrato']), limpiar_ansi(
                p['numero_egreso']) or str(p['cuenta'])
            nsup, csup = limpiar_ansi(p.get('nombre_supervisor', ''))[:100], limpiar_ansi(
                p.get('cedula_supervisor', ''))[:17]
            out.write(
                f"3|{cons}|{idr}|{nit}|I|1|{cc}|{fi}|{ft}|{o[:500]}|{p['valor_contrato']:.2f}|CC|{limpiar_ansi(p['numero_documento'])[:17]}|{limpiar_ansi(p['nombre_completo'])[:100]}|CC|{csup}|{nsup}\n")
            out.write(f"5|{cons + 1}|{idr}|{nit}|I|1|{cc}|1|{ne}|{fc}|{p['pago_real']:.2f}|{p['pago_real']:.2f}|||\n")
            cons += 2
    elif anexo.upper() == 'APS124CCFP':
        with engine.connect() as conn:
            fams = conn.execute(text("SELECT datos_adicionales FROM solicitudes_acceso")).mappings().fetchall()
        out.write(f"1|NI|{nit}|{fim}|{fc}|{len(fams)}\n");
        cons = 1
        for f in fams:
            d = json.loads(f['datos_adicionales']) if isinstance(f['datos_adicionales'], str) else (
                        f['datos_adicionales'] or {})
            out.write(
                f"2|{cons}|1|{limpiar_ansi(d.get('departamento_vivienda', '50'))}||{limpiar_ansi(d.get('municipio_vivienda', '50001'))}|||{limpiar_ansi(d.get('area_ubicacion_vivienda', '1'))}" + "|" * 110 + "\n")
            cons += 1
    else:
        return jsonify({"status": "error"}), 400

    out.seek(0)
    return Response(out.read(), mimetype="text/plain", headers={
        "Content-Disposition": f"attachment;filename={anexo.upper()}{fcf}NI{nit.zfill(12)}{idr if anexo.upper() == 'SER124DREC' else ''}.txt"})
