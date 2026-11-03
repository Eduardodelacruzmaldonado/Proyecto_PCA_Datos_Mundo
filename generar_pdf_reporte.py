# -*- coding: utf-8 -*-
"""
Generador de Reporte Académico en Formato PDF
Materia: Métodos Matemáticos para Ciencia de Datos
Institución: UNAM - IIMAS - Licenciatura en Ciencia de Datos
Alumnos: De La Cruz Maldonado José Eduardo, López Reyes Jorge
Profesora: Mtra. Nora Isabel Pérez Quezadas
"""
import os
import pandas as pd
import numpy as np

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

BASE_DIR = r"C:\Users\casa\.gemini\antigravity\scratch\pca_countries_project"
IMG_DIR = os.path.join(BASE_DIR, "graficas")
DATA_DIR = os.path.join(BASE_DIR, "datos")
PDF_PATH = os.path.join(BASE_DIR, "reporte", "Reporte_PCA_Countries_UNAM_IIMAS.pdf")

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            # Portada: sin encabezado ni pie de página
            return
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#444444"))
        
        # Encabezado superior
        self.drawString(54, 750, "UNAM · IIMAS · Licenciatura en Ciencia de Datos · Métodos Matemáticos para Ciencia de Datos")
        self.setStrokeColor(colors.HexColor("#002B49")) # Azul UNAM
        self.setLineWidth(0.8)
        self.line(54, 744, 558, 744)
        
        # Pie de página inferior
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        self.drawString(54, 34, "Proyecto: Análisis Multivariado y PCA de Países del Mundo")
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(558, 34, page_text)
        self.restoreState()


def build_academic_pdf():
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Paleta UNAM: Azul Marino (#002B49), Oro (#B8860B), Gris Oxford (#222222)
    c_unam_blue = colors.HexColor("#002B49")
    c_unam_gold = colors.HexColor("#B8860B")
    c_dark = colors.HexColor("#222222")
    c_accent = colors.HexColor("#1A5276")
    c_box_bg = colors.HexColor("#F8F9FA")
    c_box_border = colors.HexColor("#D5D8DC")
    
    # Estilos tipográficos
    title_univ = ParagraphStyle(
        'UnivTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=13, leading=17,
        alignment=1, textColor=c_unam_blue, spaceAfter=3
    )
    title_inst = ParagraphStyle(
        'InstTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10.5, leading=14,
        alignment=1, textColor=c_dark, spaceAfter=2
    )
    title_deg = ParagraphStyle(
        'DegTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10, leading=13,
        alignment=1, textColor=c_unam_gold, spaceAfter=14
    )
    doc_title = ParagraphStyle(
        'DocTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=17, leading=22,
        alignment=1, textColor=c_unam_blue, spaceAfter=10
    )
    doc_subtitle = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10.5, leading=14,
        alignment=1, textColor=c_dark, spaceAfter=20
    )
    meta_label = ParagraphStyle(
        'MetaLabel', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=9, leading=13,
        textColor=c_unam_blue
    )
    meta_val = ParagraphStyle(
        'MetaVal', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=13,
        textColor=c_dark
    )
    
    h1 = ParagraphStyle(
        'Heading1_Custom', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=12, leading=16,
        textColor=c_unam_blue, spaceBefore=12, spaceAfter=6,
        keepWithNext=True
    )
    h2 = ParagraphStyle(
        'Heading2_Custom', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10, leading=13.5,
        textColor=c_accent, spaceBefore=8, spaceAfter=4,
        keepWithNext=True
    )
    body = ParagraphStyle(
        'Body_Custom', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.5, leading=12.2,
        textColor=c_dark, spaceAfter=5, alignment=4
    )
    body_bold = ParagraphStyle(
        'BodyBold_Custom', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8.5, leading=12.2,
        textColor=c_dark, spaceAfter=4, keepWithNext=True
    )
    bullet = ParagraphStyle(
        'Bullet_Custom', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.2, leading=11.8,
        textColor=c_dark, leftIndent=14, firstLineIndent=-10, spaceAfter=2.5
    )
    formula_style = ParagraphStyle(
        'Formula_Custom', parent=styles['Normal'],
        fontName='Courier-Bold', fontSize=8.8, leading=12,
        textColor=c_unam_blue, alignment=1, spaceBefore=3, spaceAfter=5
    )
    code_text = ParagraphStyle(
        'CodeText', parent=styles['Normal'],
        fontName='Courier', fontSize=7.2, leading=9.8,
        textColor=colors.HexColor("#1A252C")
    )
    caption_style = ParagraphStyle(
        'Caption', parent=styles['Normal'],
        fontName='Helvetica-Oblique', fontSize=7.8, leading=10.5,
        alignment=1, textColor=colors.HexColor("#555555"), spaceBefore=3, spaceAfter=6
    )
    
    story = []
    
    # -------------------------------------------------------------
    # PORTADA ACADÉMICA
    # -------------------------------------------------------------
    story.append(Spacer(1, 10))
    story.append(Paragraph("UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICO", title_univ))
    story.append(Paragraph("INSTITUTO DE INVESTIGACIONES EN MATEMÁTICAS APLICADAS Y EN SISTEMAS (IIMAS)", title_inst))
    story.append(Paragraph("LICENCIATURA EN CIENCIA DE DATOS", title_deg))
    story.append(HRFlowable(width="100%", thickness=2, color=c_unam_blue, spaceBefore=0, spaceAfter=14))
    
    story.append(Spacer(1, 15))
    story.append(Paragraph("ANÁLISIS ESTADÍSTICO MULTIVARIADO Y REDUCCIÓN DE DIMENSIONALIDAD MEDIANTE COMPONENTES PRINCIPALES (PCA)", doc_title))
    story.append(Paragraph("Estudio Comparativo sobre Indicadores Socioeconómicos, Demográficos y Geográficos Globales", doc_subtitle))
    
    story.append(Spacer(1, 20))
    
    portada_table_data = [
        [Paragraph("ASIGNATURA:", meta_label), Paragraph("Métodos Matemáticos para Ciencia de Datos", meta_val)],
        [Paragraph("PROFESORA:", meta_label), Paragraph("Mtra. Nora Isabel Pérez Quezadas", meta_val)],
        [Paragraph("INTEGRANTES:", meta_label), Paragraph("De La Cruz Maldonado José Eduardo<br/>López Reyes Jorge", meta_val)],
        [Paragraph("FECHA:", meta_label), Paragraph("Noviembre de 2026", meta_val)],
        [Paragraph("DATASET:", meta_label), Paragraph("Countries of the World (Kaggle / CIA World Factbook)", meta_val)]
    ]
    t_portada = Table(portada_table_data, colWidths=[110, 394])
    t_portada.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('LINEBELOW', (0,0), (-1,-2), 0.5, colors.HexColor("#EEEEEE")),
        ('LINEBELOW', (0,-1), (-1,-1), 1, c_unam_gold),
    ]))
    story.append(t_portada)
    
    story.append(Spacer(1, 25))
    
    # Resumen Ejecutivo en Portada
    resumen_text = (
        "<b>Resumen Metodológico:</b> El presente proyecto desarrolla una investigación estadística y matemática rigurosa "
        "sobre el comportamiento multivariado de las naciones del mundo a partir de 16 variables cuantitativas de índole "
        "demográfica, geográfica, productiva y socioeconómica. A partir de los conceptos analizados en clase y plasmados en las notas "
        "de pizarrón, se abordan sistemáticamente las fases de: (1) preprocesamiento, limpieza técnica y justificación de exclusión de datos atípicos/incompletos; "
        "(2) clasificación teórica de dependencias estructurales; (3) análisis descriptivo de tendencia central y dispersión; "
        "(4) diagnóstico de multicolinealidad mediante matrices de covarianza y correlación de Pearson; "
        "(5) contrastación matemática experimental del impacto de la estandarización frente al uso de datos crudos; "
        "(6) descomposición espectral para la extracción de Componentes Principales sustentada en los criterios de Kaiser, scree plot y varianza acumulada; y "
        "(7) interpretación de cargas factoriales y proyección geopolítica en el Biplot factorial."
    )
    t_resumen = Table([[Paragraph(resumen_text, body)]], colWidths=[504])
    t_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_box_bg),
        ('BOX', (0,0), (-1,-1), 1, c_box_border),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_resumen)
    story.append(PageBreak())
    
    # -------------------------------------------------------------
    # SECCIÓN 1: INTRODUCCIÓN Y CONTEXTO MATEMÁTICO
    # -------------------------------------------------------------
    story.append(Paragraph("1. Introducción y Contexto del Análisis Multivariado", h1))
    story.append(Paragraph(
        "El análisis de Componentes Principales (PCA, por sus siglas en inglés) es una técnica matemática fundamental de reducción "
        "de dimensionalidad no supervisada en la ciencia de datos. Su propósito consiste en transformar linealmente un conjunto de p variables "
        "originales correlacionadas en un nuevo sistema ortogonal de variables no correlacionadas (ortogonales) denominadas componentes principales, "
        "ordenadas de manera decreciente según la proporción de varianza total explicada.",
        body
    ))
    story.append(Paragraph(
        "<b>Ventajas Matemáticas y Prácticas de PCA en Ciencia de Datos:</b>", body_bold
    ))
    story.append(Paragraph("• <b>Eliminación de Multicolinealidad:</b> Al ser ortogonales por construcción, las componentes principales poseen covarianza nula entre sí (Cov(CP_i, CP_j) = 0 para i ≠ j), lo que erradica la redundancia de información y estabiliza algoritmos de regresión o agrupamiento posteriores.", bullet))
    story.append(Paragraph("• <b>Compresión de Información y Mitigación del Ruido:</b> Permite retener la mayor parte de la inercia del sistema utilizando una cantidad sustancialmente menor de dimensiones (k << p), filtrando fluctuaciones aleatorias.", bullet))
    story.append(Paragraph("• <b>Visualización Geométrica Intuitiva:</b> Hace posible proyectar un espacio muestral de dimensión d = 16 sobre un subespacio de dos o tres dimensiones (Biplot), permitiendo detectar conglomerados naturales, patrones regionales y relaciones entre variables.", bullet))
    
    # -------------------------------------------------------------
    # SECCIÓN 2: LIMPIEZA, PREPROCESAMIENTO Y DEPURACIÓN DE DATOS
    # -------------------------------------------------------------
    story.append(Paragraph("2. Comprensión, Limpieza y Depuración del Conjunto de Datos", h1))
    story.append(Paragraph(
        "El conjunto de datos original <i>Countries of the World</i> contiene 227 observaciones y 20 columnas. "
        "Durante el diagnóstico exploratorio inicial se identificaron dos retos técnicos prioritarios:",
        body
    ))
    story.append(Paragraph("1. <b>Inconsistencia de Formato Numérico:</b> Múltiples columnas numéricas empleaban la convención europea de comas para separar cifras decimales (ej. '48,0' o '12,13'), interpretándose inicialmente como cadenas de texto (object). Se realizó una conversión vectorizada a coma flotante estándar.", bullet))
    story.append(Paragraph("2. <b>Presencia de Microterritorios con Pérdida Masiva de Datos:</b> Se realizó una auditoría de valores ausentes (NaN). Se identificó que 11 entidades territoriales carecían de 4 o más indicadores críticos (ej. Sahara Occidental, Gibraltar, San Marino, Groenlandia, Mayotte, Montserrat, Nauru, San Pedro y Miquelón, Santa Elena, Wallis y Futuna, Guernsey).", bullet))
    story.append(Paragraph(
        "<b>Justificación de la Exclusión de Entidades Territoriales:</b> En estadística multivariada, cuando una observación "
        "carece de más del 25-30% de sus atributos, cualquier mecanismo de imputación inventaría una proporción excesiva de su perfil, "
        "distorsionando artificialmente la matriz de covarianza muestral. Dichas 11 entidades no corresponden a naciones soberanas con economías "
        "autónomas completas, sino a micro-enclaves o colonias dependientes. Su exclusión matemática garantiza que los 216 países restantes "
        "formen una base sólida y confiable.",
        body
    ))
    story.append(Paragraph(
        "Para los 216 países soberanos restantes que presentaban datos ausentes aislados (1 o 2 atributos en Alfabetización, Telefonía o Sectores del PIB), "
        "se aplicó una imputación guiada por la <b>mediana dentro de su región geográfica</b> (ej. Europa del Este, África Subsahariana, Asia), "
        "respetando el nivel socioeconómico de cada contexto regional sin introducir sesgos homogéneos globales.",
        body
    ))
    
    # Anexo de código 1
    code_limpieza = (
        "# Conversión de texto con comas decimales a punto flotante\n"
        "for col in numeric_cols:\n"
        "    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.').str.strip(), errors='coerce')\n"
        "\n"
        "# Depuración fundamentada: exclusión de territorios con >= 4 datos faltantes\n"
        "df_clean = df[df.isnull().sum(axis=1) < 4].copy()   # De 227 a 216 observaciones\n"
        "\n"
        "# Imputación por mediana de la región geográfica respectiva\n"
        "for col in numeric_cols:\n"
        "    df_clean[col] = df_clean.groupby('Region')[col].transform(lambda x: x.fillna(x.median()))"
    )
    t_code1 = Table([[Paragraph(code_limpieza.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_text)]], colWidths=[504])
    t_code1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F2F4F4")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#BDC3C7")),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(KeepTogether([
        t_code1,
        Paragraph("Fragmento 1: Depuración de formato decimal, exclusión justificada e imputación condicional regional.", caption_style)
    ]))
    
    # -------------------------------------------------------------
    # SECCIÓN 3: CLASIFICACIÓN DE VARIABLES Y RELACIONES DE DEPENDENCIA
    # -------------------------------------------------------------
    story.append(Paragraph("3. Variables Independientes y Dependencias Estructurales", h1))
    story.append(Paragraph(
        "En el contexto de PCA no se asume formalmente un modelo de respuesta supervisado Y = f(X). No obstante, "
        "desde el punto de vista de la teoría del desarrollo económico y la geografía humana, las características analizadas "
        "presentan claras relaciones de causalidad y dependencia estructural:",
        body
    ))
    story.append(Paragraph("• <b>Variables Físico-Geográficas (Estrictamente Independientes/Exógenas):</b> <i>Área territorial</i> y <i>Tasa de Litoral/Superficie</i>. Son magnitudes dadas por la geografía física del planeta; no se modifican por el nivel de desarrollo humano ni por las políticas económicas.", bullet))
    story.append(Paragraph("• <b>Variables Demográficas Base:</b> <i>Población total</i> y <i>Densidad poblacional</i>. Son acumulativas e históricas, actuando como factores de escala demográfica.", bullet))
    story.append(Paragraph("• <b>Variables Socioeconómicas Fuertemente Dependientes:</b> <i>Mortalidad Infantil</i>, <i>Tasa de Natalidad</i> y <i>Teléfonos por 1000 hab.</i> dependen estrechamente del <i>PIB per cápita</i> y del porcentaje de <i>Alfabetización</i>. A mayores ingresos y educación, se observan inversiones directas en infraestructura médica y tecnológica, reduciendo la mortalidad e incrementando la cobertura de servicios.", bullet))
    story.append(Paragraph("• <b>Estructura Productiva (Dependencia Algebraica y de Etapa de Desarrollo):</b> Los sectores <i>Agricultura</i>, <i>Industria</i> y <i>Servicios</i> representan fracciones que suman aproximadamente la unidad. Economías con bajo PIB per cápita concentran su fuerza productiva en la agricultura primaria; economías terciarizadas transfieren su PIB masivamente al sector servicios.", bullet))
    
    # -------------------------------------------------------------
    # SECCIÓN 4: ANÁLISIS ESTADÍSTICO DESCRIPTIVO
    # -------------------------------------------------------------
    story.append(Paragraph("4. Análisis Estadístico Descriptivo Univariado", h1))
    story.append(Paragraph(
        "Siguiendo lo estipulado en las anotaciones del pizarrón escolar, se calcularon de forma exhaustiva las medidas "
        "de tendencia central (Media, Mediana) y de dispersión (Varianza s², Desviación Estándar s, Mínimo y Máximo) para las 16 características seleccionadas:",
        body
    ))
    
    df_desc = pd.read_csv(os.path.join(DATA_DIR, "estadisticas_descriptivas.csv"))
    tabla_stats_data = [["Variable", "Media", "Mediana", "Desv. Est.", "Mínimo", "Máximo"]]
    for _, row in df_desc.iterrows():
        v_name = str(row['Variable'])
        if len(v_name) > 23:
            v_name = v_name[:21] + "..."
        m_val = f"{row['Media']:,.2f}" if abs(row['Media']) < 10000 else f"{row['Media']:,.0f}"
        med_val = f"{row['Mediana']:,.2f}" if abs(row['Mediana']) < 10000 else f"{row['Mediana']:,.0f}"
        std_val = f"{row['Desv. Estándar']:,.2f}" if abs(row['Desv. Estándar']) < 10000 else f"{row['Desv. Estándar']:,.0f}"
        min_val = f"{row['Mínimo']:,.2f}" if abs(row['Mínimo']) < 10000 else f"{row['Mínimo']:,.0f}"
        max_val = f"{row['Máximo']:,.2f}" if abs(row['Máximo']) < 10000 else f"{row['Máximo']:,.0f}"
        tabla_stats_data.append([v_name, m_val, med_val, std_val, min_val, max_val])
    
    t_stats = Table(tabla_stats_data, colWidths=[144, 72, 72, 72, 72, 72])
    t_stats.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_unam_blue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.2),
        ('LEADING', (0,0), (-1,-1), 9.2),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D0D3D4")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8F9F9")]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(KeepTogether([
        t_stats,
        Paragraph("Tabla 1: Resumen de parámetros estadísticos descriptivos calculados sobre la muestra depurada (N = 216).", caption_style)
    ]))
    
    story.append(Paragraph(
        "<b>Interpretación de Dispersión y Asimetría:</b> Destaca la profunda discrepancia entre la media aritmética y la mediana "
        "en variables con distribución asimétrica positiva: en <i>Población</i> la media es de 30.2 millones pero la mediana es de únicamente 5.6 millones, "
        "debido a la influencia de superpotencias demográficas (China e India con más de 1,000 millones). "
        "Asimismo, la varianza de la <i>Población</i> (s² ≈ 1.37×10¹⁴) y del <i>Área</i> (s² ≈ 3.32×10¹²) superan por más de doce órdenes de magnitud "
        "a la varianza de las variables porcentuales y sectoriales (s² ≈ 0.02).",
        body
    ))
    
    # -------------------------------------------------------------
    # SECCIÓN 5: ANÁLISIS GRÁFICO UNIVARIADO (DISTRIBUCIONES Y BOXPLOTS)
    # -------------------------------------------------------------
    story.append(Paragraph("5. Análisis Gráfico Univariado y Detección de Datos Extremos", h1))
    story.append(Paragraph(
        "Para corroborar visualmente la presencia de colas pesadas y asimetrías, se construyeron los histogramas de frecuencia con estimación de densidad por kernel (KDE) "
        "y los diagramas de caja (boxplots) para los principales indicadores socioeconómicos.",
        body
    ))
    
    img_dist = os.path.join(IMG_DIR, "01_distribuciones_histogramas.png")
    if os.path.exists(img_dist):
        story.append(KeepTogether([
            Image(img_dist, width=6.6*inch, height=3.8*inch),
            Paragraph("Figura 1: Distribución empírica e histogramas de frecuencias con ajuste KDE para las 16 características.", caption_style)
        ]))
    
    img_box = os.path.join(IMG_DIR, "02_boxplots_socioeconomicos.png")
    if os.path.exists(img_box):
        story.append(KeepTogether([
            Image(img_box, width=6.6*inch, height=2.6*inch),
            Paragraph("Figura 2: Boxplots identificando valores atípicos y extremos (outliers) en las principales métricas del desarrollo.", caption_style)
        ]))
    
    story.append(Paragraph(
        "<b>Diagnóstico de Outliers:</b> En la Figura 2 se comprueba que el <i>PIB per cápita</i> y la tasa de <i>Teléfonos por 1000 habitantes</i> "
        "muestran una concentración masiva en niveles bajos, con un conjunto reducido de naciones atípicas de ingresos muy altos "
        "(ej. Luxemburgo con 55,100 USD, Noruega con 37,800 USD, Estados Unidos con 37,800 USD). Por el contrario, la <i>Mortalidad Infantil</i> "
        "presenta outliers superiores severos en países africanos subsaharianos (Angola con 191.19 por cada mil nacidos vivos).",
        body
    ))
    
    # -------------------------------------------------------------
    # SECCIÓN 6: MATRICES DE ASOCIACIÓN: COVARIANZA VS CORRELACIÓN
    # -------------------------------------------------------------
    story.append(Paragraph("6. Asociación Multivariada: Matriz de Covarianza vs. Matriz de Correlación", h1))
    story.append(Paragraph(
        "En consonancia con la formulación de Pearson anotada en el pizarrón escolar, la relación lineal entre dos variables aleatorias se define como:",
        body
    ))
    story.append(Paragraph("Pearson:   r_XY = Cov(X, Y) / ( s_X * s_Y )   =   ∑(x_i - x̄)(y_i - ȳ) / [ √(∑(x_i - x̄)²) * √(∑(y_i - ȳ)²) ]", formula_style))
    story.append(Paragraph(
        "La matriz de covarianza Σ cuantifica la covariación en unidades cruzadas de medida, mientras que la matriz de correlación R "
        "normaliza todas las relaciones al intervalo adimensional [-1, 1], reflejando la fuerza y sentido relativo de asociación.",
        body
    ))
    
    img_corr = os.path.join(IMG_DIR, "03_matriz_correlacion_heatmap.png")
    if os.path.exists(img_corr):
        story.append(KeepTogether([
            Image(img_corr, width=6.4*inch, height=4.2*inch),
            Paragraph("Figura 3: Matriz de Correlación de Pearson (r) para las 16 características numéricas analizadas.", caption_style)
        ]))
    
    story.append(Paragraph(
        "<b>Patrones de Multicolinealidad Detectados:</b>", body_bold
    ))
    story.append(Paragraph("• <b>Sinergia Tecnológico-Económica:</b> Fuerte correlación positiva entre <i>PIB per cápita</i> y <i>Teléfonos</i> (r = +0.83) y <i>Alfabetización</i> (r = +0.51).", bullet))
    story.append(Paragraph("• <b>Vulnerabilidad Demográfica y Rezago:</b> Fuerte correlación positiva entre <i>Mortalidad Infantil</i> y <i>Tasa de Natalidad</i> (r = +0.76) y <i>Sector Agrícola</i> (r = +0.70).", bullet))
    story.append(Paragraph("• <b>Antagonismo Estructural:</b> El <i>PIB per cápita</i> presenta marcada correlación negativa con la <i>Mortalidad Infantil</i> (r = -0.60), <i>Natalidad</i> (r = -0.64) y <i>Sector Agrícola</i> (r = -0.58).", bullet))
    
    # -------------------------------------------------------------
    # SECCIÓN 7: EXPERIMENTO COMPARATIVO DE ESTANDARIZACIÓN
    # -------------------------------------------------------------
    story.append(Paragraph("7. El Papel Crucial de la Estandarización: Comparativa Experimental", h1))
    story.append(Paragraph(
        "Un punto central de la clase fue responder: <i>'¿Qué pasa si estandarizamos y si no estandarizamos?'</i>. "
        "Para responderlo de forma rigurosa, se implementaron ambos esquemas y se comparó la descomposición espectral resultante:",
        body
    ))
    story.append(Paragraph("• <b>Sin Estandarizar (PCA sobre Covarianza Σ):</b> Las variables conservan sus unidades originales. La inercia total está dominada por las magnitudes cuadráticas.", bullet))
    story.append(Paragraph("• <b>Con Estandarización (PCA sobre Correlación R):</b> Cada variable se transforma a puntuaciones Z (media 0, varianza 1). La inercia total es igual al número de variables (Tr(R) = p = 16).", bullet))
    
    img_comp = os.path.join(IMG_DIR, "04_comparativa_estandarizacion_varianza.png")
    if os.path.exists(img_comp):
        story.append(KeepTogether([
            Image(img_comp, width=6.6*inch, height=2.8*inch),
            Paragraph("Figura 4: Comparativa empírica de varianza explicada por componente con y sin estandarización previa.", caption_style)
        ]))
    
    story.append(Paragraph(
        "<b>Demostración de la Falla Matemática sin Estandarización:</b> En la Figura 4 (panel izquierdo) se observa que "
        "<b>la primera componente principal absorbe el 99.98% de la varianza total</b> al no estandarizar. "
        "Esto ocurre exclusivamente porque la <i>Población</i> (en millones) tiene una varianza de 10¹⁴ y el <i>Área</i> de 10¹². "
        "PCA en covarianza cruda minimiza la distancia cuadrática en las escalas más grandes, volviendo 'invisibles' al PIB, "
        "la educación o la salud. Al estandarizar (panel derecho), cada variable aporta exactamente 1.0 a la inercia total, "
        "permitiendo que emerjan las verdaderas relaciones latentes multivariadas.",
        body
    ))
    
    # -------------------------------------------------------------
    # SECCIÓN 8: SELECCIÓN DE COMPONENTES PRINCIPALES (CRITERIOS FORMALES)
    # -------------------------------------------------------------
    story.append(Paragraph("8. Selección Formal de las Componentes Principales", h1))
    story.append(Paragraph(
        "La determinación del número k de componentes principales a retener se fundamentó en tres criterios matemáticos canónicos:",
        body
    ))
    story.append(Paragraph("1. <b>Criterio de Kaiser:</b> Retener componentes con valor propio λ_j > 1. Representan una cantidad de varianza mayor a la que aporta cualquier variable individual original estandarizada.", bullet))
    story.append(Paragraph("2. <b>Criterio del Scree Plot (Método del Codo):</b> Identificar el punto geométrico donde la curva de autovalores deja de descender drásticamente y se convierte en una meseta o sedimento.", bullet))
    story.append(Paragraph("3. <b>Criterio de Varianza Acumulada:</b> Alcanzar un porcentaje acumulado representativo del sistema (convencionalmente entre 70% y 80%).", bullet))
    
    img_scree = os.path.join(IMG_DIR, "05_scree_plot_kaiser.png")
    if os.path.exists(img_scree):
        story.append(KeepTogether([
            Image(img_scree, width=6.0*inch, height=3.0*inch),
            Paragraph("Figura 5: Gráfico de sedimentación (Scree Plot) con la cota teórica del Criterio de Kaiser (λ = 1.0).", caption_style)
        ]))
    
    pca_summary_data = [
        ["Componente", "Valor Propio (λ)", "Varianza Explicada (%)", "Varianza Acumulada (%)", "Criterio de Kaiser"],
        ["CP1", "5.3124", "33.05 %", "33.05 %", "Retener (λ > 1.0)"],
        ["CP2", "1.9523", "12.15 %", "45.19 %", "Retener (λ > 1.0)"],
        ["CP3", "1.5508", "9.65 %", "54.84 %", "Retener (λ > 1.0)"],
        ["CP4", "1.2743", "7.93 %", "62.77 %", "Retener (λ > 1.0)"],
        ["CP5", "1.0788", "6.71 %", "69.48 %", "Retener (λ > 1.0)"],
        ["CP6", "0.9686", "6.03 %", "75.51 %", "Cercano al corte (λ ≈ 1)"],
        ["CP7", "0.7838", "4.88 %", "80.38 %", "Descartar (λ < 1.0)"],
        ["CP8", "0.6883", "4.28 %", "84.66 %", "Descartar (λ < 1.0)"],
    ]
    t_pca_sum = Table(pca_summary_data, colWidths=[70, 95, 110, 115, 114])
    t_pca_sum.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_unam_blue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('LEADING', (0,0), (-1,-1), 9.5),
        ('ALIGN', (1,0), (3,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D0D3D4")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8F9F9")]),
        ('TEXTCOLOR', (4,1), (4,5), colors.HexColor("#196F3D")),
        ('FONTNAME', (4,1), (4,5), 'Helvetica-Bold'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(KeepTogether([
        t_pca_sum,
        Paragraph("Tabla 2: Valores propios de la matriz de correlación y decisión de retención dimensional.", caption_style)
    ]))
    
    story.append(Paragraph(
        "<b>Decisión y Fundamentación:</b> El Criterio de Kaiser determina la retención estricta de las primeras <b>5 componentes principales</b> "
        "(λ₁ = 5.31, λ₂ = 1.95, λ₃ = 1.55, λ₄ = 1.27, λ₅ = 1.08), las cuales resumen el <b>69.48% de la inercia total</b>. "
        "En el Scree Plot (Figura 5), el cambio de pendiente más pronunciado ocurre en el paso de CP1 a CP2, alcanzando una estabilización clara "
        "a partir de CP5. Si se requiere superar el umbral del 75%, CP6 representa una incorporación válida de soporte.",
        body
    ))
    
    # -------------------------------------------------------------
    # SECCIÓN 9: INTERPRETACIÓN DE LAS COMPONENTES Y CARGAS (LOADINGS)
    # -------------------------------------------------------------
    story.append(Paragraph("9. Interpretación Semántica y Cargas Factoriales (Loadings)", h1))
    story.append(Paragraph(
        "Las cargas factoriales (loadings) representan los coeficientes del vector propio ortonormal que definen cada componente principal. "
        "Miden la correlación directa entre cada variable original y el eje latente.",
        body
    ))
    
    img_loadings = os.path.join(IMG_DIR, "06_cargas_loadings_heatmap.png")
    if os.path.exists(img_loadings):
        story.append(KeepTogether([
            Image(img_loadings, width=4.2*inch, height=4.2*inch),
            Paragraph("Figura 6: Mapa de calor de las cargas factoriales (loadings) para las cinco componentes retenidas.", caption_style)
        ]))
    
    story.append(Paragraph(
        "<b>Interpretación Semántica de los Nuevos Ejes Latentes:</b>", body_bold
    ))
    story.append(Paragraph("• <b>Componente Principal 1 (33.05% varianza) - 'Eje de Desarrollo Socioeconómico':</b> "
                           "Presenta cargas marcadamente positivas en <i>Mortalidad Infantil (+0.40)</i>, <i>Tasa de Natalidad (+0.39)</i> y <i>Sector Agrícola (+0.35)</i>, "
                           "y cargas marcadamente negativas en <i>Teléfonos (-0.37)</i>, <i>Alfabetización (-0.35)</i>, <i>PIB per cápita (-0.35)</i> y <i>Servicios (-0.33)</i>. "
                           "Sintetiza la transición global entre economías agrarias vulnerables (valores positivos) y economías industrializadas con alto bienestar (valores negativos).",
                           body))
    story.append(Paragraph("• <b>Componente Principal 2 (12.15% varianza) - 'Eje de Insularidad y Cultivos Tropicales':</b> "
                           "Liderada positivamente por <i>Cultivos Permanentes (+0.55)</i> y <i>Tasa de Litoral (+0.41)</i>, y negativamente por <i>Migración Neta (-0.42)</i> y <i>Área (-0.32)</i>. "
                           "Distingue a pequeños estados insulares y costeros frente a grandes países continentales receptores de migración.",
                           body))
    story.append(Paragraph("• <b>Componente Principal 3 (9.65% varianza) - 'Eje de Escala Demográfica y Territorial':</b> "
                           "Cargada por <i>Población (+0.52)</i>, <i>Área (+0.39)</i> y <i>Tierra Arable (+0.33)</i> frente a <i>Densidad (-0.36)</i>. "
                           "Aísla de manera natural a los gigantes continentales (China, India, Rusia, EE.UU., Brasil).",
                           body))
    
    # -------------------------------------------------------------
    # SECCIÓN 10: PROYECCIÓN FACTORIAL Y BIPLOT
    # -------------------------------------------------------------
    story.append(Paragraph("10. Proyección Factorial Geopolítica y Biplot (CP1 vs. CP2)", h1))
    story.append(Paragraph(
        "El Biplot proyecta de manera simultánea las observaciones (los 216 países clasificados por región) y los vectores directores "
        "de las variables en el plano bidimensional definido por CP1 y CP2 (que agrupan el 45.20% de la varianza total).",
        body
    ))
    
    img_biplot = os.path.join(IMG_DIR, "07_biplot_cp1_cp2.png")
    if os.path.exists(img_biplot):
        story.append(KeepTogether([
            Image(img_biplot, width=6.6*inch, height=4.2*inch),
            Paragraph("Figura 7: Biplot bidimensional (CP1 vs. CP2). Proyección de naciones por región y vectores de características.", caption_style)
        ]))
    
    story.append(Paragraph(
        "<b>Interpretación de la Proyección Geopolítica:</b>", body_bold
    ))
    story.append(Paragraph("• <b>Europa Occidental y Norteamérica:</b> Se proyectan en el sector izquierdo (CP1 negativo), perfectamente alineadas con las flechas de PIB per cápita, servicios y telefonía (ej. Noruega, Alemania, EE.UU.).", bullet))
    story.append(Paragraph("• <b>África Subsahariana:</b> Se agrupa en el sector derecho (CP1 positivo), en concordancia con los vectores de mortalidad infantil, natalidad y agricultura (ej. Sierra Leona, Somalia, Etiopía).", bullet))
    story.append(Paragraph("• <b>América Latina y Asia Intermedia:</b> Países como México, Colombia o Tailandia ocupan posiciones centrales en CP1, evidenciando economías mixtas en etapas medias de transición demográfica.", bullet))
    
    # -------------------------------------------------------------
    # SECCIÓN 11: CONCLUSIONES METODOLÓGICAS
    # -------------------------------------------------------------
    story.append(Paragraph("11. Conclusiones Metodológicas", h1))
    story.append(Paragraph(
        "1. <b>Necesidad Ineludible de la Estandarización:</b> Se probó de forma fehaciente que el PCA aplicado directamente sobre matrices de covarianza con variables en unidades heterogéneas falla al colapsar en las magnitudes absolutas mayores (Población). La estandarización sobre la matriz de correlación es matemáticamente indispensable.",
        body
    ))
    story.append(Paragraph(
        "2. <b>Eficiencia en la Reducción Dimensional:</b> Aplicando rigurosamente el criterio de Kaiser (λ > 1.0), se redujo el espacio de 16 a 5 variables sintéticas ortogonales, conservando cerca del 70% de la información original sin redundancia lineal.",
        body
    ))
    story.append(Paragraph(
        "3. <b>Capacidad de Descubrimiento de PCA:</b> Sin utilizar información de supervisión ni etiquetas predeterminadas, la primera componente principal reconstruyó de forma matemática y espontánea el gradiente de desarrollo socioeconómico global.",
        body
    ))
    
    # -------------------------------------------------------------
    # SECCIÓN 12: ANEXO DE IMPLEMENTACIÓN EN PYTHON
    # -------------------------------------------------------------
    story.append(Paragraph("12. Anexo de Implementación en Python", h1))
    story.append(Paragraph(
        "Fragmentos modulares y ordenados empleados para la reproducción exacta de la metodología matemática:",
        body
    ))
    
    code_mod1 = (
        "# MÓDULO A: ESTANDARIZACIÓN Y DESCOMPOSICIÓN ESPECTRAL (PCA)\n"
        "from sklearn.preprocessing import StandardScaler\n"
        "from sklearn.decomposition import PCA\n"
        "\n"
        "# Estandarización Z-score (mu = 0, sigma^2 = 1)\n"
        "scaler = StandardScaler()\n"
        "X_scaled = scaler.fit_transform(X_clean[pca_features])\n"
        "\n"
        "# Ajuste de PCA sobre la matriz de correlación implícita\n"
        "pca = PCA()\n"
        "scores = pca.fit_transform(X_scaled)\n"
        "eigenvalues = pca.explained_variance_                  # Autovalores (lambda)\n"
        "var_ratio = pca.explained_variance_ratio_ * 100         # Varianza por componente (%)\n"
        "kaiser_idx = np.where(eigenvalues > 1.0)[0]             # Componentes que cumplen Kaiser"
    )
    t_mod1 = Table([[Paragraph(code_mod1.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_text)]], colWidths=[504])
    t_mod1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F2F4F4")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#BDC3C7")),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(KeepTogether([
        t_mod1,
        Paragraph("Fragmento 2: Estandarización de variables, cálculo de autovalores y verificación del Criterio de Kaiser.", caption_style)
    ]))
    
    story.append(Spacer(1, 6))
    
    code_mod2 = (
        "# MÓDULO B: CONSTRUCCIÓN DEL BIPLOT Y MATRIZ DE CARGAS (LOADINGS)\n"
        "loadings = pd.DataFrame(pca.components_.T, index=pca_features, columns=[f'CP{i+1}' for i in range(len(pca_features))])\n"
        "\n"
        "# Gráfico Biplot bidimensional (CP1 vs CP2)\n"
        "fig, ax = plt.subplots(figsize=(12, 8))\n"
        "ax.scatter(scores[:, 0], scores[:, 1], c=colores_region, alpha=0.7)\n"
        "scale = 4.5\n"
        "for i, feat in enumerate(pca_features):\n"
        "    ax.arrow(0, 0, pca.components_[0, i]*scale, pca.components_[1, i]*scale, color='red', head_width=0.15)\n"
        "    ax.text(pca.components_[0, i]*scale*1.1, pca.components_[1, i]*scale*1.1, feat, color='darkred', weight='bold')\n"
        "ax.set_xlabel(f'CP1 ({var_ratio[0]:.1f}% varianza)')\n"
        "ax.set_ylabel(f'CP2 ({var_ratio[1]:.1f}% varianza)')"
    )
    t_mod2 = Table([[Paragraph(code_mod2.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_text)]], colWidths=[504])
    t_mod2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F2F4F4")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#BDC3C7")),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(KeepTogether([
        t_mod2,
        Paragraph("Fragmento 3: Algoritmo para la proyección del Biplot y trazado de vectores ortogonales de carga.", caption_style)
    ]))
    
    # Compilar documento final
    doc.build(story, canvasmaker=NumberedCanvas)
    print("¡PDF recompilado con flujo continuo en:", PDF_PATH)

if __name__ == "__main__":
    build_academic_pdf()
