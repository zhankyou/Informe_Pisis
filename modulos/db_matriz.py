# -*- coding: utf-8 -*-
import logging
from sqlalchemy import text
from modulos.db_config import engine

def inicializar_tabla_pagos():
    """
    Crea o verifica la existencia de la tabla 'pagos' para el módulo de matriz de ponderación.
    Cualquier adición de columnas debe realizarse en este script.
    """
    query_create = text("""
        CREATE TABLE IF NOT EXISTS pagos (
            id SERIAL PRIMARY KEY,
            categoria VARCHAR(50) NOT NULL,
            nombre_completo VARCHAR(150) NOT NULL,
            numero_documento VARCHAR(20) NOT NULL,
            numero_contrato VARCHAR(20) NOT NULL,
            cuenta VARCHAR(50) NOT NULL,
            fecha_inicio DATE NOT NULL,
            fecha_fin DATE NOT NULL,
            valor_contrato NUMERIC(17,2) NOT NULL,
            valor_cobrar NUMERIC(17,2) NOT NULL,
            observaciones VARCHAR(500),
            detalles_items TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    try:
        with engine.begin() as conn:
            conn.execute(query_create)
            logging.info("[DB] Tabla 'pagos' inicializada correctamente.")
    except Exception as e:
        logging.error(f"[DB ERROR] Fallo al inicializar tabla pagos: {e}")