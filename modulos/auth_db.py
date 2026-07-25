# -*- coding: utf-8 -*-
from sqlalchemy import text
from modulos.db_config import engine

def inicializar_tabla_usuarios():
    """
    Crea o actualiza la tabla de usuarios con la integración de roles estrictos.
    Aplica AUTOCOMMIT para garantizar la ejecución de DDL.
    """
    query_create = text("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        session_token VARCHAR(255),
        device_id VARCHAR(255),
        rol VARCHAR(20) DEFAULT 'visualizador' 
            CHECK (rol IN ('administrador', 'coordinador', 'visualizador'))
    );
    """)

    query_alter = text("""
    DO $$ 
    BEGIN 
        BEGIN
            ALTER TABLE usuarios ADD COLUMN rol VARCHAR(20) DEFAULT 'visualizador';
        EXCEPTION
            WHEN duplicate_column THEN NULL;
        END;
        
        BEGIN
            ALTER TABLE usuarios ADD CONSTRAINT chk_rol_valido 
            CHECK (rol IN ('administrador', 'coordinador', 'visualizador'));
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END;
    END $$;
    """)

    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(query_create)
            conn.execute(query_alter)
    except Exception as e:
        print(f"[*] Error DDL (Crear/Alterar Tabla 'usuarios'): {e}")

# Ejecutar la inicialización al importar el módulo
inicializar_tabla_usuarios()