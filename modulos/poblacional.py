# -*- coding: utf-8 -*-
import os
import io
import datetime
import logging
from flask import Blueprint, request, jsonify, send_file, send_from_directory
from sqlalchemy import text
from modulos.db_config import engine
from modulos.etl_mapper import transformar_registro_vivienda, transformar_registro_integrante, sanitizar_pisis

poblacional_bp = Blueprint('poblacional', __name__)
DIR_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TABLAS_FAMILIA = ["aps_2024_familias", "caracterizacion_si_aps_familiar", "caracterizacion_si_aps_familiar_2026"]
TABLAS_INTEGRANTE = ["aps_2024_integrantes", "caracterizacion_si_aps_individual",
                     "caracterizacion_si_aps_individual_2026"]


def table_exists(conn, table_name):
    query = text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :t)")
    return conn.execute(query, {"t": table_name}).scalar()


@poblacional_bp.route('/poblacional')
def vista_poblacional():
    return send_from_directory(DIR_BASE, "poblacional.html")


@poblacional_bp.route('/api/dashboard/poblacional', methods=['GET'])
def get_metricas_poblacional():
    try:
        with engine.connect() as conn:
            # Sincronizados extraídos desde siaps_pisis (única fuente para la exportación final)
            sinc_familias = conn.execute(text("SELECT COUNT(*) FROM siaps_pisis WHERE tipo_registro = 2")).scalar() or 0
            sinc_integrantes = conn.execute(
                text("SELECT COUNT(*) FROM siaps_pisis WHERE tipo_registro = 3")).scalar() or 0

            epi_familias, epi_integrantes = 0, 0
            detalle_epi = {}

            for t in TABLAS_FAMILIA:
                if table_exists(conn, t):
                    c = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar() or 0
                    epi_familias += c
                    detalle_epi[t] = c

            for t in TABLAS_INTEGRANTE:
                if table_exists(conn, t):
                    c = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar() or 0
                    epi_integrantes += c
                    detalle_epi[t] = c

        return jsonify({
            "status": "success",
            "data": {
                "familias": {"epicollect": epi_familias, "sincronizadas": sinc_familias,
                             "pendientes": max(0, epi_familias - sinc_familias)},
                "integrantes": {"epicollect": epi_integrantes, "sincronizadas": sinc_integrantes,
                                "pendientes": max(0, epi_integrantes - sinc_integrantes)},
                "detalle_tablas_epicollect": detalle_epi
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


def _construir_linea(p, n_campos):
    """Arma la línea delimitada por pipe (|) según el Anexo Técnico."""
    return "|".join([str(p.get(f"c{i}") or "") for i in range(n_campos)]).replace('"', '').replace('\r', '').replace(
        '\n', ' ')


@poblacional_bp.route('/api/sincronizar_epicollect', methods=['POST'])
def sincronizar_epicollect():
    query_pisis = text("""
                       INSERT INTO siaps_pisis (tipo_registro, id_familia, id_integrante, linea_pisis, origen_tabla)
                       VALUES (:tipo_registro, :id_familia, :id_integrante, :linea_pisis, :origen_tabla) ON CONFLICT (tipo_registro, clave_natural) 
        DO
                       UPDATE SET linea_pisis = EXCLUDED.linea_pisis, origen_tabla = EXCLUDED.origen_tabla, sincronizado_en = CURRENT_TIMESTAMP
                       """)

    try:
        viv_insertadas, int_insertados = 0, 0
        omitidos = {}
        batch_size = 2000

        with engine.begin() as conn:
            # 1. Familias (Tipo 2)
            for t in TABLAS_FAMILIA:
                if not table_exists(conn, t): continue
                rows = conn.execute(text(f"SELECT * FROM {t}")).mappings().fetchall()
                batch_p, omi = [], 0
                for row in rows:
                    p = transformar_registro_vivienda(dict(row))
                    if not p.get("c124"):
                        omi += 1
                        continue

                    batch_p.append({"tipo_registro": 2, "id_familia": p["c124"], "id_integrante": None,
                                    "linea_pisis": _construir_linea(p, 125), "origen_tabla": t})
                    viv_insertadas += 1

                    if len(batch_p) >= batch_size:
                        conn.execute(query_pisis, batch_p)
                        batch_p = []
                if batch_p:
                    conn.execute(query_pisis, batch_p)
                if omi: omitidos[t] = omi

            # 2. Integrantes (Tipo 3)
            for t in TABLAS_INTEGRANTE:
                if not table_exists(conn, t): continue
                rows = conn.execute(text(f"SELECT * FROM {t}")).mappings().fetchall()
                batch_p, omi = [], 0
                for row in rows:
                    p = transformar_registro_integrante(dict(row))
                    if not p.get("c118"):
                        omi += 1
                        continue

                    batch_p.append({"tipo_registro": 3, "id_familia": p["c117"], "id_integrante": p["c118"],
                                    "linea_pisis": _construir_linea(p, 119), "origen_tabla": t})
                    int_insertados += 1

                    if len(batch_p) >= batch_size:
                        conn.execute(query_pisis, batch_p)
                        batch_p = []
                if batch_p:
                    conn.execute(query_pisis, batch_p)
                if omi: omitidos[t] = omi

        msg = f"ETL Completado. Familias: {viv_insertadas} | Integrantes: {int_insertados}."
        if omitidos:
            msg += f" ⚠️ {sum(omitidos.values())} filas sin ID en Epicollect descartadas. Revise el diagnóstico."

        return jsonify({"status": "success", "msg": msg, "omitidos": omitidos}), 200
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


@poblacional_bp.route('/api/debug/epicollect_columnas', methods=['GET'])
def debug_columnas_epicollect():
    res = {}
    try:
        with engine.connect() as conn:
            for t in TABLAS_FAMILIA + TABLAS_INTEGRANTE:
                if not table_exists(conn, t):
                    res[t] = {"existe": False}
                    continue
                cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = :t"),
                                    {"t": t}).scalars().all()
                total = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar() or 0
                muestra = conn.execute(text(f"SELECT * FROM {t} LIMIT 1")).mappings().fetchone()

                info = {"existe": True, "total_filas": total, "columnas": cols}
                if muestra:
                    fila = dict(muestra)
                    if t in TABLAS_FAMILIA:
                        p = transformar_registro_vivienda(fila)
                        info["se_perderia_por_falta_de_id"] = not bool(p.get("c124"))
                    else:
                        p = transformar_registro_integrante(fila)
                        info["se_perderia_por_falta_de_id"] = not bool(p.get("c118"))
                res[t] = info
        return jsonify({"status": "success", "data": res}), 200
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


@poblacional_bp.route('/api/aps124ccfp/control', methods=['POST'])
def save_control():
    datos = {k: sanitizar_pisis(v) for k, v in request.json.items() if str(v).strip() != ""}
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM aps_control"))  # Solo mantener el último registro de control
            col = ", ".join(datos.keys())
            val = ", ".join([f":{k}" for k in datos.keys()])
            conn.execute(text(f"INSERT INTO aps_control ({col}) VALUES ({val})"), datos)
        return jsonify({"status": "success", "msg": "Parámetros de Control (Tipo 1) almacenados correctamente."}), 200
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


@poblacional_bp.route('/api/exportar/aps124ccfp', methods=['GET'])
def exportar_aps124ccfp():
    try:
        fecha_inicial = request.args.get('fecha_inicial', '2026-01-01')
        fecha_final = request.args.get('fecha_final', datetime.datetime.now().strftime('%Y-%m-%d'))
        t_id = request.args.get('tipo_id', 'NI')
        n_id = request.args.get('num_id', '822002459').zfill(12)
        fecha_corte = fecha_final.replace('-', '')

        lineas = []
        with engine.connect() as conn:
            ctrl = conn.execute(text("SELECT * FROM aps_control ORDER BY id DESC LIMIT 1")).fetchone()

            t2 = conn.execute(
                text("SELECT linea_pisis FROM siaps_pisis WHERE tipo_registro = 2 ORDER BY id ASC")).scalars().all()
            t3 = conn.execute(
                text("SELECT linea_pisis FROM siaps_pisis WHERE tipo_registro = 3 ORDER BY id ASC")).scalars().all()

            total_registros = len(t2) + len(t3)
            if total_registros == 0:
                return jsonify(
                    {"status": "error", "msg": "Debe ejecutar el Motor ETL primero. La tabla PISIS está vacía."}), 400

            # Tipo 1. Usa base de datos si está parametrizado, de lo contrario toma valores del input GET.
            if ctrl:
                lineas.append(
                    f"1|{ctrl.tipo_id_entidad}|{ctrl.num_id_entidad}|{ctrl.fecha_inicial}|{ctrl.fecha_final}|{total_registros}")
            else:
                lineas.append(f"1|{t_id}|{n_id}|{fecha_inicial}|{fecha_final}|{total_registros}")

            lineas.extend(t2)
            lineas.extend(t3)

        contenido = "\n".join(lineas)
        stream = io.BytesIO(contenido.encode('utf-8'))
        return send_file(stream, as_attachment=True, download_name=f"APS124CCFP{fecha_corte}{t_id}{n_id}.TXT",
                         mimetype='text/plain; charset=utf-8')
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500