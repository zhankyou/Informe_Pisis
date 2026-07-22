# -*- coding: utf-8 -*-
from sqlalchemy import text
from modulos.db_config import engine

def get_list(query, params=None):
    """Ejecuta una consulta y retorna una lista de diccionarios (Compatible con SQLAlchemy 2.0+)"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            return [dict(row) for row in result.mappings().fetchall()]
    except Exception as e:
        print(f"[*] Error crítico en get_list: {e}")
        return []

def get_record(query, params=None):
    """Ejecuta una consulta y retorna un único diccionario"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            row = result.mappings().fetchone()
            return dict(row) if row else None
    except Exception as e:
        print(f"[*] Error crítico en get_record: {e}")
        return None

def execute_query(query, params=None):
    """Ejecuta operaciones DML (INSERT, UPDATE, DELETE)"""
    try:
        with engine.begin() as conn:
            conn.execute(text(query), params or {})
            return True
    except Exception as e:
        print(f"[*] Error crítico en execute_query: {e}")
        return False

def get_count(query, params=None):
    """Ejecuta una consulta COUNT y retorna el valor numérico entero"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            valor = result.scalar()
            return int(valor) if valor else 0
    except Exception as e:
        print(f"[*] Error crítico en get_count: {e}")
        return 0

def table_exists(table_name):
    """Verifica de forma agnóstica si una tabla existe en el esquema de la base de datos"""
    query = """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = :table_name
        )
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), {"table_name": table_name})
            return bool(result.scalar())
    except Exception as e:
        print(f"[*] Error crítico en table_exists: {e}")
        return False

def find_column(table_name, column_name):
    """
    Verifica si una columna (o una lista de posibles nombres) existe en una tabla.
    Itera secuencialmente para evitar el error de casteo ARRAY de PostgreSQL.
    Retorna el nombre exacto de la columna encontrada como String o False.
    """
    query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = :table_name 
        AND column_name = :col_name
    """
    try:
        # Aseguramos que siempre sea un iterable para evaluar
        nombres = column_name if isinstance(column_name, (list, tuple)) else [column_name]
        
        with engine.connect() as conn:
            for nombre in nombres:
                result = conn.execute(text(query), {
                    "table_name": str(table_name), 
                    "col_name": str(nombre)
                }).scalar()
                if result:
                    return str(result)
                    
        return False
    except Exception as e:
        print(f"[*] Error crítico en find_column: {e}")
        return False
