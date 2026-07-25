# -*- coding: utf-8 -*-
import os
import logging
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

    cadena_admin = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/postgres"
    engine_postgres = create_engine(cadena_admin, isolation_level="AUTOCOMMIT")

    try:
        with engine_postgres.connect() as conn:
            existe = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :dbname"), {"dbname": db_name}).fetchone()
            if not existe:
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                logging.info(f"⚙️ Base de datos '{db_name}' creada automáticamente.")
    except Exception as e:
        logging.warning(f"⚠️ No se pudo verificar la creación de la DB local: {e}")

def get_engine(admin=False):
    # Autodetección de Render o validación manual
    is_render = os.getenv("RENDER") == "true"
    ambiente = os.getenv("AMBIENTE", "local").strip().lower()

    if is_render or ambiente == "produccion":
        db_url = os.getenv("DATABASE_URL")
        
        # Prioridad 1: Uso de URI completa (Render/Heroku/Aiven URI)
        if db_url:
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            # Asegurar soporte SSL requerido por Aiven
            if "sslmode=require" not in db_url:
                db_url += "?sslmode=require" if "?" not in db_url else "&sslmode=require"
                
            return create_engine(
                db_url, 
                pool_size=10, 
                max_overflow=20, 
                pool_pre_ping=True, 
                pool_recycle=300
            )

        # Prioridad 2: Construcción manual por variables (Aiven nativo)
        db_user = os.getenv("DB_USER_AIVEN", "").strip()
        db_pass = os.getenv("DB_PASSWORD_AIVEN", "").strip()
        db_host = os.getenv("DB_HOST_AIVEN", "").strip()
        db_port = os.getenv("DB_PORT_AIVEN", "5432").strip()
        db_name = os.getenv("DB_NAME_AIVEN", "").strip()

        cadena = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?sslmode=require&client_encoding=utf8"
        return create_engine(
            cadena, 
            pool_size=10, 
            max_overflow=20, 
            pool_pre_ping=True, 
            pool_recycle=300
        )

    else:
        # Entorno Local
        db_user = os.getenv("DB_USER", "postgres")
        db_pass = os.getenv("DB_PASSWORD", "1234")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = "postgres" if admin else os.getenv("DB_NAME", "aps_local_db")

        cadena = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?client_encoding=utf8"
        isolation = "AUTOCOMMIT" if admin else "READ COMMITTED"
        return create_engine(cadena, isolation_level=isolation, pool_pre_ping=True)

# Inicialización global
engine = get_engine()
