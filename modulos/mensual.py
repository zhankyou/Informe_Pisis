# -*- coding: utf-8 -*-
import math
import datetime as dt
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


def registrar_rutas_mensual(bp):
    @bp.route('/api/cronograma/mensual', methods=['GET'])
    def get_mensual():
        mes = request.args.get('mes', datetime.now().strftime('%Y-%m'))
        try:
            with engine.connect() as conn:
                if engine.dialect.name == 'sqlite':
                    query = text(
                        "SELECT * FROM cro_programacion WHERE strftime('%Y-%m', fecha) = :m ORDER BY fecha ASC")
                else:
                    query = text(
                        "SELECT * FROM cro_programacion WHERE TO_CHAR(fecha, 'YYYY-MM') = :m ORDER BY fecha ASC")
                rows = conn.execute(query, {"m": mes}).mappings().fetchall()
            return jsonify({"status": "success", "data": [serialize_row(r) for r in rows]}), 200
        except Exception as e:
            return jsonify({"status": "error", "msg": str(e)}), 500

    @bp.route('/api/cronograma/mensual', methods=['POST'])
    def save_mensual():
        datos = request.json
        dias = datos.get('dias', [])
        mes = datos.get('mes')
        territorio_str = f"EQUIPO {datos.get('equipo')} / TERRITORIO {datos.get('territorio')}"

        if not dias:
            return jsonify({"status": "error", "msg": "Debe seleccionar al menos un día del mes."}), 400

        try:
            with engine.begin() as conn:
                if engine.dialect.name == 'sqlite':
                    conn.execute(
                        text("DELETE FROM cro_programacion WHERE territorio = :t AND strftime('%Y-%m', fecha) = :m"),
                        {"t": territorio_str, "m": mes})
                else:
                    conn.execute(
                        text("DELETE FROM cro_programacion WHERE territorio = :t AND TO_CHAR(fecha, 'YYYY-MM') = :m"),
                        {"t": territorio_str, "m": mes})

                for dia in dias:
                    fecha = f"{mes}-{str(dia).zfill(2)}"
                    conn.execute(text("""
                                      INSERT INTO cro_programacion (actividad_desc, territorio, fecha, hora_inicio, hora_fin)
                                      VALUES (:a, :t, :f, :hi, :hf)
                                      """), {
                                     "a": datos.get('actividad', ''),
                                     "t": territorio_str,
                                     "f": fecha,
                                     "hi": datos.get('hora_inicio', '00:00'),
                                     "hf": datos.get('hora_fin', '00:00')
                                 })
            return jsonify({"status": "success", "msg": "Cronograma mensual registrado/actualizado."}), 200
        except Exception as e:
            return jsonify({"status": "error", "msg": str(e)}), 500

    @bp.route('/api/cronograma/mensual', methods=['DELETE'])
    def delete_mensual():
        mes = request.args.get('mes')
        territorio = request.args.get('territorio')
        try:
            with engine.begin() as conn:
                if engine.dialect.name == 'sqlite':
                    conn.execute(
                        text("DELETE FROM cro_programacion WHERE territorio = :t AND strftime('%Y-%m', fecha) = :m"),
                        {"t": territorio, "m": mes})
                else:
                    conn.execute(
                        text("DELETE FROM cro_programacion WHERE territorio = :t AND TO_CHAR(fecha, 'YYYY-MM') = :m"),
                        {"t": territorio, "m": mes})
            return jsonify({"status": "success", "msg": "Programación mensual eliminada."}), 200
        except Exception as e:
            return jsonify({"status": "error", "msg": str(e)}), 500

    @bp.route('/api/cronograma/mensual/pdf', methods=['GET'])
    def export_mensual_pdf():
        if not FPDF:
            return jsonify({"status": "error", "msg": "Librería FPDF no instalada."}), 500

        mes = request.args.get('mes', datetime.now().strftime('%Y-%m'))
        try:
            with engine.connect() as conn:
                if engine.dialect.name == 'sqlite':
                    query = text(
                        "SELECT * FROM cro_programacion WHERE strftime('%Y-%m', fecha) = :m ORDER BY fecha ASC, territorio ASC")
                else:
                    query = text(
                        "SELECT * FROM cro_programacion WHERE TO_CHAR(fecha, 'YYYY-MM') = :m ORDER BY fecha ASC, territorio ASC")
                rows = conn.execute(query, {"m": mes}).mappings().fetchall()

            programacion = {}
            dias_set = set()

            for r in rows:
                fecha_obj = r['fecha']
                if isinstance(fecha_obj, str):
                    fecha_obj = datetime.strptime(fecha_obj, '%Y-%m-%d').date()
                dia = fecha_obj.day
                dias_set.add(dia)

                hora_i = r['hora_inicio'].strftime('%H:%M') if not isinstance(r['hora_inicio'], str) else str(
                    r['hora_inicio'])[:5]

                key = (r['actividad_desc'], r['territorio'], hora_i)
                if key not in programacion:
                    programacion[key] = set()
                programacion[key].add(dia)

            dias_list = sorted(list(dias_set))
            if not dias_list:
                return jsonify({"status": "error", "msg": "No hay datos para generar el PDF en este mes."}), 400

            meses_nombres = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE",
                             "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
            anio, mes_num = mes.split('-')
            mes_texto = f"{meses_nombres[int(mes_num) - 1]} ({anio})"
            dias_semana = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]

            col1_w, col2_w, col3_w = 55, 35, 20
            fixed_w = col1_w + col2_w + col3_w
            day_w = (277 - fixed_w) / max(len(dias_list), 1)

            pdf = FPDF(orientation='L', unit='mm', format='A4')
            pdf.set_auto_page_break(auto=False)

            def dibujar_encabezados():
                pdf.set_fill_color(219, 234, 254)
                pdf.set_text_color(0, 0, 0)

                pdf.set_font("Arial", 'B', 9)
                pdf.cell(277, 5, "CRONOGRAMA DE ACTIVIDADES MENSUAL", border=1, ln=True, align='C', fill=True)
                pdf.set_font("Arial", 'B', 7)
                pdf.cell(277, 4, "EMPRESA SOCIAL DEL ESTADO", border=1, ln=True, align='C', fill=True)
                pdf.cell(277, 4, "IDENTIFICACIÓN DEL EQUIPO BÁSICO DE SALUD", border=1, ln=True, align='C', fill=True)

                pdf.cell(fixed_w, 4, "MES", border=1, align='C', fill=True)
                pdf.cell(277 - fixed_w, 4, mes_texto, border=1, ln=True, align='C', fill=True)

                x_start = pdf.get_x()
                y_start = pdf.get_y()

                pdf.cell(col1_w, 8, "", border=1, align='C', fill=True)
                pdf.set_xy(x_start, y_start)
                pdf.cell(col1_w, 4, "ACTIVIDAD", border='LTR', align='C', fill=True)
                pdf.cell(col2_w, 4, "TERRITORIO", border='LTR', align='C', fill=True)
                pdf.set_font("Arial", 'B', 5)
                pdf.cell(col3_w, 4, "HORA DE INICIO", border='LTR', align='C', fill=True)
                pdf.set_font("Arial", 'B', 7)

                for dia in dias_list:
                    pdf.cell(day_w, 4, str(dia), border=1, align='C', fill=True)
                pdf.ln()

                pdf.cell(col1_w, 4, "", border='LBR', align='C', fill=True)
                pdf.cell(col2_w, 4, "", border='LBR', align='C', fill=True)
                pdf.set_font("Arial", 'B', 5)
                pdf.cell(col3_w, 4, "DE LA ACTIVIDAD", border='LBR', align='C', fill=True)

                for dia in dias_list:
                    fecha_dt = dt.date(int(anio), int(mes_num), dia)
                    nombre_dia = dias_semana[fecha_dt.weekday()]
                    if day_w < 8:
                        nombre_dia = nombre_dia[:3]
                    pdf.cell(day_w, 4, nombre_dia, border=1, align='C', fill=True)
                pdf.ln()

            pdf.add_page()
            dibujar_encabezados()

            pdf.set_font("Arial", '', 6)
            for (act, terr, hora), dias_marcados in programacion.items():
                act_str = str(act)
                terr_str = str(terr)

                try:
                    h_obj = datetime.strptime(hora, "%H:%M")
                    hora_str = h_obj.strftime("%I:%M %p").replace("AM", "A.M.").replace("PM", "P.M.")
                except:
                    hora_str = hora

                lines_act = math.ceil(len(act_str) / 32.0)
                lines_terr = len(terr_str.split('/'))
                max_lines = max(lines_act, lines_terr, 1)

                h_cell = 3.5
                h_row = max_lines * h_cell
                if h_row < 7: h_row = 7

                x, y = pdf.get_x(), pdf.get_y()
                if y + h_row > 195:
                    pdf.add_page()
                    dibujar_encabezados()
                    pdf.set_font("Arial", '', 6)
                    x, y = pdf.get_x(), pdf.get_y()

                pdf.cell(col1_w, h_row, "", border=1)
                pdf.cell(col2_w, h_row, "", border=1)
                pdf.cell(col3_w, h_row, "", border=1)
                for dia in dias_list:
                    if dia in dias_marcados:
                        pdf.set_fill_color(191, 219, 254)
                        pdf.cell(day_w, h_row, "X", border=1, align='C', fill=True)
                    else:
                        pdf.set_fill_color(255, 255, 255)
                        pdf.cell(day_w, h_row, "", border=1, align='C', fill=True)

                pdf.set_xy(x, y + max((h_row - lines_act * h_cell) / 2, 0))
                pdf.multi_cell(col1_w, h_cell, act_str, border=0, align='C')

                pdf.set_xy(x + col1_w, y + max((h_row - lines_terr * h_cell) / 2, 0))
                pdf.multi_cell(col2_w, h_cell, terr_str.replace(" / ", "\n"), border=0, align='C')

                pdf.set_xy(x + col1_w + col2_w, y)
                pdf.cell(col3_w, h_row, hora_str, border=0, align='C')

                pdf.set_xy(x, y + h_row)

            response = make_response(pdf.output(dest='S').encode('latin1'))
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=cronograma_mensual_{mes}.pdf'
            return response
        except Exception as e:
            return jsonify({"status": "error", "msg": str(e)}), 500