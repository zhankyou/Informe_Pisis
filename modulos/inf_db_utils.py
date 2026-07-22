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
    """Verifica si una tabla existe en el esquema public de la base de datos"""
    query = """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = :tname
        )
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), {"tname": str(table_name).lower()})
            return bool(result.scalar())
    except Exception as e:
        print(f"[*] Error crítico en table_exists: {e}")
        return False

def find_column(table_name, column_name):
    """
    Solución definitiva: Extrae el mapa de columnas y evalúa la lista en memoria mediante Python.
    Evita excepciones de casteo de tipos (ARRAY vs sql_identifier) en PostgreSQL.
    """
    nombres = column_name if isinstance(column_name, (list, tuple)) else [column_name]
    query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = :tname
    """
    try:
        with engine.connect() as conn:
            # Trae todas las columnas de la tabla a la memoria
            result = conn.execute(text(query), {"tname": str(table_name).lower()})
            columnas_db = [str(row[0]).lower() for row in result.fetchall()]
            
            # Realiza el match flexible en Python iterando sobre las posibles variaciones
            for nombre in nombres:
                if str(nombre).lower() in columnas_db:
                    return str(nombre).lower()  # Retorna el nombre exacto de la columna en la BD
                    
        return False
    except Exception as e:
        print(f"[*] Error crítico en find_column: {e}")
        return False
