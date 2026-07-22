# -*- coding: utf-8 -*-
import os
from flask import Blueprint, request, jsonify, send_from_directory
from sqlalchemy import text
from modulos.db_config import engine

consultas_bp = Blueprint('consultas', __name__)
DIR_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@consultas_bp.route('/consultas_ui')
def vista_consultas():
    return send_from_directory(DIR_BASE, "consultas.html")


@consultas_bp.route('/api/consultas/<tabla>', methods=['GET'])
def obtener_datos(tabla):
    tablas_validas = [
        'ser_control', 'ser_incorporacion', 'ser_contratos',
        'ser_polizas', 'ser_seguimiento', 'ser_reintegro_no_ejecutado',
        'ser_reintegro_rendimientos'
    ]
    if tabla not in tablas_validas:
        return jsonify({"status": "error", "msg": "Tabla no válida"}), 400

    id_recurso = request.args.get('id_recurso', '').strip()
    num_contrato = request.args.get('num_contrato', '').strip()
    num_acto = request.args.get('num_acto', '').strip()

    where_clauses = []
    params = {}

    if id_recurso and tabla != 'ser_control':
        where_clauses.append("id_recurso = :id_recurso")
        params['id_recurso'] = id_recurso

    if num_contrato and tabla in ['ser_contratos', 'ser_polizas', 'ser_seguimiento']:
        where_clauses.append("num_contrato ILIKE :num_contrato")
        params['num_contrato'] = f"%{num_contrato}%"

    if num_acto and tabla in ['ser_incorporacion', 'ser_reintegro_no_ejecutado', 'ser_reintegro_rendimientos']:
        where_clauses.append("num_acto ILIKE :num_acto")
        params['num_acto'] = f"%{num_acto}%"

    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    query = text(f"SELECT * FROM {tabla}{where_sql} ORDER BY created_at DESC")

    try:
        with engine.connect() as conn:
            result = conn.execute(query, params).mappings().all()
            data = [dict(row) for row in result]

            for row in data:
                for k, v in row.items():
                    if hasattr(v, 'isoformat'):
                        row[k] = v.isoformat()[:10]
                    elif v is not None and type(v).__name__ == 'Decimal':
                        row[k] = float(v)

        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


@consultas_bp.route('/api/consultas/<tabla>/<int:id_registro>', methods=['DELETE'])
def eliminar_registro(tabla, id_registro):
    tablas_validas = [
        'ser_control', 'ser_incorporacion', 'ser_contratos',
        'ser_polizas', 'ser_seguimiento', 'ser_reintegro_no_ejecutado',
        'ser_reintegro_rendimientos'
    ]
    if tabla not in tablas_validas:
        return jsonify({"status": "error", "msg": "Tabla no válida"}), 400

    try:
        with engine.begin() as conn:
            # Validar si el recurso está bloqueado antes de eliminar (excepto ser_control)
            if tabla != 'ser_control':
                rec_query = text(f"SELECT id_recurso FROM {tabla} WHERE id = :id")
                id_rec = conn.execute(rec_query, {"id": id_registro}).scalar()
                if id_rec:
                    est_query = text("SELECT estado FROM ser_recursos WHERE id_recurso = :id_rec")
                    estado = conn.execute(est_query, {"id_rec": id_rec}).scalar()
                    if estado == 'FINALIZADA':
                        return jsonify({"status": "error", "msg": "Resolución FINALIZADA. Operación denegada."}), 403

            query = text(f"DELETE FROM {tabla} WHERE id = :id")
            result = conn.execute(query, {"id": id_registro})
            if result.rowcount == 0:
                return jsonify({"status": "error", "msg": "Registro no encontrado."}), 404

        return jsonify({"status": "success", "msg": "Registro eliminado correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500