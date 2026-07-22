# -*- coding: utf-8 -*-
import os
import io
import pandas as pd
import unicodedata
import re
from flask import Blueprint, request, jsonify, send_file
from sqlalchemy import text
from modulos.db_config import engine

cargador_bp = Blueprint('cargador', __name__)


def sanitizar_pisis(texto):
    if pd.isna(texto) or not isinstance(texto, str):
        return texto
    texto = str(texto).upper()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    texto = texto.replace('N°', 'NO').replace('°', 'NO').replace('"', '')
    texto = re.sub(r'[^A-Z0-9\s/.-]', '', texto)
    texto = re.sub(r'\s{2,}', ' ', texto).strip()
    return texto


@cargador_bp.route('/api/cargador/plantilla/<tabla>', methods=['GET'])
def descargar_plantilla(tabla):
    formato = request.args.get('formato', 'excel').lower()

    estructuras = {
        'ser_incorporacion': {
            'cols': ['resolucion_origen', 'nit_entidad', 'id_recurso', 'ind_incorporacion', 'cod_tipo_acto', 'num_acto',
                     'fecha_incorporacion', 'valor_incorporado'],
            'ejemplo': ['RES_2026', '822002459', 'ID2069625612', 'I', '4', 'RES-123', '2026-01-15', '15000000.00']
        },
        'ser_contratos': {
            'cols': ['resolucion_origen', 'nit_entidad', 'id_recurso', 'ind_actualizacion', 'cod_tipo_contrato',
                     'num_contrato', 'fecha_contrato', 'fecha_terminacion', 'objeto', 'valor_contrato',
                     'tipo_id_contratista', 'num_id_contratista', 'nombre_contratista', 'tipo_id_supervisor',
                     'num_id_supervisor', 'nombre_supervisor'],
            'ejemplo': ['RES_2026', '822002459', 'ID2069625612', 'I', '1', 'CPS-001', '2026-02-01', '2026-12-31',
                        'PRESTACION DE SERVICIOS PROFESIONALES', '34000000.00', 'CC', '1121962500', 'ANGIE NATALIA',
                        'CC', '1001234567', 'SUPERVISOR EJEMPLO']
        },
        'ser_polizas': {
            'cols': ['resolucion_origen', 'nit_entidad', 'id_recurso', 'ind_poliza', 'cod_tipo_contrato',
                     'num_contrato', 'num_poliza', 'fecha_poliza'],
            'ejemplo': ['RES_2026', '822002459', 'ID2069625612', 'I', '1', 'CPS-001', 'POL-998877', '2026-02-05']
        },
        'ser_seguimiento': {
            'cols': ['resolucion_origen', 'nit_entidad', 'id_recurso', 'ind_seguimiento', 'cod_tipo_contrato',
                     'num_contrato', 'cod_tipo_acta', 'num_acta', 'fecha_acta', 'valor_ejecutado', 'valor_pagado',
                     'porcentaje_ejecucion', 'conclusiones'],
            'ejemplo': ['RES_2026', '822002459', 'ID2069625612', 'I', '1', 'CPS-001', '1', 'ACT-001', '2026-03-01',
                        '3400000.00', '3400000.00', '10.00', 'CUMPLIMIENTO DE METAS AL 10 POR CIENTO']
        },
        'ser_reintegro_no_ejecutado': {
            'cols': ['resolucion_origen', 'nit_entidad', 'id_recurso', 'ind_reintegro', 'cod_tipo_acto', 'num_acto',
                     'fecha_acto', 'cod_entidad_reintegro', 'nit_banco', 'num_cuenta', 'valor_reintegrado',
                     'fecha_consignacion', 'portafolio'],
            'ejemplo': ['RES_2026', '822002459', 'ID2069625612', 'I', '4', 'RES-123', '2026-01-15', '2', '860000000',
                        '123456789012', '500000.00', '2026-04-10', '496']
        },
        'ser_reintegro_rendimientos': {
            'cols': ['resolucion_origen', 'nit_entidad', 'id_recurso', 'ind_reintegro', 'cod_tipo_acto', 'num_acto',
                     'fecha_acto', 'cod_entidad_reintegro', 'nit_banco', 'num_cuenta', 'valor_reintegrado',
                     'fecha_consignacion', 'portafolio'],
            'ejemplo': ['RES_2026', '822002459', 'ID2069625612', 'I', '4', 'RES-123', '2026-01-15', '2', '860000000',
                        '123456789012', '12500.50', '2026-04-10', '496']
        }
    }

    if tabla not in estructuras:
        return jsonify({"status": "error", "msg": "Tabla no válida para plantilla"}), 400

    config = estructuras[tabla]
    df = pd.DataFrame([config['ejemplo']], columns=config['cols'])

    output = io.BytesIO()

    if formato == 'txt':
        df.to_csv(output, sep='|', index=False, encoding='utf-8')
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=f"Plantilla_{tabla}.txt", mimetype="text/plain")
    else:
        # Se asegura de usar openpyxl o xlsxwriter según disponibilidad
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Plantilla_PISIS')
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=f"Plantilla_{tabla}.xlsx",
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@cargador_bp.route('/api/cargador/preview/<tabla>', methods=['POST'])
def preview_archivo(tabla):
    if 'archivo' not in request.files:
        return jsonify({"status": "error", "msg": "No se proporcionó ningún archivo."}), 400

    file = request.files['archivo']
    filename = file.filename.lower()

    try:
        if filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file, dtype=str)
        elif filename.endswith('.csv'):
            df = pd.read_csv(file, dtype=str, sep=None, engine='python')
        elif filename.endswith('.txt'):
            df = pd.read_csv(file, dtype=str, sep='|')
        else:
            return jsonify({"status": "error", "msg": "Formato no soportado. Use Excel, CSV o TXT."}), 400

        df.fillna("", inplace=True)
        for col in df.columns:
            df[col] = df[col].apply(sanitizar_pisis)

        data = df.to_dict(orient='records')
        return jsonify({"status": "success", "data": data, "columns": df.columns.tolist()}), 200
    except Exception as e:
        return jsonify({"status": "error", "msg": f"Error procesando archivo: {str(e)}"}), 500


@cargador_bp.route('/api/cargador/confirm/<tabla>', methods=['POST'])
def confirm_carga(tabla):
    payload = request.json
    if not payload or not isinstance(payload, list):
        return jsonify({"status": "error", "msg": "Payload inválido para carga masiva."}), 400

    try:
        with engine.begin() as conn:
            for row in payload:
                datos_limpios = {k: v for k, v in row.items() if v != ""}
                if not datos_limpios: continue

                if 'id_recurso' in datos_limpios:
                    estado = conn.execute(text("SELECT estado FROM ser_recursos WHERE id_recurso = :id"),
                                          {"id": datos_limpios['id_recurso']}).scalar()
                    if estado == 'FINALIZADA':
                        return jsonify({"status": "error",
                                        "msg": f"Resolución {datos_limpios['id_recurso']} está FINALIZADA. Carga abortada."}), 403

                columnas = ", ".join(datos_limpios.keys())
                valores = ", ".join([f":{k}" for k in datos_limpios.keys()])
                query = text(f"INSERT INTO {tabla} ({columnas}) VALUES ({valores})")
                conn.execute(query, datos_limpios)

        return jsonify({"status": "success", "msg": f"Se insertaron {len(payload)} registros correctamente."}), 200
    except Exception as e:
        error_msg = str(getattr(e, 'orig', e))
        return jsonify({"status": "error", "msg": f"Fallo en base de datos: {error_msg}"}), 500