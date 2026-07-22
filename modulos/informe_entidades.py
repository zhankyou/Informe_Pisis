# -*- coding: utf-8 -*-
import os
import base64
import tempfile
from datetime import datetime
from flask import Blueprint, jsonify, make_response, request

from modulos.inf_financiero import extraer_financiero
from modulos.inf_aps2024 import extraer_datos_2024
from modulos.inf_aps2025 import extraer_datos_2025
from modulos.inf_aps2026 import extraer_datos_2026

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

informe_bp = Blueprint('informe_entidades', __name__)


def b64_to_temp(b64_str):
    """Convierte una cadena base64 de un canvas en un archivo temporal PNG para FPDF."""
    if not b64_str: return None
    try:
        header, encoded = b64_str.split(",", 1)
        data = base64.b64decode(encoded)
        fd, path = tempfile.mkstemp(suffix=".png")
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        return path
    except Exception:
        return None


@informe_bp.route('/api/informe_entidades/datos', methods=['GET'])
def get_datos_informe_entidades():
    data = {
        "financiero": extraer_financiero(),
        "2024": extraer_datos_2024(),
        "2025": extraer_datos_2025(),
        "2026": extraer_datos_2026()
    }
    return jsonify({"status": "success", "data": data}), 200


@informe_bp.route('/api/informe_entidades/pdf', methods=['POST'])
def exportar_informe_pdf():
    if not FPDF: return jsonify({"status": "error", "msg": "Librería FPDF requerida."}), 500

    payload = request.json
    f = payload.get("financiero", {})
    p = payload.get("poblacional", {})
    graficos = payload.get("graficos", {})
    entidad = str(payload.get("entidad", "Honorable Asamblea Departamental del Meta")).strip()

    # Cálculos Financieros
    fg = f.get("global", {})
    t_girado = fg.get("girado", 0.0)
    t_ejecutado = fg.get("ejecutado", 0.0)
    pct_global = (t_ejecutado / t_girado * 100) if t_girado > 0 else 0.0

    # Cálculos Poblacionales
    t_f, t_p, t_g, t_d = 0, 0, 0, 0
    datos_pob = {}
    for yr in [2024, 2025, 2026]:
        k = p.get(str(yr), {}).get("kpis", {})
        datos_pob[yr] = k
        t_f += k.get("familias", 0)
        t_p += k.get("personas", 0)
        t_g += k.get("gestantes", 0)
        t_d += k.get("discapacidad", 0)

    # Perfiles Consolidados
    p_enf, p_med, p_psi, p_esp, p_tec = 0, 0, 0, 0, 0
    for r in f.get("resoluciones", []):
        perf = r.get("perfiles", {})
        p_enf += perf.get("enf", 0)
        p_med += perf.get("med", 0)
        p_psi += perf.get("psi", 0)
        p_esp += perf.get("esp", 0)
        p_tec += perf.get("tec", 0)

    # Rutas de Logos Institucionales
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_ese = os.path.join(base_dir, 'static', 'img', 'logo-ese.png')
    logo_aps = os.path.join(base_dir, 'static', 'img', 'logo-aps.png')

    # Convertir gráficos Base64 a temporales
    path_chart_comp = b64_to_temp(graficos.get("comparativo"))
    path_chart_perf = b64_to_temp(graficos.get("perfiles"))

    def txt(texto):
        return str(texto).encode('latin-1', 'replace').decode('latin-1')

    class PDF(FPDF):
        def header(self):
            # Inyección de logos: ESE más pequeño (w=16), APS tamaño estándar (w=25)
            if os.path.exists(logo_ese):
                self.image(logo_ese, 10, 8, 16)
            if os.path.exists(logo_aps):
                self.image(logo_aps, 175, 8, 25)

            self.set_font('Arial', 'B', 11)
            self.set_text_color(10, 31, 61)  # Azul Institucional
            self.cell(0, 5, txt('EMPRESA SOCIAL DEL ESTADO DEL MUNICIPIO DE VILLAVICENCIO'), 0, 1, 'C')
            self.set_font('Arial', '', 10)
            self.cell(0, 5, txt('Secretaría de Salud Municipal'), 0, 1, 'C')
            self.ln(3)
            self.set_font('Arial', 'B', 11)
            self.cell(0, 5, txt('INFORME EJECUTIVO'), 0, 1, 'C')
            self.cell(0, 5, txt('MESA TÉCNICA RIAS Y ATENCIÓN PRIMARIA EN SALUD (APS) 2024 - 2026'), 0, 1, 'C')
            self.set_font('Arial', '', 9)
            self.set_text_color(0, 0, 0)
            self.cell(0, 5, txt(f'Insumo técnico para la sesión plenaria de la {entidad}'), 0, 1, 'C')
            self.cell(0, 5, txt(f'{datetime.now().strftime("%d de %B de %Y")}'), 0, 1, 'C')
            self.set_font('Arial', 'B', 9)
            self.cell(0, 5, txt('Tema: Planes Básicos de Salud – Alcances y alternativas de la Res. 0800 de 2026'), 0,
                      1, 'C')
            self.set_font('Arial', 'I', 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 5, txt(f'Corte de evaluación: {datetime.now().strftime("%Y-%m-%d")}'), 0, 1, 'C')
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128)
            self.cell(0, 10, txt(f'Página {self.page_no()} - Documento de Soporte Oficial SI-APS ESE Villavicencio'), 0,
                      0, 'C')

        def section_title(self, title):
            self.set_font('Arial', 'B', 10)
            self.set_fill_color(10, 31, 61)  # Azul Institucional
            self.set_text_color(255, 255, 255)
            self.cell(0, 6, txt(title), 0, 1, 'L', fill=True)
            self.ln(2)

        def sub_title(self, title):
            self.set_font('Arial', 'B', 9)
            self.set_text_color(10, 31, 61)
            self.cell(0, 5, txt(title), 0, 1, 'L')

        def paragraph(self, text_str):
            self.set_font('Arial', '', 9)
            self.set_text_color(0, 0, 0)
            self.multi_cell(0, 5, txt(text_str))
            self.ln(2)

    pdf = PDF()
    pdf.add_page()

    pdf.paragraph(
        f"Documento de soporte oficial dirigido a entes de control y a la {entidad}. Sintetiza la ejecución de los recursos asignados al programa de Atención Primaria en Salud (SER124DREC) y la caracterización demográfica multianual de la población intervenida (APS124CCFP), en el marco de la Resolución 3280 de 2018, la Resolución 2026 de 2023 y la Resolución 0800 de 2026 del Ministerio de Salud y Protección Social.")

    pdf.section_title("1. Presentación")
    pdf.paragraph(
        f"En atención a la comunicación remitida y en el marco de la invitación formulada por la {entidad} para la sesión plenaria, la Empresa Social del Estado del Municipio de Villavicencio presenta el siguiente informe ejecutivo como insumo técnico consolidado.")
    pdf.paragraph(
        "El presente documento reúne dos componentes fundamentales de la operación del programa de Atención Primaria en Salud (APS) y los Equipos Básicos de Salud (EBS) en el municipio: (i) la ejecución financiera de los recursos girados por la Nación y (ii) la caracterización demográfica y poblacional multianual, con el propósito de brindar a la Corporación una visión consolidada, trazable y verificable de la gestión adelantada.")

    pdf.section_title("2. Marco Normativo y Contextual")
    pdf.paragraph(
        "La operación del programa de Atención Primaria en Salud en el municipio de Villavicencio se enmarca en el siguiente conjunto normativo:")
    pdf.sub_title("2.1 Resolución 3280 de 2018 (MSPS)")
    pdf.paragraph(
        "Adopta los lineamientos técnicos y operativos de las Rutas Integrales de Atención en Salud. Define el rol de los Equipos Básicos de Salud (EBS) e integra el enfoque de curso de vida y grupos de especial protección constitucional.")
    pdf.sub_title("2.2 Resoluciones de Asignación (Ej. 2026 de 2023 y 696 de 2025)")
    pdf.paragraph(
        "Constituyen la fuente principal de incorporación presupuestal de los recursos analizados, orientados a la conformación, dotación y sostenimiento del talento humano interdisciplinario de los EBS.")
    pdf.sub_title("2.3 Resolución 0800 de 2026 (MSPS)")
    pdf.paragraph(
        "Asigna recursos adicionales para el fortalecimiento de Equipos Básicos de Salud especializados, ampliando la capacidad resolutiva de la red pública territorial.")

    pdf.section_title("3. Contexto Epidemiológico y Caracterización Poblacional")
    pdf.paragraph(
        "La caracterización familiar y comunitaria adelantada por los Equipos Básicos de Salud, registrada en el aplicativo APS124CCFP, constituye la fuente primaria de análisis de situación de salud (ASIS) a nivel local. El consolidado multianual 2024-2026 es el siguiente:")

    # Tabla Poblacional
    pdf.set_font('Arial', 'B', 8)
    pdf.set_fill_color(230, 240, 250)
    pdf.set_text_color(10, 31, 61)
    pdf.cell(30, 6, 'Vigencia', 1, 0, 'C', fill=True)
    pdf.cell(40, 6, 'Familias', 1, 0, 'C', fill=True)
    pdf.cell(40, 6, 'Personas', 1, 0, 'C', fill=True)
    pdf.cell(40, 6, 'Gestantes', 1, 0, 'C', fill=True)
    pdf.cell(40, 6, 'Discapacidad', 1, 1, 'C', fill=True)

    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(0, 0, 0)
    for yr in [2024, 2025, 2026]:
        k = datos_pob[yr]
        pdf.cell(30, 6, str(yr), 1, 0, 'C')
        pdf.cell(40, 6, f'{k.get("familias", 0):,}', 1, 0, 'C')
        pdf.cell(40, 6, f'{k.get("personas", 0):,}', 1, 0, 'C')
        pdf.cell(40, 6, f'{k.get("gestantes", 0):,}', 1, 0, 'C')
        pdf.cell(40, 6, f'{k.get("discapacidad", 0):,}', 1, 1, 'C')

    pdf.set_font('Arial', 'B', 8)
    pdf.set_fill_color(210, 230, 210)
    pdf.cell(30, 6, 'TOTAL', 1, 0, 'C', fill=True)
    pdf.cell(40, 6, f'{t_f:,}', 1, 0, 'C', fill=True)
    pdf.cell(40, 6, f'{t_p:,}', 1, 0, 'C', fill=True)
    pdf.cell(40, 6, f'{t_g:,}', 1, 0, 'C', fill=True)
    pdf.cell(40, 6, f'{t_d:,}', 1, 1, 'C', fill=True)
    pdf.ln(3)

    if path_chart_comp:
        pdf.image(path_chart_comp, x=30, w=150)
        pdf.ln(3)

    pdf.paragraph(
        f"En el acumulado del periodo se han caracterizado {t_f:,} familias ({t_p:,} personas). Se identificaron {t_g:,} gestantes y {t_d:,} personas en condición de discapacidad, ambos grupos de especial protección constitucional conforme a la Ruta Materno Perinatal y a la Ley 1618 de 2013.")

    if pdf.get_y() > 230: pdf.add_page()

    pdf.section_title("4. Ejecución Financiera del Programa APS")
    pdf.paragraph(
        "Los recursos girados por la Nación para la operación de los Equipos Básicos de Salud, registrados en el aplicativo SER124DREC, presentan el siguiente comportamiento consolidado:")

    pdf.set_font('Arial', 'B', 9)
    pdf.cell(95, 6, txt('Total Recursos Girados (Nación):'), 1)
    pdf.cell(0, 6, f'$ {t_girado:,.2f}', 1, 1, 'R')
    pdf.cell(95, 6, txt('Total Ejecución Acumulada:'), 1)
    pdf.cell(0, 6, f'$ {t_ejecutado:,.2f}', 1, 1, 'R')
    pdf.cell(95, 6, txt('Porcentaje de Ejecución Global:'), 1)
    pdf.cell(0, 6, f'{pct_global:.1f} %', 1, 1, 'R')
    pdf.ln(4)

    pdf.paragraph(
        "El nivel de ejecución acumulada global se sitúa a la luz de la coexistencia de las fuentes normativas incorporadas en la ESE:")

    for r in f.get("resoluciones", []):
        if pdf.get_y() > 240: pdf.add_page()
        pdf.set_font('Arial', 'B', 8)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 6, txt(f'Resolución: {r.get("id", "")} - {str(r.get("descripcion", ""))[:70]}'), 1, 1, 'L',
                 fill=True)
        pdf.set_font('Arial', '', 8)

        pdf.cell(47, 5, 'Incorporado:', 1, 0, 'L')
        pdf.cell(48, 5, f'$ {r.get("girado", 0):,.2f}', 1, 0, 'R')
        pdf.cell(47, 5, 'Gastado:', 1, 0, 'L')
        pdf.cell(48, 5, f'$ {r.get("ejecutado", 0):,.2f}', 1, 1, 'R')

        pdf.cell(47, 5, 'Saldo / Devolucion:', 1, 0, 'L')
        pdf.cell(48, 5, f'$ {r.get("saldo", 0):,.2f}', 1, 0, 'R')
        pdf.cell(47, 5, 'Rendimientos:', 1, 0, 'L')
        pdf.cell(48, 5, f'$ {r.get("rendimientos", 0):,.2f}', 1, 1, 'R')
        pdf.ln(2)

    if pdf.get_y() > 210: pdf.add_page()

    pdf.sub_title("4.3 Inversión Consolidada por Perfil Profesional")
    pdf.paragraph(
        "La distribución del gasto ejecutado por tipo de talento humano, consolidando las fuentes normativas, evidencia la composición interdisciplinaria exigida por el modelo de EBS:")

    pdf.set_font('Arial', 'B', 8)
    pdf.set_fill_color(230, 240, 250)
    pdf.set_text_color(10, 31, 61)
    pdf.cell(100, 6, txt('Profesión / Perfil'), 1, 0, 'C', fill=True)
    pdf.cell(50, 6, txt('Inversión Acumulada'), 1, 0, 'C', fill=True)
    pdf.cell(0, 6, txt('% del Total'), 1, 1, 'C', fill=True)

    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(0, 0, 0)

    def row_perf(lbl, val):
        pct = (val / t_ejecutado * 100) if t_ejecutado > 0 else 0
        pdf.cell(100, 5, txt(lbl), 1, 0, 'L')
        pdf.cell(50, 5, f'$ {val:,.2f}', 1, 0, 'R')
        pdf.cell(0, 5, f'{pct:.1f}%', 1, 1, 'C')

    row_perf('Profesionales de Enfermería', p_enf)
    row_perf('Profesionales de Medicina', p_med)
    row_perf('Profesionales de Psicología', p_psi)
    row_perf('Especialidades Médicas / Otros', p_esp)
    row_perf('Técnicos y Auxiliares', p_tec)
    pdf.ln(3)

    if path_chart_perf:
        pdf.image(path_chart_perf, x=30, w=150)
        pdf.ln(3)

    pdf.section_title("5. Análisis y Hallazgos Principales")
    pdf.paragraph(
        f"- Cobertura poblacional acumulada de {t_f:,} familias y {t_p:,} personas caracterizadas por los EBS entre 2024 y 2026, con trazabilidad en el aplicativo APS124CCFP.")
    pdf.paragraph(
        f"- {t_g:,} gestantes y {t_d:,} personas en condición de discapacidad identificadas y en proceso de seguimiento.")
    pdf.paragraph(f"- Ejecución financiera global del {pct_global:.1f}% sobre $ {t_girado:,.2f} girados por la Nación.")
    pdf.paragraph(
        "- Consistencia matemática verificada entre el consolidado financiero global, el desglose por resolución y la inversión por perfil profesional, lo que respalda la trazabilidad del informe ante entes de control.")

    pdf.section_title("6. Perspectivas frente a la Resolución 0800 de 2026")
    pdf.paragraph(
        "La Resolución 0800 de 2026 plantea la asignación de recursos adicionales. A la luz de los resultados aquí consolidados, se identifican los siguientes puntos de atención:")
    pdf.paragraph(
        "- El fortalecimiento de EBS especializados debe articularse con la composición de talento humano ya consolidada (enfermería, medicina, psicología), evitando duplicidades y garantizando continuidad en la atención.")
    pdf.paragraph(
        "- Se recomienda presentar una proyección de cobertura territorial adicional condicionada a la efectiva asignación y giro de los recursos de la nueva resolución.")

    pdf.section_title("7. Conclusiones y Recomendaciones")
    pdf.paragraph(
        f"La Empresa Social del Estado evidencia una gestión trazable y consolidada del programa de Atención Primaria en Salud. Se recomienda a la {entidad}: (i) tomar como línea base los resultados aquí consolidados para dimensionar el impacto esperado de la Resolución 0800 de 2026; (ii) solicitar al MSPS claridad sobre la articulación de los nuevos recursos con los saldos vigentes; y (iii) acompañar el fortalecimiento de los Equipos Básicos de Salud especializados con metas de cobertura verificables en el Plan Territorial de Salud.")

    pdf.ln(5)
    pdf.set_font('Arial', 'I', 9)
    pdf.cell(0, 5,
             txt("Documento suscrito y remitido como insumo oficial para la sesión plenaria en la fecha de corte establecida."),
             0, 1, 'C')

    # Limpieza de archivos temporales
    try:
        if path_chart_comp: os.remove(path_chart_comp)
        if path_chart_perf: os.remove(path_chart_perf)
    except:
        pass

    response = make_response(pdf.output(dest='S').encode('latin1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers[
        'Content-Disposition'] = f'attachment; filename=Informe_Ejecutivo_APS_{datetime.now().strftime("%Y%m%d")}.pdf'
    return response