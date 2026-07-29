# -*- coding: utf-8 -*-
import os
import jwt
from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta
from flask_caching import Cache

# Configuración de Caché en memoria (previene saturación de BD)
cache = Cache(config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})

SECRET_KEY = os.environ.get('SECRET_KEY', 'PISIS_SECURE_KEY_2026_COMPLEX_0987654321')


def generar_token_jwt(username, rol):
    """Genera un token JWT (Estándar OAuth 2.0) firmado criptográficamente"""
    payload = {
        'exp': datetime.utcnow() + timedelta(hours=12),  # Expiración estricta
        'iat': datetime.utcnow(),
        'sub': username,
        'rol': rol
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def token_requerido(f):
    """Decorador para proteger APIs contra accesos no autorizados e inyecciones sin sesión"""

    @wraps(f)
    def decorador(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            partes = request.headers['Authorization'].split()
            if len(partes) == 2 and partes[0] == 'Bearer':
                token = partes[1]

        if not token:
            return jsonify({'status': 'error', 'message': 'Acceso denegado. Token faltante.'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            usuario_actual = data['sub']
            rol_actual = data['rol']
        except jwt.ExpiredSignatureError:
            return jsonify({'status': 'error', 'message': 'Token expirado. Inicie sesión nuevamente.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'status': 'error', 'message': 'Token manipulado o inválido.'}), 401

        # Inyecta la identidad verificada en la ruta
        return f(usuario_actual, rol_actual, *args, **kwargs)

    return decorador
