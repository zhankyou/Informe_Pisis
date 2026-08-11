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

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Aval de Ingreso y Accesos a Plataformas - INFORME APS"
    msg["From"] = f"Soporte INFORME APS <{sender_email}>"
    msg["To"] = destinatario

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
    msg.attach(MIMEText("Su solicitud de acceso ha sido aprobada.", "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        service = _get_gmail_service()
        service.users().messages().send(userId="me",
                                        body={"raw": base64.urlsafe_b64encode(msg.as_bytes()).decode()}).execute()
        return True
    except Exception as e:
        logging.error(f"Error SMTP Aval: {e}")
        return False


def enviar_correo_denegacion(destinatario, nombre_usuario):
    sender_email = os.getenv("GMAIL_SENDER")
    if not sender_email: return False

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Rechazo de Solicitud de Acceso (Documentación Inválida) - INFORME APS"
    msg['From'] = f"Soporte INFORME APS <{sender_email}>"
    msg['To'] = destinatario

    text_content = f"Hola, {nombre_usuario}. Su solicitud fue rechazada por inconsistencias en el adjunto de Mi Seguridad Social."

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"></head>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #1f2937; line-height: 1.6; max-width: 650px; margin: 0 auto; padding: 20px; border: 1px solid #e5e7eb; border-radius: 8px;">
        <h2 style="color: #dc2626; border-bottom: 2px solid #fecaca; padding-bottom: 10px;">Solicitud Denegada</h2>
        <p style="font-size: 16px;">Hola, <strong>{nombre_usuario}</strong>.</p>
        <p style="font-size: 16px;">Su solicitud de acceso a las plataformas PISIS y formularios operativos ha sido <strong>rechazada</strong> debido a que el archivo adjunto suministrado no cumple con los criterios exigidos.</p>

        <div style="background-color: #f8fafc; border-left: 5px solid #004b87; padding: 18px; margin: 25px 0; border-radius: 6px;">
            <h3 style="margin-top: 0; color: #004b87; font-size: 1.1rem;">Sobre el adjunto de "Mi Seguridad Social"</h3>
            <p style="margin-bottom: 15px; font-size: 0.95rem;">El soporte de "Mi Seguridad Social" solicitado corresponde al registro exitoso en dicha plataforma. Encontrará el paso a paso detallado (en formato PDF y videos instructivos) para el ingreso y creación de usuario en la página web dentro del material de apoyo suministrado en el siguiente enlace:</p>

            <a href="https://drive.google.com/drive/folders/18N7IifT4nZSn-eZcp7G-fkT3-ZyeXKP8" target="_blank" style="display: inline-block; background-color: #004b87; color: #ffffff; text-decoration: none; padding: 10px 18px; border-radius: 6px; font-weight: bold; font-size: 0.95rem;">
                📁 Acceder al Material de Apoyo (Google Drive)
            </a>

            <p style="margin-top: 15px; margin-bottom: 0; font-size: 0.95rem;">Una vez finalizado el registro de manera exitosa, <strong>debe tomar un pantallazo y cargar dicha imagen como evidencia obligatoria</strong> en el formulario.</p>
        </div>

        <p style="font-size: 15px; color: #4b5563;">Por favor, diligencie nuevamente la solicitud asegurándose de adjuntar la evidencia correcta.</p>
        <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 30px 0 20px 0;">
        <p style="font-size: 12px; color: #9ca3af; text-align: center;">Este es un correo generado automáticamente por el sistema SI-APS. Por favor no responda a este mensaje.</p>
    </body>
    </html>
    """
    msg.attach(MIMEText(text_content, 'plain'))
    msg.attach(MIMEText(html_content, 'html'))

    try:
        service = _get_gmail_service()
        service.users().messages().send(userId="me",
                                        body={"raw": base64.urlsafe_b64encode(msg.as_bytes()).decode()}).execute()
        return True
    except Exception as e:
        logging.error(f"Error SMTP Denegación: {e}")
        return False
