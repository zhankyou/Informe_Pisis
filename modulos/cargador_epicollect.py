# -*- coding: utf-8 -*-
import pandas as pd
from flask import Blueprint, request, jsonify
from modulos.db_config import engine

epicollect_bp = Blueprint('epicollect', __name__)


@epicollect_bp.route('/api/epicollect/upload/<tipo>', methods=['POST'])
def upload_epicollect(tipo):
    if 'archivo' not in request.files:
        return jsonify({"status": "error", "msg": "No se adjuntó archivo."}), 400

    file = request.files['archivo']
    tabla_destino = "caracterizacion_si_aps_familiar_2026" if tipo == 'familias' else "caracterizacion_si_aps_individual_2026"

    try:
        if file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file, dtype=str)
        else:
            df = pd.read_csv(file, dtype=str, sep=None, engine='python')

        df.columns = [c.strip().lower().replace(" ", "_").replace(".", "") for c in df.columns]
        df.fillna("", inplace=True)

        df.to_sql(tabla_destino, engine, if_exists='replace', index=False)
        return jsonify(
            {"status": "success", "msg": f"Archivo {tipo} cargado en {tabla_destino} ({len(df)} registros)."}), 200
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500