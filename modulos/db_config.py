# -*- coding: utf-8 -*-
import os
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

def verificar_crear_bd_local():
    db_user = os.getenv("DB_USER", "postgres")
    db_pass = os.getenv("DB_PASSWORD", "1234")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "aps_local_db")

    cadena_admin = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/postgres"
    
    try:
        engine_postgres = create_engine(cadena_admin, isolation_level="AUTOCOMMIT", connect_args={"client_encoding": "utf8"})
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
        db_url = os.getenv("DATABASE_URL")
        
        # Delegación estricta de seguridad a psycopg2 (Previene corrupción de URL en SQLAlchemy 2.0+)
        conn_args = {
            "sslmode": "require",
            "client_encoding": "utf8"
        }
        
        if db_url:
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            
            # Limpiar cualquier parámetro previo en la URL nativa de Render
            if "?" in db_url:
                db_url = db_url.split("?")[0]
                
            return create_engine(db_url, poolclass=NullPool, connect_args=conn_args)
            
        # Fallback a variables individuales AIVEN
        db_user = os.getenv("DB_USER_AIVEN", "")
        db_pass = os.getenv("DB_PASSWORD_AIVEN", "")
        db_host = os.getenv("DB_HOST_AIVEN", "")
        db_port = os.getenv("DB_PORT_AIVEN", "5432")
        db_name = os.getenv("DB_NAME_AIVEN", "")
        
        cadena = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        
        return create_engine(cadena, poolclass=NullPool, connect_args=conn_args)
        
    else:
        # Entorno de Desarrollo Local
        db_user = os.getenv("DB_USER", "postgres")
        db_pass = os.getenv("DB_PASSWORD", "1234")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = "postgres" if admin else os.getenv("DB_NAME", "aps_local_db")
        
        cadena = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        isolation = "AUTOCOMMIT" if admin else "READ COMMITTED"
        
        return create_engine(cadena, isolation_level=isolation, pool_pre_ping=True, connect_args={"client_encoding": "utf8"})

# Inicialización global del motor
engine = get_engine()
