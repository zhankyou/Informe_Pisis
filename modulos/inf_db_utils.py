# -*- coding: utf-8 -*-
from sqlalchemy import text
from modulos.db_config import engine

def get_list(query, params=None):
    """Ejecuta una consulta y retorna una lista de diccionarios (Compatible con SQLAlchemy 2.0+)"""
    try:
        with engine.connect() as conn:
            if params:
                result = conn.execute(text(query), params)
            else:
                result = conn.execute(text(query))
            # .mappings() es obligatorio en producción para evitar ValueError de Tuplas
            return [dict(row) for row in result.mappings().fetchall()]
    except Exception as e:
        print(f"[*] Error crítico en get_list: {e}")
        return []

def get_record(query, params=None):
    """Ejecuta una consulta y retorna un único diccionario"""
    try:
        with engine.connect() as conn:
            if params:
                result = conn.execute(text(query), params)
            else:
                result = conn.execute(text(query))
            row = result.mappings().fetchone()
            return dict(row) if row else None
    except Exception as e:
        print(f"[*] Error crítico en get_record: {e}")
        return None

def execute_query(query, params=None):
    """Ejecuta operaciones DML (INSERT, UPDATE, DELETE)"""
    try:
        with engine.begin() as conn:
            if params:
                conn.execute(text(query), params)
            else:
                conn.execute(text(query))
            return True
    except Exception as e:
        print(f"[*] Error crítico en execute_query: {e}")
        return False
