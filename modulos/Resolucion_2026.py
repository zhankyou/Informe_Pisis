# -*- coding: utf-8 -*-
from modulos.financiero import financiero_bp
from modulos.poblacional import poblacional_bp
from modulos.consultas import consultas_bp
from modulos.cargador_masivo import cargador_bp
from modulos.cargador_epicollect import epicollect_bp
from modulos.cronograma import cronograma_bp

def registrar_modulos_2026(app):
    app.register_blueprint(financiero_bp)
    app.register_blueprint(poblacional_bp)
    app.register_blueprint(consultas_bp)
    app.register_blueprint(cargador_bp)
    app.register_blueprint(epicollect_bp)
    app.register_blueprint(cronograma_bp)