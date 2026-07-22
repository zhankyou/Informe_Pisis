# -*- coding: utf-8 -*-
import math
from datetime import datetime, date, time
from flask import request, jsonify, make_response
from sqlalchemy import text
from modulos.db_config import engine

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None


def serialize_row(row):
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, (datetime, date, time)):
            d[k] = str(v)
    return d


def registrar_rutas_diario(bp):
    @bp.route('/api/cronograma/diario', methods=['GET'])
    def get_diario():
        fecha = request.args.get('fecha', datetime.now().strftime('%Y-%m-%d'))
        try:
            with engine.connect() as conn:
                rows = conn.execute(text("SELECT * FROM cro_vacunacion WHERE fecha = :f ORDER BY dupla ASC"),
                                    {"f": fecha}).mappings().fetchall()
                config = conn.execute(text("SELECT * FROM cro_diario_config WHERE fecha = :f"),
                                      {"f": fecha}).mappings().fetchone()

            config_data = serialize_row(dict(config)) if config else {
                "entrega_nombres": "", "entrega_telefonos": "",
                "archivo_hora_inicio": "08:00", "archivo_hora_fin": "16:00",
                "papeleria_nombres": "", "papeleria_telefonos": "",
                "cargue_nombres": "", "cargue_telefonos": "",
                "validacion_nombres": "", "validacion_telefonos": "",
                "observaciones": "OBSERVACIONES: 1. DEBERÁN GESTIONAR LA RECEPCIÓN Y ENTREGA DE BIOLÓGICO EN CEMI SEGÚN PROGRAMACIÓN DEL DÍA A CARGO DE VACUNADOR.\nANOTADOR: DILIGENCIA EPICOLLECT BARRIDO DIARIO Y EPICOLLECT VACUNACION\nPSICOLOGO: DILIGENCIA EPICOLLECT DESESTIMIENTO"
            }

            return jsonify({"status": "success", "data": [serialize_row(r) for r in rows], "config": config_data}), 200
        except Exception as e:
            return jsonify({"status": "error", "msg": str(e)}), 500

    @bp.route('/api/cronograma/diario', methods=['POST'])
    def save_diario():
        datos = request.json
        record_id = datos.pop('id', None)

        try:
            with engine.begin() as conn:
                if record_id:
                    set_clause = ", ".join([f"{k} = :{k}" for k in datos.keys()])
                    datos['id'] = record_id
                    conn.execute(text(f"UPDATE cro_vacunacion SET {set_clause} WHERE id = :id"), datos)
                    msg = "Asignación actualizada correctamente."
                else:
                    col = ", ".join(datos.keys())
                    val = ", ".join([f":{k}" for k in datos.keys()])
                    conn.execute(text(f"INSERT INTO cro_vacunacion ({col}) VALUES ({val})"), datos)
                    msg = "Asignación registrada correctamente."
            return jsonify({"status": "success", "msg": msg}), 200
        except Exception as e:
            return jsonify({"status": "error", "msg": str(e)}), 500

    @bp.route('/api/cronograma/diario/<int:id>', methods=['DELETE'])
    def delete_diario(id):
        try:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM cro_vacunacion WHERE id = :id"), {"id": id})
            return jsonify({"status": "success", "msg": "Asignación eliminada."}), 200
        except Exception as e:
            return jsonify({"status": "error", "msg": str(e)}), 500

    @bp.route('/api/cronograma/diario/config', methods=['POST'])
    def save_diario_config():
        datos = request.json
        datos['observaciones'] = datos.get('observaciones', '').upper()
        try:
            with engine.begin() as conn:
                query = text("""
                             INSERT INTO cro_diario_config (fecha, entrega_nombres, entrega_telefonos,
                                                            archivo_hora_inicio, archivo_hora_fin,
                                                            papeleria_nombres, papeleria_telefonos,
                                                            cargue_nombres, cargue_telefonos,
                                                            validacion_nombres, validacion_telefonos, observaciones)
                             VALUES (:fecha, :entrega_nombres, :entrega_telefonos,
                                     :archivo_hora_inicio, :archivo_hora_fin,
                                     :papeleria_nombres, :papeleria_telefonos,
                                     :cargue_nombres, :cargue_telefonos,
                                     :validacion_nombres, :validacion_telefonos, :observaciones) ON CONFLICT (fecha) DO
                             UPDATE SET
                                 entrega_nombres = EXCLUDED.entrega_nombres,
                                 entrega_telefonos = EXCLUDED.entrega_telefonos,
                                 archivo_hora_inicio = EXCLUDED.archivo_hora_inicio,
                                 archivo_hora_fin = EXCLUDED.archivo_hora_fin,
                                 papeleria_nombres = EXCLUDED.papeleria_nombres,
                                 papeleria_telefonos = EXCLUDED.papeleria_telefonos,
                                 cargue_nombres = EXCLUDED.cargue_nombres,
                                 cargue_telefonos = EXCLUDED.cargue_telefonos,
                                 validacion_nombres = EXCLUDED.validacion_nombres,
                                 validacion_telefonos = EXCLUDED.validacion_telefonos,
                                 observaciones = EXCLUDED.observaciones,
                                 updated_at = CURRENT_TIMESTAMP
                             """)
                conn.execute(query, datos)
            return jsonify({"status": "success", "msg": "Configuración del día actualizada."}), 200
        except Exception as e:
            return jsonify({"status": "error", "msg": str(e)}), 500

    @bp.route('/api/cronograma/diario/duplicar', methods=['POST'])
    def duplicar_diario():
        datos = request.json
        origen = datos.get('fecha_origen')
        destino = datos.get('fecha_destino')

        if not origen or not destino:
            return jsonify({"status": "error", "msg": "Fechas de origen y destino requeridas."}), 400

        try:
            with engine.begin() as conn:
                config_origen = conn.execute(text("SELECT * FROM cro_diario_config WHERE fecha = :f"),
                                             {"f": origen}).mappings().fetchone()
                if config_origen:
                    query_cfg = text("""
                                     INSERT INTO cro_diario_config (fecha, entrega_nombres, entrega_telefonos,
                                                                    archivo_hora_inicio, archivo_hora_fin,
                                                                    papeleria_nombres, papeleria_telefonos,
                                                                    cargue_nombres, cargue_telefonos,
                                                                    validacion_nombres, validacion_telefonos,
                                                                    observaciones, updated_at)
                                     VALUES (:d, :en, :et, :ahi, :ahf, :pn, :pt, :cn, :ct, :vn, :vt, :obs,
                                             CURRENT_TIMESTAMP) ON CONFLICT (fecha) DO
                                     UPDATE
                                     SET
                                         entrega_nombres = EXCLUDED.entrega_nombres, entrega_telefonos = EXCLUDED.entrega_telefonos, archivo_hora_inicio = EXCLUDED.archivo_hora_inicio, archivo_hora_fin = EXCLUDED.archivo_hora_fin, papeleria_nombres = EXCLUDED.papeleria_nombres, papeleria_telefonos = EXCLUDED.papeleria_telefonos, cargue_nombres = EXCLUDED.cargue_nombres, cargue_telefonos = EXCLUDED.cargue_telefonos, validacion_nombres = EXCLUDED.validacion_nombres, validacion_telefonos = EXCLUDED.validacion_telefonos, observaciones = EXCLUDED.observaciones, updated_at = CURRENT_TIMESTAMP
                                     """)
                    conn.execute(query_cfg, {
                        "d": destino, "en": config_origen['entrega_nombres'], "et": config_origen['entrega_telefonos'],
                        "ahi": config_origen['archivo_hora_inicio'], "ahf": config_origen['archivo_hora_fin'],
                        "pn": config_origen['papeleria_nombres'], "pt": config_origen['papeleria_telefonos'],
                        "cn": config_origen['cargue_nombres'], "ct": config_origen['cargue_telefonos'],
                        "vn": config_origen['validacion_nombres'], "vt": config_origen['validacion_telefonos'],
                        "obs": config_origen['observaciones']
                    })

                filas_origen = conn.execute(text("SELECT * FROM cro_vacunacion WHERE fecha = :f"),
                                            {"f": origen}).mappings().fetchall()
                if filas_origen:
                    conn.execute(text("DELETE FROM cro_vacunacion WHERE fecha = :f"), {"f": destino})
                    insert_query = text("""
                                        INSERT INTO cro_vacunacion (fecha, dupla, lugar, horario, vacunador,
                                                                    tel_vacunador, anotador, tel_anotador,
                                                                    profesional_valoracion, tel_profesional,
                                                                    desistimientos, tel_desistimientos, hora_inicio,
                                                                    hora_fin)
                                        VALUES (:fecha, :dupla, :lugar, :horario, :vacunador, :tel_vacunador, :anotador,
                                                :tel_anotador,
                                                :profesional_valoracion, :tel_profesional, :desistimientos,
                                                :tel_desistimientos, :hora_inicio, :hora_fin)
                                        """)
                    for row in filas_origen:
                        conn.execute(insert_query, {
                            "fecha": destino, "dupla": row['dupla'], "lugar": row['lugar'], "horario": row['horario'],
                            "vacunador": row['vacunador'], "tel_vacunador": row['tel_vacunador'],
                            "anotador": row['anotador'],
                            "tel_anotador": row['tel_anotador'],
                            "profesional_valoracion": row['profesional_valoracion'],
                            "tel_profesional": row['tel_profesional'], "desistimientos": row['desistimientos'],
                            "tel_desistimientos": row['tel_desistimientos'], "hora_inicio": row['hora_inicio'],
                            "hora_fin": row['hora_fin']
                        })

            return jsonify(
                {"status": "success", "msg": f"Jornada clonada exitosamente del {origen} al {destino}."}), 200
        except Exception as e:
            return jsonify({"status": "error", "msg": str(e)}), 500

    @bp.route('/api/cronograma/pdf', methods=['GET'])
    def export_pdf():
        if not FPDF:
            return jsonify({"status": "error", "msg": "Librería FPDF no instalada."}), 500
        fecha = request.args.get('fecha', datetime.now().strftime('%Y-%m-%d'))
        try:
            with engine.connect() as conn:
                schedules = conn.execute(text("SELECT * FROM cro_vacunacion WHERE fecha = :f ORDER BY dupla ASC"),
                                         {"f": fecha}).mappings().fetchall()
                config = conn.execute(text("SELECT * FROM cro_diario_config WHERE fecha = :f"),
                                      {"f": fecha}).mappings().fetchone()

            cfg = dict(config) if config else {
                "entrega_nombres": "", "entrega_telefonos": "",
                "archivo_hora_inicio": "08:00", "archivo_hora_fin": "16:00",
                "papeleria_nombres": "", "papeleria_telefonos": "",
                "cargue_nombres": "", "cargue_telefonos": "",
                "validacion_nombres": "", "validacion_telefonos": "",
                "observaciones": "OBSERVACIONES: 1. DEBERÁN GESTIONAR LA RECEPCIÓN Y ENTREGA DE BIOLÓGICO EN CEMI SEGÚN PROGRAMACIÓN DEL DÍA A CARGO DE VACUNADOR.\nANOTADOR: DILIGENCIA EPICOLLECT BARRIDO DIARIO Y EPICOLLECT VACUNACION\nPSICOLOGO: DILIGENCIA EPICOLLECT DESESTIMIENTO"
            }

            pdf = FPDF(orientation='L', unit='mm', format='A4')
            pdf.set_auto_page_break(auto=False)
            pdf.add_page()

            def dibujar_encabezados_principales():
                pdf.set_font("Arial", 'B', 12)
                pdf.set_fill_color(30, 58, 138)
                pdf.set_text_color(255, 255, 255)
                pdf.cell(277, 8, txt="CRONOGRAMA VACUNACION APS", border=1, ln=True, align='C', fill=True)
                pdf.set_font("Arial", 'B', 10)
                pdf.set_fill_color(254, 240, 138)
                pdf.set_text_color(133, 77, 14)
                pdf.cell(277, 8, txt=f"{fecha}", border=1, ln=True, align='C', fill=True)

                pdf.set_font("Arial", 'B', 8)
                pdf.set_fill_color(255, 237, 213)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(277, 6, txt="ENTREGA Y RECIBIDO DE BIOLÓGICO EN CEMI", border=1, ln=True, align='L', fill=True)

                n_ent = str(cfg.get('entrega_nombres', '')).split(' | ')
                t_ent = str(cfg.get('entrega_telefonos', '')).split(' | ')
                ent_str = ""
                for n, t in zip(n_ent, t_ent):
                    if n.strip():
                        ent_str += f"{n.upper()} ({t})   "
                if ent_str:
                    pdf.set_font("Arial", 'B', 7)
                    pdf.set_text_color(30, 58, 138)
                    pdf.cell(277, 5, txt=ent_str, border=1, ln=True, align='L')

                pdf.ln(2)

                pdf.set_font("Arial", 'B', 5)
                pdf.set_fill_color(30, 58, 138)
                pdf.set_text_color(255, 255, 255)

                headers = ["DUPLA", "LUGAR VACUNACION", "HORARIO", "VACUNADORES", "TELEFONOS", "ANOTADORES",
                           "TELEFONOS", "PROFESIONALES VALORACION", "TELEFONOS", "DESISTIMIENTOS BARRIDO", "TELEFONOS"]
                global widths
                widths = [10, 28, 17, 35, 19, 35, 19, 38, 19, 38, 19]

                for h, w in zip(headers, widths):
                    pdf.cell(w, 8, h, border=1, align='C', fill=True)
                pdf.ln()

            dibujar_encabezados_principales()

            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", '', 5)
            h_cell = 3.5

            for s in schedules:
                hi = s['hora_inicio'].strftime('%H:%M') if isinstance(s['hora_inicio'], time) else str(
                    s.get('hora_inicio', ''))[:5]
                hf = s['hora_fin'].strftime('%H:%M') if isinstance(s['hora_fin'], time) else str(s.get('hora_fin', ''))[
                    :5]
                h_str = f"{hi} - {hf}"

                vac = str(s['vacunador']).replace(' | ', '\n')
                tvac = str(s['tel_vacunador']).replace(' | ', '\n')
                ano = str(s['anotador']).replace(' | ', '\n')
                tano = str(s['tel_anotador']).replace(' | ', '\n')
                pro = str(s['profesional_valoracion'] or '').replace(' | ', '\n')
                tpro = str(s['tel_profesional'] or '').replace(' | ', '\n')
                des = str(s['desistimientos'] or '').replace(' | ', '\n')
                tdes = str(s['tel_desistimientos'] or '').replace(' | ', '\n')

                lines_lugar = math.ceil(len(str(s['lugar'])) / 22.0)
                lines = max(
                    len(vac.split('\n')), len(ano.split('\n')),
                    len(pro.split('\n')), len(des.split('\n')),
                    lines_lugar
                )
                h_row = max(lines * h_cell, 6)

                if pdf.get_y() + h_row > 190:
                    pdf.add_page()
                    dibujar_encabezados_principales()
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font("Arial", '', 5)

                x = pdf.get_x()
                y = pdf.get_y()

                for w in widths:
                    pdf.cell(w, h_row, "", border=1)
                pdf.set_xy(x, y)

                pdf.cell(widths[0], h_row, str(s['dupla']), align='C')

                pdf.set_xy(x + sum(widths[:1]), y + max((h_row - lines_lugar * h_cell) / 2, 0))
                pdf.multi_cell(widths[1], h_cell, str(s['lugar']).upper(), align='C')

                pdf.set_xy(x + sum(widths[:2]), y)
                pdf.cell(widths[2], h_row, h_str, align='C')

                pdf.set_xy(x + sum(widths[:3]), y + max((h_row - len(vac.split('\n')) * h_cell) / 2, 0))
                pdf.multi_cell(widths[3], h_cell, vac, align='L')

                pdf.set_xy(x + sum(widths[:4]), y + max((h_row - len(tvac.split('\n')) * h_cell) / 2, 0))
                pdf.multi_cell(widths[4], h_cell, tvac, align='C')

                pdf.set_xy(x + sum(widths[:5]), y + max((h_row - len(ano.split('\n')) * h_cell) / 2, 0))
                pdf.multi_cell(widths[5], h_cell, ano, align='L')

                pdf.set_xy(x + sum(widths[:6]), y + max((h_row - len(tano.split('\n')) * h_cell) / 2, 0))
                pdf.multi_cell(widths[6], h_cell, tano, align='C')

                pdf.set_xy(x + sum(widths[:7]), y + max((h_row - len(pro.split('\n')) * h_cell) / 2, 0))
                pdf.multi_cell(widths[7], h_cell, pro, align='L')

                pdf.set_xy(x + sum(widths[:8]), y + max((h_row - len(tpro.split('\n')) * h_cell) / 2, 0))
                pdf.multi_cell(widths[8], h_cell, tpro, align='C')

                pdf.set_xy(x + sum(widths[:9]), y + max((h_row - len(des.split('\n')) * h_cell) / 2, 0))
                pdf.multi_cell(widths[9], h_cell, des, align='L')

                pdf.set_xy(x + sum(widths[:10]), y + max((h_row - len(tdes.split('\n')) * h_cell) / 2, 0))
                pdf.multi_cell(widths[10], h_cell, tdes, align='C')

                pdf.set_xy(x, y + h_row)

            if pdf.get_y() + 35 > 190:
                pdf.add_page()

            pdf.ln(3)
            pdf.set_fill_color(255, 237, 213)
            pdf.set_font("Arial", 'B', 7)
            pdf.cell(277, 6, "ARCHIVO Y PAIWEB EN OFICINA ADMINISTRATIVA APS", border=1, ln=True, fill=True)

            hi_arch = str(cfg.get('archivo_hora_inicio', '08:00'))[:5]
            hf_arch = str(cfg.get('archivo_hora_fin', '16:00'))[:5]
            horario_arch = f"{hi_arch} A {hf_arch}"

            x_arch = pdf.get_x()
            y_arch = pdf.get_y()
            pdf.cell(40, 18, "", border=1, fill=True)
            pdf.set_xy(x_arch, y_arch + 6)
            pdf.cell(40, 6, horario_arch, border=0, align='C')

            pdf.set_xy(x_arch + 40, y_arch)
            pdf.set_font("Arial", 'B', 7)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(45, 6, "PAPELERIA", border=1, align='C', fill=True)
            pdf.set_text_color(30, 58, 138)
            pdf.cell(152, 6, str(cfg.get('papeleria_nombres', '')).upper(), border=1, align='L', fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(40, 6, str(cfg.get('papeleria_telefonos', '')), border=1, align='R', fill=True)
            pdf.ln()

            pdf.set_x(x_arch + 40)
            pdf.cell(45, 6, "CARGUE A PAIWEB", border=1, align='C', fill=True)
            pdf.set_text_color(30, 58, 138)
            pdf.cell(152, 6, str(cfg.get('cargue_nombres', '')).upper(), border=1, align='L', fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(40, 6, str(cfg.get('cargue_telefonos', '')), border=1, align='R', fill=True)
            pdf.ln()

            pdf.set_x(x_arch + 40)
            pdf.cell(45, 6, "VALIDACION PAIWEB", border=1, align='C', fill=True)
            pdf.set_text_color(30, 58, 138)
            pdf.cell(152, 6, str(cfg.get('validacion_nombres', '')).upper(), border=1, align='L', fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(40, 6, str(cfg.get('validacion_telefonos', '')), border=1, align='R', fill=True)
            pdf.ln()

            pdf.set_font("Arial", 'B', 7)
            pdf.set_text_color(185, 28, 28)
            pdf.multi_cell(277, 5, txt=str(cfg.get('observaciones', '')).upper(), border=1, fill=True)

            response = make_response(pdf.output(dest='S').encode('latin1'))
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=cronograma_diario_{fecha}.pdf'
            return response
        except Exception as e:
            return jsonify({"status": "error", "msg": str(e)}), 500