# -*- coding: utf-8 -*-
import os
import requests
import logging
from threading import Thread


def _enviar_telegram_async(mensaje):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logging.warning("[NOTIFICACIONES] Credenciales de Telegram no configuradas en .env")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensaje,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if response.status_code == 403:
            logging.error(
                "[NOTIFICACIONES ERROR] 403 Forbidden: El bot está bloqueado. Debe abrir el bot en Telegram y enviar '/start' desde el CHAT_ID configurado.")
        else:
            logging.error(f"[NOTIFICACIONES ERROR] Falla HTTP en webhook de Telegram: {err}")
    except Exception as e:
        logging.error(f"[NOTIFICACIONES ERROR] Excepción general en webhook de Telegram: {e}")


def notificar_nuevo_registro(modulo, detalles):
    """
    Dispara una notificación push a Telegram en segundo plano.
    """
    mensaje = f"🔔 *NUEVO REGISTRO INGRESADO*\n\n*Módulo:* {modulo}\n*Detalles:*\n{detalles}"
    Thread(target=_enviar_telegram_async, args=(mensaje,)).start()
