# -*- coding: utf-8 -*-
from sqlalchemy import text
from modulos.db_config import engine

def table_exists(t_name):
    try:
        with engine.connect() as conn:
            return conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :t)"), {"t": t_name}).scalar()
    except Exception:
        return False

def col_exists(t_name, c_name):
    c_clean = c_name.strip('"')
    try:
        with engine.connect() as conn:
            return conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = :t AND column_name = :c)"), {"t": t_name, "c": c_clean}).scalar()
    except Exception:
        return False

def find_column(t_name, keywords):
    """Búsqueda dinámica de la columna real basada en fragmentos clave."""
    try:
        with engine.connect() as conn:
            cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = :t"), {"t": t_name}).fetchall()
            col_names = [c[0] for c in cols]
            for k in keywords:
                for c in col_names:
                    if k.lower() in c.lower():
                        return f'"{c}"'
    except Exception:
        pass
    return None

def get_count(query):
    try:
        with engine.connect() as conn:
            res = conn.execute(text(query)).scalar()
            return res if res is not None else 0
    except Exception:
        return 0

def get_list(query):
    try:
        with engine.connect() as conn:
            res = conn.execute(text(query)).mappings().fetchall()
            return [dict(r) for r in res]
    except Exception:
        return []