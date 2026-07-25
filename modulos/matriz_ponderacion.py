# -*- coding: utf-8 -*-
import os
import logging
from flask import Blueprint, request, jsonify
from sqlalchemy import text
from modulos.db_config import engine
from modulos.db_matriz import inicializar_tabla_pagos

ponderacion_bp = Blueprint('ponderacion', __name__)

# Llamada al inicializador externo de la base de datos
inicializar_tabla_pagos()


@ponderacion_bp.route('/api/ponderacion', methods=['POST'])
def guardar_registro():
    data = request.json
    query = text("""
                 INSERT INTO pagos
                 (categoria, nombre_completo, numero_documento, numero_contrato, cuenta, fecha_inicio, fecha_fin,
                  valor_contrato, valor_cobrar, observaciones, detalles_items)
                 VALUES (:categoria, :nombre_completo, :numero_documento, :numero_contrato, :cuenta, :fecha_inicio,
                         :fecha_fin, :valor_contrato, :valor_cobrar, :observaciones, :detalles_items)
                 """)
    try:
        with engine.begin() as conn:
            conn.execute(query, {
                "categoria": data.get('categoria'),
                "nombre_completo": data.get('nombre_completo', '').upper(),
                "numero_documento": data.get('numero_documento'),
                "numero_contrato": data.get('numero_contrato', '').upper(),
                "cuenta": data.get('cuenta'),
                "fecha_inicio": data.get('fecha_inicio'),
                "fecha_fin": data.get('fecha_fin'),
                "valor_contrato": float(data.get('valor_contrato', 0)),
                "valor_cobrar": float(data.get('valor_cobrar', 0)),
                "observaciones": data.get('observaciones', ''),
                "detalles_items": data.get('detalles_items', '[]')
            })
        return jsonify({"status": "success", "msg": "Registro guardado correctamente en la tabla Pagos."})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


@ponderacion_bp.route('/api/ponderacion/<int:id_registro>', methods=['PUT'])
def actualizar_registro(id_registro):
    data = request.json
    query = text("""
                 UPDATE pagos
                 SET nombre_completo  = :nombre_completo,
                     numero_documento = :numero_documento,
                     numero_contrato  = :numero_contrato,
                     cuenta           = :cuenta,
                     fecha_inicio     = :fecha_inicio,
                     fecha_fin        = :fecha_fin,
                     valor_contrato   = :valor_contrato,
                     valor_cobrar     = :valor_cobrar,
                     observaciones    = :observaciones,
                     detalles_items   = :detalles_items
                 WHERE id = :id
                 """)
    try:
        with engine.begin() as conn:
            conn.execute(query, {
                "nombre_completo": data.get('nombre_completo', '').upper(),
                "numero_documento": data.get('numero_documento'),
                "numero_contrato": data.get('numero_contrato', '').upper(),
                "cuenta": data.get('cuenta'),
                "fecha_inicio": data.get('fecha_inicio'),
                "fecha_fin": data.get('fecha_fin'),
                "valor_contrato": float(data.get('valor_contrato', 0)),
                "valor_cobrar": float(data.get('valor_cobrar', 0)),
                "observaciones": data.get('observaciones', ''),
                "detalles_items": data.get('detalles_items', '[]'),
                "id": id_registro
            })
        return jsonify({"status": "success", "msg": "Registro actualizado correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


@ponderacion_bp.route('/api/ponderacion/<categoria>', methods=['GET'])
def obtener_registros(categoria):
    busqueda = request.args.get('q', '').strip().upper()

    where_sql = "WHERE categoria = :categoria"
    params = {"categoria": categoria}

    if busqueda:
        where_sql += " AND (nombre_completo LIKE :q OR numero_documento LIKE :q OR numero_contrato LIKE :q)"
        params["q"] = f"%{busqueda}%"

    query = text(f"SELECT * FROM pagos {where_sql} ORDER BY created_at DESC")

    try:
        with engine.connect() as conn:
            result = conn.execute(query, params).mappings().all()
            data = [dict(row) for row in result]

            for row in data:
                row['fecha_inicio'] = str(row['fecha_inicio'])
                row['fecha_fin'] = str(row['fecha_fin'])
                row['created_at'] = str(row['created_at'])
                row['valor_contrato'] = float(row['valor_contrato'])
                row['valor_cobrar'] = float(row['valor_cobrar'])
                row['detalles_items'] = row['detalles_items'] or '[]'

        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500