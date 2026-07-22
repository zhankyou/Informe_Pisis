# -*- coding: utf-8 -*-
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
os.environ["PGCLIENTENCODING"] = "utf-8"

def verificar_crear_bd_local():
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")

    cadena_admin = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/postgres"
    engine_postgres = create_engine(cadena_admin, isolation_level="AUTOCOMMIT")
    
    try:
        with engine_postgres.connect() as conn:
            existe = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")).fetchone()
            if not existe:
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"⚙️ Base de datos '{db_name}' creada automáticamente.")
    except Exception as e:
        print(f"⚠️ No se pudo verificar la creación de la DB local: {e}")

def get_engine(admin=False):
    ambiente = os.getenv("AMBIENTE", "local").strip().lower()
    
    if ambiente == "produccion":
        # Soporte nativo para Render (Prioridad 1)
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            # SQLAlchemy 1.4+ requiere 'postgresql://'
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            return create_engine(db_url, pool_pre_ping=True)
            
        # Fallback a variables separadas (Evitando puertos nulos)
        db_user = os.getenv("DB_USER_AIVEN")
        db_pass = os.getenv("DB_PASSWORD_AIVEN")
        db_host = os.getenv("DB_HOST_AIVEN")
        db_port = os.getenv("DB_PORT_AIVEN")
        db_name = os.getenv("DB_NAME_AIVEN")
        
        cadena = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?sslmode=require&client_encoding=utf8"
        return create_engine(cadena, pool_pre_ping=True)
        
    else:
        # Entorno Local
        db_user = os.getenv("DB_USER")
        db_pass = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT")
        db_name = "postgres" if admin else os.getenv("DB_NAME")
        
        cadena = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?client_encoding=utf8"
        isolation = "AUTOCOMMIT" if admin else "READ COMMITTED"
        return create_engine(cadena, isolation_level=isolation, pool_pre_ping=True)

# Inicialización global
engine = get_engine()
