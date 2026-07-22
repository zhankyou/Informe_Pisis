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

def get_count(query, params=None):
    """Ejecuta una consulta COUNT y retorna el valor escalar"""
    try:
        with engine.connect() as conn:
            if params:
                result = conn.execute(text(query), params)
            else:
                result = conn.execute(text(query))
            return result.scalar() or 0
    except Exception as e:
        print(f"[*] Error crítico en get_count: {e}")
        return 0

def table_exists(table_name):
    """Verifica si una tabla existe en la base de datos"""
    query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = :table_name
        )
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), {"table_name": table_name})
            return result.scalar()
    except Exception as e:
        print(f"[*] Error crítico en table_exists: {e}")
        return False

def find_column(table_name, column_name):
    """Verifica si una columna (o una de varias) existe dentro de una tabla. Retorna el nombre de la columna encontrada o False."""
    # Soporte para iterar si se envía una lista de posibles nombres (Ej: ['eapb', 'eps', 'aseguradora'])
    nombres = column_name if isinstance(column_name, (list, tuple)) else [column_name]
    
    query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = :table_name 
        AND column_name = :column_name
    """
    try:
        with engine.connect() as conn:
            for nombre in nombres:
                result = conn.execute(text(query), {"table_name": table_name, "column_name": nombre}).scalar()
                if result:
                    return result # Retorna el String (equivalente a True) para ensamblajes dinámicos
            return False
    except Exception as e:
        print(f"[*] Error crítico en find_column: {e}")
        return False
