# -*- coding: utf-8 -*-
import os
import unicodedata
from fpdf import FPDF

# Resolución dinámica de rutas absolutas para las imágenes
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_ESE = os.path.join(BASE_DIR, 'static', 'img', 'logo-ese.png')
LOGO_APS = os.path.join(BASE_DIR, 'static', 'img', 'logo-aps.png')


class PDF_Acceso(FPDF):
    def header(self):
        # Logo ESE (Extremo Superior Izquierdo) - Escala reducida (ancho 14)
        if os.path.exists(LOGO_ESE):
            try:
                self.image(LOGO_ESE, 12, 10, 14)
            except Exception:
                pass

        # Logo APS (Extremo Superior Derecho) - Escala conservada (ancho 35)
        if os.path.exists(LOGO_APS):
            try:
                self.image(LOGO_APS, 163, 10, 35)
            except Exception:
                pass

        # Título Central Institucional
        self.set_y(15)
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 51, 102)  # Azul oscuro corporativo
        self.cell(0, 8, 'SOLICITUD DE ACCESO UNIFICADO', 0, 1, 'C')

        self.set_font('Arial', 'B', 11)
        self.set_text_color(100, 100, 100)  # Gris técnico
        self.cell(0, 6, 'PLATAFORMAS PISIS - SI-APS', 0, 1, 'C')

        # Línea divisoria elegante
        self.set_draw_color(0, 75, 135)
        self.set_line_width(0.6)
        self.line(12, 35, 198, 35)
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.2)
        self.line(12, 282, 198, 282)

        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Documento tecnico autogenerado - Sistema RBAC PISIS - Pagina {self.page_no()}', 0, 0, 'C')


def normalizar_texto(texto):
    if not texto:
        return 'N/A'
    texto_str = str(texto).strip().replace('\n', ' ')
    texto_norm = unicodedata.normalize('NFKD', texto_str).encode('latin-1', 'ignore').decode('latin-1')
    return texto_norm


def generar_documento_pdf(datos):
    pdf = PDF_Acceso()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    secciones = {
        "1. IDENTIFICACION PERSONAL": [
            ('Tipo Documento', datos.get('tipo_documento', '')),
            ('Numero Documento', datos.get('numero_documento', '')),
            ('Nombre Completo', datos.get('nombre_completo', '')),
            ('Fecha Nacimiento', datos.get('fecha_nacimiento', '')),
            ('Nacionalidad', datos.get('nacionalidad', '')),
            ('Sexo al nacer', datos.get('sexo', ''))
        ],
        "2. CONTACTO Y AFILIACION EN SALUD": [
            ('Telefono Movil', datos.get('telefono', '')),
            ('Correo Electronico', datos.get('correo', '')),
            ('Regimen en Salud', datos.get('regimen', '')),
            ('EAPB (EPS)', datos.get('eapb', ''))
        ],
        "3. INFORMACION CONTRACTUAL Y OPERATIVA": [
            ('Rol Solicitado', datos.get('rol_solicitado', '')),
            ('Programa', datos.get('programa', '')),
            ('Territorio Asignado', datos.get('territorio', '')),
            ('Microterritorio', datos.get('microterritorio', '')),
            ('Perfil Profesional', datos.get('perfil_profesional', '')),
            ('Numero de Contrato', datos.get('numero_contrato', '')),
            ('Valor del Contrato', datos.get('valor_contrato', '')),
            ('Fecha de Inicio', datos.get('fecha_contrato', '')),
            ('Fecha de Finalizacion', datos.get('fecha_finalizacion_contrato', '')),
            ('Objeto Contractual', datos.get('objeto_contrato', ''))
        ]
    }

    for titulo, campos in secciones.items():
        # Encabezado de Sección
        pdf.set_font('Arial', 'B', 10)
        pdf.set_fill_color(0, 75, 135)
        pdf.set_text_color(255, 255, 255)
        pdf.set_draw_color(0, 75, 135)
        pdf.cell(0, 7, f"  {titulo}", border=1, ln=1, align='L', fill=True)

        pdf.set_text_color(50, 50, 50)
        pdf.set_draw_color(200, 200, 200)

        for key, val in campos:
            val_str = normalizar_texto(val)

            # Lógica inteligente para textos largos (ej. Objeto Contractual)
            if len(val_str) > 65:
                pdf.set_fill_color(245, 247, 250)
                pdf.set_font('Arial', 'B', 9)
                pdf.cell(0, 6, f" {key}:", border='LTR', ln=1, align='L', fill=True)

                pdf.set_fill_color(255, 255, 255)
                pdf.set_font('Arial', '', 9)
                pdf.multi_cell(0, 6, f" {val_str}", border='LBR', align='J', fill=True)
            else:
                # Estructura tabular a dos columnas para datos estándar
                pdf.set_fill_color(245, 247, 250)
                pdf.set_font('Arial', 'B', 9)
                pdf.cell(65, 7, f" {key}:", border=1, align='L', fill=True)

                pdf.set_fill_color(255, 255, 255)
                pdf.set_font('Arial', '', 9)
                pdf.cell(0, 7, f" {val_str}", border=1, align='L', fill=True, ln=1)

        pdf.ln(5)  # Espaciado entre secciones

    # Renderizado final a binario
    return pdf.output(dest='S').encode('latin-1')
