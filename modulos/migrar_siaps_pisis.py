# -*- coding: utf-8 -*-
"""
Migración puntual: agrega la tabla siaps_pisis a una base de datos que ya
tenía aps_vivienda / aps_integrante creadas con el esquema anterior.

Uso: python -m modulos.migrar_siaps_pisis
(Es idempotente: si la tabla ya existe, no hace nada — CREATE TABLE IF NOT EXISTS).
"""
from sqlalchemy import text
from modulos.db_config import engine

DDL_SIAPS_PISIS = """
CREATE TABLE IF NOT EXISTS siaps_pisis (
    id SERIAL PRIMARY KEY,
    tipo_registro SMALLINT NOT NULL CHECK (tipo_registro IN (2, 3)),
    id_familia VARCHAR(31) NOT NULL,
    id_integrante VARCHAR(53),
    clave_natural VARCHAR(53) GENERATED ALWAYS AS (COALESCE(id_integrante, id_familia)) STORED,
    linea_pisis TEXT NOT NULL,
    origen_tabla VARCHAR(100),
    sincronizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tipo_registro, clave_natural)
);
"""


def migrar():
    with engine.begin() as conn:
        conn.execute(text(DDL_SIAPS_PISIS))
    print("✅ Tabla siaps_pisis verificada/creada.")


if __name__ == "__main__":
    migrar()