# -*- coding: utf-8 -*-
import os
import logging
import datetime
import re
from flask import Blueprint, request, jsonify, send_file, send_from_directory
from sqlalchemy import text
from modulos.db_config import engine
from modulos.exportador_txt import generar_txt_ser124drec

financiero_bp = Blueprint('financiero', __name__)
DIR_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@financiero_bp.route('/financiero')
def vista_financiero():
    return send_from_directory(DIR_BASE, "financiero.html")


def insertar_registro(tabla, payload):
    datos_limpios = {k: v for k, v in payload.items() if v != ""}
    if not datos_limpios: return False, "El payload está vacío."

    if 'id_recurso' in datos_limpios:
        try:
            with engine.connect() as conn:
                estado = conn.execute(text("SELECT estado FROM ser_recursos WHERE id_recurso = :id"),
                                      {"id": datos_limpios['id_recurso']}).scalar()
                if estado == 'FINALIZADA':
                    return False, "Operación Denegada. La resolución de este recurso se encuentra FINALIZADA y bloqueada."
        except Exception as e:
            return False, f"Error validando estado del recurso: {str(e)}"

    columnas, valores = ", ".join(datos_limpios.keys()), ", ".join([f":{k}" for k in datos_limpios.keys()])
    query = text(f"INSERT INTO {tabla} ({columnas}) VALUES ({valores})")

    try:
        with engine.begin() as conn:
            conn.execute(query, datos_limpios)
        return True, "Registro guardado exitosamente."
    except Exception as e:
        logging.error(f"Error insertando en {tabla}: {e}")
        return False, "Error interno DB. Verifique esquemas."


@financiero_bp.route('/api/recursos', methods=['GET'])
def get_recursos():
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id_recurso, descripcion, estado FROM ser_recursos ORDER BY created_at DESC")).fetchall()
        return jsonify(
            [{"id_recurso": r.id_recurso, "descripcion": r.descripcion, "estado": r.estado} for r in result]), 200
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


@financiero_bp.route('/api/recursos', methods=['POST'])
def save_recurso():
    ok, msg = insertar_registro("ser_recursos", request.json)
    return jsonify({"status": "success" if ok else "error", "msg": msg}), 200 if ok else 500


@financiero_bp.route('/api/recursos/toggle', methods=['POST'])
def toggle_recurso():
    data = request.json
    try:
        with engine.begin() as conn:
            conn.execute(text("UPDATE ser_recursos SET estado = :est WHERE id_recurso = :id"),
                         {"est": data.get('estado'), "id": data.get('id_recurso')})
        return jsonify({"status": "success", "msg": "Estado actualizado."}), 200
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


@financiero_bp.route('/api/dashboard/ejecucion', methods=['GET'])
def get_dashboard_ejecucion():
    query_recursos = """
                     SELECT r.id_recurso, \
                            r.descripcion, \
                            r.estado, \
                            COALESCE((SELECT SUM(valor_incorporado) \
                                      FROM ser_incorporacion \
                                      WHERE id_recurso = r.id_recurso \
                                        AND ind_incorporacion NOT IN ('E', 'NA')), 0)                               as incorporado, \
                            COALESCE((SELECT SUM(valor_contrato) \
                                      FROM ser_contratos \
                                      WHERE id_recurso = r.id_recurso AND ind_actualizacion NOT IN ('E', 'NA')), \
                                     0)                                                                             as ejecutado_contratos, \
                            (SELECT COUNT(*) \
                             FROM ser_contratos \
                             WHERE id_recurso = r.id_recurso \
                               AND ind_actualizacion = 'I')                                                         as contratos_i, \
                            (SELECT COUNT(*) \
                             FROM ser_contratos \
                             WHERE id_recurso = r.id_recurso \
                               AND ind_actualizacion = 'A')                                                         as contratos_a, \
                            (SELECT COUNT(*) \
                             FROM ser_contratos \
                             WHERE id_recurso = r.id_recurso \
                               AND ind_actualizacion = 'E')                                                         as contratos_e, \
                            (SELECT COUNT(*) \
                             FROM ser_polizas \
                             WHERE id_recurso = r.id_recurso \
                               AND ind_poliza NOT IN ('E', 'NA'))                                                   as polizas_totales, \
                            COALESCE((SELECT SUM(valor_ejecutado) \
                                      FROM ser_seguimiento \
                                      WHERE id_recurso = r.id_recurso AND ind_seguimiento NOT IN ('E', 'NA')), \
                                     0)                                                                             as seg_ejecutado, \
                            COALESCE((SELECT SUM(valor_pagado) \
                                      FROM ser_seguimiento \
                                      WHERE id_recurso = r.id_recurso AND ind_seguimiento NOT IN ('E', 'NA')), \
                                     0)                                                                             as seg_pagado, \
                            (SELECT COUNT(*) \
                             FROM ser_seguimiento \
                             WHERE id_recurso = r.id_recurso \
                               AND ind_seguimiento NOT IN ('E', 'NA'))                                              as actas_totales, \
                            COALESCE((SELECT SUM(valor_reintegrado) \
                                      FROM ser_reintegro_no_ejecutado \
                                      WHERE id_recurso = r.id_recurso \
                                        AND ind_reintegro NOT IN ('E', 'NA')), \
                                     0)                                                                             as reintegro_no_ejecutado_oficial, \
                            COALESCE((SELECT SUM(valor_reintegrado) \
                                      FROM ser_reintegro_rendimientos \
                                      WHERE id_recurso = r.id_recurso \
                                        AND ind_reintegro NOT IN ('E', 'NA')), \
                                     0)                                                                             as reintegro_rendimientos
                     FROM ser_recursos r \
                     ORDER BY r.created_at ASC \
                     """

    query_contratos = "SELECT id_recurso, cod_tipo_contrato, ind_actualizacion, valor_contrato, objeto FROM ser_contratos WHERE ind_actualizacion NOT IN ('E','NA')"
    query_seguimiento = "SELECT id_recurso, cod_tipo_contrato, cod_tipo_acta, valor_ejecutado, valor_pagado FROM ser_seguimiento WHERE ind_seguimiento NOT IN ('E','NA')"
    query_control = "SELECT fecha_inicial, fecha_final FROM ser_control ORDER BY fecha_inicial DESC"

    try:
        with engine.connect() as conn:
            result_rec = conn.execute(text(query_recursos)).fetchall()
            result_ct = conn.execute(text(query_contratos)).fetchall()
            result_seg = conn.execute(text(query_seguimiento)).fetchall()
            result_ctrl = conn.execute(text(query_control)).fetchall()

        data_rec = [dict(row._mapping) for row in result_rec]

        # Procesamiento analítico en memoria
        for rec in data_rec:
            id_rec = rec['id_recurso']

            # 1. Perfiles de Contratación Semántica (Análisis de Objeto)
            perfiles = {"MEDICINA": {"cant": 0, "val": 0}, "ENFERMERIA": {"cant": 0, "val": 0},
                        "PSICOLOGIA": {"cant": 0, "val": 0}, "TECNICO": {"cant": 0, "val": 0},
                        "OTROS": {"cant": 0, "val": 0}}

            # 2. Contratos por Tipo
            tipos_ct = {}

            for ct in result_ct:
                if ct.id_recurso != id_rec: continue
                val = float(ct.valor_contrato or 0)
                cod = str(ct.cod_tipo_contrato)

                # Agrupación por Tipo
                if cod not in tipos_ct:
                    tipos_ct[cod] = {"tipo": cod, "valor_total": 0, "cantidad": 0}
                tipos_ct[cod]["valor_total"] += val
                tipos_ct[cod]["cantidad"] += 1

                # Análisis de Perfil
                obj = str(ct.objeto).upper() if ct.objeto else ""
                if re.search(r'MEDIC', obj):
                    perfiles["MEDICINA"]["cant"] += 1
                    perfiles["MEDICINA"]["val"] += val
                elif re.search(r'ENFERMER', obj):
                    perfiles["ENFERMERIA"]["cant"] += 1
                    perfiles["ENFERMERIA"]["val"] += val
                elif re.search(r'PSICOLOG', obj):
                    perfiles["PSICOLOGIA"]["cant"] += 1
                    perfiles["PSICOLOGIA"]["val"] += val
                elif re.search(r'TECNIC', obj):
                    perfiles["TECNICO"]["cant"] += 1
                    perfiles["TECNICO"]["val"] += val
                else:
                    perfiles["OTROS"]["cant"] += 1
                    perfiles["OTROS"]["val"] += val

            rec['perfiles_contratacion'] = perfiles
            rec['contratos_por_tipo'] = list(tipos_ct.values())

            # 3. Seguimiento (Actas)
            seg_agrupado = {}
            for sg in result_seg:
                if sg.id_recurso != id_rec: continue
                clave = f"{sg.cod_tipo_contrato}-{sg.cod_tipo_acta}"
                if clave not in seg_agrupado:
                    seg_agrupado[clave] = {"tipo_contrato": sg.cod_tipo_contrato, "tipo_acta": sg.cod_tipo_acta,
                                           "cantidad_actas": 0, "ejecutado": 0, "pagado": 0}
                seg_agrupado[clave]["cantidad_actas"] += 1
                seg_agrupado[clave]["ejecutado"] += float(sg.valor_ejecutado or 0)
                seg_agrupado[clave]["pagado"] += float(sg.valor_pagado or 0)

            rec['seguimiento_detalle'] = list(seg_agrupado.values())

        data_ctrl = [{"fecha_inicial": str(r.fecha_inicial), "fecha_final": str(r.fecha_final)} for r in result_ctrl]

        return jsonify({"status": "success", "data_recursos": data_rec, "data_control": data_ctrl}), 200
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


for endpoint, tabla in [('control', 'ser_control'), ('incorporacion', 'ser_incorporacion'),
                        ('contratos', 'ser_contratos'), ('polizas', 'ser_polizas'), ('seguimiento', 'ser_seguimiento'),
                        ('reintegro_no_ejecutado', 'ser_reintegro_no_ejecutado'),
                        ('reintegro_rendimientos', 'ser_reintegro_rendimientos')]:
    def crear_ruta(t):
        def route_func():
            ok, msg = insertar_registro(t, request.json)
            return jsonify({"status": "success" if ok else "error", "msg": msg}), 200 if ok else 500

        return route_func


    financiero_bp.add_url_rule(f'/api/ser124drec/{endpoint}', f'save_{endpoint}', crear_ruta(tabla), methods=['POST'])


@financiero_bp.route('/api/exportar/ser124drec', methods=['GET'])
def exportar_ser124drec():
    try:
        resolucion, fecha_corte = request.args.get('res', 'RES_2026'), request.args.get('fecha',
                                                                                        datetime.datetime.now().strftime(
                                                                                            '%Y-%m-%d'))
        tipo_id, num_id, id_recurso = request.args.get('tipo_id', 'NI'), request.args.get('num_id',
                                                                                          '822002459'), request.args.get(
            'id_recurso', 'ID2026000000')
        nombre_archivo, stream = generar_txt_ser124drec(engine, resolucion, fecha_corte, tipo_id, num_id, id_recurso)
        return send_file(stream, as_attachment=True, download_name=nombre_archivo, mimetype='text/plain; charset=utf-8')
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500