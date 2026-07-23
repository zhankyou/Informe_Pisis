# -*- coding: utf-8 -*-
from sqlalchemy import text
from modulos.db_config import engine

def get_list(query, params=None):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            return [dict(row) for row in result.mappings().fetchall()]
    except Exception as e:
        print(f"[*] Error crítico en get_list: {e}")
        return []

def get_record(query, params=None):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            row = result.mappings().fetchone()
            return dict(row) if row else None
    except Exception as e:
        print(f"[*] Error crítico en get_record: {e}")
        return None

def execute_query(query, params=None):
    try:
        with engine.begin() as conn:
            conn.execute(text(query), params or {})
            return True
    except Exception as e:
        return False

def get_count(query, params=None):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            valor = result.scalar()
            return int(valor) if valor else 0
    except Exception as e:
        print(f"[*] Error crítico en get_count: {e}")
        return 0

def table_exists(table_name):
    """Bypasses information_schema limitations using direct querying (Active Probing)"""
    try:
        with engine.connect() as conn:
            conn.execute(text(f'SELECT 1 FROM "{table_name}" LIMIT 1'))
        return True
    except Exception:
        return False

def find_column(table_name, column_name):
    """Busca la columna ejecutando un test real, evadiendo restricciones de metadatos en la nube"""
    nombres = column_name if isinstance(column_name, (list, tuple)) else [column_name]
    for col in nombres:
        try:
            with engine.connect() as conn:
                conn.execute(text(f'SELECT "{col}" FROM "{table_name}" LIMIT 1'))
            return col
        except Exception:
            continue
    return False
