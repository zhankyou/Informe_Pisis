# -*- coding: utf-8 -*-
import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def enviar_correo_aval(destinatario, nombre_usuario):
    """
    Envía el correo de aval de acceso utilizando SMTP de Gmail mediante App Passwords.
    Requuye las variables de entorno GMAIL_SENDER y GMAIL_APP_PASSWORD.
    """
    sender_email = os.getenv("GMAIL_SENDER")
    sender_password = os.getenv("GMAIL_APP_PASSWORD")

    if not sender_email or not sender_password:
        logging.error("Credenciales GMAIL_SENDER / GMAIL_APP_PASSWORD no encontradas en el archivo .env")
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
                <li style="margin-bottom: 10px;"><strong>Android:</strong> <a href="https://play.google.com/store/apps/details?id=uk.ac.imperial.epicollect.five&hl=en_GB&pli=1" style="color: #004b87; text-decoration: none;">Descargar en Google Play</a></li>
                <li><strong>iOS:</strong> <a href="https://apps.apple.com/us/app/epicollect5/id1183858199" style="color: #004b87; text-decoration: none;">Descargar en App Store</a></li>
            </ul>
        </div>

        <p style="font-size: 15px;">Recuerda iniciar sesión dentro de la plataforma de <strong>Epicollect 5</strong> con el correo previamente registrado y dirigirse al apartado de <strong>"+ AÑADIR PROYECTO"</strong> y escribir los formularios correspondientes a su perfil profesional o técnico:</p>

        <ul style="background-color: #ffffff; border: 1px solid #e0e0e0; padding: 20px 40px; border-radius: 6px; list-style-type: square;">
            <li style="margin-bottom: 12px;"><strong>DESISTIMIENTO VACUNACION:</strong> <a href="https://five.epicollect.net/project/desistimiento-vacunacion" style="color: #00b09b;">Enlace al proyecto</a></li>
            <li style="margin-bottom: 12px;"><strong>APS VACUNACION REGULAR:</strong> <a href="https://five.epicollect.net/project/aps-vacunacion-regular" style="color: #00b09b;">Enlace al proyecto</a></li>
            <li style="margin-bottom: 12px;"><strong>CARACTERIZACION SI_APS 2026:</strong> <a href="https://five.epicollect.net/project/caracterizacion-si-aps-2026" style="color: #00b09b;">Enlace al proyecto</a></li>
            <li style="margin-bottom: 12px;"><strong>APS TRAMITES 2026:</strong> <a href="https://five.epicollect.net/project/aps-tramites-2026" style="color: #00b09b;">Enlace al proyecto</a></li>
            <li style="margin-bottom: 12px;"><strong>APS PCC 2026:</strong> <a href="https://five.epicollect.net/project/aps-pcc-2026" style="color: #00b09b;">Enlace al proyecto</a></li>
            <li style="margin-bottom: 12px;"><strong>Desistimiento APS:</strong> <a href="https://five.epicollect.net/project/desistimiento-aps" style="color: #00b09b;">Enlace al proyecto</a></li>
            <li><strong>APS PCF 2026:</strong> <a href="https://five.epicollect.net/project/aps-pcf-2026" style="color: #00b09b;">Enlace al proyecto</a></li>
        </ul>

        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
            <p style="font-size: 16px; margin-bottom: 5px;">🎥 <strong>Video tutoriales Epicollect</strong></p>
            <p style="margin-top: 0; color: #555;">Recuerda que en el siguiente link de Drive encontrará las capacitaciones del uso de los formularios de Epicollect:<br>
            🔗 <a href="https://drive.google.com/drive/folders/1eCjUOR01ysj-_icM9sH6lq5btIfva9F-?usp=sharing" style="color: #004b87; font-weight: bold;">Ver capacitaciones en Google Drive</a></p>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = asunto
    msg['From'] = f"Soporte INFORME APS <{sender_email}>"
    msg['To'] = destinatario
    msg.attach(MIMEText(html_content, 'html'))

    try:
        # Configuración exclusiva para el servidor SMTP de Gmail
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, destinatario, msg.as_string())
        server.quit()
        logging.info(f"Correo de aval enviado exitosamente a: {destinatario}")
        return True
    except smtplib.SMTPAuthenticationError:
        logging.error(
            "Fallo de Autenticación SMTP. Verifique que la contraseña de aplicación sea correcta y no tenga espacios.")
        return False
    except Exception as e:
        logging.error(f"Error crítico al enviar correo SMTP a {destinatario}: {e}")
        return False
