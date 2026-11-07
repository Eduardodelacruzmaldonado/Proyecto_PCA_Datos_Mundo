# -*- coding: utf-8 -*-
"""
Genera el reporte en PDF del proyecto a partir de los resultados de exploracion_pca.py.

Uso (desde la carpeta del proyecto):
    python exploracion_pca.py        # en macOS / Linux: python3
    python generar_pdf_reporte.py

El PDF queda en reporte/Proyecto_PCA_Paises.pdf. Todos los números del texto se leen de la
carpeta "resultados" y los fragmentos de código se copian de exploracion_pca.py, de modo que el
reporte siempre corresponde al análisis que se ejecutó. Las fuentes tipográficas vienen en la
carpeta "fuentes", así que el PDF se ve igual en Windows, macOS y Linux.
"""
import json
import math
import re
import sys
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Preformatted, Spacer, Table,
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
CODIGO = BASE / "exploracion_pca.py"

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
                        ("Serif-BoldItalic", "LiberationSerif-BoldItalic.ttf"),
                        ("Mono", "DejaVuSansMono.ttf")):
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
codigo = ParagraphStyle("codigo", fontName="Mono", fontSize=6.7, leading=8.3, leftIndent=3,
                        spaceBefore=3, spaceAfter=8)
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
ORDEN_FIG = (["categoricas", "faltantes", "log"] + [f"hb_{i:02d}" for i in range(len(estad))]
             + ["atipicos", "cov", "corr", "comparacion", "contraste", "relaciones", "scree", "cargas",
                "biplot", "cp1", "planos"])
F = {k: i + 1 for i, k in enumerate(ORDEN_FIG)}
ORDEN_TAB = ["variables", "descartadas", "descriptivas", "covarianza", "atipicos", "pares", "menos",
             "clasificacion", "valores", "rango", "comparacion"]
T = {k: i + 1 for i, k in enumerate(ORDEN_TAB)}


def figura(archivo, ancho, texto, clave):
    ruta = FIG / archivo
    from reportlab.lib.utils import ImageReader
    w, h = ImageReader(str(ruta)).getSize()
    img = Image(str(ruta), width=ancho, height=ancho * h / w)
    story.append(KeepTogether([Spacer(1, 4), img, Paragraph(f"Figura {F[clave]}. {texto}", pie)]))


def tabla(clave, titulo, filas, anchos, encabezado=True, alinear_der=()):
    datos = [[Paragraph(str(c), celda_b if (encabezado and i == 0) else celda) for c in fila]
             for i, fila in enumerate(filas)]
    t = Table(datos, colWidths=anchos, repeatRows=1 if encabezado else 0, hAlign="CENTER")
    estilo = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 2.2),
              ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2), ("LEFTPADDING", (0, 0), (-1, -1), 3),
              ("RIGHTPADDING", (0, 0), (-1, -1), 3),
              ("LINEABOVE", (0, 0), (-1, 0), .9, colors.black),
              ("LINEBELOW", (0, -1), (-1, -1), .9, colors.black)]
    if encabezado:
        estilo.append(("LINEBELOW", (0, 0), (-1, 0), .5, colors.black))
    t.setStyle(TableStyle(estilo))
    story.append(Paragraph(f"Tabla {T[clave]}. {titulo}", tit_tabla))
    story.append(t)
    story.append(Spacer(1, 8))


BLOQUES = {}
_actual = None
for linea in CODIGO.read_text(encoding="utf-8").splitlines():
    m = re.match(r"\s*# >>> (\w+)", linea)
    if m:
        _actual = m.group(1); BLOQUES[_actual] = []; continue
    if re.match(r"\s*# <<< (\w+)", linea):
        _actual = None; continue
    if _actual:
        BLOQUES[_actual].append(linea)


def bloque_codigo(nombre, ancho_max=112):
    """Copia un bloque de exploracion_pca.py y corta las líneas largas como en un editor."""
    lineas = []
    for linea in BLOQUES[nombre]:
        sangria = len(linea) - len(linea.lstrip())
        while len(linea) > ancho_max:
            corte = linea.rfind(" ", 0, ancho_max)
            corte = ancho_max if corte <= sangria else corte
            lineas.append(linea[:corte])
            linea = " " * (sangria + 4) + linea[corte:].lstrip()
        lineas.append(linea)
    while lineas and not lineas[-1].strip():
        lineas.pop()
    story.append(Preformatted("\n".join(lineas), codigo))


def formula(clave, tex, tam=12.5):
    """Dibuja una fórmula con mathtext de matplotlib y la inserta centrada."""
    ruta = FORM / f"{clave}.png"
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, tex, fontsize=tam, math_fontfamily="stix")
    fig.savefig(ruta, dpi=300, bbox_inches="tight", pad_inches=0.04, transparent=False)
    plt.close(fig)
    from reportlab.lib.utils import ImageReader
    w, h = ImageReader(str(ruta)).getSize()
    img = Image(str(ruta), width=w * 72 / 300, height=h * 72 / 300)
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
        self.addPageTemplates([PageTemplate("portada", [marco]),
                               PageTemplate("normal", [marco], onPage=self.pie_de_pagina)])

    @staticmethod
    def pie_de_pagina(canv, doc):
        canv.saveState()
        canv.setStrokeColorRGB(.6, .6, .6); canv.setLineWidth(.4); canv.line(72, 54, 540, 54)
        canv.setFont("Serif", 8.5); canv.setFillColor(colors.HexColor("#444444"))
        canv.drawString(72, 39.6, "Métodos Matemáticos para Ciencia de Datos")
        canv.drawRightString(540, 39.6, str(doc.page))
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
P("Métodos Matemáticos para Ciencia de Datos", centro(14, esp=24))
P("Exploración de datos y reducción de dimensiones<br/>con componentes principales",
  ParagraphStyle("titulo", fontName="Serif-Bold", fontSize=21, leading=27, alignment=TA_CENTER, spaceAfter=12))
P(f"Indicadores demográficos, económicos y geográficos de {R['n_paises']} países", centro(13, "Serif-Italic", 26))
story.append(Table([[""]], colWidths=[ANCHO], style=[("LINEABOVE", (0, 0), (-1, 0), .8, colors.black)]))
story.append(Spacer(1, 34))
etq = ParagraphStyle("etq", fontName="Serif-Bold", fontSize=11.5, leading=16)
val = ParagraphStyle("val", fontName="Serif", fontSize=11.5, leading=16)
datos_portada = [[Paragraph("Integrantes", etq), Paragraph("De La Cruz Maldonado José Eduardo<br/>López Reyes Jorge", val)],
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
  "principales. Se depuró la base (variables redundantes descartadas, tres territorios eliminados por exceso de faltantes, "
  "imputación con la mediana regional y logaritmo en las variables de asimetría extrema) y se obtuvieron gráficas, medidas "
  "descriptivas, valores atípicos y matrices de covarianza y correlación, identificando las variables más y menos relacionadas. "
  "Luego se aplicó el análisis de componentes principales (PCA) con y sin estandarización, eligiendo el número de componentes "
  f"con los criterios de Kaiser, Horn y varianza acumulada. Con datos estandarizados, cuatro componentes explican "
  f"{100 * acum_z[k - 1]:.1f} % de la varianza y la primera ({100 * prop_z[0]:.1f} %) funciona como un eje de nivel de desarrollo; "
  f"sin estandarizar, la primera explica {100 * R['prop_s'][0]:.2f} % pero solo refleja el PIB per cápita por su escala. Por ello, "
  "estandarizar es indispensable cuando las variables tienen unidades distintas.")
P("<b>Palabras clave:</b> análisis exploratorio, componentes principales, estandarización, correlación, indicadores de países.",
  ParagraphStyle("pc", fontName="Serif", fontSize=8.5, leading=11))
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
P("El objetivo de este trabajo es realizar un análisis exploratorio del conjunto de datos <i>Countries of the World</i> [1] y, "
  "con la base ya depurada, determinar si los indicadores demográficos, económicos y geográficos de los países pueden "
  "resumirse en unas pocas componentes principales sin perder demasiada información. El análisis sigue el flujo planteado "
  "en clase: datos, exploración (gráficas, preprocesamiento, correlaciones, medidas descriptivas y valores atípicos), "
  "corrección de los datos cuando hace falta y reducción de dimensiones con PCA.")
P("Partimos de dos hipótesis de trabajo que se retoman en la Discusión. <b>H1:</b> muchas variables miden en el fondo el nivel "
  "de desarrollo de un país (salud, ingreso, educación, estructura económica), por lo que estarán fuertemente correlacionadas y "
  "unas pocas componentes bastarán para resumir buena parte de la varianza. <b>H2:</b> como las variables están en unidades muy "
  "distintas, el PCA sin estandarizar quedará dominado por la variable de mayor escala, mientras que con estandarización sí "
  "resumirá la estructura de los datos.")
H2("1.2 Justificación y antecedentes")
P("Los países se describen con decenas de indicadores y varios de ellos dicen casi lo mismo. Resumirlos en pocas dimensiones "
  "permite comparar países, visualizarlos en un plano y usar menos variables en modelos posteriores. Además, este conjunto es un "
  "buen caso para entender el PCA, porque la decisión de estandarizar o no cambia por completo el resultado.")
P("El análisis de componentes principales es una técnica clásica para reducir dimensiones [2], y los criterios para decidir "
  "cuántas componentes conservar se han estudiado desde hace décadas [3, 4]. Como antecedente de la idea de resumir el desarrollo "
  "de un país con pocas dimensiones, el Índice de Desarrollo Humano del PNUD [5] combina salud, educación e ingreso en un solo "
  "indicador; a diferencia del PCA, se construye con una fórmula fija y no a partir de la estructura de los datos.")
H2("1.3 Origen y descripción de los datos")
P("Los datos vienen del conjunto <i>Countries of the World</i>, publicado en Kaggle por el usuario fernandol "
  "(https://www.kaggle.com/datasets/fernandol/countries-of-the-world) [1]. Cada fila es un país o territorio y cada columna una "
  "característica. Por los valores que contiene (por ejemplo, China aparece con 1,313,973,713 habitantes), la información "
  "corresponde a mediados de la década de 2000, así que las conclusiones describen ese periodo y no la situación actual.")
P("El archivo usa coma como separador decimal (\"48,0\") y los nombres de país y de región traen espacios al final, por lo que "
  f"al leerlo indicamos <i>decimal=\",\"</i> y limpiamos los textos. La Tabla {T['variables']} resume las columnas.")
bloque_codigo("lectura")
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
H2("1.4 Herramientas y métodos")
P("Todo el análisis se hizo en Python 3 con estos paquetes: pandas [6] (lectura del CSV con <i>read_csv</i>, imputación con "
  "<i>groupby/transform</i> y <i>fillna</i>, y los métodos <i>mean, median, var, std, skew, cov</i> y <i>corr</i>); NumPy [7] "
  "(matriz de covarianza con <i>numpy.cov</i>, valores y vectores propios con <i>numpy.linalg.eigh</i> y <i>log10</i>); "
  "Matplotlib [8] y seaborn [9] (histogramas, diagramas de caja, dispersión y mapas de calor); SciPy (valor crítico de la "
  "correlación) y scikit-learn [10], cuya clase <i>PCA</i> usamos solo para verificar nuestro cálculo. Las herramientas que "
  "aparecen en el pizarrón de clase (matrices de covarianza y correlación, PCA y estandarización) se describen a grandes "
  "rasgos; las demás (transformación logarítmica, criterio del rango intercuartílico y simulación de Horn) se explican con más detalle.")
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
  "columnas son los vectores propios y <i>T</i> contiene las puntuaciones (scores) de cada país. Si <i>S</i> se calcula con datos "
  "estandarizados, es la matriz de correlación. La carga de la variable <i>i</i> en la componente <i>j</i> es "
  "<i>v<sub>ij</sub></i>·√λ<sub>j</sub>, y equivale a la correlación entre ambas cuando se parte de datos estandarizados.")

H3("1.4.6 Cuántas componentes conservar")
p_ = len(VARS)
P(f"El PCA produce tantas componentes como variables (aquí <i>p</i> = {p_}) y solo conservándolas todas se mantiene el 100 % de "
  "la varianza; reducir dimensiones significa quedarse con las primeras <i>k</i> y descartar las demás. La elección de <i>k</i> es "
  "un compromiso entre dos errores. Si se conservan <b>muy pocas</b>, se pierde estructura real de los datos. Si se conservan "
  "<b>demasiadas</b>, se incluyen componentes que solo reflejan el ruido del muestreo o la variación propia de una sola variable: "
  "no se pueden interpretar y cambiarían con otra muestra de países. Como no hay una regla única, usamos varios criterios con "
  "lógicas distintas y comparamos sus resultados. Damos el papel principal a los criterios de Kaiser y de Horn por dos razones: "
  "son reglas numéricas y reproducibles, que no dependen de apreciar a ojo una gráfica, y se complementan, porque Kaiser compara "
  "cada valor propio con una referencia teórica fija y Horn lo compara con una referencia obtenida del azar para el tamaño de "
  "nuestra muestra.")
P("<b>Criterio de Kaiser [3, 11].</b> Con datos estandarizados se conservan las componentes cuyo valor propio es mayor que 1:")
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
  f"solo por azar. Con {R['n_depurados']} países y {p_} variables de puro ruido salen en promedio {R['ruido_mayor_1']:.1f} valores "
  "propios mayores que 1, de modo que Kaiser tiende a conservar más componentes de las necesarias.")
P("<b>Simulación (análisis paralelo) de Horn [4].</b> Corrige esa limitación comparando cada valor propio con el que produce el "
  "azar. El procedimiento es: (1) se generan <i>B</i> matrices de números aleatorios normales independientes, del mismo tamaño que "
  f"nuestros datos ({R['n_depurados']} × {p_}), es decir, datos sin ninguna correlación real; (2) a cada una se le calcula la matriz de "
  "correlación y sus valores propios, ordenados de mayor a menor; (3) para cada posición <i>j</i> se toma un valor de referencia "
  "de los <i>B</i> valores simulados, ya sea el percentil 95, que es la versión más exigente [12], o la media, que es la propuesta "
  "original de Horn; y (4) se conservan las componentes cuyo λ<sub>j</sub> observado supera la referencia de su misma posición:")
formula("horn", r"$\mathrm{se\ conserva\ la\ CP}_j\ \mathrm{si}\ \lambda_j>P_{95}\left(\lambda_j^{(1)},\lambda_j^{(2)},\ldots,\lambda_j^{(B)}\right)$", 12)
P("donde λ<sub>j</sub><super>(b)</super> es el <i>j</i>-ésimo valor propio de la simulación <i>b</i>. La idea es que una componente "
  "vale la pena solo si explica más varianza de la que explicaría por casualidad con este número de países y de variables. Cuando "
  "<i>n</i> crece, los valores propios simulados se acercan a 1 y Horn coincide con Kaiser; con <i>n</i> finito, la referencia de "
  "Horn baja con la posición en lugar de ser constante. En estudios de simulación, el análisis paralelo está entre los métodos que "
  "mejor recuperan el número correcto de componentes, mientras que Kaiser tiende a sobrestimarlo [13].")
P("<b>Cómo los usamos en este trabajo.</b> Aplicamos ambos criterios a los valores propios de la matriz de correlación (datos "
  "transformados y estandarizados), con 500 simulaciones de Horn, semilla fija y el percentil 95; como comprobación también "
  "reportamos la media de las simulaciones. Leemos los dos criterios como cotas: Kaiser marca un límite permisivo y Horn uno "
  "exigente, que separa lo que con seguridad no es ruido. Los complementamos con el criterio de varianza acumulada, que toma el "
  "menor número de componentes que explica al menos 80 %, y con el gráfico de sedimentación (<i>scree plot</i>), que ayuda a ver "
  "dónde la curva de valores propios deja de bajar con fuerza. El programa toma como número de componentes la mediana de Kaiser, "
  "Horn y varianza acumulada, y la sección 3.5.3 discute el resultado.")

# =============================================================================================
# 2. ANÁLISIS EXPERIMENTAL
# =============================================================================================
H1("2. Análisis experimental")
P("Esta sección describe qué se hizo con los datos antes de analizarlos y sobre qué base se obtuvo cada resultado de la sección 3. "
  "El tratamiento tiene cuatro pasos: contar y tratar los valores faltantes, decidir qué variables y países se quedan, imputar los "
  "vacíos restantes y transformar las variables muy asimétricas. Las gráficas de la sección 3.1 se hicieron con los datos "
  "originales, antes de modificar nada, para mostrar la información tal como viene en la fuente.")
H2("2.1 Valores faltantes")
falt = list(R["faltantes"].items())
mas = [f"{N(v)} ({c} países, {pc:.1f} %)" for v, (c, pc) in falt[:5]]
max_num = max(pc for v, (c, pc) in falt if v != "Climate")
P(f"Primero contamos los vacíos de cada columna. Las que más faltan son {lista(mas)}. Ninguna columna numérica pasa del "
  f"{math.ceil(max_num)} % de vacíos, así que no hay razón para descartarlas únicamente por faltantes.")
figura("fig_faltantes.png", 374, "Porcentaje de países sin dato en cada columna (solo se muestran las que tienen vacíos).", "faltantes")
bloque_codigo("faltantes")
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
                                "con ella. La usamos para colorear gráficas y para imputar faltantes."],
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
P(f"Para decidir qué hacer con los vacíos de las {p_} variables que sí usamos, contamos cuántos le faltan a cada país. Eliminamos a "
  f"los que tienen cuatro o más vacíos (más del 30 % de sus variables): {', '.join(R['eliminados'])}. Quedan {R['n_depurados']} "
  "países. A los demás les rellenamos cada vacío con la mediana de su región; usamos la mediana porque no la afectan los valores "
  "extremos y la región porque agrupa países con condiciones parecidas, de modo que es mejor imputar con ella que con la mediana mundial.")
P(f"Se imputaron {', '.join(f'{N(v)} ({c})' for v, c in imp[:3])}, {N(imp[3][0])} ({imp[3][1]}) y pocos valores en el resto. "
  f"El caso más grande, {n_(imp[0][0])}, representa {100 * imp[0][1] / R['n_depurados']:.1f} % de los países. Imputar con la "
  "mediana reduce un poco la varianza real de esas variables, lo cual dejamos señalado como limitación.")
bloque_codigo("depuracion")
H2("2.4 Transformación de variables muy asimétricas")
P("Esta es la flecha de \"corregir datos\" del esquema del pizarrón: los resultados de la sección 3.1 muestran que algunas variables "
  "tienen colas derechas extremas que, al calcular correlaciones y componentes, dejarían que unos pocos países decidan el resultado. "
  "Con un criterio fijo, aplicamos <i>log10(x + 1)</i> a las variables con coeficiente de asimetría mayor o igual a 2 en valor "
  "absoluto. Elegimos el logaritmo porque comprime las colas derechas y respeta el orden de los países, y sumamos 1 porque estas "
  f"variables tienen ceros (por ejemplo, países sin costa). Las variables transformadas son: {', '.join(N(v) for v in R['a_log'])}.")
bloque_codigo("logaritmo")
figura("fig_log.png", 431, "Efecto de la transformación logarítmica sobre las tres variables más asimétricas (izquierda: original; "
       "derecha: transformada).", "log")
al = R["asim_log"]
P(f"La asimetría de densidad baja de {al[VARS[0]][0]:.2f} a {al[VARS[0]][1]:.2f}, la de costa/área de {al[VARS[1]][0]:.2f} a "
  f"{al[VARS[1]][1]:.2f} y la de cultivos permanentes de {al['Crops (%)'][0]:.2f} a {al['Crops (%)'][1]:.2f}. Las demás variables "
  "tienen asimetría menor que 2 y se dejan en su escala original para conservar su interpretación.")
H2("2.5 Cómo se obtuvo cada resultado")
P(f"<b>Gráficas de cada variable (3.1).</b> Se hicieron con los datos originales ({R['n_paises']} filas, omitiendo los vacíos de "
  "cada variable): un histograma de 20 intervalos con líneas de media y mediana, y un diagrama de caja, con la función "
  "<i>hist_box</i> del programa.")
P(f"<b>Medidas descriptivas y covarianza (3.2) y atípicos (3.3).</b> Se calcularon sobre la base depurada ({R['n_depurados']} países "
  f"× {p_} variables), antes de transformar, con <i>mean, median, var, std</i> y <i>cov</i>. Los atípicos se contaron con el "
  "criterio del RIC antes y después de la transformación logarítmica; los diagramas de caja comparativos usan valores z para que "
  "las variables sean comparables.")
P(f"<b>Correlaciones (3.4).</b> Se calcularon sobre la base transformada ({R['n_depurados']} × {p_}) con "
  "<i>corr(method=\"pearson\")</i>. La selección de las variables más y menos correlacionadas usa criterios explícitos (sección "
  "3.4.3). La clasificación en variables independientes y dependientes se hizo a partir del significado de cada variable y de su "
  "mayor correlación con las demás; es una hipótesis razonada, no una prueba.")
P("<b>PCA (3.5).</b> Se aplicó a la base transformada y estandarizada. Calculamos la matriz de covarianza, extrajimos valores y "
  "vectores propios con <i>numpy.linalg.eigh</i> y los ordenamos de mayor a menor. El signo de una componente es arbitrario, así que "
  "fijamos una convención (CP1 con signo positivo en el PIB per cápita). Verificamos el cálculo con <i>sklearn.decomposition.PCA</i> "
  "(los valores propios coinciden) y comprobamos que las componentes no están correlacionadas. La simulación de Horn usa 500 "
  "repeticiones con semilla fija, de modo que el resultado se puede reproducir. El programa toma como número de componentes la "
  f"mediana de los tres criterios ({R['k_kaiser']}, {R['k_horn']} y {R['k_80']}, por lo que resulta {k}); la justificación "
  "detallada está en la sección 3.5.3.")
P("<b>Comparación con y sin estandarización (3.6).</b> Se repite el mismo cálculo sobre la misma base transformada, una vez con los "
  "datos solo centrados (matriz de covarianza) y otra con datos estandarizados (matriz de correlación). Por eso, \"sin "
  "estandarizar\" significa sin dividir entre la desviación estándar, pero con la transformación logarítmica ya aplicada. Todo el "
  "código está en el archivo <i>exploracion_pca.py</i>.")

# =============================================================================================
# 3. RESULTADOS
# =============================================================================================
H1("3. Resultados")
P("Los resultados se presentan en el orden del flujo de trabajo: gráficas de cada variable (3.1), medidas descriptivas (3.2), "
  "valores atípicos (3.3), correlaciones (3.4), componentes principales (3.5) y comparación con y sin estandarización (3.6). Cada "
  "resultado lleva una lectura breve; la comparación con las hipótesis, las limitaciones y las mejoras posibles se discuten en la sección 4.")
H2("3.1 Gráficas de cada característica")
P("Antes de modificar nada, graficamos cada variable numérica con un histograma y un diagrama de caja. En el histograma la línea "
  "discontinua marca la media y la continua la mediana; cuando están muy separadas, la distribución es asimétrica. En el diagrama de "
  "caja, la caja va del primer al tercer cuartil, los bigotes llegan hasta 1.5 veces el rango intercuartílico y los círculos son "
  "valores atípicos. Las variables se grafican con los datos originales, con los vacíos omitidos en cada una.")
bloque_codigo("histogramas")
top3 = R["top3"]
DESCRIP = {
    "Population": "Unos pocos países enormes (China, India, Estados Unidos) contrastan con una mayoría de países pequeños.",
    "Area (sq. mi.)": f"Pocos países ocupan superficies muy grandes ({', '.join(top3['Area (sq. mi.)'])}); la mayoría son pequeños o islas.",
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
    figura(fila["archivo"], ANCHO, f"{fila['nombre']}. {DESCRIP[fila['var']]} Asimetría {fila['asim']:.1f}; media "
                                   f"{num(fila['media'])} frente a mediana {num(fila['mediana'])}; {atip_txt} por el criterio "
                                   "del rango intercuartílico.", fila["archivo"][:-4])
asim = estad.set_index("var")["asim"]
muy_asim = asim[asim.abs() >= 3].sort_values(ascending=False)
P("En conjunto, casi todas las variables tienen asimetría positiva (la media es mayor que la mediana). Las más asimétricas son "
  f"{lista([n_(v) for v in muy_asim.index])}, con coeficientes de asimetría de {muy_asim.min():.1f} a {muy_asim.max():.1f}. Esto "
  "anticipa que algunas necesitarán una transformación antes de calcular correlaciones y componentes principales, algo que se "
  "resuelve en la sección 2.")

# 3.2 ------------------------------------------------------------------------------------------------------
H2("3.2 Medidas descriptivas")
P(f"Calculamos las medidas descriptivas con las {p_} variables elegidas, ya depuradas pero todavía en su escala original (así se "
  "pueden interpretar). La media resume el centro, pero se mueve con los valores extremos; la mediana no. Por eso comparar ambas "
  "dice si hay asimetría. La varianza mide la dispersión alrededor de la media, y su raíz cuadrada (desviación estándar) está en "
  "las mismas unidades que la variable:")
formula("media_varianza_2", F_MEDIA)
formula("covarianza_2", F_COV)
P("Los símbolos son los definidos en la sección 1.4: <i>n</i> es el número de países, <i>x<sub>i</sub></i> y <i>y<sub>i</sub></i> "
  "son los valores de cada variable en el país <i>i</i>, y la barra sobre una letra indica su media.")
bloque_codigo("descriptivas")
filas = [["Variable", "Media", "Mediana", "Varianza", "Desv. est.", "Mínimo", "Máximo"]]
for v in VARS:
    d = desc.loc[v]
    filas.append([N(v)] + [num(d[c]) for c in ("media", "mediana", "varianza", "desv_est", "minimo", "maximo")])
tabla("descriptivas", f"Medidas descriptivas de las {p_} variables elegidas ({R['n_depurados']} países, escala original).",
      filas, [118, 54, 54, 70, 58, 54, 60])
mayor_media = [v for v in VARS if desc.loc[v, "media"] > desc.loc[v, "mediana"]]
menor_media = [v for v in VARS if v not in mayor_media]
cst, den, pib = "Coastline (coast/area ratio)", "Pop. Density (per sq. mi.)", "GDP ($ per capita)"
P(f"La media supera a la mediana en {len(mayor_media)} de las {p_} variables (todas salvo {lista([n_(v) for v in menor_media])}), lo "
  f"que confirma la asimetría derecha. El caso más claro es costa/área, con media {desc.loc[cst, 'media']:.1f} y mediana "
  f"{redondeo(desc.loc[cst, 'mediana'], 2)}, y también densidad de población ({desc.loc[den, 'media']:.0f} contra "
  f"{desc.loc[den, 'mediana']:.0f}). En el PIB per cápita la media ({desc.loc[pib, 'media']:,.0f}) casi duplica a la mediana "
  f"({desc.loc[pib, 'mediana']:,.0f}): un país \"típico\" tiene un ingreso mucho menor al que sugiere el promedio.")
clave = R["clave_cov"]
filas = [[""] + [N(v) for v in clave]] + [[N(a)] + [num(cov_orig.loc[a, b]) for b in clave] for a in clave]
tabla("covarianza", "Matriz de covarianza (escala original) de cinco indicadores de desarrollo. La diagonal contiene las varianzas.",
      filas, [98, 82, 72, 72, 72, 72])
P("Elegimos estas cinco variables para mostrar la covarianza porque son las que, como veremos en la sección 3.4, más se relacionan "
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
bloque_codigo("atipicos")
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
  f"cápita más alto de la muestra, {dens_txt}; no son errores de captura. Quitarlos haría que el estudio dejara fuera justamente a los países que más contrastan. "
  "En su lugar, reducimos su influencia de dos maneras: la transformación logarítmica (que baja los atípicos de densidad de "
  f"{dl[0]} a {dl[1]}, de costa/área de {cl[0]} a {cl[1]} y de cultivos permanentes de {crl[0]} a {crl[1]}) y la estandarización "
  "que se discute en la sección 3.6.")
P(f"Un caso aparte es migración neta, con {mig[0]} atípicos. Aquí el criterio engaña: como {R['ceros_migracion']} países tienen "
  "exactamente cero, el rango intercuartílico es muy angosto y valores de apenas unas unidades quedan señalados. La variable va "
  f"solo de {desc.loc['Net migration', 'minimo']:.0f} a {desc.loc['Net migration', 'maximo']:.0f}".replace("-", "−") + ","
  f" de modo que no tiene valores "
  f"realmente extremos y la dejamos sin cambios. Mortalidad ({at['Deathrate'][0]}) y alfabetización ({at['Literacy (%)'][0]}) se "
  "mantienen por la misma razón: son países reales con situaciones distintas, como el sur de África con alta mortalidad.")

# 3.4 -------------------------------------------------------------------------------------------------------
H2("3.4 Correlaciones y relación entre variables")
H3("3.4.1 Covarianza y correlación de Pearson")
P("Como se vio en la sección 3.2, la covarianza depende de las unidades. El coeficiente de correlación de Pearson la divide entre "
  "las desviaciones estándar de ambas variables:")
formula("pearson_2", F_PEARSON)
exp_pib = int(math.floor(math.log10(R["var_pib_trans"])))
P("Aquí σ(X) y σ(Y) son las desviaciones estándar de X y de Y. Así el resultado queda entre −1 y 1, sin unidades: valores cercanos "
  "a 1 indican que las variables crecen juntas, cercanos a −1 que una crece cuando la otra baja y cercanos a 0 que no hay relación "
  "lineal. A partir de aquí trabajamos con la base transformada (la que usaremos en el PCA). La Figura "
  f"{F['cov']} muestra por qué la covarianza sola es difícil de leer: el PIB per cápita, con varianza del orden de "
  f"10<super>{exp_pib}</super>, domina todo el mapa de color.")
figura("fig_cov.png", 398, f"Matriz de covarianza de las {p_} variables (escala simétrica logarítmica para que se aprecien todas las "
                           "magnitudes).", "cov")
H3("3.4.2 Matriz de correlación")
bloque_codigo("correlacion")
figura("fig_corr.png", 445, f"Matriz de correlación de Pearson de las {p_} variables (base transformada).", "corr")
P(f"De los {R['n_pares']} pares distintos de variables, {R['n_pares_05']} tienen correlación de al menos 0.5 en valor absoluto y "
  f"{R['n_pares_08']} superan 0.8. La diagonal vale 1 porque cada variable se correlaciona perfectamente consigo misma, y la matriz "
  "es simétrica.")
filas = [["Par de variables", "r"]] + [[f"{N(b)} y {n_(a)}", f"{r:.2f}"] for a, b, r in R["pares_top"]]
tabla("pares", "Los ocho pares con mayor correlación en valor absoluto.", filas, [260, 60])
r_cul_mi = corr.loc["Crops (%)", "Infant mortality (per 1000 births)"]
P("Se forma un bloque claro: la natalidad, la mortalidad infantil y la proporción de agricultura se mueven juntas y en sentido "
  "contrario al PIB, los teléfonos, la alfabetización y los servicios. Es decir, varias columnas están diciendo casi lo mismo, el "
  "grado de desarrollo del país. En cambio, la tierra cultivable y los cultivos permanentes casi no se relacionan con ese bloque "
  f"(por ejemplo, |r| = {abs(r_cul_mi):.2f} entre cultivos permanentes y mortalidad infantil). Esta redundancia es lo que hace útil un PCA.")

# 3.4.3 (nuevo) ---------------------------------------------------------------------------------------------
top4, bottom2, intens = R["top4"], R["bottom2"], R["intensidad"]
grupos4 = R["grupos_4"]
bloque_des = ["Infant mortality (per 1000 births)", "Birthrate", "Agriculture", "Literacy (%)", "GDP ($ per capita)",
              "Phones (per 1000)", "Service"]
pares05 = [(a, b) for a, b, r in [tuple(x) for x in R["pares_top"]]]
todos_pares = [(VARS[i], VARS[j], corr.iloc[i, j]) for i in range(p_) for j in range(i + 1, p_)]
fuertes = [(a, b) for a, b, r in todos_pares if abs(r) >= 0.5]
en_bloque = sum(1 for a, b in fuertes if a in bloque_des and b in bloque_des)
H3("3.4.3 Variables más y menos relacionadas")
P(f"Para leer el mapa de calor con más detalle conviene verlo de forma geométrica. Cada variable es un vector de {R['n_depurados']} "
  "valores, uno por país; si se centran restando su media, el coeficiente de Pearson es el coseno del ángulo que forman los dos "
  "vectores. Así, |<i>r</i>| cercano a 1 indica vectores casi paralelos (<i>r</i> &gt; 0) u opuestos (<i>r</i> &lt; 0), es decir, "
  "información repetida, y <i>r</i> cercano a 0 indica vectores casi perpendiculares, que aportan información distinta. Con "
  f"<i>n</i> = {R['n_depurados']}, una correlación es significativamente distinta de cero al 5 % si |<i>r</i>| &gt; "
  f"{R['r_crit']:.3f} (prueba <i>t</i> de Pearson); por debajo de ese valor no se puede afirmar que haya relación lineal.")
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
bloque_codigo("mas_menos_correlacionadas")

# 3.4.4 (nuevo) ---------------------------------------------------------------------------------------------
H3("3.4.4 Comparación gráfica de los vectores más y menos correlacionados")
rez = [v for v in top4 if corr.loc[v, pib] < 0]
des_ = [v for v in top4 if v not in rez]
r_rez = [corr.loc[a, b] for i, a in enumerate(rez) for b in rez[i + 1:]]
r_cruz = [corr.loc[a, b] for a in rez for b in des_]
cg = R["cargas"]
P(f"La Figura {F['comparacion']} compara por pares las cuatro variables más correlacionadas y la Figura {F['contraste']} las "
  "contrasta con las dos menos correlacionadas. Ambas usan la base transformada, la misma del mapa de calor.")
figura("fig_comparacion_correlaciones.png", 430, "Comparación por pares de las cuatro variables más correlacionadas. Diagonal: "
       "distribución; abajo: dispersión con su recta de mínimos cuadrados (siena: <i>r</i> positivo; azul: <i>r</i> negativo); "
       "arriba: coeficiente de Pearson con el color del mapa de calor.", "comparacion")
P(f"<b>Relaciones positivas.</b> {lista([N(rez[0])] + [n_(v) for v in rez[1:]])} forman un bloque de rezago, con correlaciones entre "
  f"+{min(r_rez):.2f} y +{max(r_rez):.2f}: donde nacen más niños también mueren más y la economía depende más de la agricultura. "
  "Sus vectores son casi paralelos.")
P(f"<b>Relaciones negativas.</b> {lista([N(v) for v in des_])} tiene correlación negativa con las tres (de "
  f"{max(r_cruz):.2f} a {min(r_cruz):.2f}): su vector apunta en sentido contrario, porque los países con más alfabetización tienen menos natalidad, "
  "menos mortalidad infantil y menos peso agrícola.")
P("<b>No todo es lineal.</b> La alfabetización se satura en el 100 % y la agricultura frente a la mortalidad infantil se abre en "
  "abanico. Pearson mide solo la parte lineal de la relación, así que en esos pares la asociación real es incluso más fuerte que "
  f"<i>r</i>. <b>Consecuencia para el PCA:</b> cuatro vectores casi colineales contienen esencialmente una sola dirección de "
  f"variación; por eso, en la sección 3.5.4, las cuatro tienen cargas grandes en la CP1 "
  f"({', '.join(f'{cg[v][0]:.2f}'.replace('-', '−') for v in top4)}).")
bloque_codigo("figura_comparacion")
largo = R["largo_circulo"]
figura("fig_contraste_correlaciones.png", ANCHO, "Contraste entre las cuatro variables más correlacionadas (siena: bloque de "
       "rezago; azul: alfabetización) y las dos menos correlacionadas (gris). (a) Submatriz de correlación. (b) Cargas en el plano "
       "CP1–CP2, con la longitud de cada flecha entre paréntesis. (c) |<i>r</i>| promedio de cada variable con las demás. (d) Par "
       "más correlacionado frente al par de las dos menos correlacionadas, en valores z.", "contraste")
lt = [largo[v] for v in top4]
cgb0, cgb1 = cg[bottom2[0]], cg[bottom2[1]]
cp_b1 = max(range(4), key=lambda j: abs(cgb1[j]))
socio_b1 = corr[bottom2[1]].drop(bottom2[1]).abs().idxmax()
rank = sorted(intens, key=intens.get, reverse=True)
P(f"<b>(a)</b> El bloque de 4 × 4 está lleno de colores intensos, mientras que las filas y columnas de {n_(bottom2[0])} y "
  f"{n_(bottom2[1])} son casi blancas: su |<i>r</i>| con las cuatro variables no pasa de {R['r_bottom2_con_top4']:.2f} y entre ellas "
  f"vale {R['r_bottom2']:.2f}. Geométricamente, sus vectores son casi perpendiculares a los otros cuatro y entre sí.")
P("<b>(b)</b> Las coordenadas de cada flecha son sus cargas en la CP1 y la CP2, es decir, sus correlaciones con esas componentes "
  "(sección 1.4.5); la longitud al cuadrado es la fracción de la varianza de la variable que explica ese plano. Las cuatro variables "
  f"correlacionadas tienen longitudes de {min(lt):.2f} a {max(lt):.2f} (de {100 * min(lt) ** 2:.0f} % a {100 * max(lt) ** 2:.0f} % "
  "de su varianza) y se alinean sobre el eje horizontal: la CP1 es justamente la dirección que comparten. La flecha de "
  f"{n_(bottom2[0])} mide {largo[bottom2[0]]:.2f} ({100 * largo[bottom2[0]] ** 2:.0f} %): su información está en la CP3 y la CP4 "
  f"(cargas de {cgb0[2]:.2f} y {cgb0[3]:.2f}). La de {n_(bottom2[1])} mide {largo[bottom2[1]]:.2f}, casi toda en la "
  f"CP{cp_b1 + 1} ({cgb1[cp_b1]:.2f}), que comparte con {n_(socio_b1)} (<i>r</i> = {corr.loc[bottom2[1], socio_b1]:.2f}): se "
  "relaciona poco con el resto, pero no está completamente aislada.")
P(f"<b>(c)</b> En el ordenamiento por intensidad media, las cuatro variables están entre las siete más asociadas (de "
  f"{min(intens[v] for v in top4):.2f} a {max(intens[v] for v in top4):.2f}; {n_(rank[1])}, con {intens[rank[1]]:.2f}, es la "
  f"segunda) y las dos menos correlacionadas cierran la lista ({intens[bottom2[1]]:.2f} y {intens[bottom2[0]]:.2f}).")
pf = R["par_fuerte"]
P(f"<b>(d)</b> En valores z, la pendiente de la recta de regresión es exactamente <i>r</i>. {N(pf[1])} frente a {n_(pf[0])} se "
  f"alinea sobre una recta de pendiente {pf[2]:.2f}; {n_(bottom2[0])} frente a {n_(bottom2[1])} forma una nube sin dirección "
  f"(pendiente {R['r_bottom2']:.2f}).")
P("En resumen, las variables muy correlacionadas son redundantes y el PCA las resume en una sola componente, mientras que las poco "
  "correlacionadas tienen información propia que solo aparece en componentes posteriores. Por eso una o dos componentes no bastan "
  "para resumir las trece variables, y decidir cuántas conservar requiere criterios formales (secciones 1.4.6 y 3.5.3).")

# 3.4.5 ---------------------------------------------------------------------------------------------------------
H3("3.4.5 Variables independientes y dependientes")
P("Para separar variables que actúan como punto de partida de las que parecen depender de otras, usamos dos pistas: el sentido que "
  "tiene cada variable (una característica física del territorio no depende del ingreso de un país; la mortalidad infantil sí puede "
  "depender de él) y qué tan fuerte es su correlación con las demás. La Tabla "
  f"{T['clasificacion']} resume la clasificación junto con la mayor correlación de cada variable.")
PAPEL = {
    "Pop. Density (per sq. mi.)": ("Independiente", "Es una condición de partida (población entre superficie)."),
    "Coastline (coast/area ratio)": ("Independiente", "Es una característica geográfica fija."),
    "Net migration": ("Dependiente (débil)", "Responde a condiciones económicas, pero su relación lineal es baja."),
    "Infant mortality (per 1000 births)": ("Dependiente", "Resultado de la salud y el ingreso; muy ligada a la natalidad."),
    "GDP ($ per capita)": ("Dependiente", "Se mueve con la infraestructura (teléfonos) y la educación."),
    "Literacy (%)": ("Dependiente", "Resultado de la educación, relacionada con el desarrollo."),
    "Phones (per 1000)": ("Dependiente", "Indicador de infraestructura que acompaña al ingreso."),
    "Arable (%)": ("Independiente", "Depende del suelo y del clima, no del ingreso."),
    "Crops (%)": ("Independiente", "Depende del suelo y del clima."),
    "Birthrate": ("Dependiente", "Cambia con el nivel de desarrollo y educación."),
    "Deathrate": ("Dependiente", "Depende de la edad de la población y de la salud."),
    "Agriculture": ("Dependiente", "Su peso disminuye al crecer la economía."),
    "Service": ("Dependiente", "Su peso aumenta al crecer la economía."),
}
mc = R["mayor_corr"]
filas = [["Variable", "Papel", "Justificación", "Mayor |r| (con)"]]
filas += [[N(v), PAPEL[v][0], PAPEL[v][1], f"{mc[v][0]:.2f} ({N(mc[v][1])})"] for v in VARS]
tabla("clasificacion", "Clasificación de las variables según su papel y mayor correlación con otra variable.", filas,
      [108, 82, 168, 110])
ind = [mc[v][0] for v in VARS if PAPEL[v][0] == "Independiente"]
dep = [mc[v][0] for v in VARS if PAPEL[v][0] == "Dependiente"]
P(f"Las cuatro variables que clasificamos como independientes tienen correlaciones máximas bajas (entre {min(ind):.2f} y "
  f"{max(ind):.2f}), lo que es coherente con que no las determine el resto. Las dependientes forman el bloque con correlaciones de "
  f"{min(dep):.2f} a {max(dep):.2f}. La correlación no demuestra causalidad, de modo que la clasificación debe leerse como una "
  "hipótesis razonable: por ejemplo, el PIB y los teléfonos pueden influirse mutuamente. Si más adelante se quisiera ajustar un "
  "modelo, buenas variables respuesta serían el PIB per cápita o la mortalidad infantil, explicadas con las condiciones geográficas "
  "y demográficas.")
figura("fig_relaciones.png", ANCHO, "Tres relaciones entre variables dependientes, con su recta de ajuste y su coeficiente de "
                                    "correlación.", "relaciones")

# 3.5 -------------------------------------------------------------------------------------------------------
H2("3.5 Componentes principales (PCA)")
H3("3.5.1 Qué ventaja ofrece el PCA")
P(f"Con {p_} variables y una estructura de correlación como la de la sección 3.4, trabajar variable por variable es redundante. El "
  "PCA construye combinaciones lineales de las variables (las componentes principales, CP) que están ordenadas por la varianza que "
  "explican y no están correlacionadas entre sí. Las ventajas concretas para estos datos son:")
P(f"Primero, la reducción: veremos que {k} componentes conservan alrededor de {100 * acum_z[k - 1]:.0f} % de la información de las "
  f"{p_} variables. Segundo, la eliminación de redundancia: las componentes son ortogonales, y lo verificamos numéricamente, pues la "
  f"mayor covarianza entre dos componentes es {R['cov_entre_cp']:.1e}, es decir, cero salvo error de redondeo. Tercero, la "
  f"visualización: las dos primeras componentes ({100 * acum_z[1]:.1f} % de la varianza) permiten dibujar a los países en un plano. "
  "Cuarto, en un modelo posterior las componentes evitan la multicolinealidad entre las variables originales. A cambio, perdemos "
  "parte de la información (lo que queda fuera de las componentes elegidas) y las componentes son más difíciles de interpretar que "
  "las variables originales.")
H3("3.5.2 Cómo se calculan")
P("El procedimiento es el siguiente. Se centran los datos restando la media de cada variable; se calcula la matriz de covarianza; se "
  "obtienen sus valores propios λ y vectores propios; cada vector propio da los coeficientes de una componente y su valor propio es "
  "la varianza de esa componente. La proporción de varianza explicada por la componente <i>i</i> es λ<sub>i</sub> / Σλ, donde "
  "λ<sub>i</sub> es el valor propio de la componente <i>i</i> y Σλ es la suma de todos los valores propios (la varianza total). Las "
  "puntuaciones (scores) de cada país se obtienen multiplicando los datos centrados por los vectores propios.")
P("Calculamos el PCA de dos formas: con la matriz de covarianza de los datos sin estandarizar y con la de los datos estandarizados "
  "(cada variable dividida entre su desviación estándar). Como se anota en el pizarrón, la matriz de covarianza de los datos "
  "estandarizados es igual a la matriz de correlación; lo comprobamos en el programa. Programamos el cálculo con los valores propios "
  "directamente y lo comparamos con la función <i>PCA</i> de scikit-learn, con coincidencia total en los valores propios "
  f"({'verificado' if R['verificacion_sklearn'] else 'no verificado'}).")
bloque_codigo("pca")
H3("3.5.3 Por qué elegimos cuatro componentes")
P("El número de componentes no se puede escoger al azar, así que usamos los criterios de la sección 1.4.6 sobre el caso "
  "estandarizado, que es el que tiene sentido interpretar (la sección 3.6 lo justifica):")
P(f"El criterio de Kaiser conserva las componentes con valor propio mayor que 1, es decir, las que explican más varianza que una "
  f"variable original estandarizada; da {R['k_kaiser']} componentes. La simulación de Horn compara cada valor propio con el que se "
  f"obtendría por azar con datos sin estructura (percentil 95 de 500 simulaciones); da {R['k_horn']}. El criterio de la varianza "
  f"acumulada pide llegar a una proporción alta, aquí 80 %; da {R['k_80']}. Además, la gráfica de sedimentación (scree plot) "
  "muestra un codo después de la segunda componente.")
bloque_codigo("criterios")
figura("fig_scree.png", ANCHO, "Izquierda: valores propios, umbral de Kaiser y valores esperados por azar. Derecha: varianza "
                               "explicada individual y acumulada.", "scree")
hp, hm = R["horn"], R["horn_media"]
filas = [["Componente", "Valor propio", "% de varianza", "% acumulado", "Umbral por azar (Horn, p. 95)", "Media por azar"]]
filas += [[f"CP{i + 1}", f"{val_z[i]:.2f}", f"{100 * prop_z[i]:.1f}", f"{100 * acum_z[i]:.1f}", f"{hp[i]:.2f}", f"{hm[i]:.2f}"]
          for i in range(6)]
tabla("valores", "Valores propios de la matriz de correlación (primeras seis componentes).", filas, [62, 62, 66, 66, 122, 82])
P(f"Los criterios no coinciden. Kaiser pide {R['k_kaiser']}, la simulación de Horn solo {R['k_horn']} y la varianza acumulada "
  f"{R['k_80']}. Elegimos {k} componentes por tres razones. La CP3 y la CP4 tienen valores propios de {val_z[2]:.2f} y "
  f"{val_z[3]:.2f}, por encima de 1, y juntas aportan {100 * (prop_z[2] + prop_z[3]):.1f} % de la varianza. Con {k} componentes se "
  f"explica {100 * acum_z[k - 1]:.1f} %, cercano al 80 % y mucho más que el {100 * acum_z[1]:.1f} % de dos componentes. Y, como se "
  f"ve en la siguiente subsección, la CP3 y la CP4 tienen una interpretación geográfica clara. La CP5 ({val_z[4]:.2f}) queda por "
  "debajo de 1 y no la incluimos aunque con ella se pasaría de 80 %.")
P("La sección 1.4.6 explica que la referencia de Horn depende de qué tan exigente se quiera ser, y aquí eso importa. Con el "
  f"percentil 95, la CP3 queda justo por debajo del umbral (λ<sub>3</sub> = {val_z[2]:.3f} frente a {hp[2]:.3f}; el "
  f"{100 * R['horn_supera'][2]:.1f} % de las simulaciones dio un tercer valor propio igual o mayor). Con la media de las "
  f"simulaciones, que es el criterio original de Horn, se conservan {R['k_horn_media']} componentes, porque la CP4 ({val_z[3]:.3f}) "
  f"apenas supera la media de {hm[3]:.3f}. La CP1 y la CP2, en cambio, superan cualquier referencia con amplitud. Reconocemos, por "
  "tanto, que la CP3 y la CP4 son marginales (sus valores propios están en la frontera de lo que puede producir el azar), así que la "
  "parte sólida del resultado son las dos primeras componentes.")
H3("3.5.4 Interpretación de las componentes")
P("Los coeficientes de cada componente se interpretan mejor como cargas, es decir, como la correlación entre cada variable original "
  "y la componente. Una carga grande en valor absoluto indica que esa variable pesa mucho en la componente.")
bloque_codigo("cargas")
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
bloque_codigo("biplot")
figura("fig_biplot.png", 445, "Países en el plano de CP1 y CP2, coloreados por grupo de regiones; las flechas son las cargas de "
                              "las variables.", "biplot")
mg = R["media_grupo_cp1"]
P("Las regiones se ordenan sobre la CP1 como cabría esperar. Las puntuaciones medias son: "
  f"{', '.join(f'{g} {m:.2f}' for g, m in list(mg.items())[:-1])} y {list(mg)[-1]} {list(mg.values())[-1]:.2f}. Los puntos más "
  f"altos en la CP1 son {', '.join(R['cp1_altos'])}, y los más bajos {', '.join(R['cp1_bajos'])}. Que una variable construida solo "
  "con números reproduzca la geografía del desarrollo es una señal de que las componentes recogen estructura real y no ruido.")

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
  "variables. Si no se estandariza, el PCA solo \"ve\" al PIB.")
H3("3.6.2 Qué ocurre sin estandarizar y estandarizando")
bloque_codigo("sin_estandarizar")
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
  "PIB per cápita y casi cero en las demás variables. La componente es, en la práctica, el PIB con otro nombre, y el PCA no reduce "
  "nada: ordena a los países por ingreso e ignora la mortalidad infantil, la natalidad o la alfabetización. El "
  f"{100 * R['prop_s'][0]:.2f} % es un artefacto de la escala, no una señal de que la información esté concentrada.")
P(f"Al estandarizar, cada variable tiene varianza 1 y la información se reparte: la CP1 explica {100 * prop_z[0]:.1f} % y recibe peso "
  f"de {R['n_cargas_05']} variables, las cuatro primeras componentes suman {100 * acum_z[3]:.1f} %. Las puntuaciones de la CP1 de "
  f"ambos casos tienen correlación de {R['r_cp1']:.2f}: ordenan de forma parecida a los países, porque el PIB también forma parte del "
  "eje de desarrollo, pero la versión estandarizada incorpora la información social y demográfica que la otra descarta.")
H3("3.6.3 Conclusión sobre la estandarización")
P("Las variables de este conjunto están en unidades distintas (dólares, porcentajes, fracciones, razones), así que estandarizar es "
  "la decisión adecuada y la que usamos para elegir componentes en la sección 3.5. Solo tendría sentido no estandarizar si todas las "
  "variables estuvieran en la misma unidad y la diferencia de varianzas fuera información que se quiere conservar. Aquí no es el caso.")

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
  f"reducción es moderada: hacen falta cuatro componentes para llegar a {100 * acum_z[3]:.1f} %, y la simulación de Horn con el "
  f"percentil 95 solo respalda {R['k_horn']} ({100 * acum_z[R['k_horn'] - 1]:.1f} %). Es decir, los {p_} indicadores no se reducen "
  "a una sola dimensión, porque las variables geográficas (tierra cultivable, cultivos permanentes, costa) aportan estructura propia.")
P(f"<b>H2 (la estandarización es necesaria).</b> Se cumple de forma contundente: sin estandarizar, la CP1 explica "
  f"{100 * R['prop_s'][0]:.2f} % de la varianza y es prácticamente el PIB per cápita; estandarizando, explica "
  f"{100 * prop_z[0]:.1f} % y recibe peso de {R['n_cargas_05']} variables.")
H2("4.2 Resultados inesperados y limitaciones")
P(f"Los criterios para elegir componentes no coinciden (Kaiser {R['k_kaiser']}, Horn {R['k_horn']}, varianza acumulada {R['k_80']}). "
  f"Una explicación es que Horn es el más exigente, pues descuenta lo que se obtendría por azar con {R['n_depurados']} países y {p_} "
  f"variables, mientras que Kaiser es más permisivo; la CP3 y la CP4 tienen valores propios de {val_z[2]:.2f} y {val_z[3]:.2f}, "
  "apenas por encima de 1, y quedan en la frontera del azar: con la media de las simulaciones Horn sí las respalda "
  f"({R['k_horn_media']} componentes). Son interpretables pero marginales, por lo que las dos primeras componentes son el resultado "
  "más firme.")
P(f"Otras limitaciones: (1) en migración neta, {R['ceros_migracion']} países tienen exactamente cero, y es probable que algunos de "
  "esos ceros sean datos no disponibles, lo que debilita su correlación con las demás variables; (2) la imputación con la mediana "
  f"regional reduce algo la varianza de las variables más afectadas ({n_(imp[0][0])}, con {imp[0][1]} de {R['n_depurados']} países "
  "imputados); (3) los datos son de mediados de la década de 2000, de modo que las conclusiones describen ese periodo; (4) la "
  "interpretación de la CP2, CP3 y CP4 es nuestra lectura de las cargas; (5) la clasificación en variables independientes y "
  "dependientes se apoya en correlaciones, que no prueban causalidad; y (6) la selección de las variables más y menos "
  "correlacionadas usa la correlación de Pearson, que no capta relaciones no lineales como la saturación de la alfabetización.")
H2("4.3 Cómo se podría mejorar el análisis")
P("Con más tiempo se podría: tratar los ceros de migración neta como faltantes y repetir el análisis; comparar la imputación con la "
  f"mediana regional contra otros métodos de imputación; repetir el PCA sin los territorios muy pequeños ({', '.join(dl[2])}) para "
  "ver si cambian las componentes; complementar la correlación de Pearson con la de Spearman, que capta relaciones monótonas no "
  "lineales; actualizar los datos con fuentes más recientes; y usar las componentes como variables explicativas en un modelo para "
  "el PIB per cápita o la mortalidad infantil.")

# =============================================================================================
# 5. CONCLUSIONES
# =============================================================================================
H1("5. Conclusiones")
P(f"Partimos de {R['n_paises']} países y {R['n_columnas']} variables. Después de la depuración quedaron {R['n_depurados']} países "
  f"y {p_} variables numéricas; descartamos las variables categóricas y las redundantes (otros usos del suelo, industria) con razones "
  "explícitas, y transformamos con logaritmo las tres variables de asimetría extrema.")
P("Las correlaciones muestran un bloque de variables que describe el nivel de desarrollo (mortalidad infantil, natalidad, "
  "alfabetización, PIB per cápita, teléfonos, agricultura y servicios), mientras que las condiciones geográficas (tierra cultivable, "
  f"cultivos permanentes, costa) se relacionan poco con él. Las cuatro variables más correlacionadas ({lista([n_(v) for v in top4])}, "
  f"con |r| promedio de {R['top4_puntaje']:.2f}) son casi redundantes y se resumen en la primera componente; las dos menos "
  f"correlacionadas ({n_(bottom2[0])} y {n_(bottom2[1])}) aportan información propia. Por eso clasificamos las condiciones "
  "geográficas como independientes y el bloque como dependiente, aclarando que se trata de una hipótesis y no de una prueba de causalidad.")
P(f"Con datos estandarizados, cuatro componentes explican {100 * acum_z[3]:.1f} % de la varianza. La primera (el "
  f"{100 * prop_z[0]:.1f} %) es un eje de desarrollo que ordena a las regiones de forma coherente. La elección de cuatro componentes "
  f"se apoya en Kaiser, en la varianza acumulada y en Horn con la media de las simulaciones, aunque Horn con el percentil 95 sugiere "
  f"solo {PALABRA.get(R['k_horn'], R['k_horn'])}, de modo que las dos primeras son las más firmes.")
P("Sin estandarizar, el PCA se reduce al PIB por la diferencia de escalas y pierde su utilidad. Limitaciones: los datos son de "
  "mediados de los años 2000; imputamos con la mediana regional una parte pequeña de los valores; y el cero de migración neta puede "
  "ser un dato faltante disfrazado. Una extensión natural sería ajustar un modelo para el PIB per cápita o la mortalidad infantil "
  "usando las componentes como predictores.")

# =============================================================================================
# 6. BIBLIOGRAFÍA
# =============================================================================================
H1("6. Bibliografía")
for ref in [
    "[1] fernandol. <i>Countries of the World</i> [conjunto de datos]. Kaggle. https://www.kaggle.com/datasets/fernandol/countries-of-the-world",
    "[2] Jolliffe, I. T. (2002). <i>Principal Component Analysis</i> (2.ª ed.). Springer.",
    "[3] Kaiser, H. F. (1960). The application of electronic computers to factor analysis. <i>Educational and Psychological "
    "Measurement</i>, 20(1), 141–151.",
    "[4] Horn, J. L. (1965). A rationale and test for the number of factors in factor analysis. <i>Psychometrika</i>, 30(2), 179–185.",
    "[5] United Nations Development Programme (1990). <i>Human Development Report 1990</i>. Oxford University Press.",
    "[6] McKinney, W. (2010). Data structures for statistical computing in Python. <i>Proceedings of the 9th Python in Science "
    "Conference</i>, 51–56.",
    "[7] Harris, C. R. et al. (2020). Array programming with NumPy. <i>Nature</i>, 585, 357–362.",
    "[8] Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. <i>Computing in Science &amp; Engineering</i>, 9(3), 90–95.",
    "[9] Waskom, M. L. (2021). seaborn: statistical data visualization. <i>Journal of Open Source Software</i>, 6(60), 3021.",
    "[10] Pedregosa, F. et al. (2011). Scikit-learn: Machine learning in Python. <i>Journal of Machine Learning Research</i>, 12, 2825–2830.",
    "[11] Guttman, L. (1954). Some necessary conditions for common-factor analysis. <i>Psychometrika</i>, 19(2), 149–161.",
    "[12] Glorfeld, L. W. (1995). An improvement on Horn's parallel analysis methodology for selecting the correct number of factors "
    "to retain. <i>Educational and Psychological Measurement</i>, 55(3), 377–393.",
    "[13] Zwick, W. R. y Velicer, W. F. (1986). Comparison of five rules for determining the number of components to retain. "
    "<i>Psychological Bulletin</i>, 99(3), 432–442.",
]:
    P(ref, biblio)

# ---------------------------------------------------------------------------------------------
doc = Reporte(SALIDA)
doc.multiBuild(story)
print("Reporte generado en:", SALIDA.relative_to(BASE))
