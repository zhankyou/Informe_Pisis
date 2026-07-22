# -*- coding: utf-8 -*-
from sqlalchemy import text
from modulos.db_config import engine

def crear_tablas_poblacional():
    cols_vivienda = ", ".join([f"c{i} VARCHAR(255)" for i in range(125)])
    cols_integrante = ", ".join([f"c{i} VARCHAR(255)" for i in range(119)])

    tablas_sql = [
        """CREATE TABLE IF NOT EXISTS aps_control (
            id SERIAL PRIMARY KEY,
            tipo_registro SMALLINT DEFAULT 1,
            tipo_id_entidad VARCHAR(2) NOT NULL,
            num_id_entidad VARCHAR(12) NOT NULL,
            fecha_inicial DATE NOT NULL,
            fecha_final DATE NOT NULL,
            total_registros INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
        f"""CREATE TABLE IF NOT EXISTS aps_vivienda (
            id SERIAL PRIMARY KEY, 
            id_vivienda VARCHAR(26) NOT NULL, 
            id_familia VARCHAR(31) UNIQUE NOT NULL,
            {cols_vivienda}, 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
        f"""CREATE TABLE IF NOT EXISTS aps_integrante (
            id SERIAL PRIMARY KEY, 
            id_familia VARCHAR(31) NOT NULL, 
            id_integrante VARCHAR(53) UNIQUE NOT NULL,
            {cols_integrante}, 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
        """CREATE TABLE IF NOT EXISTS siaps_pisis (
            id SERIAL PRIMARY KEY,
            tipo_registro SMALLINT NOT NULL CHECK (tipo_registro IN (2, 3)),
            id_familia VARCHAR(31) NOT NULL,
            id_integrante VARCHAR(53),
            clave_natural VARCHAR(53) GENERATED ALWAYS AS (COALESCE(id_integrante, id_familia)) STORED,
            linea_pisis TEXT NOT NULL,
            origen_tabla VARCHAR(100),
            sincronizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (tipo_registro, clave_natural)
        );"""
    ]
    try:
        with engine.begin() as conn:
            for query in tablas_sql:
                conn.execute(text(query))
        print("✅ Estructura poblacional (SI-APS) verificada correctamente.")
    except Exception as e:
        print(f"❌ Error creando esquemas SI-APS: {e}")

if __name__ == "__main__":
    crear_tablas_poblacional()