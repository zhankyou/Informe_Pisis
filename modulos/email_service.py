# -*- coding: utf-8 -*-
import os
import base64
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def _get_gmail_service():
    creds = Credentials(
        token=None,
        refresh_token=os.getenv("GMAIL_REFRESH_TOKEN"),
        client_id=os.getenv("GMAIL_CLIENT_ID"),
        client_secret=os.getenv("GMAIL_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    return build("gmail", "v1", credentials=creds)

def enviar_correo_aval(destinatario, nombre_usuario):
    sender_email = os.getenv("GMAIL_SENDER")
    if not sender_email:
        logging.error("Variable GMAIL_SENDER no encontrada en .env")
        return False

    asunto = "Aval de Ingreso y Accesos a Plataformas - INFORME APS"

    html_content = f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #004b87; border-bottom: 2px solid #00b09b; padding-bottom: 10px;">Hola, {nombre_usuario}</h2>
        <p style="font-size: 16px;">Se ha otorgado el aval para su ingreso a los formularios solicitados.</p>
        <div style="background-color: #f8fbff; padding: 20px; border-left: 5px solid #00b09b; margin: 25px 0; border-radius: 4px;">
            <p style="margin-top: 0;"><strong>📱 Recuerda descargar Epicollect 5 desde su dispositivo móvil:</strong></p>
            <ul style="margin-bottom: 0;">
                <li style="margin-bottom: 10px;"><strong>Android:</strong> <a href="https://play.google.com/store/apps/details?id=uk.ac.imperial.epicollect.five&hl=en_GB&pli=1">Descargar en Google Play</a></li>
                <li><strong>iOS:</strong> <a href="https://apps.apple.com/us/app/epicollect5/id1183858199">Descargar en App Store</a></li>
            </ul>
        </div>
        <p style="font-size: 15px;">Recuerda iniciar sesión dentro de la plataforma de <strong>Epicollect 5</strong> con el correo previamente registrado y dirigirse al apartado de <strong>"+ AÑADIR PROYECTO"</strong> y escribir los formularios correspondientes a su perfil profesional o técnico:</p>
        <ul style="background-color: #ffffff; border: 1px solid #e0e0e0; padding: 20px 40px; border-radius: 6px; list-style-type: square;">
            <li style="margin-bottom: 12px;"><strong>DESISTIMIENTO VACUNACION:</strong> <a href="https://five.epicollect.net/project/desistimiento-vacunacion">Enlace al proyecto</a></li>
            <li style="margin-bottom: 12px;"><strong>APS VACUNACION REGULAR:</strong> <a href="https://five.epicollect.net/project/aps-vacunacion-regular">Enlace al proyecto</a></li>
            <li style="margin-bottom: 12px;"><strong>CARACTERIZACION SI_APS 2026:</strong> <a href="https://five.epicollect.net/project/caracterizacion-si-aps-2026">Enlace al proyecto</a></li>
            <li style="margin-bottom: 12px;"><strong>APS TRAMITES 2026:</strong> <a href="https://five.epicollect.net/project/aps-tramites-2026">Enlace al proyecto</a></li>
            <li style="margin-bottom: 12px;"><strong>APS PCC 2026:</strong> <a href="https://five.epicollect.net/project/aps-pcc-2026">Enlace al proyecto</a></li>
            <li style="margin-bottom: 12px;"><strong>Desistimiento APS:</strong> <a href="https://five.epicollect.net/project/desistimiento-aps">Enlace al proyecto</a></li>
            <li><strong>APS PCF 2026:</strong> <a href="https://five.epicollect.net/project/aps-pcf-2026">Enlace al proyecto</a></li>
        </ul>
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
            <p style="font-size: 16px; margin-bottom: 5px;">🎥 <strong>Video tutoriales Epicollect</strong></p>
            <p style="margin-top: 0; color: #555;">Recuerda que en el siguiente link de Drive encontrará las capacitaciones del uso de los formularios de Epicollect:<br>
            🔗 <a href="https://drive.google.com/drive/folders/1eCjUOR01ysj-_icM9sH6lq5btIfva9F-?usp=sharing">Ver capacitaciones en Google Drive</a></p>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"] = f"Soporte INFORME APS <{sender_email}>"
    msg["To"] = destinatario
    msg.attach(MIMEText(html_content, "html"))

    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    try:
        service = _get_gmail_service()
        service.users().messages().send(
            userId="me", body={"raw": raw_message}
        ).execute()
        logging.info(f"Correo de aval enviado exitosamente a: {destinatario}")
        return True
    except HttpError as e:
        logging.error(f"Error API Gmail al enviar a {destinatario}: {e}")
        return False
    except Exception as e:
        logging.error(f"Error crítico al enviar correo (Gmail API) a {destinatario}: {e}")
        return False
