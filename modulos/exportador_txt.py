# -*- coding: utf-8 -*-
import io
import datetime
from sqlalchemy import text


def generar_txt_ser124drec(engine, resolucion, fecha_corte, tipo_id, num_id, id_recurso):
    """
    Genera el archivo plano SER124DREC según especificaciones técnicas de PISIS.
    Delimitador: Pipe (|). Sin caracteres especiales al final de línea.
    """
    fecha_str = fecha_corte.replace('-', '')
    num_id_formateado = str(num_id).zfill(12)
    nombre_archivo = f"SER124DREC{fecha_str}{tipo_id}{num_id_formateado}{id_recurso}.txt"

    lineas = []

    with engine.connect() as conn:
        # 1. REGISTRO TIPO 1 - CONTROL
        query_control = text("""
                             SELECT tipo_id_entidad, num_id_entidad, fecha_inicial, fecha_final
                             FROM ser_control
                             WHERE resolucion_origen = :res LIMIT 1
                             """)
        control = conn.execute(query_control, {"res": resolucion}).fetchone()

        # Calcular total de registros sumando conteos de todas las tablas detalle
        tablas_detalle = [
            "ser_incorporacion", "ser_contratos", "ser_polizas",
            "ser_seguimiento", "ser_reintegro_no_ejecutado", "ser_reintegro_rendimientos"
        ]
        total_registros_detalle = 0
        for tabla in tablas_detalle:
            total_registros_detalle += conn.execute(
                text(f"SELECT COUNT(*) FROM {tabla} WHERE resolucion_origen = :res"),
                {"res": resolucion}
            ).scalar()

        total_registros = total_registros_detalle + 1  # +1 por el registro de control

        if control:
            f_ini = control.fecha_inicial.strftime('%Y-%m-%d') if control.fecha_inicial else '1900-01-01'
            f_fin = control.fecha_final.strftime('%Y-%m-%d') if control.fecha_final else '1900-01-01'
            linea_1 = f"1|{control.tipo_id_entidad[:2]}|{str(control.num_id_entidad)[:12]}|{f_ini}|{f_fin}|{total_registros}"
            lineas.append(linea_1)

        consecutivo = 1

        # 2. REGISTRO TIPO 2 - INCORPORACIÓN
        query_incorp = text("SELECT * FROM ser_incorporacion WHERE resolucion_origen = :res")
        for row in conn.execute(query_incorp, {"res": resolucion}):
            consecutivo += 1
            f_inc = row.fecha_incorporacion.strftime('%Y-%m-%d') if getattr(row, 'fecha_incorporacion',
                                                                            None) else '1900-01-01'
            ind = row.ind_incorporacion[:2]

            # Formatear línea asegurando campos vacíos si es "NA"
            if ind == 'NA':
                linea_2 = f"2|{consecutivo}|{row.id_recurso[:12]}|{str(row.nit_entidad)[:9]}|{ind}||||"
            else:
                val_inc = f"{row.valor_incorporado:.2f}" if row.valor_incorporado else "0.00"
                linea_2 = f"2|{consecutivo}|{row.id_recurso[:12]}|{str(row.nit_entidad)[:9]}|{ind}|{row.tipo_acto}|{row.num_acto[:20]}|{f_inc}|{val_inc}"
            lineas.append(linea_2)

        # 3. REGISTRO TIPO 3 - CONTRATOS (Implementación homóloga basada en anexo)
        query_contratos = text("SELECT * FROM ser_contratos WHERE resolucion_origen = :res")
        for row in conn.execute(query_contratos, {"res": resolucion}):
            consecutivo += 1
            ind = row.ind_actualizacion[:2]
            if ind == 'NA':
                linea_3 = f"3|{consecutivo}|{row.id_recurso[:12]}|{str(row.nit_entidad)[:9]}|{ind}||||||||||||"
            else:
                f_con = row.fecha_contrato.strftime('%Y-%m-%d') if getattr(row, 'fecha_contrato',
                                                                           None) else '1900-01-01'
                f_ter = row.fecha_terminacion.strftime('%Y-%m-%d') if getattr(row, 'fecha_terminacion',
                                                                              None) else '1900-01-01'
                val_con = f"{row.valor_contrato:.2f}" if row.valor_contrato else "0.00"
                linea_3 = f"3|{consecutivo}|{row.id_recurso[:12]}|{str(row.nit_entidad)[:9]}|{ind}|{row.tipo_contrato}|{row.num_contrato[:20]}|{f_con}|{f_ter}|{row.objeto[:500]}|{val_con}|{row.tipo_id_contratista[:2]}|{row.num_id_contratista[:17]}|{row.nombre_contratista[:100]}|{row.tipo_id_supervisor[:2]}|{row.num_id_supervisor[:17]}|{row.nombre_supervisor[:100]}"
            lineas.append(linea_3)

        # 4. REGISTRO TIPO 4 - PÓLIZAS
        query_polizas = text("SELECT * FROM ser_polizas WHERE resolucion_origen = :res")
        for row in conn.execute(query_polizas, {"res": resolucion}):
            consecutivo += 1
            ind = row.ind_poliza[:2]
            if ind == 'NA':
                linea_4 = f"4|{consecutivo}|{row.id_recurso[:12]}|{str(row.nit_entidad)[:9]}|{ind}||||"
            else:
                f_pol = row.fecha_poliza.strftime('%Y-%m-%d') if getattr(row, 'fecha_poliza', None) else '1900-01-01'
                linea_4 = f"4|{consecutivo}|{row.id_recurso[:12]}|{str(row.nit_entidad)[:9]}|{ind}|{row.tipo_contrato}|{row.num_contrato[:20]}|{row.num_poliza[:20]}|{f_pol}"
            lineas.append(linea_4)

        # 5. REGISTRO TIPO 5 - SEGUIMIENTO
        query_seguimiento = text("SELECT * FROM ser_seguimiento WHERE resolucion_origen = :res")
        for row in conn.execute(query_seguimiento, {"res": resolucion}):
            consecutivo += 1
            ind = row.ind_seguimiento[:2]
            if ind == 'NA':
                linea_5 = f"5|{consecutivo}|{row.id_recurso[:12]}|{str(row.nit_entidad)[:9]}|{ind}|||||||||"
            else:
                f_acta = row.fecha_acta.strftime('%Y-%m-%d') if getattr(row, 'fecha_acta', None) else '1900-01-01'
                val_ej = f"{row.valor_ejecutado:.2f}" if row.valor_ejecutado else "0.00"
                val_pg = f"{row.valor_pagado:.2f}" if row.valor_pagado else "0.00"
                pct_tec = f"{row.porcentaje_tecnica:.2f}" if row.porcentaje_tecnica else "0.00"
                linea_5 = f"5|{consecutivo}|{row.id_recurso[:12]}|{str(row.nit_entidad)[:9]}|{ind}|{row.tipo_contrato}|{row.num_contrato[:20]}|{row.tipo_acta}|{row.num_acta[:20]}|{f_acta}|{val_ej}|{val_pg}|{pct_tec}|{row.conclusiones[:500]}"
            lineas.append(linea_5)

        # 6. REGISTRO TIPO 6 - REINTEGRO NO EJECUTADO
        query_r_no_ejec = text("SELECT * FROM ser_reintegro_no_ejecutado WHERE resolucion_origen = :res")
        for row in conn.execute(query_r_no_ejec, {"res": resolucion}):
            consecutivo += 1
            ind = row.ind_reintegro[:2]
            if ind == 'NA':
                linea_6 = f"6|{consecutivo}|{row.id_recurso[:12]}|{str(row.nit_entidad)[:9]}|{ind}|||||||||"
            else:
                f_acto = row.fecha_acto.strftime('%Y-%m-%d') if getattr(row, 'fecha_acto', None) else '1900-01-01'
                f_consig = row.fecha_consignacion.strftime('%Y-%m-%d') if getattr(row, 'fecha_consignacion',
                                                                                  None) else '1900-01-01'
                val_rt = f"{row.valor_reintegrado:.2f}" if row.valor_reintegrado else "0.00"
                linea_6 = f"6|{consecutivo}|{row.id_recurso[:12]}|{str(row.nit_entidad)[:9]}|{ind}|{row.tipo_acto}|{row.num_acto[:20]}|{f_acto}|{row.cod_entidad_reintegro}|{str(row.nit_banco)[:9]}|{str(row.num_cuenta)[:12]}|{val_rt}|{f_consig}|{row.portafolio}"
            lineas.append(linea_6)

        # 7. REGISTRO TIPO 7 - REINTEGRO RENDIMIENTOS
        query_r_rend = text("SELECT * FROM ser_reintegro_rendimientos WHERE resolucion_origen = :res")
        for row in conn.execute(query_r_rend, {"res": resolucion}):
            consecutivo += 1
            ind = row.ind_reintegro[:2]
            if ind == 'NA':
                linea_7 = f"7|{consecutivo}|{row.id_recurso[:12]}|{str(row.nit_entidad)[:9]}|{ind}|||||||||"
            else:
                f_acto = row.fecha_acto.strftime('%Y-%m-%d') if getattr(row, 'fecha_acto', None) else '1900-01-01'
                f_consig = row.fecha_consignacion.strftime('%Y-%m-%d') if getattr(row, 'fecha_consignacion',
                                                                                  None) else '1900-01-01'
                val_rt = f"{row.valor_reintegrado:.2f}" if row.valor_reintegrado else "0.00"
                linea_7 = f"7|{consecutivo}|{row.id_recurso[:12]}|{str(row.nit_entidad)[:9]}|{ind}|{row.tipo_acto}|{row.num_acto[:20]}|{f_acto}|{row.cod_entidad_reintegro}|{str(row.nit_banco)[:9]}|{str(row.num_cuenta)[:12]}|{val_rt}|{f_consig}|{row.portafolio}"
            lineas.append(linea_7)

    contenido = "\n".join(lineas)
    stream = io.BytesIO(contenido.encode('utf-8'))
    return nombre_archivo, stream


def generar_txt_siaps(engine, fecha_corte, tipo_id, num_id):
    """
    Exportación dummy / base para SI-APS Poblacional.
    """
    fecha_str = fecha_corte.replace('-', '')
    nombre_archivo = f"SIAPS{fecha_str}{tipo_id}{str(num_id).zfill(12)}.txt"
    contenido = "1|CC|123456789|... (Estructura Poblacional SI-APS según DB)"
    stream = io.BytesIO(contenido.encode('utf-8'))
    return nombre_archivo, stream


def limpiar_duplicados_control(engine):
    query = text("""
                 DELETE
                 FROM ministerio_siaps_ccfp
                 WHERE id NOT IN (SELECT MAX(id)
                                  FROM ministerio_siaps_ccfp
                                  GROUP BY hash_registro)
                 """)
    with engine.begin() as conn:
        res = conn.execute(query)
        return res.rowcount


def resumen_control(engine, fecha_corte=None):
    base_query = """
                 SELECT fecha_corte, \
                        nombre_archivo, \
                        tipo_registro, \
                        COUNT(*)              as total_registros,
                        MIN(fecha_generacion) as primera_generacion, \
                        MAX(fecha_generacion) as ultima_generacion
                 FROM ministerio_siaps_ccfp \
                 """
    if fecha_corte:
        base_query += " WHERE fecha_corte = :fc "
    base_query += " GROUP BY fecha_corte, nombre_archivo, tipo_registro"

    with engine.connect() as conn:
        return conn.execute(text(base_query), {"fc": fecha_corte}).fetchall()