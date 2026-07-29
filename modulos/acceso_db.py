# -*- coding: utf-8 -*-
import os
import re
import json
import base64
import unicodedata
import tempfile
from sqlalchemy import text
from modulos.db_config import engine
from werkzeug.utils import secure_filename

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    DRIVE_AVAILABLE = True
except ImportError:
    DRIVE_AVAILABLE = False


def remove_accents_and_upper(val):
    if not val: return None
    s = str(val).strip()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return s.upper()


def clean_objeto(val):
    if not val: return None
    s = str(val).replace('°', 'O').replace('º', 'O')
    return remove_accents_and_upper(s)[:500]


def clean_numeric(val):
    if not val: return None
    return re.sub(r'[^\d]', '', str(val))


def upload_to_drive(file_path, filename):
    if not DRIVE_AVAILABLE: return "ERROR"
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    FOLDER_ID = '1friBrLX8x-FNKzGBwSMJh60vNUIkYuGl'
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")

    if not creds_json: return "ERROR"

    try:
        creds_dict = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {'name': filename, 'parents': [FOLDER_ID]}
        media = MediaFileUpload(file_path, resumable=True)

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='webViewLink',
            supportsAllDrives=True
        ).execute()

        return file.get('webViewLink')
    except Exception as e:
        print(f"[*] Fallo en API de Drive: {e}")
        return "ERROR"


def crear_tabla_acceso():
    """Ejecuta DDL garantizando integridad esquemática y persistencia JSONB dinámica"""
    query_create = text("""
                        CREATE TABLE IF NOT EXISTS solicitudes_acceso
                        (
                            id
                            SERIAL
                            PRIMARY
                            KEY,
                            sistema
                            VARCHAR
                        (
                            50
                        ) NOT NULL,
                            programa VARCHAR
                        (
                            10
                        ),
                            territorio VARCHAR
                        (
                            5
                        ),
                            microterritorio VARCHAR
                        (
                            5
                        ),
                            tipo_documento VARCHAR
                        (
                            2
                        ),
                            numero_documento VARCHAR
                        (
                            20
                        ),
                            nombre_completo VARCHAR
                        (
                            150
                        ),
                            primer_nombre VARCHAR
                        (
                            60
                        ),
                            segundo_nombre VARCHAR
                        (
                            60
                        ),
                            primer_apellido VARCHAR
                        (
                            60
                        ),
                            segundo_apellido VARCHAR
                        (
                            60
                        ),
                            fecha_nacimiento DATE,
                            nacionalidad VARCHAR
                        (
                            60
                        ),
                            sexo VARCHAR
                        (
                            20
                        ),
                            celular VARCHAR
                        (
                            20
                        ),
                            correo VARCHAR
                        (
                            100
                        ),
                            regimen VARCHAR
                        (
                            20
                        ),
                            eapb VARCHAR
                        (
                            100
                        ),
                            perfil_profesional VARCHAR
                        (
                            150
                        ),
                            numero_contrato VARCHAR
                        (
                            20
                        ),
                            objeto_contrato TEXT,
                            fecha_contrato DATE,
                            fecha_finalizacion_contrato DATE,
                            valor_contrato NUMERIC,
                            seguridad_social_url VARCHAR
                        (
                            255
                        ),
                            archivo_base64 TEXT,
                            datos_adicionales JSONB DEFAULT '{}'::jsonb,
                            fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            );
                        """)

    query_alter = text("""
    DO $$ 
    BEGIN 
        BEGIN
            ALTER TABLE solicitudes_acceso ADD COLUMN archivo_base64 TEXT;
        EXCEPTION
            WHEN duplicate_column THEN NULL;
        END;
        BEGIN
            ALTER TABLE solicitudes_acceso ADD COLUMN datos_adicionales JSONB DEFAULT '{}'::jsonb;
        EXCEPTION
            WHEN duplicate_column THEN NULL;
        END;
    END $$;
    """)

    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(query_create)
            conn.execute(query_alter)
    except Exception as e:
        print(f"[*] Error DDL (Crear/Alterar Tabla): {e}")


def procesar_y_guardar_solicitud(form_data, file_obj=None):
    crear_tabla_acceso()

    datos = {
        'sistema': "ACCESO_UNIFICADO",
        'programa': str(form_data.get('programa')).strip() if form_data.get('programa') else None,
        'territorio': remove_accents_and_upper(form_data.get('territorio')),
        'microterritorio': remove_accents_and_upper(form_data.get('microterritorio')),
        'tipo_documento': str(form_data.get('tipo_documento')).strip() if form_data.get('tipo_documento') else None,
        'numero_documento': clean_numeric(form_data.get('numero_documento')),
        'nombre_completo': remove_accents_and_upper(form_data.get('nombre_completo')),
        'primer_nombre': remove_accents_and_upper(form_data.get('primer_nombre')),
        'segundo_nombre': remove_accents_and_upper(form_data.get('segundo_nombre')),
        'primer_apellido': remove_accents_and_upper(form_data.get('primer_apellido')),
        'segundo_apellido': remove_accents_and_upper(form_data.get('segundo_apellido')),
        'fecha_nacimiento': form_data.get('fecha_nacimiento') if form_data.get('fecha_nacimiento') else None,
        'nacionalidad': remove_accents_and_upper(form_data.get('nacionalidad')),
        'sexo': remove_accents_and_upper(form_data.get('sexo')),
        'celular': clean_numeric(form_data.get('celular')),
        'correo': str(form_data.get('correo', '')).lower().strip() if form_data.get('correo') else None,
        'regimen': remove_accents_and_upper(form_data.get('regimen')),
        'eapb': remove_accents_and_upper(form_data.get('eapb')),
        'perfil_profesional': str(form_data.get('perfil_profesional')).strip() if form_data.get(
            'perfil_profesional') else None,
        'numero_contrato': remove_accents_and_upper(form_data.get('numero_contrato')),
        'objeto_contrato': clean_objeto(form_data.get('objeto_contrato')),
        'fecha_contrato': form_data.get('fecha_contrato') if form_data.get('fecha_contrato') else None,
        'fecha_finalizacion_contrato': form_data.get('fecha_finalizacion_contrato') if form_data.get(
            'fecha_finalizacion_contrato') else None,
        'valor_contrato': clean_numeric(form_data.get('valor_contrato')),
        'seguridad_social_url': None,
        'archivo_base64': None
    }

    # Captura dinámica de datos del formulario en estructura JSONB
    datos_adicionales = {}
    columnas_base = list(datos.keys()) + ['validacion_bot_oculta']

    for key, value in form_data.items():
        if key not in columnas_base:
            datos_adicionales[key] = str(value).strip() if value else None

    datos['datos_adicionales'] = json.dumps(datos_adicionales)

    if file_obj and file_obj.filename != '':
        filename = secure_filename(f"SS_{datos['numero_documento']}_{file_obj.filename}")
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
        file_obj.save(temp_path)

        drive_link = upload_to_drive(temp_path, filename)

        if drive_link != "ERROR":
            datos['seguridad_social_url'] = drive_link
        else:
            with open(temp_path, "rb") as f:
                b64_encoded = base64.b64encode(f.read()).decode('utf-8')
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'pdf'
                mime_type = 'application/pdf' if ext == 'pdf' else f'image/{ext}'
                datos['archivo_base64'] = f"data:{mime_type};base64,{b64_encoded}"
                datos['seguridad_social_url'] = "ALMACENADO_EN_BD"

        if os.path.exists(temp_path): os.remove(temp_path)

    query = text("""
                 INSERT INTO solicitudes_acceso
                 (sistema, programa, territorio, microterritorio, tipo_documento, numero_documento, nombre_completo,
                  primer_nombre, segundo_nombre, primer_apellido, segundo_apellido, fecha_nacimiento, nacionalidad,
                  sexo, celular, correo, regimen, eapb, perfil_profesional, numero_contrato, objeto_contrato,
                  fecha_contrato, fecha_finalizacion_contrato, valor_contrato, seguridad_social_url, archivo_base64,
                  datos_adicionales)
                 VALUES (:sistema, :programa, :territorio, :microterritorio, :tipo_documento, :numero_documento,
                         :nombre_completo,
                         :primer_nombre, :segundo_nombre, :primer_apellido, :segundo_apellido, :fecha_nacimiento,
                         :nacionalidad,
                         :sexo, :celular, :correo, :regimen, :eapb, :perfil_profesional, :numero_contrato,
                         :objeto_contrato,
                         :fecha_contrato, :fecha_finalizacion_contrato, :valor_contrato, :seguridad_social_url,
                         :archivo_base64, :datos_adicionales)
                 """)

    try:
        with engine.begin() as conn:
            conn.execute(query, datos)
        return True
    except Exception as e:
        print(f"[*] Error DML (Insertar Solicitud): {e}")
        return False
