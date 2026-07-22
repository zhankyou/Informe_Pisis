# -*- coding: utf-8 -*-
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
os.environ["PGCLIENTENCODING"] = "utf-8"

def verificar_crear_bd_local():
    db_user = os.getenv("DB_USER", "postgres")
    db_pass = os.getenv("DB_PASSWORD", "1234")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "aps_local_db")

    engine_postgres = create_engine(f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/postgres", isolation_level="AUTOCOMMIT")
    try:
        with engine_postgres.connect() as conn:
            existe = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")).fetchone()
            if not existe:
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"⚙️ Base de datos '{db_name}' creada automáticamente.")
    except Exception as e:
        print("⚠️ No se pudo verificar la creación de la DB local. Verifique credenciales.")

def get_engine(admin=False):
    ambiente = os.getenv("AMBIENTE", "local").strip().lower()
    if ambiente == "produccion":
        db_user = os.getenv("DB_USER_AIVEN")
        db_pass = os.getenv("DB_PASSWORD_AIVEN")
        db_host = os.getenv("DB_HOST_AIVEN")
        db_port = os.getenv("DB_PORT_AIVEN")
        db_name = os.getenv("DB_NAME_AIVEN")
        return create_engine(f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?sslmode=require&client_encoding=utf8")
    else:
        db_user = os.getenv("DB_USER", "postgres")
        db_pass = os.getenv("DB_PASSWORD", "1234")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = "postgres" if admin else os.getenv("DB_NAME", "aps_local_db")
        return create_engine(f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?client_encoding=utf8", isolation_level="AUTOCOMMIT" if admin else "READ COMMITTED")

def resetear_y_crear_tablas_financieras():
    if os.getenv("AMBIENTE", "local").strip().lower() != "produccion":
        verificar_crear_bd_local()

    engine = get_engine()

    query_drop = """
        DROP TABLE IF EXISTS
            ser_recursos, ser_control, ser_incorporacion, ser_contratos, 
            ser_polizas, ser_seguimiento, ser_reintegro_no_ejecutado, ser_reintegro_rendimientos
        CASCADE;
    """

    tablas_sql = [
        """CREATE TABLE ser_recursos (
            id_recurso VARCHAR(12) PRIMARY KEY, 
            descripcion VARCHAR(150) NOT NULL, 
            estado VARCHAR(20) DEFAULT 'ACTIVA',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""",
        """CREATE TABLE ser_control (id SERIAL PRIMARY KEY, resolucion_origen VARCHAR(50) NOT NULL, tipo_id_entidad VARCHAR(2), num_id_entidad VARCHAR(12), fecha_inicial DATE, fecha_final DATE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);""",
        """CREATE TABLE ser_incorporacion (id SERIAL PRIMARY KEY, resolucion_origen VARCHAR(50) NOT NULL, id_recurso VARCHAR(12), nit_entidad VARCHAR(9), ind_incorporacion VARCHAR(2), cod_tipo_acto VARCHAR(1), num_acto VARCHAR(20), fecha_incorporacion DATE, valor_incorporado NUMERIC(17, 2), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);""",
        """CREATE TABLE ser_contratos (id SERIAL PRIMARY KEY, resolucion_origen VARCHAR(50) NOT NULL, id_recurso VARCHAR(12), nit_entidad VARCHAR(9), ind_actualizacion VARCHAR(2), cod_tipo_contrato VARCHAR(1), num_contrato VARCHAR(20), fecha_contrato DATE, fecha_terminacion DATE, objeto VARCHAR(500), valor_contrato NUMERIC(17, 2), tipo_id_contratista VARCHAR(2), num_id_contratista VARCHAR(17), nombre_contratista VARCHAR(100), tipo_id_supervisor VARCHAR(2), num_id_supervisor VARCHAR(17), nombre_supervisor VARCHAR(100), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);""",
        """CREATE TABLE ser_polizas (id SERIAL PRIMARY KEY, resolucion_origen VARCHAR(50) NOT NULL, id_recurso VARCHAR(12), nit_entidad VARCHAR(9), ind_poliza VARCHAR(2), cod_tipo_contrato VARCHAR(1), num_contrato VARCHAR(20), num_poliza VARCHAR(20), fecha_poliza DATE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);""",
        """CREATE TABLE ser_seguimiento (id SERIAL PRIMARY KEY, resolucion_origen VARCHAR(50) NOT NULL, id_recurso VARCHAR(12), nit_entidad VARCHAR(9), ind_seguimiento VARCHAR(2), cod_tipo_contrato VARCHAR(1), num_contrato VARCHAR(20), cod_tipo_acta VARCHAR(1), num_acta VARCHAR(20), fecha_acta DATE, valor_ejecutado NUMERIC(17, 2), valor_pagado NUMERIC(17, 2), porcentaje_ejecucion NUMERIC(5, 2), conclusiones VARCHAR(500), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);""",
        """CREATE TABLE ser_reintegro_no_ejecutado (id SERIAL PRIMARY KEY, resolucion_origen VARCHAR(50) NOT NULL, id_recurso VARCHAR(12), nit_entidad VARCHAR(9), ind_reintegro VARCHAR(2), cod_tipo_acto VARCHAR(1), num_acto VARCHAR(20), fecha_acto DATE, cod_entidad_reintegro VARCHAR(1), nit_banco VARCHAR(9), num_cuenta VARCHAR(12), valor_reintegrado NUMERIC(17, 2), fecha_consignacion DATE, portafolio VARCHAR(3), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);""",
        """CREATE TABLE ser_reintegro_rendimientos (id SERIAL PRIMARY KEY, resolucion_origen VARCHAR(50) NOT NULL, id_recurso VARCHAR(12), nit_entidad VARCHAR(9), ind_reintegro VARCHAR(2), cod_tipo_acto VARCHAR(1), num_acto VARCHAR(20), fecha_acto DATE, cod_entidad_reintegro VARCHAR(1), nit_banco VARCHAR(9), num_cuenta VARCHAR(12), valor_reintegrado NUMERIC(17, 2), fecha_consignacion DATE, portafolio VARCHAR(3), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"""
    ]

    seed_recursos = """
    INSERT INTO ser_recursos (id_recurso, descripcion, estado) VALUES 
    ('ID2069625612', 'Resolución 696 - 2025 (Mod. 763)', 'ACTIVA'), 
    ('ID2202623619', 'Resolución 2026 - 2023', 'ACTIVA') 
    ON CONFLICT (id_recurso) DO NOTHING;
    """

    try:
        with engine.begin() as conn:
            print("🗑️ Eliminando esquemas anteriores...")
            conn.execute(text(query_drop))
            for query in tablas_sql:
                conn.execute(text(query))
            conn.execute(text(seed_recursos))
        print("✅ Base de datos SER124DREC creada con control de estado de resoluciones.")
    except Exception as e:
        print(f"❌ Error en la ejecución SQL: {str(e)}")

if __name__ == "__main__":
    resetear_y_crear_tablas_financieras()