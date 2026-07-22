# -*- coding: utf-8 -*-
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
os.environ["PGCLIENTENCODING"] = "utf-8"

def get_engine():
    ambiente = os.getenv("AMBIENTE", "local").strip().lower()
    if ambiente == "produccion":
        db_user = os.getenv("DB_USER_AIVEN")
        db_pass = os.getenv("DB_PASSWORD_AIVEN")
        db_host = os.getenv("DB_HOST_AIVEN")
        db_port = os.getenv("DB_PORT_AIVEN")
        db_name = os.getenv("DB_NAME_AIVEN")
        cadena = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?sslmode=require&client_encoding=utf8"
    else:
        db_user = os.getenv("DB_USER")
        db_pass = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT")
        db_name = os.getenv("DB_NAME")
        cadena = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?client_encoding=utf8"
    return create_engine(cadena, pool_pre_ping=True)

engine = get_engine()