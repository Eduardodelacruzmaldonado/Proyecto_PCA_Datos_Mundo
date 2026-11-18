# -*- coding: utf-8 -*-
"""
Genera el reporte en PDF del proyecto a partir de los resultados de exploracion_pca.py.

Uso (desde la carpeta del proyecto):
    python exploracion_pca.py        # en macOS / Linux: python3
    python generar_pdf_reporte.py

El PDF queda en reporte/Proyecto_PCA_Paises.pdf. Todos los números del texto se leen de la carpeta
"resultados", de modo que el reporte siempre corresponde al análisis que se ejecutó. El código del
análisis no aparece en el reporte: está explicado en el notebook analisis_pca.ipynb. Las fuentes
tipográficas vienen en la carpeta "fuentes", así que el PDF se ve igual en Windows, macOS y Linux.
"""
import json
import math
import sys
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent
FIG = BASE / "graficas"
RES = BASE / "resultados"
FUENTES = BASE / "fuentes"
FORM = FIG / "formulas"
SALIDA = BASE / "reporte" / "Proyecto_PCA_Paises.pdf"

if not (RES / "resultados.json").exists():
    sys.exit("No se encontraron los resultados. Ejecuta primero: python exploracion_pca.py")
FORM.mkdir(parents=True, exist_ok=True)
SALIDA.parent.mkdir(parents=True, exist_ok=True)

R = json.loads((RES / "resultados.json").read_text(encoding="utf-8"))
NOMBRES = R["NOMBRES"]
VARS = R["VARS"]
desc = pd.read_csv(RES / "medidas_descriptivas.csv", index_col=0, encoding="utf-8")
cov_orig = pd.read_csv(RES / "matriz_covarianza_original.csv", index_col=0, encoding="utf-8")
corr = pd.read_csv(RES / "matriz_correlacion.csv", index_col=0, encoding="utf-8")
estad = pd.read_csv(RES / "estadisticas_por_variable.csv", encoding="utf-8")
rango = pd.read_csv(RES / "rango_varianza_transformada.csv", index_col=0, encoding="utf-8")
N = lambda v: NOMBRES[v]                                       # nombre en español
def n_(v):
    """Nombre de la variable en minúscula para usarlo dentro de una frase (respeta siglas como PIB)."""
    t = NOMBRES[v]
    return t if t[:3].isupper() else t[0].lower() + t[1:]


# ---------------------------------------------------------------------------------------------
# Tipografía y estilos
# ---------------------------------------------------------------------------------------------
for nombre, archivo in (("Serif", "LiberationSerif-Regular.ttf"), ("Serif-Bold", "LiberationSerif-Bold.ttf"),
                        ("Serif-Italic", "LiberationSerif-Italic.ttf"),
                        ("Serif-BoldItalic", "LiberationSerif-BoldItalic.ttf")):
    pdfmetrics.registerFont(TTFont(nombre, str(FUENTES / archivo)))
pdfmetrics.registerFontFamily("Serif", normal="Serif", bold="Serif-Bold", italic="Serif-Italic",
                              boldItalic="Serif-BoldItalic")

ANCHO = 468                                                     # ancho útil (8.5 in - 2 in)
cuerpo = ParagraphStyle("cuerpo", fontName="Serif", fontSize=10.5, leading=14.6, alignment=TA_JUSTIFY,
                        spaceAfter=6)
h1 = ParagraphStyle("h1", fontName="Serif-Bold", fontSize=15, leading=19, spaceBefore=16, spaceAfter=8,
                    keepWithNext=True)
h2 = ParagraphStyle("h2", fontName="Serif-Bold", fontSize=11.5, leading=15, spaceBefore=11, spaceAfter=3,
                    keepWithNext=True)
h3 = ParagraphStyle("h3", fontName="Serif-BoldItalic", fontSize=10.5, leading=14, spaceBefore=10,
                    spaceAfter=2, keepWithNext=True)
pie = ParagraphStyle("pie", fontName="Serif-Italic", fontSize=9, leading=11.5, alignment=TA_CENTER,
                     spaceBefore=3, spaceAfter=8)
tit_tabla = ParagraphStyle("tit_tabla", fontName="Serif-Italic", fontSize=9, leading=11.5, alignment=TA_LEFT,
                           spaceBefore=4, spaceAfter=3, keepWithNext=True)
celda = ParagraphStyle("celda", fontName="Serif", fontSize=8.5, leading=10.5)
celda_b = ParagraphStyle("celda_b", parent=celda, fontName="Serif-Bold")
biblio = ParagraphStyle("biblio", fontName="Serif", fontSize=9, leading=12, leftIndent=0, spaceAfter=3)
centro = lambda tam, fuente="Serif", esp=0: ParagraphStyle(f"c{tam}{fuente}{esp}", fontName=fuente, fontSize=tam,
                                                           leading=tam * 1.3, alignment=TA_CENTER, spaceAfter=esp)


# ---------------------------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------------------------
def num(x):
    """Formato de los números del reporte (separador de miles y decimales según la magnitud)."""
    x = float(x)
    if x == 0:
        return "0"
    a = abs(x)
    if a >= 1e4:
        return f"{x:,.0f}"
    if a >= 1000:
        return f"{x:,.1f}"
    if a >= 100:
        return f"{x:.1f}"
    if a >= 1:
        return f"{x:.2f}"
    return f"{x:.3f}"


PALABRA = {1: "una", 2: "dos", 3: "tres", 4: "cuatro", 5: "cinco", 6: "seis"}


def redondeo(x, dec):
    """Redondeo comercial (0.725 -> 0.73), como se escribe a mano."""
    from decimal import Decimal, ROUND_HALF_UP
    return str(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-dec), rounding=ROUND_HALF_UP))


def lista(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " y " + items[-1]


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


story = []
P = lambda texto, estilo=cuerpo: story.append(Paragraph(texto, estilo))


def H1(texto):
    story.append(Paragraph(texto, h1))


def H2(texto):
    story.append(Paragraph(texto, h2))


def H3(texto):
    story.append(Paragraph(texto, h3))


# Numeración automática de figuras y tablas en el orden en que aparecen
ORDEN_FIG = (["categoricas", "faltantes", "imputacion", "log"] + [f"hb_{i:02d}" for i in range(len(estad))]
             + ["atipicos", "cov", "corr", "comparacion", "vec_pares", "scree", "cargas",
                "biplot", "recon", "cp1", "planos", "spline_pib", "rendimientos"])
F = {k: i + 1 for i, k in enumerate(ORDEN_FIG)}
ORDEN_TAB = ["variables", "descartadas", "imputacion", "descriptivas", "cov_completa", "covarianza", "atipicos", "pares", "menos",
             "eig_pares", "valores", "recon", "rango", "comparacion", "spline_coef", "spline_pred"]
T = {k: i + 1 for i, k in enumerate(ORDEN_TAB)}


def figura(archivo, ancho, texto, clave):
    ruta = FIG / archivo
    from reportlab.lib.utils import ImageReader
    w, h = ImageReader(str(ruta)).getSize()
    img = Image(str(ruta), width=ancho, height=ancho * h / w)
    story.append(KeepTogether([Spacer(1, 4), img, Paragraph(f"Figura {F[clave]}. {texto}", pie)]))


def tabla(clave, titulo, filas, anchos, encabezado=True, alinear_der=(), est_celda=None, est_cab=None, relleno=3):
    personalizado = est_celda is not None              # la primera columna también va en negritas
    est_celda, est_cab = est_celda or celda, est_cab or celda_b
    datos = [[Paragraph(str(c), est_cab if (encabezado and i == 0) or (personalizado and j == 0) else est_celda)
              for j, c in enumerate(fila)] for i, fila in enumerate(filas)]
    t = Table(datos, colWidths=anchos, repeatRows=1 if encabezado else 0, hAlign="CENTER")
    estilo = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 2.2),
              ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2), ("LEFTPADDING", (0, 0), (-1, -1), relleno),
              ("RIGHTPADDING", (0, 0), (-1, -1), relleno),
              ("LINEABOVE", (0, 0), (-1, 0), .9, colors.black),
              ("LINEBELOW", (0, -1), (-1, -1), .9, colors.black)]
    if encabezado:
        estilo.append(("LINEBELOW", (0, 0), (-1, 0), .5, colors.black))
    t.setStyle(TableStyle(estilo))
    story.append(Paragraph(f"Tabla {T[clave]}. {titulo}", tit_tabla))
    story.append(t)
    story.append(Spacer(1, 8))


def mat(tex, clave, tam=10.5):
    """Fórmula pequeña dentro de un párrafo: imagen alineada con la línea base del texto."""
    from matplotlib import mathtext
    from matplotlib.font_manager import FontProperties
    ruta = FORM / f"en_linea_{clave}.png"
    prof = mathtext.math_to_image(tex, str(ruta), prop=FontProperties(size=tam, math_fontfamily="stix"), dpi=300)
    from reportlab.lib.utils import ImageReader
    w, h = ImageReader(str(ruta)).getSize()
    return (f'<img src="{ruta}" width="{w * 72 / 300:.2f}" height="{h * 72 / 300:.2f}" '
            f'valign="{-prof * 72 / 300:.2f}"/>')


def formula(clave, tex, tam=12.5):
    """Dibuja una fórmula con mathtext de matplotlib y la inserta centrada."""
    ruta = FORM / f"{clave}.png"
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, tex, fontsize=tam, math_fontfamily="stix")
    fig.savefig(ruta, dpi=300, bbox_inches="tight", pad_inches=0.04, transparent=False)
    plt.close(fig)
    from reportlab.lib.utils import ImageReader
    w, h = ImageReader(str(ruta)).getSize()
    escala = min(1.0, ANCHO / (w * 72 / 300))
    img = Image(str(ruta), width=w * 72 / 300 * escala, height=h * 72 / 300 * escala)
    story.append(Spacer(1, 3)); story.append(img); story.append(Spacer(1, 5))


# ---------------------------------------------------------------------------------------------
# Plantillas de página, encabezados del índice y pie de página
# ---------------------------------------------------------------------------------------------
class Reporte(BaseDocTemplate):
    def __init__(self, ruta, **kw):
        super().__init__(str(ruta), pagesize=letter, leftMargin=72, rightMargin=72, topMargin=72,
                         bottomMargin=66, title="Exploración de datos y componentes principales",
                         author="De La Cruz Maldonado José Eduardo; López Reyes Jorge", **kw)
        marco = Frame(72, 66, ANCHO, letter[1] - 72 - 66, id="marco")
        ancho_h, alto_h = landscape(letter)
        marco_h = Frame(72, 66, ancho_h - 144, alto_h - 72 - 66, id="marco_h")
        self.addPageTemplates([PageTemplate("portada", [marco]),
                               PageTemplate("normal", [marco], onPage=self.pie_de_pagina),
                               PageTemplate("horizontal", [marco_h], onPage=self.pie_de_pagina,
                                            pagesize=landscape(letter))])

    @staticmethod
    def pie_de_pagina(canv, doc):
        canv.saveState()
        derecha = canv._pagesize[0] - 72
        canv.setStrokeColorRGB(.6, .6, .6); canv.setLineWidth(.4); canv.line(72, 54, derecha, 54)
        canv.setFont("Serif", 8.5); canv.setFillColor(colors.HexColor("#444444"))
        canv.drawString(72, 39.6, "Métodos Matemáticos Computacionales para Ciencia de Datos")
        canv.drawRightString(derecha, 39.6, str(doc.page))
        canv.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in ("h1", "h2", "h3"):
            nivel = {"h1": 0, "h2": 1, "h3": 2}[flowable.style.name]
            texto = flowable.getPlainText()
            if texto in ("Resumen", "Contenido"):
                return
            clave = f"s{id(flowable)}"
            self.canv.bookmarkPage(clave)
            self.canv.addOutlineEntry(texto, clave, level=nivel, closed=nivel > 0)
            self.notify("TOCEntry", (nivel, texto, self.page, clave))


# =============================================================================================
# CONTENIDO
# =============================================================================================
# Portada ---------------------------------------------------------------------------------------
story.append(Spacer(1, 22))
P("UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICO", centro(15, "Serif-Bold", 2))
P("Instituto de Investigaciones en Matemáticas Aplicadas y en Sistemas", centro(13))
P("Licenciatura en Ciencia de Datos", centro(13, esp=26))
story.append(Table([[""]], colWidths=[ANCHO], style=[("LINEABOVE", (0, 0), (-1, 0), .8, colors.black)]))
story.append(Spacer(1, 30))
P("Métodos Matemáticos Computacionales para Ciencia de Datos", centro(14, esp=24))
P("Exploración de datos y reducción de dimensiones<br/>con componentes principales",
  ParagraphStyle("titulo", fontName="Serif-Bold", fontSize=21, leading=27, alignment=TA_CENTER, spaceAfter=12))
P(f"Indicadores demográficos, económicos y geográficos de {R['n_paises']} países", centro(13, "Serif-Italic", 26))
story.append(Table([[""]], colWidths=[ANCHO], style=[("LINEABOVE", (0, 0), (-1, 0), .8, colors.black)]))
story.append(Spacer(1, 34))
etq = ParagraphStyle("etq", fontName="Serif-Bold", fontSize=11.5, leading=16)
val = ParagraphStyle("val", fontName="Serif", fontSize=11.5, leading=16)
datos_portada = [[Paragraph("Integrantes", etq), Paragraph("De La Cruz Maldonado José Eduardo<br/>López Reyes Jorge Armando", val)],
                 [Paragraph("Profesora", etq), Paragraph("Nora Isabel Pérez Quezadas", val)],
                 [Paragraph("Datos", etq), Paragraph("Countries of the World (Kaggle, fernandol)", val)]]
story.append(Table(datos_portada, colWidths=[108, 336], hAlign="CENTER",
                   style=[("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
story.append(Spacer(1, 70))
P("Ciudad Universitaria, Ciudad de México<br/>Noviembre de 2026", ParagraphStyle("lugar", fontName="Serif", fontSize=13,
                                                                                leading=18, alignment=TA_CENTER))
story.append(NextPageTemplate("normal"))
story.append(PageBreak())

# Resumen -----------------------------------------------------------------------------------------
val_z, prop_z, acum_z = R["val_z"], R["prop_z"], R["acum_z"]
k = R["k"]
story.append(Paragraph("Resumen", h1))
P(f"Se realiza un análisis exploratorio de {R['n_paises']} países descritos por {R['n_columnas']} variables demográficas, "
  "económicas y geográficas (<i>Countries of the World</i>, Kaggle) para saber si pueden resumirse en pocas componentes "
  "principales (PCA). Se depuró la base (variables redundantes descartadas, tres territorios eliminados, vacíos estimados por "
  "interpolación y logaritmo en las variables muy asimétricas) y se obtuvieron gráficas, medidas descriptivas, valores atípicos y "
  "matrices de covarianza y correlación. Luego se aplicó el PCA con y sin estandarización y se eligió el número de componentes "
  f"con el criterio de Kaiser. Con datos estandarizados, cuatro componentes explican "
  f"{100 * acum_z[k - 1]:.1f} % de la varianza y la primera ({100 * prop_z[0]:.1f} %) funciona como un eje de nivel de desarrollo; "
  f"sin estandarizar, la primera explica {100 * R['prop_s'][0]:.2f} % pero solo refleja el PIB per cápita, por lo que estandarizar "
  "es indispensable. Además, un spline cúbico construido con los países predijo la mortalidad infantil a partir del PIB per "
  f"cápita en países que no se usaron para construirlo, con un error {100 * (1 - R['spline_pib']['rmse']['spline'] / R['spline_pib']['rmse']['media']):.0f} % "
  "menor que sin usar el PIB.")
story.append(PageBreak())

# Índice ----------------------------------------------------------------------------------------------
story.append(Paragraph("Contenido", h1))
toc = TableOfContents()
toc.dotsMinLevel = 1
toc.levelStyles = [
    ParagraphStyle("toc0", fontName="Serif-Bold", fontSize=10.5, leading=14, spaceBefore=6, leftIndent=0, firstLineIndent=0),
    ParagraphStyle("toc1", fontName="Serif", fontSize=10, leading=13.5, leftIndent=18, firstLineIndent=0, spaceBefore=2),
    ParagraphStyle("toc2", fontName="Serif", fontSize=10, leading=13.5, leftIndent=36, firstLineIndent=0, spaceBefore=2),
]
story.append(toc)
story.append(PageBreak())

# =============================================================================================
# 1. INTRODUCCIÓN
# =============================================================================================
H1("1. Introducción")
H2("1.1 Objetivo e hipótesis de trabajo")
P("El objetivo de este trabajo es realizar un análisis exploratorio del conjunto de datos <i>Countries of the World</i> [1], "
  "con la base ya depurada, determinar si los indicadores demográficos, económicos y geográficos de los países pueden "
  "resumirse en unas pocas componentes principales sin perder demasiada información. El análisis sigue el siguiente flujo "
  "planteado: datos, exploración (gráficas, preprocesamiento, correlaciones, medidas descriptivas y valores atípicos), "
  "corrección de los datos y reducción de dimensiones con PCA.")
P("Partimos de dos hipótesis, que se retoman en la Discusión (sección 4). <b>H1:</b> muchas variables miden en el fondo el nivel "
  "de desarrollo de un país (salud, ingreso, educación, estructura económica), por lo que estarán fuertemente correlacionadas y "
  "unas pocas componentes bastarán para resumir buena parte de la varianza. <b>H2:</b> la relación entre la infraestructura de "
  "un país y su bienestar no es proporcional: las primeras mejoras (por ejemplo, las primeras líneas telefónicas por habitante) "
  "van acompañadas de saltos grandes en alfabetización, en salud infantil y en la estructura económica, y después el efecto se "
  "agota, de modo que entre los países mejor equipados esas variables casi no cambian.")
H2("1.2 Justificación y antecedentes")
P("Los países se describen con decenas de indicadores y varios de ellos dicen casi lo mismo. Resumirlos en pocas dimensiones "
  "permite comparar países, visualizarlos en un plano y usar menos variables en modelos posteriores.")
P("El análisis de componentes principales es una técnica clásica para reducir dimensiones [2], y los criterios para decidir "
  "cuántas componentes conservar se han estudiado desde hace décadas [3]. Como antecedente de la idea de resumir el desarrollo "
  "de un país con pocas dimensiones, el Índice de Desarrollo Humano del PNUD [4] combina salud, educación e ingreso en un solo "
  "indicador; a diferencia del PCA, se construye con una fórmula fija y no a partir de la estructura de los datos.")
H2("1.3 Origen y descripción de los datos")
P("Los datos vienen del conjunto <i>Countries of the World</i>, publicado en Kaggle por el usuario fernandol "
  "(https://www.kaggle.com/datasets/fernandol/countries-of-the-world) [1]. Cada fila es un país o territorio y cada columna una "
  "característica. Por los valores que contiene (por ejemplo, China aparece con 1,313,973,713 habitantes), la información "
  "corresponde a mediados de la década de 2000, así que las conclusiones describen ese periodo y no la actualidad.")
P("El archivo usa coma como separador decimal (\"48,0\") y los nombres de país y de región traen espacios al final, por lo que "
  f"al leerlo indicamos <i>decimal=\",\"</i> y limpiamos los textos. La Tabla {T['variables']} resume las columnas.")
tabla("variables", "Variables del conjunto de datos tal como se usan en este trabajo.", [
    ["Variable", "Tipo", "Qué mide"],
    ["País", "texto", "Nombre del país o territorio (se usa como identificador)."],
    ["Región", f"categórica ({len(R['regiones'])} niveles)", "Región geográfica definida por la fuente."],
    ["Población", "numérica", "Número de habitantes."],
    ["Superficie", "numérica", "Área en millas cuadradas."],
    ["Densidad de población", "numérica", "Habitantes por milla cuadrada."],
    ["Costa / área", "numérica", "Razón entre la longitud de costa y la superficie."],
    ["Migración neta", "numérica", "Migrantes netos por cada 1000 habitantes."],
    ["Mortalidad infantil", "numérica", "Muertes por cada 1000 nacimientos."],
    ["PIB per cápita", "numérica", "Dólares estadounidenses por habitante."],
    ["Alfabetización", "numérica", "Porcentaje de la población alfabetizada."],
    ["Teléfonos", "numérica", "Líneas telefónicas por cada 1000 habitantes."],
    ["Tierra cultivable, cultivos permanentes, otros usos", "numéricas", "Porcentaje de la superficie en cada uso del suelo."],
    ["Clima", "categórica ordinal", "Tipo de clima codificado de 1 a 4, con algunos valores intermedios (1.5 y 2.5)."],
    ["Natalidad, mortalidad", "numéricas", "Nacimientos y muertes por cada 1000 habitantes."],
    ["Agricultura, industria, servicios", "numéricas", "Fracción del PIB que aporta cada sector."],
], [140, 104, 224])
REG_ES = {"SUB-SAHARAN AFRICA": "África subsahariana", "LATIN AMER. & CARIB": "América Latina y el Caribe",
          "BALTICS": "Países Bálticos", "WESTERN EUROPE": "Europa occidental", "ASIA (EX. NEAR EAST)": "Asia",
          "OCEANIA": "Oceanía", "NEAR EAST": "Cercano Oriente", "EASTERN EUROPE": "Europa del este",
          "C.W. OF IND. STATES": "Comunidad de Estados Independientes", "NORTHERN AFRICA": "África del norte",
          "NORTHERN AMERICA": "América del norte"}
regs = list(R["regiones"].items())
clima = {k_: v for k_, v in R["clima"].items() if k_ != "s/d"}
clima_max = max(clima, key=clima.get)
figura("fig_categoricas.png", 431, f"Distribución de las dos variables categóricas. Clima tiene {R['clima']['s/d']} países sin dato (s/d).",
       "categoricas")
P(f"La región con más países es {REG_ES[regs[0][0]]} ({regs[0][1]}), seguida de {REG_ES[regs[1][0]]} ({regs[1][1]}); "
  f"{REG_ES[regs[-1][0]]} ({regs[-1][1]}) es la más pequeña. En clima, el tipo {clima_max} concentra {clima[clima_max]} países.")
H2("1.4 Herramientas y métodos") # 1.4
P("Todo el análisis se hizo en Python con estos paquetes: pandas (lectura del CSV con <i>read_csv</i>, medianas por grupos "
  "con <i>qcut</i> y <i>groupby</i>, y los métodos <i>mean, median, var, std, skew, cov</i> y <i>corr</i>); NumPy "
  "(matriz de covarianza con <i>numpy.cov</i>, valores y vectores propios con <i>numpy.linalg.eigh</i>, solución del sistema del "
  "spline con <i>numpy.linalg.solve</i> y <i>log10</i>); "
  "Matplotlib y seaborn (histogramas, diagramas de caja, dispersión y mapas de calor); SciPy (valor crítico de la "
  "correlación y comprobación del spline cúbico con <i>CubicSpline</i>) y scikit-learn, cuya clase <i>PCA</i> usamos solo "
  "para verificar nuestro cálculo. El código completo, con el cálculo de cada tabla y de cada figura, está explicado en el "
  "notebook <i>analisis_pca.ipynb</i> del repositorio del proyecto, y el notebook <i>analisis_pca_reporte.ipynb</i> es una "
  "versión autocontenida que calcula y muestra todo sin escribir archivos.")
H3("1.4.1 Medidas descriptivas y covarianza")
P("La media, la varianza y la covarianza de dos variables X e Y medidas en <i>n</i> países son:")
F_MEDIA = r"$\bar{x}=\frac{1}{n}\sum_{i=1}^{n}x_i\qquad\qquad s^2(X)=\frac{\sum_{i=1}^{n}(x_i-\bar{x})^2}{n-1}$"
F_COV = r"$\mathrm{Cov}(X,Y)=\frac{\sum_{i=1}^{n}(x_i-\bar{x})(y_i-\bar{y})}{n-1}$"
F_PEARSON = r"$r(X,Y)=\frac{\mathrm{Cov}(X,Y)}{\sigma(X)\,\sigma(Y)}$"
formula("media_varianza", F_MEDIA)
formula("covarianza", F_COV)
P("Aquí <i>n</i> es el número de países, <i>x<sub>i</sub></i> y <i>y<sub>i</sub></i> son los valores de X y Y en el país <i>i</i>, "
  "la barra sobre una letra indica su media y cada suma recorre <i>i</i> = 1, …, <i>n</i>. La desviación estándar <i>s</i> es la "
  "raíz cuadrada de la varianza. La mediana es el valor central de los datos ordenados y, a diferencia de la media, no la afectan "
  "los valores extremos.")
H3("1.4.2 Correlación de Pearson")
formula("pearson", F_PEARSON)
P("donde σ(X) y σ(Y) son las desviaciones estándar de X y de Y. El coeficiente <i>r</i> va de −1 a 1 y no depende de las "
  "unidades. La matriz de correlación reúne el valor de <i>r</i> de todos los pares de variables; vale 1 en la diagonal y es simétrica.")
H3("1.4.3 Valores atípicos: rango intercuartílico")
formula("ric", r"$x<Q_1-1.5\,\mathrm{RIC}\quad\mathrm{o}\quad x>Q_3+1.5\,\mathrm{RIC},\qquad\mathrm{RIC}=Q_3-Q_1$")
P("donde Q<sub>1</sub> y Q<sub>3</sub> son el primer y el tercer cuartil de la variable (los valores que dejan por debajo al 25 % "
  "y al 75 % de los países) y RIC es el rango intercuartílico. Un valor <i>x</i> que cumple alguna de las dos condiciones se "
  "considera atípico. Es el criterio que dibuja los círculos de los diagramas de caja.")
H3("1.4.4 Transformación logarítmica y estandarización")
formula("log_z", r"$y=\log_{10}(x+1)\qquad\qquad z_i=\frac{x_i-\bar{x}}{s}$")
P("donde <i>x</i> es el valor original, <i>y</i> el valor transformado y <i>z<sub>i</sub></i> el valor estandarizado de la "
  "variable en el país <i>i</i>, con media 0 y desviación estándar 1. El logaritmo comprime las colas derechas largas y conserva "
  "el orden de los países; se suma 1 porque hay valores iguales a cero. La estandarización pone todas las variables en la misma escala.")
H3("1.4.5 Componentes principales")
formula("pca", r"$S\,v_j=\lambda_j\,v_j\qquad\qquad\mathrm{prop}_j=\frac{\lambda_j}{\lambda_1+\cdots+\lambda_p}\qquad\qquad T=Z\,V$")
P(f"Aquí <i>S</i> es la matriz de covarianza de los datos (de <i>p</i> × <i>p</i>, con <i>p</i> = {len(VARS)} variables), "
  "<i>v<sub>j</sub></i> es el vector propio de la componente <i>j</i> (sus coeficientes) y λ<sub>j</sub> su valor propio, que es la "
  "varianza de esa componente; las componentes se ordenan de mayor a menor λ, y prop<sub>j</sub> es la proporción de varianza que "
  "explica la componente <i>j</i>. <i>Z</i> es la matriz de datos estandarizados (<i>n</i> × <i>p</i>), <i>V</i> es la matriz cuyas "
  "columnas son los vectores propios y <i>T</i> contiene las puntuaciones de cada país. Si <i>S</i> se calcula con datos "
  "estandarizados, es la matriz de correlación.")
P("<b>Cómo se calculan las cargas.</b> La carga de la variable <i>i</i> en la componente <i>j</i> es la correlación entre esa "
  "variable y las puntuaciones de la componente. Se obtiene así, con datos estandarizados. Las puntuaciones de la componente "
  "<i>j</i> son una combinación lineal de las variables cuyos coeficientes son las entradas de su vector propio:")
formula("carga_puntuacion", r"$t_j=Z\,v_j=v_{1j}\,z_1+v_{2j}\,z_2+\cdots+v_{pj}\,z_p$", 12)
P("donde <i>z<sub>i</sub></i> es la columna de <i>Z</i> que contiene la variable <i>i</i> y <i>t<sub>j</sub></i> la columna de "
  "<i>T</i> con las puntuaciones de la componente <i>j</i>. Como las dos tienen media cero, su covarianza es el producto "
  "<i>z<sub>i</sub></i><super>T</super><i>t<sub>j</sub></i> entre <i>n</i> − 1. Al sustituir <i>t<sub>j</sub></i> aparece la fila "
  "<i>i</i> de la matriz de correlación <i>R</i> = <i>Z</i><super>T</super><i>Z</i> / (<i>n</i> − 1) multiplicada por "
  "<i>v<sub>j</sub></i>, y como <i>v<sub>j</sub></i> es vector propio de <i>R</i>, se cumple <i>R v<sub>j</sub></i> = "
  "λ<sub>j</sub><i>v<sub>j</sub></i>:")
formula("carga_cov", r"$\mathrm{Cov}(z_i,t_j)=\dfrac{z_i^{\top}t_j}{n-1}=\dfrac{z_i^{\top}Z\,v_j}{n-1}=(R\,v_j)_i=\lambda_j\,v_{ij}$", 12)
P("La correlación se obtiene dividiendo entre las dos desviaciones estándar. La variable estandarizada tiene varianza 1 y la "
  "componente tiene varianza λ<sub>j</sub>, de modo que:")
formula("carga_corr", r"$\ell_{ij}=\mathrm{Corr}(z_i,t_j)=\dfrac{\mathrm{Cov}(z_i,t_j)}{\sqrt{\mathrm{Var}(z_i)}\,\sqrt{\mathrm{Var}(t_j)}}"
                      r"=\dfrac{\lambda_j\,v_{ij}}{1\cdot\sqrt{\lambda_j}}=v_{ij}\,\sqrt{\lambda_j}$", 12)
P("Es decir, la carga es el coeficiente del vector propio multiplicado por la raíz del valor propio. En forma matricial, la "
  "matriz de cargas es <i>L</i> = <i>V</i> Λ<super>1/2</super>, donde Λ es la matriz diagonal de valores propios. De aquí salen "
  "dos propiedades que usamos al interpretar:")
formula("carga_prop", r"$\sum_{i=1}^{p}\ell_{ij}^{2}=\lambda_j\,\sum_{i=1}^{p}v_{ij}^{2}=\lambda_j\qquad\qquad"
                      r"\sum_{j=1}^{p}\ell_{ij}^{2}=\sum_{j=1}^{p}\lambda_j\,v_{ij}^{2}=R_{ii}=1$", 12)
_pib = "GDP ($ per capita)"
_c11 = R["cargas"][_pib][0]
P("La primera dice que los cuadrados de las cargas de una componente suman su valor propio (porque el vector propio tiene norma "
  "1), y la segunda que los cuadrados de las cargas de una variable en todas las componentes suman 1 (porque <i>R</i> = "
  "<i>V</i> Λ <i>V</i><super>T</super> y su diagonal vale 1). Por ejemplo, el PIB per cápita tiene coeficiente {_c11 / R['val_z'][0] ** .5:.3f} en "
  f"el primer vector propio y λ<sub>1</sub> = {R['val_z'][0]:.3f}, así que su carga es {_c11 / R['val_z'][0] ** .5:.3f} × "
  f"√{R['val_z'][0]:.3f} = {_c11:.2f}: la primera componente explica {100 * _c11 ** 2:.0f} % de su varianza.")

p_ = len(VARS)

H3("1.4.6 Cuántas componentes conservar")
P(f"El PCA produce tantas componentes como variables (aquí <i>p</i> = {p_}) y solo conservándolas todas se mantiene el 100 % de "
  "la varianza; reducir dimensiones significa quedarse con las primeras <i>k</i> y descartar las demás. La elección de <i>k</i> es "
  "un compromiso entre dos errores. Si se conservan <b>muy pocas</b>, se pierde estructura real de los datos. Si se conservan "
  "<b>demasiadas</b>, se incluyen componentes que solo reflejan el ruido del muestreo o la variación propia de una sola variable: "
  "no se pueden interpretar y cambiarían con otra muestra de países.")
P("<b>Criterio de Kaiser [3].</b> Con datos estandarizados se conservan las componentes cuyo valor propio es mayor que 1:")
formula("kaiser", r"$\mathrm{tr}(R)=\lambda_1+\lambda_2+\cdots+\lambda_p=p\quad\Rightarrow\quad\bar{\lambda}=1;"
                  r"\qquad\mathrm{se\ conserva\ la\ CP}_j\ \mathrm{si}\ \lambda_j>1$", 12)
P("La justificación es la siguiente. Al estandarizar, cada variable tiene varianza 1, así que la varianza total es la traza de la "
  f"matriz de correlación <i>R</i>, que vale <i>p</i>, y el valor propio promedio es 1. Como λ<sub>j</sub> es la varianza de la "
  "componente <i>j</i>, una componente con λ<sub>j</sub> &gt; 1 resume más varianza que cualquiera de las variables originales por "
  "separado, es decir, sí comprime información; una con λ<sub>j</sub> &lt; 1 explica menos que una sola variable y conservarla no "
  "supone ninguna ganancia frente a quedarse con esa variable. Por eso el criterio solo tiene sentido con datos estandarizados: "
  "sin estandarizar, el umbral equivalente sería el promedio de los valores propios de <i>S</i>, que en estos datos domina el PIB "
  "per cápita (sección 3.6). Su limitación es que el umbral 1 vale para la población y no toma en cuenta el tamaño de la muestra: "
  "aunque las variables fueran independientes, los valores propios muestrales se dispersan alrededor de 1 y los primeros lo superan "
  "solo por azar.")
H3("1.4.7 Reconstrucción de la matriz con k componentes")
P("Con solo las primeras <i>k</i> componentes se puede volver a la matriz de datos:")
formula("recon", r"$\hat{Z}_k=T_k\,V_k^{\top}\qquad\qquad \hat{X}_k=\hat{Z}_k\,D+\mathbf{1}\,\bar{x}^{\top}$")
P("Aquí <i>T<sub>k</sub></i> y <i>V<sub>k</sub></i> son las primeras <i>k</i> columnas de <i>T</i> y de <i>V</i>, <i>Ẑ<sub>k</sub></i> es la "
  "matriz estandarizada aproximada, <i>D</i> es la matriz diagonal con las desviaciones estándar <i>s</i> de cada variable, <b>1</b> "
  "es un vector columna de unos y <i>x</i> con barra es el vector de medias. Si además se aplicó el logaritmo, se deshace con "
  "<i>x</i> = 10<super><i>y</i></super> − 1. Con <i>k</i> = <i>p</i> la reconstrucción es exacta; con <i>k</i> &lt; <i>p</i> se pierde "
  "justo la varianza de las componentes descartadas:")
formula("recon_err", r"$\frac{\Vert Z-\hat{Z}_k\Vert_F^2}{n-1}=\lambda_{k+1}+\cdots+\lambda_p$")
P("donde ‖·‖<sub>F</sub> es la norma de Frobenius (la raíz de la suma de los cuadrados de todas las entradas de la matriz). Esto da "
  "una medida directa de lo que cuesta quedarse con <i>k</i> componentes.")

# =============================================================================================
# 2. ANÁLISIS EXPERIMENTAL
# =============================================================================================
H1("2. Análisis experimental")
P("Esta sección describe qué se hizo con los datos antes de analizarlos y sobre qué base se obtuvo cada resultado de la sección 3. "
  "El procedimiento tiene cuatro pasos: contar y tratar los valores faltantes, decidir qué variables y países se quedan, imputar los "
  "vacíos restantes y transformar las variables muy asimétricas. Las gráficas de la sección 3.1 se hicieron con los datos "
  "originales, antes de modificar nada, para mostrar la información tal cual viene en la fuente.")
H2("2.1 Valores faltantes")
falt = list(R["faltantes"].items())
mas = [f"{N(v)} ({c} países, {pc:.1f} %)" for v, (c, pc) in falt[:5]]
max_num = max(pc for v, (c, pc) in falt if v != "Climate")
P(f"Primero contamos los vacíos de cada columna. Las que más faltan son {lista(mas)}. Ninguna columna numérica pasa del "
  f"{math.ceil(max_num)} % de vacíos, así que no hay razón para descartarlas únicamente por faltantes.")
figura("fig_faltantes.png", 374, "Porcentaje de países sin dato en cada columna (solo se muestran las que tienen vacíos).", "faltantes")
H2("2.2 Variables que descartamos y por qué")
P(f"De las {R['n_columnas']} columnas distintas de País, {p_} numéricas entran al estudio de correlaciones y componentes principales. "
  f"Las demás se descartan por las razones de la Tabla {T['descartadas']}. Hablamos de variables (columnas): descartar una significa "
  "que no participa en las matrices de covarianza y correlación ni en el PCA, pero sigue visible en las gráficas de la sección 3.1.")
s_min, s_max = R["suma_suelo"]
c_min, c_max = R["suma_sectores"]
ci_a, ci_s = R["corr_industria"]
tabla("descartadas", "Variables que no entran a las matrices de correlación ni al PCA.", [
    ["Variable", "Decisión", "Razón"],
    ["País", "Índice", "Es un identificador; no es una medición."],
    ["Región", "Fuera del PCA", f"Es categórica nominal ({len(R['regiones'])} niveles) y no tiene sentido calcular media o covarianza "
                                "con ella. La usamos solo para colorear gráficas."],
    ["Clima", "Se descarta", f"Es una categoría ordinal con {R['faltantes']['Climate'][0]} países sin dato "
                             f"({R['faltantes']['Climate'][1]:.1f} %) y con valores intermedios (1.5 y 2.5) que no son medidas reales. "
                             "Su media o covarianza no tiene interpretación."],
    ["Otros usos del suelo", "Se descarta", f"Es exactamente 100 menos tierra cultivable menos cultivos permanentes (la suma de las tres "
                                            f"va de {s_min:.2f} a {s_max:.2f}, la diferencia es redondeo). Una variable que es combinación "
                                            "lineal de otras hace singular la matriz de covarianza y no agrega información."],
    ["Industria", "Se descarta", f"Agricultura + industria + servicios suman entre {c_min:.3f} y {c_max:.3f}, por lo que las tres son "
                                 "casi dependientes. Conservamos agricultura y servicios; industria queda como el resto (su correlación "
                                 f"con ellas es {ci_a:.2f} y {ci_s:.2f}) y además tiene {R['faltantes']['Industry'][0]} vacíos."],
    ["Población y superficie", "Fuera del PCA", "Miden el tamaño del país, no sus condiciones de vida, y su resumen útil ya está en la "
                                                "densidad de población (población entre superficie). Tienen la asimetría más fuerte "
                                                f"({R['asim_tamano'][0]:.1f} y {R['asim_tamano'][1]:.1f}) y dominarían las matrices."],
], [92, 70, 306])
H2("2.3 Países eliminados y valores imputados")
imp = list(R["imputados"].items())
_fp = {int(c): n for c, n in R["faltan_por_pais"].items()}
_fe = R["faltan_eliminados"]
_con_vacios = sum(n for c, n in _fp.items() if c > 0)
P(f"Para decidir qué hacer con los vacíos de las {p_} variables que sí usamos, contamos cuántos le faltan a cada país: "
  f"{_fp[0]} países están completos, {_fp.get(1, 0)} tienen un vacío, {_fp.get(2, 0)} tienen dos y {_fp.get(3, 0)} tienen tres. "
  f"Eliminamos a los que tienen cuatro o más vacíos (más del 30 % de sus variables): "
  f"{lista([f'{pais} ({c} vacíos)' for pais, c in _fe.items()])}. Quedan {R['n_depurados']} países.")
P("Elegimos ese límite por cuatro razones. Primera, es el corte natural de los datos: ningún país tiene exactamente cuatro "
  f"vacíos, así que el límite separa a los países a los que les faltan de una a tres variables de los tres territorios a los que "
  f"les faltan de {min(_fe.values())} a {max(_fe.values())} (entre {100 * min(_fe.values()) / p_:.0f} % y "
  f"{100 * max(_fe.values()) / p_:.0f} % de su información). Segunda, un país con cuatro vacíos tendría más del 30 % de su perfil "
  "estimado en lugar de medido, y en un PCA esos valores estimados pesarían lo mismo que los reales. Tercera, cada vacío se estima "
  "a partir de otra variable del mismo país, y mientras más variables faltan, menos información propia queda para estimar: a "
  "Western Sahara y a Wallis and Futuna les faltan, entre otras, la mortalidad infantil y la natalidad, que están entre las "
  "variables más relacionadas con las demás. Cuarta, el costo es bajo: se pierden "
  f"{len(_fe)} de {R['n_paises']} territorios ({100 * len(_fe) / R['n_paises']:.1f} %), todos con poca población, mientras que un "
  f"criterio más estricto, como conservar solo los países completos, habría eliminado {_con_vacios} "
  f"({100 * _con_vacios / R['n_paises']:.1f} %).")
P(f"A los demás países les faltan {sum(c for _, c in imp)} valores: {', '.join(f'{n_(v)} ({c})' for v, c in imp[:3])}, "
  f"{n_(imp[3][0])} ({imp[3][1]}) y uno o dos valores en otras variables. El caso más grande, {n_(imp[0][0])}, representa "
  f"{100 * imp[0][1] / R['n_depurados']:.1f} % de los países. Estimamos cada vacío por "
  "interpolación lineal a partir de otra variable del mismo país, que llamamos variable predictora.")
P("<b>Variable predictora.</b> Para cada variable con vacíos usamos como predictora la variable con mayor correlación de Pearson "
  "en valor absoluto (sección 1.4.2), calculada con los países que tienen ambos datos: mientras más fuerte es la relación entre "
  f"dos variables, mejor se puede estimar una a partir de la otra. La Tabla {T['imputacion']} muestra la predictora de cada "
  "variable.")
P("<b>Nodos.</b> Sean <i>x</i> la variable predictora e <i>y</i> la variable con vacíos. No se puede interpolar directamente entre "
  "países, porque dos países con casi el mismo valor de <i>x</i> pueden tener valores de <i>y</i> muy distintos y la curva oscilaría "
  f"de un punto a otro. Por eso primero resumimos la relación en pocos nodos: los países que tienen ambos datos se ordenan por "
  f"<i>x</i> y se dividen en {R['n_nodos']} grupos del mismo tamaño; cada grupo aporta un nodo (<i>x<sub>j</sub></i>, "
  "<i>y<sub>j</sub></i>) formado por la mediana de <i>x</i> y la mediana de <i>y</i> de sus países. Así se obtienen los nodos "
  "<i>x</i><sub>0</sub> &lt; <i>x</i><sub>1</sub> &lt; … &lt; <i>x<sub>n</sub></i>, con <i>n</i> + 1 = "
  f"{R['n_nodos']}. Usamos {R['n_nodos']} grupos porque cada uno tiene alrededor de {R['n_depurados'] // R['n_nodos']} países, "
  "suficientes para que su mediana sea estable, y a la vez son bastantes nodos para seguir la forma de la curva.")
P("<b>Interpolación lineal.</b> Une cada par de nodos consecutivos con una recta. Para un país cuyo valor <i>x</i> está entre "
  "<i>x<sub>j</sub></i> y <i>x</i><sub><i>j</i>+1</sub>, el valor estimado es:")
formula("interp_lineal", r"$L_j(x)=y_j+\dfrac{y_{j+1}-y_j}{x_{j+1}-x_j}\,(x-x_j)$", 12)
_vi = R["imputacion"]
filas = [["Variable", "Vacíos", "Variable predictora", "r"]]
for v, d in _vi.items():
    filas.append([N(v), d["n"], N(d["predictora"]), f"{d['r']:+.2f}".replace("-", "−")])
tabla("imputacion", "Variable predictora de cada variable con vacíos: la de mayor correlación de Pearson en valor absoluto, "
      "calculada con los países que tienen ambos datos.", filas, [140, 50, 160, 60])
figura("fig_imputacion.png", ANCHO, "Nodos (puntos negros) e interpolación lineal de las tres variables con más vacíos frente a "
       "su variable predictora. Los rombos rojos son los valores imputados.", "imputacion")
_tres = [v for v, _ in imp[:3]]
_debil = [v for v, d in _vi.items() if abs(d["r"]) < 0.3]
P(f"En las tres variables con más vacíos las predictoras son {n_(_vi[_tres[0]]['predictora'])} para {n_(_tres[0])} "
  f"(<i>r</i> = {_vi[_tres[0]]['r']:.2f}), {n_(_vi[_tres[1]]['predictora'])} para {n_(_tres[1])} ({_vi[_tres[1]]['r']:.2f}) y "
  f"{n_(_vi[_tres[2]]['predictora'])} para {n_(_tres[2])} ({_vi[_tres[2]]['r']:.2f}). La Figura {F['imputacion']} muestra que "
  "esas relaciones no son rectas: la alfabetización casi no cambia mientras la natalidad es baja y cae rápido cuando pasa de 25 "
  "nacimientos por cada 1000 habitantes, y los servicios suben rápido con los primeros teléfonos. Como cada tramo entre nodos "
  "tiene su propia pendiente, la interpolación sigue esa forma, algo que no haría una sola recta de regresión."
  .replace("-", "−")
  + (f" En {lista([n_(v) for v in _debil])} la mejor predictora apenas tiene |<i>r</i>| = "
     f"{abs(_vi[_debil[0]]['r']):.2f}, así que el valor estimado es poco más que un valor típico; como solo se estimó "
     f"{'un valor' if _vi[_debil[0]]['n'] == 1 else str(_vi[_debil[0]]['n']) + ' valores'}, su efecto en el análisis es mínimo."
     if _debil else ""))
P("Tres cuidados adicionales: el valor estimado se limita al intervalo de valores observados de la variable (por ejemplo, la "
  "alfabetización no puede pasar de 100); fuera del intervalo de los nodos no se extrapola, sino que se usa el nodo del extremo; "
  f"y si a un país también le falta la variable predictora, se usa la siguiente más correlacionada (ocurrió en "
  f"{R['imputacion_otras']} de los {sum(c for _, c in imp)} valores).")
H2("2.4 Transformación de variables muy asimétricas")
P("Los resultados de la sección 3.1 muestran que algunas variables "
  "tienen colas derechas extremas que, al calcular correlaciones y componentes, dejarían que unos pocos países decidan el resultado. "
  "Con un criterio fijo, aplicamos <i>log10(x + 1)</i> a las variables con coeficiente de asimetría mayor o igual a 2 en valor "
  "absoluto. Elegimos el logaritmo porque comprime las colas derechas y respeta el orden de los países, y sumamos 1 porque estas "
  f"variables tienen ceros (por ejemplo, países sin costa). Las variables transformadas son: {', '.join(N(v) for v in R['a_log'])}.")
figura("fig_log.png", 431, "Efecto de la transformación logarítmica sobre las tres variables más asimétricas (izquierda: original; "
       "derecha: transformada).", "log")
al = R["asim_log"]
P(f"La asimetría de densidad baja de {al[VARS[0]][0]:.2f} a {al[VARS[0]][1]:.2f}, la de costa/área de {al[VARS[1]][0]:.2f} a "
  f"{al[VARS[1]][1]:.2f} y la de cultivos permanentes de {al['Crops (%)'][0]:.2f} a {al['Crops (%)'][1]:.2f}. Las demás variables "
  "tienen asimetría menor que 2 y se dejan en su escala original para conservar su interpretación.")
H2("2.5 Cómo se obtuvo cada resultado")
P(f"<b>Gráficas de cada variable (3.1).</b> Se hicieron con los datos originales ({R['n_paises']} filas, omitiendo los vacíos de "
  "cada variable): un histograma de 20 intervalos con líneas de media y mediana, y un diagrama "
  "<i>box plot</i>.")
P("<b>Coeficiente de asimetría (2.4 y 3.1).</b> Para medir qué tan cargada hacia un lado está la distribución de cada variable "
  "usamos el coeficiente de asimetría muestral ajustado de Fisher-Pearson, que es el que calcula el método <i>skew</i> de pandas:")
formula("asimetria", r"$g=\dfrac{n}{(n-1)(n-2)}\sum_{i=1}^{n}\dfrac{(x_i-\bar{x})^{3}}{s^{3}}$")
P("donde <i>n</i> es el número de países con dato en la variable, <i>x<sub>i</sub></i> es el valor de la variable en el país "
  "<i>i</i>, " + mat(r"$\bar{x}$", "xbar") + " es su media y <i>s</i> su desviación estándar muestral (calculada con <i>n</i> − 1). Cada término mide a "
  "cuántas desviaciones estándar está un país de la media y lo eleva al cubo, de modo que conserva el signo y da mucho más peso "
  "a los valores alejados; el factor <i>n</i>/((<i>n</i> − 1)(<i>n</i> − 2)) corrige el sesgo que tiene esta medida en muestras "
  "pequeñas. Si <i>g</i> = 0, la distribución es simétrica; si <i>g</i> &gt; 0, tiene una cola larga hacia la derecha (la media "
  "queda por encima de la mediana), y si <i>g</i> &lt; 0, la cola está a la izquierda. Con este coeficiente se decidió qué "
  "variables transformar con logaritmo (|<i>g</i>| ≥ 2, sección 2.4) y se describe cada variable en la sección 3.1.")
P(f"<b>Medidas descriptivas, covarianza y atípicos. (3.2)</b> Se calcularon sobre la base depurada ({R['n_depurados']} países "
  f"× {p_} variables), antes de transformar, con <i>mean, median, var, std</i> y <i>cov</i>. Los atípicos se contaron con el "
  "criterio del RIC (Rango Intercuartílico) antes y después de la transformación logarítmica.")
P(f"<b>Correlaciones (3.4).</b> Se calcularon sobre la base transformada ({R['n_depurados']} × {p_}) con "
  "<i>corr(method=\"pearson\")</i>. La selección de las variables más y menos correlacionadas usa criterios explícitos.")

P("<b>PCA (3.5).</b> Se aplicó a la base transformada y estandarizada. Calculamos la matriz de covarianza, extrajimos valores y "
  "vectores propios con <i>numpy.linalg.eigh</i> y los ordenamos de mayor a menor. Verificamos el cálculo con <i>sklearn.decomposition.PCA</i> "
  "y comprobamos que las componentes no están correlacionadas. El número de componentes se "
  f"eligió con el criterio de Kaiser (valores propios mayores que 1), que da {k}; la justificación detallada está en la "
  "sección 3.5.3.")
P("<b>Reconstrucción (3.5.6).</b> Con las puntuaciones <i>T</i> y los vectores propios <i>V</i> se reconstruye la matriz estandarizada "
  "con <i>k</i> componentes, se deshacen la estandarización y el logaritmo, y se compara con la base. El error se mide con "
  "la norma de la diferencia entre matrices.")
P("<b>Comparación con y sin estandarización (3.6).</b> Se repite el mismo cálculo sobre la misma base transformada, una vez con los "
  "datos solo centrados (matriz de covarianza) y otra con datos estandarizados (matriz de correlación). Por eso, \"sin "
  "estandarizar\" significa sin dividir entre la desviación estándar, pero con la transformación logarítmica ya aplicada.")
P("<b>Predicción con splines cúbicos (3.7).</b> Se usaron el PIB per cápita y la mortalidad infantil de la base depurada, solo "
  "con valores observados. Ocho países con niveles de PIB muy distintos (los de la Tabla 16) se reservaron para comparar la "
  "predicción con su valor real; con el resto se formaron los nodos del spline cúbico natural que se describe en esa sección.")

# =============================================================================================
# 3. RESULTADOS
# =============================================================================================
H1("3. Resultados")
P("Los resultados se presentan en el orden del flujo de trabajo: gráficas de cada variable (3.1), medidas descriptivas (3.2), "
  "valores atípicos (3.3), correlaciones (3.4), componentes principales (3.5), estandarización (3.6) y predicción con splines "
  "cúbicos (3.7). Cada resultado lleva una "
  "explicación breve; la comparación con las hipótesis, las limitaciones y las mejoras posibles se discuten en la sección 4.")
H2("3.1 Gráficas de cada característica")
P("Antes de modificar nada, graficamos cada variable numérica con un histograma y un <i>box plot</i>. En el histograma la línea "
  "discontinua marca la media y la continua marca la mediana; cuando están muy separadas, la distribución es asimétrica. En el diagrama de "
  "caja, la caja va del primer al tercer cuartil, los bigotes llegan hasta 1.5 veces el rango intercuartílico y los círculos son "
  "valores atípicos. Las variables se grafican con los datos originales, con los vacíos omitidos en cada una.")
top3 = R["top3"]
DESCRIP = {
    "Population": "Unos pocos países enormes (China, India, Estados Unidos) contrastan con una mayoría de países pequeños.",
    "Area (sq. mi.)": f"Pocos países ocupan superficies muy grandes ({', '.join(top3['Area (sq. mi.)'])}); la mayoría son pequeños.",
    "Pop. Density (per sq. mi.)": "Casi todos los países tienen pocas centenas de habitantes por milla cuadrada, pero territorios "
                                  f"diminutos como {top3['Pop. Density (per sq. mi.)'][0]}, {top3['Pop. Density (per sq. mi.)'][1]} o "
                                  f"{top3['Pop. Density (per sq. mi.)'][2]} llegan a miles.",
    "Coastline (coast/area ratio)": "La razón vale cero en países sin litoral y es muy alta en islas pequeñas, lo que alarga la cola derecha.",
    "Net migration": f"Se concentra alrededor de cero. En {R['ceros_migracion']} de {R['n_depurados']} países vale exactamente cero, y "
                     "es probable que en la fuente ese cero sustituya un dato no disponible.",
    "Infant mortality (per 1000 births)": "La mayoría de los países tiene valores bajos; hay una cola de países africanos con más de "
                                          "100 muertes por cada 1000 nacimientos.",
    "GDP ($ per capita)": "Muchos países están por debajo de 10,000 USD y solo unos pocos superan los 30,000 "
                          f"({', '.join(top3['GDP ($ per capita)'])}).",
    "Literacy (%)": "La distribución se carga hacia el 100 %, con una cola de países de baja alfabetización (sesgo a la izquierda).",
    "Phones (per 1000)": f"Cola derecha producida por países con muchísimas líneas por habitante, sobre todo {top3['Phones (per 1000)'][0]}.",
    "Arable (%)": f"Casi todos los países destinan menos de 30 % a tierra cultivable; {top3['Arable (%)'][0]} es el extremo.",
    "Crops (%)": "La mayoría dedica menos de 5 % a cultivos permanentes, pero varias islas pasan del 40 %.",
    "Other (%)": "Es el complemento de las dos variables anteriores (se comprueba en la sección 2), por lo que no aporta información nueva.",
    "Birthrate": "Distribución bastante simétrica, sin valores atípicos por el criterio del rango intercuartílico.",
    "Deathrate": f"Concentrada entre 5 y 12; los atípicos son países del sur de África ({', '.join(top3['Deathrate'])}).",
    "Agriculture": f"La mayoría de los países depende poco de la agricultura; los extremos ({top3['Agriculture'][0]}, "
                   f"{top3['Agriculture'][1]}) superan 60 % del PIB.",
    "Industry": f"Distribución con cola derecha moderada; el máximo es {top3['Industry'][0]}.",
    "Service": "Es la más simétrica de todas, sin valores atípicos.",
}
for _, fila in estad.iterrows():
    atip = int(fila["atip"])
    atip_txt = f"{atip} valor atípico" if atip == 1 else f"{atip} valores atípicos"
    figura(fila["archivo"], ANCHO, f"{fila['nombre']}. {DESCRIP[fila['var']]} Asimetría {fila['asim']:.1f}; media de "
                                   f"{num(fila['media'])} frente a la mediana {num(fila['mediana'])}; {atip_txt} por el criterio "
                                   "del rango intercuartílico.", fila["archivo"][:-4])
asim = estad.set_index("var")["asim"]
muy_asim = asim[asim.abs() >= 3].sort_values(ascending=False)
P("En conjunto, casi todas las variables tienen asimetría positiva (la media es mayor que la mediana). Las más asimétricas son "
  f"{lista([n_(v) for v in muy_asim.index])}, con coeficientes de asimetría de {muy_asim.min():.1f} a {muy_asim.max():.1f}. Esto "
  "anticipa que algunas necesitarán una transformación antes de calcular correlaciones y componentes principales, algo que se "
  "resuelve en la sección 2.")

# 3.2 ------------------------------------------------------------------------------------------------------
H2("3.2 Medidas descriptivas")
P(f"Calculamos las medidas descriptivas con las {p_} variables elegidas, ya depuradas pero todavía en su escala original (para "
  "interpretarlas). La media resume el centro, pero se mueve con los valores extremos; la mediana no. Por eso comparar ambas "
  "dice si hay asimetría. La varianza mide la dispersión alrededor de la media; las fórmulas de la media, la varianza y la "
  "covarianza son las de la sección 1.4.1.")
filas = [["Variable", "Media", "Mediana", "Varianza", "Desv. est.", "Mínimo", "Máximo"]]
for v in VARS:
    d = desc.loc[v]
    filas.append([N(v)] + [num(d[c]) for c in ("media", "mediana", "varianza", "desv_est", "minimo", "maximo")])
tabla("descriptivas", f"Medidas descriptivas de las {p_} variables elegidas ({R['n_depurados']} países, escala original).",
      filas, [118, 54, 54, 70, 58, 54, 60])
mayor_media = [v for v in VARS if desc.loc[v, "media"] > desc.loc[v, "mediana"]]
menor_media = [v for v in VARS if v not in mayor_media]
cst, den, pib = "Coastline (coast/area ratio)", "Pop. Density (per sq. mi.)", "GDP ($ per capita)"
P(f"La media supera a la mediana en {len(mayor_media)} de las {p_} variables (todas menos {lista([n_(v) for v in menor_media])}), lo "
  f"que confirma la asimetría derecha. El caso más claro es costa/área, con media {desc.loc[cst, 'media']:.1f} y mediana "
  f"{redondeo(desc.loc[cst, 'mediana'], 2)}, y también densidad de población ({desc.loc[den, 'media']:.0f} contra "
  f"{desc.loc[den, 'mediana']:.0f}). En el PIB per cápita la media ({desc.loc[pib, 'media']:,.0f}) casi duplica a la mediana "
  f"({desc.loc[pib, 'mediana']:,.0f}): un país \"cualquiera\" tiene un ingreso mucho menor al que sugiere el promedio.")
def num_cov(x):
    """Números de la matriz de covarianza completa: cifras completas y signo menos tipográfico."""
    t = num(x) if abs(x) >= 1 else f"{x:.3g}"
    return t.replace("-", "−")


cov_abs = cov_orig.loc[VARS, VARS].abs()
v_max = cov_orig.loc[VARS, VARS].stack().idxmax()
P(f"La Tabla {T['cov_completa']} presenta la matriz de covarianza completa de las {p_} variables, en su escala original; la "
  "diagonal contiene las varianzas y la matriz es simétrica, porque Cov(X, Y) = Cov(Y, X). Las magnitudes "
  f"van de {num_cov(cov_abs.where(cov_abs > 0).min().min())} a "
  f"{num_cov(cov_orig.loc[v_max])} (la varianza del {n_(v_max[0])}), es decir, cubren muchos órdenes de magnitud solo por las "
  "unidades de cada variable.")
celda_cov = ParagraphStyle("celda_cov", fontName="Serif", fontSize=5.4, leading=6.8, alignment=2)
celda_cov_b = ParagraphStyle("celda_cov_b", fontName="Serif-Bold", fontSize=5.0, leading=6.2)
cab_cov = {"Alfabetización": "Alfabeti-<br/>zación", "Cultivos permanentes": "Cultivos perma-<br/>nentes"}
filas = [[""] + [cab_cov.get(N(v), N(v)) for v in VARS]] + [[N(a)] + [num_cov(cov_orig.loc[a, b]) for b in VARS]
                                                             for a in VARS]
tabla("cov_completa", f"Matriz de covarianza completa de las {p_} variables (escala original, {R['n_depurados']} países). "
      "La diagonal contiene las varianzas.", filas, [66] + [(ANCHO - 66) / p_] * p_, est_celda=celda_cov, est_cab=celda_cov_b, relleno=1.5)
clave = R["clave_cov"]
filas = [[""] + [N(v) for v in clave]] + [[N(a)] + [num(cov_orig.loc[a, b]) for b in clave] for a in clave]
tabla("covarianza", "Matriz de covarianza (escala original) de cinco indicadores de desarrollo, tomada de la Tabla "
      f"{T['cov_completa']}. La diagonal contiene las varianzas.",
      filas, [98, 82, 72, 72, 72, 72])
P("Estas cinco variables son las que, como veremos en la sección 3.4, más se relacionan "
  "entre sí. Los signos tienen sentido: el PIB per cápita covaría positivamente con los teléfonos y la alfabetización, y "
  "negativamente con la mortalidad infantil y la natalidad. Sin embargo, las magnitudes no son comparables entre pares: la "
  f"covarianza entre PIB y teléfonos ({num(cov_orig.loc[pib, 'Phones (per 1000)'])}) es enorme solo porque el PIB se mide en miles "
  f"de dólares, mientras que la varianza de la natalidad es {num(cov_orig.loc['Birthrate', 'Birthrate'])}. La covarianza depende de "
  "las unidades, y por eso en la sección 3.4 pasamos a la correlación, que no tiene unidades.")

# 3.3 -------------------------------------------------------------------------------------------------------
H2("3.3 Datos atípicos")
P("Un valor es atípico por el criterio del rango intercuartílico (RIC) si queda más allá de 1.5 veces el RIC por debajo del primer "
  "cuartil o por encima del tercero. Contamos esos valores en cada variable antes y después de la transformación de la sección 2, y "
  "comparamos las variables en una escala común (valores z) para ver cuáles tienen colas más pesadas.")
figura("fig_atipicos.png", ANCHO, f"Diagramas de caja de las {p_} variables estandarizadas, con los datos depurados (izquierda) y "
                                   "tras la transformación (derecha).", "atipicos")
at = R["atipicos"]
sin_atip = [v for v in VARS if at[v][0] == 0 and at[v][1] == 0]
filas = [["Variable", "Atípicos antes", "Atípicos después", "Casos más alejados (datos depurados)"]]
filas += [[N(v), at[v][0], at[v][1], ", ".join(at[v][2])] for v in VARS if v not in sin_atip]
tabla("atipicos", f"Valores atípicos por el criterio del RIC. {lista([N(v) for v in sin_atip])} no tiene ninguno y no aparece.",
      filas, [120, 66, 74, 208])
dl, cl, crl = at[den], at[cst], at["Crops (%)"]
mig = at["Net migration"]
tel_max = at['Phones (per 1000)'][2][0]
dens_txt = (f"{tel_max} el mayor número de teléfonos por habitante y también la mayor densidad, seguido de cerca por {dl[2][1]}"
            if dl[2][0] == tel_max else
            f"{tel_max} el mayor número de teléfonos por habitante y {dl[2][0]} la mayor densidad")
P(f"No eliminamos ningún país por ser atípico. Los casos extremos son valores reales y esperables: {at[pib][2][0]} tiene el PIB per "
  f"cápita más alto de la muestra, {dens_txt}. Quitarlos haría que el estudio dejara fuera justamente a los países que más contrastan. "
  "En su lugar, reducimos su influencia de dos maneras: la transformación logarítmica (que baja los atípicos de densidad de "
  f"{dl[0]} a {dl[1]}, de costa/área de {cl[0]} a {cl[1]} y de cultivos permanentes de {crl[0]} a {crl[1]}) y la estandarización.")
P(f"Un caso aparte es migración neta, con {mig[0]} atípicos. Aquí el criterio engaña: como {R['ceros_migracion']} países tienen "
  "exactamente cero, el rango intercuartílico es muy angosto y valores de apenas unas unidades quedan señalados. La variable va "
  f"solo de {desc.loc['Net migration', 'minimo']:.0f} a {desc.loc['Net migration', 'maximo']:.0f}".replace("-", "−") + ","
  f" de modo que no tiene valores "
  f"realmente extremos y la dejamos sin cambios. Mortalidad ({at['Deathrate'][0]}) y alfabetización ({at['Literacy (%)'][0]}) se "
  "mantienen por la misma razón: son países reales con situaciones distintas, como el sur de África con alta mortalidad.")

# 3.3 -------------------------------------------------------------------------------------------------------
H2("3.4 Correlaciones y relación entre variables")
H3("3.4.1 Covarianza y correlación de Pearson")
P("Como vimos, la covarianza depende de las unidades. El coeficiente de correlación de Pearson la divide entre "
  "las desviaciones estándar de ambas variables:")
formula("pearson_2", F_PEARSON)
exp_pib = int(math.floor(math.log10(R["var_pib_trans"])))
P("Aquí σ(X) y σ(Y) son las desviaciones estándar de X y de Y. Así el resultado queda entre −1 y 1, sin unidades: valores cercanos "
  "a 1 indican que las variables crecen juntas, cercanos a −1 que una crece cuando la otra baja y cercanos a 0 que no hay relación "
  "lineal. A partir de aquí trabajamos con la base transformada (la que usaremos en el PCA). La Figura "
  f"{F['cov']} muestra por qué la covarianza sola es difícil de interpretar: el PIB per cápita, con varianza del orden de "
  f"10<super>{exp_pib}</super>, domina todo el mapa de color.")
figura("fig_cov.png", 398, f"Matriz de covarianza de las {p_} variables (escala simétrica logarítmica para que se aprecien todas las "
                           "magnitudes).", "cov")
H3("3.4.2 Matriz de correlación")
figura("fig_corr.png", 445, f"Matriz de correlación de Pearson de las {p_} variables (base transformada).", "corr")
P(f"De los {R['n_pares']} pares distintos de variables, {R['n_pares_05']} tienen correlación de al menos 0.5 en valor absoluto y "
  f"{R['n_pares_08']} superan 0.8. La diagonal vale 1 porque cada variable se correlaciona perfectamente consigo misma, y la matriz "
  "es simétrica.")
filas = [["Par de variables", "r"]] + [[f"{N(b)} y {n_(a)}", f"{r:.2f}"] for a, b, r in R["pares_top"]]
tabla("pares", "Los ocho pares con mayor correlación en valor absoluto.", filas, [260, 60])
r_cul_mi = corr.loc["Crops (%)", "Infant mortality (per 1000 births)"]
P("Se forma un bloque claro: la natalidad, la mortalidad infantil y la proporción de agricultura se mueven juntas y en sentido "
  "contrario al PIB, los teléfonos, la alfabetización y los servicios. "
  "En cambio, la tierra cultivable y los cultivos permanentes casi no se relacionan con ese bloque.")

# 3.4.3  ---------------------------------------------------------------------------------------------
top4, bottom2, intens = R["top4"], R["bottom2"], R["intensidad"]
grupos4 = R["grupos_4"]
bloque_des = ["Infant mortality (per 1000 births)", "Birthrate", "Agriculture", "Literacy (%)", "GDP ($ per capita)",
              "Phones (per 1000)", "Service"]
pares05 = [(a, b) for a, b, r in [tuple(x) for x in R["pares_top"]]]
todos_pares = [(VARS[i], VARS[j], corr.iloc[i, j]) for i in range(p_) for j in range(i + 1, p_)]
fuertes = [(a, b) for a, b, r in todos_pares if abs(r) >= 0.5]
en_bloque = sum(1 for a, b in fuertes if a in bloque_des and b in bloque_des)
H3("3.4.3 Variables más y menos relacionadas")
P(f"<b>Las más relacionadas.</b> Las relaciones fuertes se concentran en siete variables: {lista([n_(v) for v in bloque_des])}. "
  f"De los {R['n_pares_05']} pares con |<i>r</i>| ≥ 0.5, {en_bloque} están dentro de ese bloque. Para elegir las cuatro variables más "
  f"correlacionadas sin arbitrariedad, evaluamos los {math.comb(p_, 4)} grupos posibles de cuatro variables y elegimos el de mayor "
  "|<i>r</i>| promedio entre sus seis pares; el valor absoluto hace que cuenten igual las relaciones positivas y las negativas. El "
  f"grupo ganador es {lista([n_(v) for v in top4])}, con |<i>r</i>| promedio de {grupos4[0][0]:.3f}. El segundo, que cambia "
  f"{n_([v for v in grupos4[0][1] if v not in grupos4[1][1]][0])} por {n_([v for v in grupos4[1][1] if v not in grupos4[0][1]][0])}, "
  f"queda prácticamente empatado ({grupos4[1][0]:.3f}), y el tercero, con PIB per cápita y teléfonos, tiene {grupos4[2][0]:.3f}. Es "
  "decir, el núcleo del bloque (mortalidad infantil y natalidad) aparece siempre, y las demás variables del bloque son casi "
  "intercambiables entre sí.")
bot = [tuple(x) for x in R["pares_bottom"]]
P(f"<b>Las menos relacionadas.</b> En el otro extremo, {R['n_no_signif']} de los {R['n_pares']} pares no son significativos. Los "
  f"valores más bajos son prácticamente cero (Tabla {T['menos']}). Para elegir las dos variables menos correlacionadas usamos la "
  "intensidad media de asociación de cada variable, es decir, su |<i>r</i>| promedio con las otras "
  f"{p_ - 1}: las más bajas son {n_(bottom2[0])} ({intens[bottom2[0]]:.2f}) y {n_(bottom2[1])} ({intens[bottom2[1]]:.2f}). "
  "Preferimos este criterio al de tomar el par con <i>r</i> más cercano a cero porque ese par puede incluir una variable muy "
  f"relacionada con las demás: {n_(bot[0][0])} y {n_(bot[0][1])} tienen <i>r</i> = {bot[0][2]:.3f}, pero "
  f"{n_(bot[0][1]) if bot[0][1] in bloque_des else n_(bot[0][0])} forma parte del bloque de desarrollo.")
filas = [["Par de variables", "r"]] + [[f"{N(b)} y {n_(a)}", f"{r:+.3f}"] for a, b, r in bot]
tabla("menos", "Los ocho pares con menor correlación en valor absoluto.", filas, [260, 60])

# 3.3.3 ---------------------------------------------------------------------------------------------
H3("3.4.4 Comparación gráfica de los vectores más y menos correlacionados")
rez = [v for v in top4 if corr.loc[v, pib] < 0]
des_ = [v for v in top4 if v not in rez]
r_rez = [corr.loc[a, b] for i, a in enumerate(rez) for b in rez[i + 1:]]
r_cruz = [corr.loc[a, b] for a in rez for b in des_]
cg = R["cargas"]
P(f"La Figura {F['comparacion']} compara por pares las cuatro variables más correlacionadas, y la Figura {F['vec_pares']} y la "
  f"Tabla {T['eig_pares']} las contrastan con las dos menos correlacionadas ({n_(bottom2[0])} y {n_(bottom2[1])}) a través de los "
  "valores y vectores propios de sus matrices de correlación. Todas usan la base transformada, la misma del mapa de calor.")
figura("fig_comparacion_correlaciones.png", 430, "Comparación por pares de las cuatro variables más correlacionadas. Diagonal: "
       "distribución; abajo: dispersión con su recta de mínimos cuadrados (siena: <i>r</i> positivo; azul: <i>r</i> negativo); "
       "arriba: coeficiente de Pearson con el color del mapa de calor.", "comparacion")
P(f"<b>Relaciones positivas.</b> {lista([N(rez[0])] + [n_(v) for v in rez[1:]])} forman un bloque de rezago, con correlaciones entre "
  f"+{min(r_rez):.2f} y +{max(r_rez):.2f}: donde nacen más niños también mueren más y la economía depende más de la agricultura. "
  "Sus vectores son casi paralelos.")
P(f"<b>Relaciones negativas.</b> {lista([N(v) for v in des_])} tiene correlación negativa con las tres (de "
  f"{max(r_cruz):.2f} a {min(r_cruz):.2f}): su vector apunta en sentido contrario, porque los países con más alfabetización tienen menos natalidad, "
  "menos mortalidad infantil y menos peso agrícola.")
ep = R["eig_pares"]
e4, e2 = R["eig_top4"], R["eig_bottom2"]
pp, pn, pb = R["pares_fig_eig"]
busca = {(a, b): (r, vals, v1) for a, b, r, vals, v1 in ep}
r_pp, l_pp, _ = busca[tuple(pp)]
r_pn, l_pn, _ = busca[tuple(pn)]
r_pb, l_pb, v_pb = busca[tuple(pb)]
grado = lambda r: math.degrees(math.acos(r))
sg = lambda x, d=2: f"{x:+.{d}f}".replace("-", "−")

P("<b>Valores y vectores propios de las variables más y menos correlacionadas.</b> Para ver qué distingue a las variables muy "
  "correlacionadas de las poco correlacionadas, conviene empezar por el caso más simple: dos "
  "variables estandarizadas. Su matriz de correlación y su descomposición en valores y vectores propios son:")
formula("par_eig", r"$R=\genfrac{(}{)}{0}{0}{1\quad r}{r\quad 1}\qquad\lambda_1=1+|r|,\quad\lambda_2=1-|r|\qquad"
                   r"v\in\left\{\dfrac{(1,\ 1)}{\sqrt{2}},\ \dfrac{(1,\,-1)}{\sqrt{2}}\right\}$", 12)
P("donde <i>r</i> es la correlación del par. Los vectores propios son siempre las dos diagonales, sin importar el valor de "
  "<i>r</i>: el primero sigue la diagonal (1, 1)/√2 cuando <i>r</i> &gt; 0 y la (1, −1)/√2 cuando <i>r</i> &lt; 0. Lo que cambia "
  "con la intensidad de la relación son los valores propios: λ<sub>1</sub> es la varianza de los países a lo largo de la diagonal "
  "principal y λ<sub>2</sub> la varianza en la dirección perpendicular. Como λ<sub>1</sub> + λ<sub>2</sub> = 2, la primera "
  "componente explica (1 + |<i>r</i>|)/2 de la varianza del par, desde 50 % cuando no hay correlación hasta 100 % cuando es "
  f"perfecta. La Figura {F['vec_pares']} lo muestra: el par más correlacionado positivamente y el más "
  "correlacionado negativamente dentro de las cuatro variables, frente al par de las dos menos correlacionadas.")
figura("fig_vectores_pares.png", ANCHO, "Vectores propios de la matriz de correlación de tres pares de variables, en valores z. "
       "La flecha siena es <i>v</i><sub>1</sub> y la azul <i>v</i><sub>2</sub>; cada una mide 2√λ, y la elipse punteada abarca dos "
       f"desviaciones estándar en cada dirección propia. (a) {N(pp[0])} y {n_(pp[1])}; (b) {n_(pn[0])} y {n_(pn[1])}; "
       f"(c) {n_(pb[0])} y {n_(pb[1])}, las dos variables menos correlacionadas.", "vec_pares")

P(f"En los paneles (a) y (b) la nube de países es una elipse alargada: λ<sub>1</sub> vale {l_pp[0]:.2f} y {l_pn[0]:.2f}, de modo "
  f"que la primera componente concentra {50 * l_pp[0]:.0f} % y {50 * l_pn[0]:.0f} % de la varianza del par y la segunda apenas "
  f"{50 * l_pp[1]:.0f} % y {50 * l_pn[1]:.0f} %. Las dos variables comparten casi toda su información, y el signo de <i>r</i> solo "
  "decide si la elipse sigue la diagonal ascendente o la descendente. En el panel (c) la nube es casi un círculo: "
  f"λ<sub>1</sub> = {l_pb[0]:.2f} y λ<sub>2</sub> = {l_pb[1]:.2f}, así que la \"dirección principal\" explica solo "
  f"{50 * l_pb[0]:.0f} % y cualquier otra dirección explicaría prácticamente lo mismo; resumir ese par en una componente perdería casi la mitad de su información.")

filas = [["Par de variables", "r", "λ<sub>1</sub>", "λ<sub>2</sub>", "% en CP1", "<i>v</i><sub>1</sub>"]]
for a, b, r, vals, v1 in ep:
    filas.append([f"{N(a)} y {n_(b)}", sg(r), f"{vals[0]:.3f}", f"{vals[1]:.3f}", f"{50 * vals[0]:.1f}",
                  f"({sg(v1[0])}, {sg(v1[1])})"])
tabla("eig_pares", "Valores propios y primer vector propio de la matriz de correlación de cada par: los seis pares de las "
      "cuatro variables más correlacionadas y, en la última fila, el par de las dos menos correlacionadas.", filas,
      [176, 46, 46, 46, 54, 100])
lb = [vals[0] for a, b, r, vals, v1 in ep[:-1]]
P(f"La Tabla {T['eig_pares']} extiende la comparación a los seis pares del bloque. En todos, λ<sub>1</sub> va de {min(lb):.2f} a "
  f"{max(lb):.2f} ({50 * min(lb):.0f} % a {50 * max(lb):.0f} % de la varianza del par), mientras que en el par de las dos menos "
  f"correlacionadas es {l_pb[0]:.2f} ({50 * l_pb[0]:.1f} %). El vector <i>v</i><sub>1</sub> solo cambia de signo en su segunda "
  "coordenada según el signo de <i>r</i>. En el programa comprobamos que λ<sub>1</sub> = 1 + |<i>r</i>| y "
  "λ<sub>2</sub> = 1 − |<i>r</i>| en todos los pares.")
v4 = e4["vecs"]
l4, l2 = e4["vals"], e2["vals"]
c1 = [v4[i][0] for i in range(4)]
P(f"<b>Las cuatro más correlacionadas.</b> Al tomar juntas las cuatro variables, en su matriz de correlación de 4 × 4, "
  f"λ<sub>1</sub> = {l4[0]:.2f} concentra "
  f"{25 * l4[0]:.1f} % de la varianza del grupo y los otros tres valores propios quedan muy por debajo de 1 ({l4[1]:.2f}, {l4[2]:.2f} y {l4[3]:.2f}): las cuatro variables "
  "ocupan, en la práctica, una sola dimensión. Su vector propio, <i>v</i><sub>1</sub> = ("
  + ", ".join(f"{sg(x)} {n_(v)}" for x, v in zip(c1, top4)) + "), reparte el peso casi por igual, con "
  f"coeficientes de magnitud entre {min(abs(x) for x in c1):.2f} y {max(abs(x) for x in c1):.2f}, muy cerca de "
  "1/√4 = 0.5, positivos para las variables de rezago y negativo para la alfabetización, por lo que la dirección principal es "
  "un promedio de las cuatro y no una de ellas en particular; los vectores siguientes solo describen diferencias pequeñas, como "
  f"lo que distingue a la agricultura del resto (<i>v</i><sub>2</sub>, coeficiente {sg(v4[2][1])}).")


# 3.4 -------------------------------------------------------------------------------------------------------
H2("3.5 Componentes principales (PCA)")
H3("3.5.1 Qué ventaja ofrece el PCA")
P(f"Con {p_} variables y una estructura de correlación como la de la sección 3.4, trabajar variable por variable es redundante. El "
  "PCA construye combinaciones lineales de las variables (las componentes principales, CP) que están ordenadas por la varianza que "
  "explican y no están correlacionadas entre sí. Las ventajas concretas para estos datos son:")
P(f"La reducción: veremos que {k} componentes conservan alrededor de {100 * acum_z[k - 1]:.0f} % de la información de las "
  f"{p_} variables. La eliminación de redundancia: las componentes son ortogonales, y lo verificamos numéricamente, pues la "
  f"mayor covarianza entre dos componentes es {R['cov_entre_cp']:.1e}, es decir, cero salvo error de redondeo. La "
  f"visualización: las dos primeras componentes ({100 * acum_z[1]:.1f} % de la varianza) permiten dibujar a los países en un plano. "
  "A cambio, perdemos parte de la información (lo que queda fuera de las componentes elegidas) y las componentes tienden a ser más difíciles de interpretar que "
  "las variables originales.")
H3("3.5.2 Cómo se calculan")
P("El procedimiento es el siguiente. Se centran los datos restando la media de cada variable; se calcula la matriz de covarianza; se "
  "obtienen sus valores propios λ y vectores propios; cada vector propio da los coeficientes de una componente y su valor propio es "
  "la varianza de esa componente. La proporción de varianza explicada por la componente <i>i</i> es λ<sub>i</sub> / Σλ, donde "
  "λ<sub>i</sub> es el valor propio de la componente <i>i</i> y Σλ es la suma de todos los valores propios (la varianza total). Las "
  "componentes principales se obtienen multiplicando los datos centrados por los vectores propios.")

P("Calculamos el PCA de dos formas: con la matriz de covarianza de los datos sin estandarizar y con la de los datos estandarizados "
  "(cada variable dividida entre su desviación estándar). La matriz de covarianza de los datos estandarizados es igual a la "
  "matriz de correlación de los datos originales. Lo demostramos desarrollando los dos procedimientos para un par cualquiera de "
  "variables X<sub>j</sub> y X<sub>k</sub>, donde <i>x<sub>ij</sub></i> es el valor de la variable <i>j</i> en el país <i>i</i>, "
  + mat(r"$\bar{x}_j$", "xbarj") + " su media, <i>s<sub>j</sub></i> su desviación estándar y <i>n</i> el número de países.")
P("<b>Procedimiento 1: covarianza de los datos estandarizados.</b> Cada valor se estandariza como "
  + mat(r"$z_{ij}=(x_{ij}-\bar{x}_j)\,/\,s_j$.", "zij") + " La media de una variable "
  "estandarizada es cero, porque la suma de los valores es <i>n</i> veces su media:")
formula("dem_media_z", r"$\bar{z}_j=\dfrac{1}{n}\sum_{i=1}^{n}\dfrac{x_{ij}-\bar{x}_j}{s_j}=\dfrac{1}{n\,s_j}"
                       r"\left(\sum_{i=1}^{n}x_{ij}-n\,\bar{x}_j\right)=\dfrac{1}{n\,s_j}\left(n\,\bar{x}_j-n\,\bar{x}_j\right)=0$", 11.5)
P("Por lo tanto, en la covarianza de Z<sub>j</sub> y Z<sub>k</sub> las medias valen cero y, al sustituir la definición de "
  "<i>z</i>, se obtiene:")
formula("dem_cov_z", r"$\mathrm{Cov}(Z_j,Z_k)=\dfrac{1}{n-1}\sum_{i=1}^{n}z_{ij}\,z_{ik}=\dfrac{1}{n-1}\sum_{i=1}^{n}"
                     r"\dfrac{x_{ij}-\bar{x}_j}{s_j}\cdot\dfrac{x_{ik}-\bar{x}_k}{s_k}="
                     r"\dfrac{\sum_{i=1}^{n}(x_{ij}-\bar{x}_j)(x_{ik}-\bar{x}_k)}{(n-1)\,s_j\,s_k}$", 11.5)
P("<b>Procedimiento 2: correlación de Pearson de los datos originales.</b> Al sustituir la definición de covarianza "
  "(sección 1.4.1) en la de correlación (sección 1.4.2):")
formula("dem_pearson", r"$r(X_j,X_k)=\dfrac{\mathrm{Cov}(X_j,X_k)}{s_j\,s_k}="
                       r"\dfrac{\dfrac{1}{n-1}\sum_{i=1}^{n}(x_{ij}-\bar{x}_j)(x_{ik}-\bar{x}_k)}{s_j\,s_k}="
                       r"\dfrac{\sum_{i=1}^{n}(x_{ij}-\bar{x}_j)(x_{ik}-\bar{x}_k)}{(n-1)\,s_j\,s_k}$", 11.5)
P("Las dos expresiones finales son idénticas, así que Cov(Z<sub>j</sub>, Z<sub>k</sub>) = r(X<sub>j</sub>, X<sub>k</sub>) para "
  "todo par de variables. En la diagonal, Var(Z<sub>j</sub>) = Cov(Z<sub>j</sub>, Z<sub>j</sub>) = "
  "<i>s<sub>j</sub></i><super>2</super> / <i>s<sub>j</sub></i><super>2</super> = 1, que coincide con r(X<sub>j</sub>, "
  "X<sub>j</sub>) = 1. En forma matricial, si X<sub>c</sub> es la matriz de datos centrados, <i>S</i> su matriz de covarianza y "
  "<i>D</i> = diag(<i>s</i><sub>1</sub>, …, <i>s<sub>p</sub></i>) la matriz diagonal de desviaciones estándar, entonces "
  "<i>Z</i> = X<sub>c</sub><i>D</i><super>−1</super> y, como <i>D</i> es simétrica:")
formula("dem_matricial", r"$S_Z=\dfrac{Z^{\top}Z}{n-1}=\dfrac{(X_cD^{-1})^{\top}(X_cD^{-1})}{n-1}="
                         r"D^{-1}\,\dfrac{X_c^{\top}X_c}{n-1}\,D^{-1}=D^{-1}S\,D^{-1}=R$", 11.5)
_ej = R["ejemplo_cov_r"]
P(f"Por ejemplo, para natalidad y mortalidad infantil, Cov = {_ej['cov']:.2f}, <i>s</i> = {_ej['s_a']:.2f} y "
  f"<i>s</i> = {_ej['s_b']:.2f}. Por el procedimiento 2, <i>r</i> = {_ej['cov']:.2f} / ({_ej['s_a']:.2f} × {_ej['s_b']:.2f}) = "
  f"{_ej['cov'] / (_ej['s_a'] * _ej['s_b']):.3f}, y la covarianza de las dos variables ya estandarizadas (procedimiento 1) da el "
  f"mismo valor, {_ej['cov_z']:.3f}.")
H3("3.5.3 Por qué elegimos cuatro componentes")
P("Para elegir el número de componentes aplicamos el criterio de Kaiser descrito en la sección 1.4.6 al caso estandarizado, "
  "que es el que tiene sentido interpretar (la sección 3.6 lo justifica): se conservan las componentes cuyo valor propio es "
  f"mayor que 1. La Figura {F['scree']} muestra los valores propios junto a ese umbral y la Tabla {T['valores']} los seis "
  "primeros con su porcentaje de varianza.")
figura("fig_scree.png", ANCHO, "Izquierda: valores propios y umbral del criterio de Kaiser (λ = 1). Derecha: varianza "
                               "explicada individual y acumulada.", "scree")
filas = [["Componente", "Valor propio", "% de varianza", "% acumulado", "¿λ > 1?"]]
filas += [[f"CP{i + 1}", f"{val_z[i]:.2f}", f"{100 * prop_z[i]:.1f}", f"{100 * acum_z[i]:.1f}", "Sí" if val_z[i] > 1 else "No"]
          for i in range(6)]
tabla("valores", "Valores propios de la matriz de correlación (primeras seis componentes).", filas, [80, 90, 90, 90, 90])
P(f"Hay {R['k_kaiser']} valores propios mayores que 1, así que el criterio de Kaiser conserva {k} componentes. La CP1 "
  f"({val_z[0]:.2f}) y la CP2 ({val_z[1]:.2f}) quedan muy por encima del umbral; la CP3 y la CP4 ({val_z[2]:.2f} y "
  f"{val_z[3]:.2f}) lo superan con menor margen y juntas aportan {100 * (prop_z[2] + prop_z[3]):.1f} % de la varianza. Con {k} "
  f"componentes se explica {100 * acum_z[k - 1]:.1f} % de la varianza, mucho más que el {100 * acum_z[1]:.1f} % de dos "
  "componentes, y, como se ve en la siguiente subsección, la CP3 y la CP4 tienen una interpretación geográfica clara. La CP5 "
  f"({val_z[4]:.2f}) queda por debajo de 1 y no se incluye.")
H3("3.5.4 Interpretación de las componentes")
P("Los coeficientes de cada componente se interpretan mejor como cargas, es decir, como la correlación entre cada variable original "
  "y la componente. Una carga grande en valor absoluto indica que esa variable pesa mucho en la componente.")
figura("fig_cargas.png", 337, "Cargas de las variables en las primeras cinco componentes (rojo: positivas; azul: negativas).", "cargas")
c_ = lambda v, j: f"{cg[v][j]:.2f}".replace("-", "−")
P(f"La CP1 ({100 * prop_z[0]:.1f} % de la varianza) separa a los países por nivel de desarrollo: pesan a favor el PIB per cápita "
  f"({c_(pib, 0)}), los teléfonos ({c_('Phones (per 1000)', 0)}), la alfabetización ({c_('Literacy (%)', 0)}) y los servicios "
  f"({c_('Service', 0)}), y en contra la mortalidad infantil ({c_('Infant mortality (per 1000 births)', 0)}), la natalidad "
  f"({c_('Birthrate', 0)}), la agricultura ({c_('Agriculture', 0)}) y la mortalidad ({c_('Deathrate', 0)}). Una puntuación alta "
  "indica un país con ingreso, infraestructura y educación altos y una población con baja natalidad.")
P(f"La CP2 ({100 * prop_z[1]:.1f} %) está dominada por los cultivos permanentes ({c_('Crops (%)', 1)}), con aportes de la migración "
  f"neta ({c_('Net migration', 1)}), la densidad ({c_(den, 1)}), el PIB ({c_(pib, 1)}) y la costa/área ({c_(cst, 1)}). Describe un "
  "perfil de territorios pequeños, con mucha costa y densidad, cultivos permanentes y emigración, típico de islas. Esta lectura es "
  "nuestra interpretación y no algo que los datos afirmen por sí mismos.")
P(f"La CP3 ({100 * prop_z[2]:.1f} %) mezcla tierra cultivable ({c_('Arable (%)', 2)}) y densidad ({c_(den, 2)}), con migración neta "
  f"y mortalidad: la intensidad del uso agrícola del territorio y su relación con la población. La CP4 ({100 * prop_z[3]:.1f} %) "
  f"contrapone la razón costa/área ({c_(cst, 3)}) con la tierra cultivable ({c_('Arable (%)', 3)}): geografía costera frente a "
  "tierra de cultivo.")
H3("3.5.5 Los países en el plano de las dos primeras componentes")
figura("fig_biplot.png", 445, "Países en el plano de CP1 y CP2, coloreados por grupo de regiones; las flechas son las cargas de "
                              "las variables.", "biplot")
mg = R["media_grupo_cp1"]
P("Las regiones se ordenan sobre la CP1 como cabría esperar. Las puntuaciones medias son: "
  f"{', '.join(f'{g} {m:.2f}' for g, m in list(mg.items())[:-1])} y {list(mg)[-1]} {list(mg.values())[-1]:.2f}. Los puntos más "
  f"altos en la CP1 son {', '.join(R['cp1_altos'])}, y los más bajos {', '.join(R['cp1_bajos'])}.")

H3("3.5.6 Regresar a la matriz original: reconstrucción con k componentes")
P("Una forma de juzgar la reducción es volver de las componentes a la matriz de datos y comparar con la original. Reconstruimos la "
  "matriz estandarizada con las primeras <i>k</i> componentes, deshacemos la estandarización y el logaritmo y medimos el error. Con "
  "las 13 componentes se recupera exactamente la matriz original, así que toda la pérdida viene de "
  "las componentes que se descartan.")
P("<b>Desarrollo.</b> Las puntuaciones se calcularon con <i>T</i> = <i>Z V</i>. Los vectores propios de una matriz simétrica son "
  "ortogonales entre sí y tienen norma 1, de modo que <i>V</i><super>T</super><i>V</i> = <i>V V</i><super>T</super> = <i>I</i> (la "
  "matriz identidad). Entonces basta multiplicar las puntuaciones por <i>V</i><super>T</super> para despejar la matriz "
  "estandarizada:")
formula("recon_paso1", r"$T=Z\,V\quad\Rightarrow\quad T\,V^{\top}=Z\,V\,V^{\top}=Z\,I=Z$", 12)
P("Con las <i>p</i> componentes el regreso es exacto. Si solo se conservan las primeras <i>k</i> columnas de <i>T</i> y de "
  "<i>V</i>, el mismo producto da una aproximación, que es la suma de lo que aporta cada componente conservada; lo que se pierde "
  "es justo lo que aportaban las componentes descartadas:")
formula("recon_paso2", r"$\hat{Z}_k=T_k\,V_k^{\top}=\sum_{j=1}^{k}t_j\,v_j^{\top}\qquad\qquad Z-\hat{Z}_k=\sum_{j=k+1}^{p}t_j\,v_j^{\top}$", 12)
P("Después se deshacen, en orden inverso, las dos transformaciones que se aplicaron a los datos. La estandarización fue "
  "<i>z<sub>ij</sub></i> = (<i>y<sub>ij</sub></i> − media<sub>j</sub>) / <i>s<sub>j</sub></i>, así que se multiplica por la "
  "desviación estándar y se suma la media de cada variable; y en las tres variables con logaritmo, <i>y</i> = "
  "log<sub>10</sub>(<i>x</i> + 1), se despeja <i>x</i>:")
formula("recon_paso3", r"$\hat{y}_{ij}=\hat{z}_{ij}\,s_j+\bar{y}_j\qquad\qquad\hat{x}_{ij}=10^{\,\hat{y}_{ij}}-1\quad"
                       r"\mathrm{(solo\ en\ las\ variables\ con\ logaritmo)}$", 12)
P("Para medir el error se compara <i>Z</i> con su aproximación. Como las puntuaciones de componentes distintas no están "
  "correlacionadas y la varianza de <i>t<sub>j</sub></i> es λ<sub>j</sub>, el error al cuadrado es la suma de los valores propios "
  "descartados, y dividido entre la varianza total da la proporción de varianza que no se recupera:")
formula("recon_paso4", r"$\dfrac{\Vert Z-\hat{Z}_k\Vert_F^{2}}{\Vert Z\Vert_F^{2}}=\dfrac{\lambda_{k+1}+\cdots+\lambda_p}"
                       r"{\lambda_1+\cdots+\lambda_p}=1-(\mathrm{varianza\ acumulada\ con\ }k\mathrm{\ componentes})$", 12)
_mi = "Infant mortality (per 1000 births)"
_xr = R["recon_paises"]["k4"][0][R["recon_paises"]["vars"].index(_mi)]
_zr = (_xr - desc.loc[_mi, "media"]) / desc.loc[_mi, "desv_est"]
P(f"Por ejemplo, para la mortalidad infantil de México con {PALABRA[k]} componentes, la suma de las {PALABRA[k]} contribuciones da "
  f"un valor estandarizado de {_zr:.3f}".replace("-", "−") + f"; como la media de la variable es {desc.loc[_mi, 'media']:.2f} y su "
  f"desviación estándar {desc.loc[_mi, 'desv_est']:.2f}, el valor reconstruido es " + f"{_zr:.3f}".replace("-", "−") +
  f" × {desc.loc[_mi, 'desv_est']:.2f} + {desc.loc[_mi, 'media']:.2f} = {_xr:.1f} (el valor real es "
  f"{R['recon_paises']['original'][0][R['recon_paises']['vars'].index(_mi)]:.1f}). Esta variable no lleva logaritmo, así que no "
  "hace falta el último paso.")
figura("fig_recon.png", 468, "Izquierda: porcentaje de la varianza que no se recupera según el número de componentes conservadas. "
                              "Derecha: R² de cada variable, en su escala original, al reconstruir con 2 y con 4 componentes.", "recon")
_e = R["err_rel"]
_r4 = R["r2_k"][str(k)]
_o = sorted(_r4.items(), key=lambda kv: -kv[1])
_mej = lista([f"{N(v)} ({x:.2f})" for v, x in _o[:5]])
_peo = lista([f"{N(v)} ({x:.2f})" for v, x in _o[-3:]])
P(f"El error relativo baja de {_e[0]:.2f} con una componente a {_e[k - 1]:.2f} con {PALABRA[k]}. Su cuadrado es igual a 1 menos la varianza "
  f"acumulada, de modo que con {PALABRA[k]} componentes se deja de recuperar {100 * (1 - acum_z[k - 1]):.1f} % de la "
  "varianza, justo la que explicaban las componentes descartadas.")
_rp = R["recon_paises"]
_nom = {"Mexico": "México", "Germany": "Alemania", "Niger": "Níger"}
filas = [["País", "Variable", "Original", "k = 2", f"k = {k}"]]
for _i, _pais in enumerate(_rp["paises"]):
    for _j, _var in enumerate(_rp["vars"]):
        filas.append([_nom[_pais] if _j == 0 else "", N(_var), num(_rp["original"][_i][_j]), num(_rp["k2"][_i][_j]), num(_rp["k4"][_i][_j])])
tabla("recon", "Valores originales y reconstruidos con 2 y 4 componentes para tres países (escala original).", filas,
      [80, 130, 80, 80, 80])
P(f"La reconstrucción de México con cuatro componentes es razonable (PIB per cápita de {_rp['k4'][0][0]:,.0f} contra "
  f"{_rp['original'][0][0]:,.0f} reales). Los extremos "
  "muestran el límite del método: para Alemania, la mortalidad infantil reconstruida con dos componentes es negativa, y para Níger el "
  "PIB per cápita sale negativo con dos y con cuatro componentes. El PCA es lineal y no sabe que estas variables no pueden ser "
  "negativas, por lo que en países muy alejados del promedio la reconstrucción puede dar valores imposibles.")

# 3.6 ---------------------------------------------------------------------------------------------------------
H2("3.6 Estandarización: con y sin")
H3("3.6.1 Por qué importa la escala")
P("El PCA maximiza la varianza, y la varianza depende de las unidades. Si una variable está en miles de dólares y otra en fracciones "
  "entre 0 y 1, la primera aporta varianza varios órdenes de magnitud mayor solo por su escala. La Tabla "
  f"{T['rango']} muestra el rango y la varianza de cada variable en la base transformada.")
filas = [["Variable", "Mínimo", "Máximo", "Rango", "Varianza"]]
filas += [[N(v)] + [num(rango.loc[v, c]) for c in ("minimo", "maximo", "rango", "varianza")] for v in VARS]
tabla("rango", "Rango y varianza de cada variable antes de estandarizar (base transformada).", filas, [130, 80, 80, 80, 98])
P(f"La varianza del PIB per cápita es {num(rango.loc[pib, 'varianza'])}, y la de agricultura es "
  f"{num(rango.loc['Agriculture', 'varianza'])}. El PIB aporta {100 * R['peso_pib']:.2f} % de la varianza total de las {p_} "
  "variables.")
H3("3.6.2 Qué ocurre sin estandarizar y estandarizando")
figura("fig_cp1_comparacion.png", ANCHO, "Izquierda: coeficientes de la CP1 en ambos casos. Derecha: varianza explicada por las "
                                         "primeras seis componentes.", "cp1")
figura("fig_planos.png", ANCHO, "Países en el plano CP1–CP2 sin estandarizar (izquierda) y estandarizando (derecha).", "planos")
tabla("comparacion", "Comparación del PCA con y sin estandarización.", [
    ["Aspecto", "Sin estandarizar", "Estandarizados"],
    ["Matriz usada", "Covarianza", "Correlación (covarianza de los datos estandarizados)"],
    ["Varianza explicada por la CP1", f"{100 * R['prop_s'][0]:.2f} %", f"{100 * prop_z[0]:.1f} %"],
    ["Componentes para llegar a 80 %", f"{R['k_80_s']}", f"{R['k_80']}"],
    ["Variables con peso importante en la CP1", f"1 (PIB per cápita, coeficiente {R['vec_s_pib']:.2f})",
     f"{R['n_cargas_05']} (|carga| ≥ 0.5)"],
    ["Qué representa la CP1", "El PIB per cápita casi por sí solo", "Un eje de desarrollo con muchas variables"],
], [168, 140, 160])
P(f"Sin estandarizar, la CP1 explica {100 * R['prop_s'][0]:.2f} % de la varianza y su vector propio vale {R['vec_s_pib']:.4f} en el "
  "PIB per cápita y casi cero en las demás variables. El PCA no reduce "
  "nada: ordena a los países por ingreso e ignora la mortalidad infantil, la natalidad o la alfabetización.")
P(f"Al estandarizar, cada variable tiene varianza 1 y la información se reparte: la CP1 explica {100 * prop_z[0]:.1f} % y recibe peso "
  f"de {R['n_cargas_05']} variables, las cuatro primeras componentes suman {100 * acum_z[3]:.1f} %. Las puntuaciones de la CP1 de "
  f"ambos casos tienen correlación de {R['r_cp1']:.2f}: ordenan de forma parecida a los países, porque el PIB también forma parte del "
  "eje de desarrollo, pero la versión estandarizada incorpora la información social y demográfica que la otra descarta.")
# 3.7 ---------------------------------------------------------------------------------------------------------
H2("3.7 Predicción con splines cúbicos")
_sp = R["spline_pib"]
_nod = _sp["nodos"]
_pr = _sp["prueba"]
_mx = _sp["mexico"]
_der = {int(k_): v for k_, v in _sp["derivada"].items()}
menos = lambda t: t.replace("-", "−")


def cientifico(x, dec=3):
    """Número en notación científica para las tablas: 1.234 × 10^-5."""
    if abs(x) < 1e-15:                                          # cero salvo error de redondeo
        return "0"
    m, e = f"{x:.{dec}e}".split("e")
    return menos(f"{m} × 10<super>{int(e)}</super>") if int(e) != 0 else menos(f"{float(m):.{dec}f}")


def tex_cientifico(x, dec=3):
    m, e = f"{x:.{dec}e}".split("e")
    return f"{float(m):+.{dec}f}" + (rf"\times 10^{{{int(e)}}}" if int(e) != 0 else "")


P("La base de países corresponde a un solo momento, así que no permite seguir una variable en el tiempo. En cambio, sí permite "
  "predecir a través de los países: un spline cúbico aprende cómo cambia una variable a lo largo de otra y, con esa curva, se "
  "estima el valor de un país que no se usó para construirla. Predecimos la mortalidad infantil, que es la variable con mayor "
  "carga en la CP1 y la más asociada con las demás, a partir del PIB per cápita, que resume el ingreso de cada país. Además, la "
  "forma de esta curva sirve para examinar la H2 con otra variable de desarrollo.")
P(f"<b>Procedimiento.</b> Tomamos los {_sp['n_entren'] + _sp['n_prueba']} países que tienen ambos datos observados (sin valores "
  f"imputados) y apartamos {_sp['n_prueba']} de ellos como países de prueba, con niveles de PIB per cápita muy distintos: "
  f"{lista(list(_sp['prueba']))}. Estos países no se usan para construir la curva. Con los {_sp['n_entren']} restantes formamos {len(_nod)} nodos igual que en la sección 2.3: los "
  "países se ordenan por PIB, se dividen en grupos del mismo tamaño y cada grupo aporta la mediana de su PIB y la mediana de su "
  f"mortalidad infantil. Por esos nodos pasa un spline cúbico natural (Tabla {T['spline_coef']}), y como referencia calculamos "
  "también la interpolación lineal entre los mismos nodos (la fórmula de la sección 2.3).")
P("<b>Spline cúbico natural [5].</b> En lugar de unir los nodos con rectas, usa un polinomio de grado 3 en cada intervalo, de "
  "modo que la curva completa es suave. Escribimos el desarrollo con una variable general <i>x</i>, que aquí es el PIB per cápita. En el intervalo [<i>x<sub>j</sub></i>, <i>x</i><sub><i>j</i>+1</sub>], con <i>j</i> = 0, …, <i>n</i> − 1:")
formula("spline_def", r"$S_j(x)=a_j+b_j\,(x-x_j)+c_j\,(x-x_j)^2+d_j\,(x-x_j)^3$", 12)
P("Hay 4<i>n</i> coeficientes por determinar, y se les piden 4<i>n</i> condiciones: que cada polinomio pase por sus dos nodos "
  "(2<i>n</i> condiciones), que la primera y la segunda derivadas de polinomios vecinos coincidan en los nodos interiores "
  "(2(<i>n</i> − 1) condiciones) y que la segunda derivada valga cero en los dos extremos, que es lo que hace natural al spline "
  "(2 condiciones):")
formula("spline_cond", r"$S_j(x_j)=y_j,\quad S_j(x_{j+1})=y_{j+1},\quad S_j'(x_{j+1})=S_{j+1}'(x_{j+1}),\quad "
                       r"S_j''(x_{j+1})=S_{j+1}''(x_{j+1}),\quad S_0''(x_0)=S_{n-1}''(x_n)=0$", 11)
P("El desarrollo es el siguiente, con <i>h<sub>j</sub></i> = <i>x</i><sub><i>j</i>+1</sub> − <i>x<sub>j</sub></i>. De "
  "<i>S<sub>j</sub></i>(<i>x<sub>j</sub></i>) = <i>y<sub>j</sub></i> se obtiene directamente <i>a<sub>j</sub></i> = "
  "<i>y<sub>j</sub></i>. La segunda derivada es <i>S<sub>j</sub></i>''(<i>x</i>) = 2<i>c<sub>j</sub></i> + "
  "6<i>d<sub>j</sub></i>(<i>x</i> − <i>x<sub>j</sub></i>), así que la continuidad de la segunda derivada da "
  "<i>c</i><sub><i>j</i>+1</sub> = <i>c<sub>j</sub></i> + 3<i>d<sub>j</sub>h<sub>j</sub></i>, de donde se despeja "
  "<i>d<sub>j</sub></i>. Al sustituir <i>a<sub>j</sub></i> y <i>d<sub>j</sub></i> en la condición "
  "<i>S<sub>j</sub></i>(<i>x</i><sub><i>j</i>+1</sub>) = <i>y</i><sub><i>j</i>+1</sub> se despeja <i>b<sub>j</sub></i>:")
formula("spline_bd", r"$d_j=\dfrac{c_{j+1}-c_j}{3\,h_j}\qquad\qquad b_j=\dfrac{y_{j+1}-y_j}{h_j}-\dfrac{h_j}{3}\,(2\,c_j+c_{j+1})$", 12)
P("Falta la continuidad de la primera derivada, <i>S<sub>j</sub></i>'(<i>x</i>) = <i>b<sub>j</sub></i> + "
  "2<i>c<sub>j</sub></i>(<i>x</i> − <i>x<sub>j</sub></i>) + 3<i>d<sub>j</sub></i>(<i>x</i> − <i>x<sub>j</sub></i>)², que da "
  "<i>b</i><sub><i>j</i>+1</sub> = <i>b<sub>j</sub></i> + <i>h<sub>j</sub></i>(<i>c<sub>j</sub></i> + "
  "<i>c</i><sub><i>j</i>+1</sub>). Al sustituir en ella la expresión de <i>b<sub>j</sub></i> queda una ecuación por cada nodo "
  "interior (<i>j</i> = 1, …, <i>n</i> − 1) en la que solo aparecen las <i>c</i>:")
formula("spline_sistema", r"$h_{j-1}\,c_{j-1}+2\,(h_{j-1}+h_j)\,c_j+h_j\,c_{j+1}=3\left(\dfrac{y_{j+1}-y_j}{h_j}-\dfrac{y_j-y_{j-1}}{h_{j-1}}\right)"
                          r",\qquad c_0=c_n=0$", 12)
P("Es un sistema de ecuaciones lineales tridiagonal (cada ecuación solo relaciona tres incógnitas vecinas) y de diagonal "
  "estrictamente dominante, por lo que tiene solución única. Lo resolvemos con <i>numpy.linalg.solve</i>; con las "
  "<i>c<sub>j</sub></i> se calculan <i>b<sub>j</sub></i> y <i>d<sub>j</sub></i> con las fórmulas anteriores, y el valor predicho "
  "para un país es <i>S<sub>j</sub></i>(<i>x</i>) en el intervalo que contiene a su PIB. Comprobamos que nuestro spline "
  "coincide con el de <i>scipy.interpolate.CubicSpline</i>.")
filas = [["Intervalo de PIB (USD)", "a", "b", "c", "d"]]
for (x0, _), (x1, _), co in zip(_nod[:-1], _nod[1:], _sp["coef"]):
    filas.append([f"{x0:,.0f} – {x1:,.0f}", f"{co[0]:.2f}", cientifico(co[1]), cientifico(co[2]), cientifico(co[3])])
tabla("spline_coef", "Coeficientes del spline cúbico natural de la mortalidad infantil en función del PIB per cápita: en cada "
      "intervalo, <i>S<sub>j</sub></i>(<i>x</i>) = <i>a</i> + <i>b</i>(<i>x</i> − <i>x<sub>j</sub></i>) + <i>c</i>(<i>x</i> − "
      "<i>x<sub>j</sub></i>)² + <i>d</i>(<i>x</i> − <i>x<sub>j</sub></i>)³, donde <i>x<sub>j</sub></i> es el primer valor del "
      "intervalo.", filas, [118, 60, 96, 96, 96])
figura("fig_spline_pib.png", ANCHO, "Izquierda: mortalidad infantil frente al PIB per cápita, con los países de entrenamiento "
       "(gris), los de prueba (azul), los nodos, el spline cúbico natural y la interpolación lineal. Derecha: derivada del spline, es "
       "decir, cuánto cambia la mortalidad infantil por cada 1,000 dólares de PIB en cada punto de la curva.", "spline_pib")
_jm = _mx["j"]
_cm = _sp["coef"][_jm]
_dx = _mx["pib"] - _nod[_jm][0]
P(f"<b>Ejemplo: México.</b> México quedó entre los países de prueba, así que su dato no se usó para construir la curva. Su PIB "
  f"per cápita es de {_mx['pib']:,.0f} dólares, que está en el intervalo {_nod[_jm][0]:,.0f} – {_nod[_jm + 1][0]:,.0f}; entonces "
  f"<i>x</i> − <i>x<sub>j</sub></i> = {_dx:,.1f} y la predicción es:")
formula("spline_ejemplo", rf"$S(9000)={_cm[0]:.2f}{tex_cientifico(_cm[1])}\,({_dx:.1f}){tex_cientifico(_cm[2])}\,({_dx:.1f})^2"
                          rf"{tex_cientifico(_cm[3])}\,({_dx:.1f})^3={_mx['pred']:.2f}$".replace("S(9000)", f"S({_mx['pib']:.0f})"), 11)
P(f"El valor real de México en la base es {_mx['real']:.2f} muertes por cada 1000 nacimientos, así que el error es de "
  f"{abs(_mx['pred'] - _mx['real']):.2f}. La Figura {F['spline_pib']} muestra la curva completa junto con los países de "
  f"entrenamiento y de prueba, y la Tabla {T['spline_pred']} la predicción para los {_sp['n_prueba']} países de prueba.")
_sel = sorted(_pr.items(), key=lambda t: t[1][0])
filas = [["País", "PIB per cápita", "Dato real", "Spline cúbico", "Error del spline", "Interpolación lineal", "Error lineal"]]
for pais, (pib_, real_, spl_, lin_) in _sel:
    filas.append([pais, f"{pib_:,.0f}", f"{real_:.2f}", f"{spl_:.2f}", menos(f"{spl_ - real_:+.2f}"), f"{lin_:.2f}",
                  menos(f"{lin_ - real_:+.2f}")])
tabla("spline_pred", "Predicción de la mortalidad infantil (muertes por cada 1000 nacimientos) de los países de prueba, "
      "ordenados por PIB per cápita.", filas, [86, 66, 54, 64, 70, 72, 56])
_peor = max(_pr.items(), key=lambda t: abs(t[1][2] - t[1][1]))
_rm = _sp["rmse"]
P(f"<b>Resultado.</b> En los {_sp['n_prueba']} países de prueba, la raíz del error cuadrático medio (RMSE) del spline es de "
  f"{_rm['spline']:.2f} muertes por cada 1000 nacimientos y la de la interpolación lineal de {_rm['lineal']:.2f}. Como referencia, "
  f"si a todos se les asignara la media de los países de entrenamiento, sin usar su PIB, el error sería de {_rm['media']:.2f}: "
  f"conocer el PIB reduce el error en {100 * (1 - _rm['spline'] / _rm['media']):.0f} %. Los dos métodos dan casi lo mismo porque "
  "pasan por los mismos nodos; la ventaja del spline no está en el error, sino en que es una curva suave con derivada continua. "
  "El error sigue siendo alto porque a un mismo nivel de ingreso hay países con mortalidad infantil muy distinta: el peor caso es "
  f"{_peor[0]}, con un PIB de {_peor[1][0]:,.0f} dólares, una mortalidad real de {_peor[1][1]:.1f} y una predicción de "
  f"{_peor[1][2]:.1f}.")
P("<b>Derivada.</b> Como cada tramo del spline es un polinomio, su derivada tiene una fórmula explícita y dice cuánto cambia la "
  "mortalidad infantil por cada dólar adicional de PIB en cada punto de la curva:")
formula("spline_derivada", r"$S_j'(x)=b_j+2\,c_j\,(x-x_j)+3\,d_j\,(x-x_j)^2$", 12)
_pos = _sp["positiva"]
P(f"Multiplicada por 1,000, da el cambio por cada 1,000 dólares: {menos(f'{_der[1000]:.1f}')} muertes por cada 1000 nacimientos "
  f"cuando el PIB es de 1,000 dólares, {menos(f'{_der[5000]:.1f}')} a los 5,000, {menos(f'{_der[10000]:.1f}')} a los 10,000 y "
  f"prácticamente cero ({menos(f'{_der[20000]:+.2f}')}) a los 20,000. Es decir, los primeros aumentos de ingreso van acompañados "
  "de una caída muy grande de la mortalidad infantil y después el efecto se agota, lo mismo que plantea la H2 para los teléfonos. "
  + (f"La derivada no es perfectamente negativa: entre {_pos[0]:,.0f} y {_pos[1]:,.0f} dólares es apenas positiva (como máximo "
     f"+{_pos[2]:.2f}), porque el spline pasa exactamente por nodos que tienen algo de ruido y se ondula un poco entre ellos; no es "
     "un aumento real de la mortalidad." if _pos else ""))
P(f"<b>¿Qué pasaría si el PIB de México se duplicara?</b> Con {2 * _mx['pib']:,.0f} dólares, la curva predice "
  f"{_mx['pred_doble']:.2f} muertes por cada 1000 nacimientos, frente a {_mx['pred']:.2f} con su PIB actual. Esta lectura es una "
  "asociación entre países y no una relación de causa: la curva describe cómo son los países con más ingreso, no garantiza lo "
  f"que ocurriría si un país aumentara el suyo. Además, fuera del intervalo de los nodos ({_nod[0][0]:,.0f} a "
  f"{_nod[-1][0]:,.0f} dólares) el spline no se usa para extrapolar: se toma el valor del nodo del extremo.")

# =============================================================================================
# 4. DISCUSIÓN
# =============================================================================================
H1("4. Discusión")
H2("4.1 Comparación con las hipótesis")
P(f"<b>H1 (las variables miden desarrollo y se pueden resumir).</b> Se cumple en lo esencial. {R['n_pares_05']} de los "
  f"{R['n_pares']} pares de variables tienen |r| ≥ 0.5 y se forma un bloque claro de desarrollo; la primera componente "
  f"({100 * prop_z[0]:.1f} %) ordena a las regiones de África a Europa. La comparación de la sección 3.4.4 lo muestra de forma "
  f"directa: las cuatro variables más correlacionadas ({lista([n_(v) for v in top4])}) se condensan en la CP1, mientras que "
  f"{n_(bottom2[0])} y {n_(bottom2[1])}, las menos correlacionadas, solo aparecen en componentes posteriores. Sin embargo, la "
  f"reducción es moderada: hacen falta cuatro componentes para llegar a {100 * acum_z[3]:.1f} %. Es decir, los {p_} indicadores no se reducen "
  "a una sola dimensión, porque las variables geográficas (tierra cultivable, cultivos permanentes, costa) aportan estructura propia.")
_h2 = R["evidencia_h2"]
_lit, _agr, _mi = (_h2[v] for v in ("Literacy (%)", "Agriculture", "Infant mortality (per 1000 births)"))
_nl = _lit["nodos"]
_veces = [abs(e["pendientes"][0] / e["pendientes"][-1]) for e in _h2.values()]
P(f"<b>H2 (las mejoras tienen rendimientos decrecientes).</b> Se cumple. Para comprobarla usamos los mismos nodos de la sección "
  f"2.3: los países se ordenan por número de teléfonos, se dividen en {R['n_nodos']} grupos y entre cada par de nodos consecutivos "
  f"se calcula la pendiente, es decir, cuánto cambia la variable por cada 100 líneas telefónicas (Figura {F['rendimientos']}). En "
  f"el primer tramo, de {_nl[0][0]:.0f} a {_nl[1][0]:.0f} teléfonos por cada 1000 habitantes, la alfabetización sube "
  f"{_nl[1][1] - _nl[0][1]:.1f} puntos (una pendiente de {_lit['pendientes'][0]:.1f} puntos por cada 100 teléfonos); en el "
  f"último, de {_nl[-2][0]:.0f} a {_nl[-1][0]:.0f} teléfonos, sube apenas {_nl[-1][1] - _nl[-2][1]:.1f} puntos "
  f"({_lit['pendientes'][-1]:.2f} por cada 100). Lo mismo ocurre con la mortalidad infantil, cuya pendiente pasa de "
  f"{_mi['pendientes'][0]:.1f} a {_mi['pendientes'][-1]:.2f} muertes por cada 1000 nacimientos, y con el peso de la agricultura "
  f"en el PIB, que pasa de {100 * _agr['pendientes'][0]:.1f} a {100 * _agr['pendientes'][-1]:.1f} puntos porcentuales: en las "
  f"tres variables la pendiente del primer tramo es entre {min(_veces):.0f} y {max(_veces):.0f} veces la del último. Es decir, "
  "la alfabetización se satura cerca de 100 % y la mortalidad infantil y la agricultura bajan muy rápido al principio y después "
  "casi no cambian.".replace("-", "−"))
_dp = {int(k_): v for k_, v in R["spline_pib"]["derivada"].items()}
P(f"El spline de la sección 3.7 lleva la misma idea: su derivada indica que, cuando el PIB per cápita es de 1,000 "
  f"dólares, cada 1,000 dólares adicionales van acompañados de {abs(_dp[1000]):.1f} muertes menos por cada 1000 nacimientos; a los "
  f"5,000 dólares, de {abs(_dp[5000]):.1f} menos, y a partir de unos 20,000 la mortalidad infantil prácticamente ya no cambia.")
figura("fig_rendimientos.png", ANCHO, "Alfabetización, peso de la agricultura en el PIB y mortalidad infantil frente al número de "
       "teléfonos por cada 1000 habitantes, con los nodos (puntos negros) y la interpolación lineal entre ellos. El tramo siena es "
       "el primero; arriba de cada panel, la pendiente del primer y del último tramo (cambio de la variable por cada 100 "
       "teléfonos).",
       "rendimientos")
H2("4.2 Limitaciones")
P(f"Las principales limitaciones son: (1) {R['ceros_migracion']} países tienen migración neta igual a cero, probablemente "
  "datos faltantes en algunos casos; (2) la imputación usa una sola variable predictora y no medimos su error, sobre todo en "
  f"{n_(imp[0][0])} ({imp[0][1]} de {R['n_depurados']} países imputados); (3) los datos son de mediados de la década de 2000; "
  "(4) la interpretación de la CP2 a la CP4 es nuestra lectura de las cargas; (5) Pearson subestima relaciones no lineales, como "
  "muestra la H2; (6) la reconstrucción con cuatro componentes recupera mal algunas variables y da valores negativos en países "
  "extremos como Níger, y (7) el spline usa solo el PIB per cápita, por lo que su error sigue siendo alto (RMSE de "
  f"{R['spline_pib']['rmse']['spline']:.1f}) y describe una asociación, no un efecto causal.")

# =============================================================================================
# 5. CONCLUSIONES
# =============================================================================================
H1("5. Conclusiones")
P(f"Partimos de {R['n_paises']} países y {R['n_columnas']} variables. Después de la depuración quedaron {R['n_depurados']} países "
  f"y {p_} variables numéricas; descartamos las variables categóricas y las redundantes (otros usos del suelo, industria) con razones "
  "explícitas, estimamos los vacíos restantes por interpolación lineal sobre nodos a partir de la variable más correlacionada "
  "con cada una, y transformamos con logaritmo las tres variables de asimetría extrema.")
P("Las correlaciones muestran un bloque de variables que describe el nivel de desarrollo (mortalidad infantil, natalidad, "
  "alfabetización, PIB per cápita, teléfonos, agricultura y servicios), mientras que las condiciones geográficas (tierra cultivable, "
  f"cultivos permanentes, costa) se relacionan poco con él. Las cuatro variables más correlacionadas ({lista([n_(v) for v in top4])}, "
  f"con |r| promedio de {R['top4_puntaje']:.2f}) son casi redundantes y se resumen en la primera componente; las dos menos "
  f"correlacionadas ({n_(bottom2[0])} y {n_(bottom2[1])}) aportan información propia.")
P("Las relaciones dentro de ese bloque son monótonas pero no rectas: los primeros aumentos de infraestructura acompañan saltos "
  "grandes en alfabetización, mortalidad infantil y peso de la agricultura, y entre los países mejor equipados esas variables casi "
  f"no cambian (en las tres, la pendiente del primer tramo es entre {min(_veces):.0f} y {max(_veces):.0f} veces la del último). "
  "Esto confirma la H2 y explica por qué la correlación de Pearson subestima la fuerza de estas relaciones.")
P(f"Con datos estandarizados, cuatro componentes explican {100 * acum_z[3]:.1f} % de la varianza. La primera (el "
  f"{100 * prop_z[0]:.1f} %) es un eje de desarrollo que ordena a las regiones de forma coherente.")
P("Al regresar a la matriz original con cuatro componentes se recuperan razonablemente las variables de desarrollo (mortalidad infantil, natalidad, teléfonos, PIB per cápita), pero no las geográficas de colas largas (densidad de población y costa/área); la reconstrucción es una aproximación y puede dar valores imposibles en países extremos.")
P("Sin estandarizar, el PCA se reduce al PIB por la diferencia de escalas y pierde su utilidad. Las variables de este conjunto "
  "están en unidades distintas (dólares, porcentajes, fracciones, razones), así que estandarizar es la decisión adecuada y la que "
  "usamos para elegir las componentes. Solo tendría sentido no estandarizar si todas las variables estuvieran en la misma unidad y "
  "la diferencia de varianzas fuera información que se quiere conservar, y aquí no es el caso.")
_sp = R["spline_pib"]
P(f"El spline cúbico natural construido con {_sp['n_entren']} países predijo la mortalidad infantil de los otros "
  f"{_sp['n_prueba']} a partir de su PIB per cápita con un error (RMSE) de {_sp['rmse']['spline']:.2f} muertes por cada 1000 "
  f"nacimientos, {100 * (1 - _sp['rmse']['spline'] / _sp['rmse']['media']):.0f} % menor que sin usar el PIB; para México estimó "
  f"{_sp['mexico']['pred']:.2f} frente al valor real de {_sp['mexico']['real']:.2f}. Su derivada muestra que la mortalidad "
  "infantil baja muy rápido con los primeros aumentos de ingreso y casi no cambia en los países más ricos.")

# =============================================================================================
# 6. BIBLIOGRAFÍA
# =============================================================================================
H1("6. Bibliografía")
for ref in [
    "[1] fernandol. <i>Countries of the World</i> [conjunto de datos]. Kaggle. https://www.kaggle.com/datasets/fernandol/countries-of-the-world",
    "[2] Jolliffe, I. T. (2002). <i>Principal Component Analysis</i> (2.ª ed.). Springer.",
    "[3] Kaiser, H. F. (1960). The application of electronic computers to factor analysis. <i>Educational and Psychological "
    "Measurement</i>, 20(1), 141–151.",
    "[4] United Nations Development Programme (1990). <i>Human Development Report 1990</i>. Oxford University Press.",
    "[5] Burden, R. L. y Faires, J. D. (2011). <i>Numerical Analysis</i> (9.ª ed.). Brooks/Cole, Cengage Learning.",
]:
    P(ref, biblio)

# ---------------------------------------------------------------------------------------------
doc = Reporte(SALIDA)
doc.multiBuild(story)
print("Reporte generado en:", SALIDA.relative_to(BASE))
