# -*- coding: utf-8 -*-
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def verificar_crear_bd_local():
    db_url = os.getenv("DATABASE_URL")
    if db_url: 
        return # En producción no se crean bases de datos por código
        
    db_user = os.getenv("DB_USER", "postgres")
    db_pass = os.getenv("DB_PASSWORD", "1234")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "aps_local_db")

    cadena_admin = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/postgres"
    
    try:
        engine_postgres = create_engine(cadena_admin, isolation_level="AUTOCOMMIT")
        with engine_postgres.connect() as conn:
            existe = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")).fetchone()
            if not existe:
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"⚙️ Base de datos '{db_name}' creada automáticamente.")
    except Exception as e:
        print(f"⚠️ No se pudo verificar la creación de la DB local: {e}")

def get_engine(admin=False):
    # 1. Prioridad absoluta: Variable nativa de Render (Igual al script de migración)
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        # 2. Fallback a variables Aiven separadas
        db_user_aiv = os.getenv("DB_USER_AIVEN")
        if db_user_aiv:
            db_pass_aiv = os.getenv("DB_PASSWORD_AIVEN", "")
            db_host_aiv = os.getenv("DB_HOST_AIVEN", "")
            db_port_aiv = os.getenv("DB_PORT_AIVEN", "5432")
            db_name_aiv = os.getenv("DB_NAME_AIVEN", "")
            db_url = f"postgresql://{db_user_aiv}:{db_pass_aiv}@{db_host_aiv}:{db_port_aiv}/{db_name_aiv}?sslmode=require"
        else:
            # 3. Entorno Local
            db_user_loc = os.getenv("DB_USER", "postgres")
            db_pass_loc = os.getenv("DB_PASSWORD", "1234")
            db_host_loc = os.getenv("DB_HOST", "localhost")
            db_port_loc = os.getenv("DB_PORT", "5432")
            db_name_loc = "postgres" if admin else os.getenv("DB_NAME", "aps_local_db")
            db_url = f"postgresql://{db_user_loc}:{db_pass_loc}@{db_host_loc}:{db_port_loc}/{db_name_loc}"

    # Soporte obligatorio para SQLAlchemy 1.4 / 2.0+
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    isolation = "AUTOCOMMIT" if admin else "READ COMMITTED"

    # Misma configuración de motor del script de migración
    return create_engine(
        db_url, 
        isolation_level=isolation, 
        pool_pre_ping=True, 
        pool_recycle=300
    )

# Inicialización global del motor
engine = get_engine()
