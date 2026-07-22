# -*- coding: utf-8 -*-
from sqlalchemy import text
from modulos.db_config import engine


def crear_tablas_cronograma():
    tablas_sql = [
        """CREATE TABLE IF NOT EXISTS cro_actividades
        (
            id
            SERIAL
            PRIMARY
            KEY,
            nombre
            VARCHAR
           (
            100
           ) NOT NULL,
            descripcion VARCHAR
           (
               255
           )
            );""",
        """CREATE TABLE IF NOT EXISTS cro_personas
        (
            id
            SERIAL
            PRIMARY
            KEY,
            documento
            VARCHAR
           (
            20
           ) UNIQUE NOT NULL,
            nombre_completo VARCHAR
           (
               150
           ) NOT NULL,
            telefono VARCHAR
           (
               20
           )
            );""",
        """CREATE TABLE IF NOT EXISTS cro_programacion
        (
            id
            SERIAL
            PRIMARY
            KEY,
            id_actividad
            INT
            REFERENCES
            cro_actividades
           (
            id
           ) ON DELETE CASCADE,
            id_persona INT REFERENCES cro_personas
           (
               id
           )
             ON DELETE CASCADE,
            territorio VARCHAR
           (
               100
           ) NOT NULL,
            fecha DATE NOT NULL,
            hora_inicio TIME NOT NULL,
            hora_fin TIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""",
        """CREATE TABLE IF NOT EXISTS cro_vacunacion
        (
            id
            SERIAL
            PRIMARY
            KEY,
            fecha
            DATE
            NOT
            NULL,
            dupla
            INT
            NOT
            NULL,
            lugar
            VARCHAR
           (
            200
           ) NOT NULL,
            horario VARCHAR
           (
               100
           ),
            vacunador TEXT NOT NULL,
            tel_vacunador TEXT,
            anotador TEXT NOT NULL,
            tel_anotador TEXT,
            profesional_valoracion TEXT,
            tel_profesional TEXT,
            desistimientos TEXT,
            tel_desistimientos TEXT,
            observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""",
        """CREATE TABLE IF NOT EXISTS cro_diario_config
           (
               fecha
               DATE
               PRIMARY
               KEY,
               observaciones
               TEXT,
               updated_at
               TIMESTAMP
               DEFAULT
               CURRENT_TIMESTAMP
           );"""
    ]

    columnas_esperadas = {
        "cro_programacion": [("actividad_desc", "VARCHAR(255)")],
        "cro_vacunacion": [("hora_inicio", "TIME"), ("hora_fin", "TIME")],
        "cro_diario_config": [
            ("entrega_nombres", "TEXT"), ("entrega_telefonos", "TEXT"),
            ("archivo_hora_inicio", "TIME"), ("archivo_hora_fin", "TIME"),
            ("papeleria_nombres", "VARCHAR(255)"), ("papeleria_telefonos", "VARCHAR(100)"),
            ("cargue_nombres", "VARCHAR(255)"), ("cargue_telefonos", "VARCHAR(100)"),
            ("validacion_nombres", "VARCHAR(255)"), ("validacion_telefonos", "VARCHAR(100)")
        ]
    }

    # Alteración a TEXT para soportar múltiples registros concatenados (Límite 5)
    conversiones_text = [
        "ALTER TABLE cro_vacunacion ALTER COLUMN vacunador TYPE TEXT;",
        "ALTER TABLE cro_vacunacion ALTER COLUMN tel_vacunador TYPE TEXT;",
        "ALTER TABLE cro_vacunacion ALTER COLUMN anotador TYPE TEXT;",
        "ALTER TABLE cro_vacunacion ALTER COLUMN tel_anotador TYPE TEXT;",
        "ALTER TABLE cro_vacunacion ALTER COLUMN profesional_valoracion TYPE TEXT;",
        "ALTER TABLE cro_vacunacion ALTER COLUMN tel_profesional TYPE TEXT;",
        "ALTER TABLE cro_vacunacion ALTER COLUMN desistimientos TYPE TEXT;",
        "ALTER TABLE cro_vacunacion ALTER COLUMN tel_desistimientos TYPE TEXT;"
    ]

    try:
        # 1. Creación de tablas base (Transacción estándar)
        with engine.begin() as conn:
            for query in tablas_sql:
                conn.execute(text(query))

        # 2. Ejecución de DDL crítico (Inyección de AUTOCOMMIT desde la instanciación)
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn_auto:
            for tabla, columnas in columnas_esperadas.items():
                for col_nombre, col_tipo in columnas:
                    check_query = text(
                        "SELECT column_name FROM information_schema.columns WHERE table_name = :tbl AND column_name = :col")
                    existe = conn_auto.execute(check_query, {"tbl": tabla, "col": col_nombre}).fetchone()
                    if not existe:
                        try:
                            conn_auto.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {col_nombre} {col_tipo};"))
                        except Exception:
                            pass

            for conv in conversiones_text:
                try:
                    conn_auto.execute(text(conv))
                except Exception as e:
                    print(f"[*] Nota (alteración omitida): {e}")

        print("✅ Esquema Cronograma actualizado. Tipo de dato TEXT aplicado correctamente.")
    except Exception as e:
        print(f"❌ Error esquema Cronograma: {e}")


if __name__ == "__main__":
    crear_tablas_cronograma()