"""Arma el documento PDF a partir de las figuras y resultados que genera exploracion_pca.py."""
import json
import re
import textwrap
from pathlib import Path

import matplotlib
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, Image, KeepTogether,
                                NextPageTemplate, PageBreak, PageTemplate, Paragraph,
                                Preformatted, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

BASE = Path(__file__).resolve().parent.parent
FIG = BASE / "figuras"
R = json.load(open(BASE / "resultados" / "resultados.json", encoding="utf-8"))
SRC = (BASE / "codigo" / "exploracion_pca.py").read_text(encoding="utf-8")

# ---------------------------------------------------------------- fuentes
LIB = Path("/usr/share/fonts/truetype/liberation")
pdfmetrics.registerFont(TTFont("Serif", LIB / "LiberationSerif-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Serif-B", LIB / "LiberationSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Serif-I", LIB / "LiberationSerif-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Serif-BI", LIB / "LiberationSerif-BoldItalic.ttf"))
pdfmetrics.registerFontFamily("Serif", normal="Serif", bold="Serif-B", italic="Serif-I", boldItalic="Serif-BI")
mono = Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSansMono.ttf"
pdfmetrics.registerFont(TTFont("Mono", mono))

# ---------------------------------------------------------------- estilos
S = {
    "body": ParagraphStyle("body", fontName="Serif", fontSize=10.5, leading=14.6, alignment=TA_JUSTIFY, spaceAfter=6),
    "H1": ParagraphStyle("H1", fontName="Serif-B", fontSize=15, leading=18, spaceBefore=14, spaceAfter=7),
    "H2": ParagraphStyle("H2", fontName="Serif-B", fontSize=11.5, leading=14, spaceBefore=10, spaceAfter=4),
    "H3": ParagraphStyle("H3", fontName="Serif-BI", fontSize=10.5, leading=13, spaceBefore=7, spaceAfter=3),
    "cap": ParagraphStyle("cap", fontName="Serif-I", fontSize=9, leading=11.5, alignment=TA_CENTER, spaceBefore=2, spaceAfter=8),
    "tcap": ParagraphStyle("tcap", fontName="Serif-I", fontSize=9, leading=11.5, alignment=TA_LEFT, spaceBefore=6, spaceAfter=3),
    "cell": ParagraphStyle("cell", fontName="Serif", fontSize=8.6, leading=10.6),
    "cellb": ParagraphStyle("cellb", fontName="Serif-B", fontSize=8.6, leading=10.6),
    "code": ParagraphStyle("code", fontName="Mono", fontSize=6.7, leading=8.3, backColor=colors.HexColor("#f4f4f4"),
                           borderColor=colors.HexColor("#c8c8c8"), borderWidth=.4, borderPadding=4,
                           spaceBefore=3, spaceAfter=9, leftIndent=3, rightIndent=3),
    "formula": ParagraphStyle("formula", fontName="Serif-I", fontSize=11, leading=15, alignment=TA_CENTER, spaceBefore=3, spaceAfter=8),
    "small": ParagraphStyle("small", fontName="Serif", fontSize=9, leading=11.5, alignment=TA_LEFT, spaceAfter=3),
}
cont = {"fig": 0, "tab": 0, "h1": 0, "h2": 0, "h3": 0}
story = []


def P(t, st="body"):
    story.append(Paragraph(t, S[st]))


def H1(t):
    cont["h1"] += 1; cont["h2"] = 0; cont["h3"] = 0
    story.append(CondPageBreak(2.6 * inch))
    story.append(Paragraph(f"{cont['h1']}. {t}", S["H1"]))


def H2(t):
    cont["h2"] += 1; cont["h3"] = 0
    story.append(CondPageBreak(1.8 * inch))
    story.append(Paragraph(f"{cont['h1']}.{cont['h2']} {t}", S["H2"]))


def H3(t):
    cont["h3"] += 1
    story.append(CondPageBreak(1.3 * inch))
    story.append(Paragraph(f"{cont['h1']}.{cont['h2']}.{cont['h3']} {t}", S["H3"]))


def ecuacion(tex, nombre):
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    matplotlib.rcParams["mathtext.fontset"] = "stix"
    d = BASE / "figuras" / "ecuaciones"; d.mkdir(exist_ok=True)
    fig = plt.figure(figsize=(0.1, 0.1))
    fig.text(0, 0, tex, fontsize=12)
    ruta = d / f"{nombre}.png"
    fig.savefig(ruta, dpi=300, bbox_inches="tight", pad_inches=0.04, transparent=True)
    plt.close(fig)
    iw, ih = ImageReader(str(ruta)).getSize()
    w = min(iw / 300 * 72, 6.3 * inch)
    story.append(Spacer(1, 3)); story.append(Image(str(ruta), width=w, height=w * ih / iw)); story.append(Spacer(1, 5))


def figura(nombre, ancho, pie):
    cont["fig"] += 1
    iw, ih = ImageReader(str(FIG / nombre)).getSize()
    story.append(KeepTogether([Image(str(FIG / nombre), width=ancho, height=ancho * ih / iw),
                               Paragraph(f"Figura {cont['fig']}. {pie}", S["cap"])]))


def codigo(nombre, ancho=100):
    m = re.search(rf"# >>> {nombre}\n(.*?)# <<< {nombre}", SRC, re.S)
    lineas = []
    for ln in m.group(1).rstrip().split("\n"):
        sang = len(ln) - len(ln.lstrip())
        lineas += textwrap.wrap(ln, ancho, subsequent_indent=" " * (sang + 4), break_long_words=False,
                                replace_whitespace=False, drop_whitespace=False) or [""]
    story.append(Preformatted("\n".join(lineas), S["code"]))


def fmt(x):
    a = abs(x)
    if a >= 1e4: return f"{x:,.0f}"
    if a >= 100: return f"{x:,.1f}"
    if a >= 1: return f"{x:.2f}"
    if a == 0: return "0"
    return f"{x:.3f}"


def tabla(filas, anchos, pie, alinear_der_desde=1):
    cont["tab"] += 1
    data = [[Paragraph(str(c), S["cellb"] if i == 0 else S["cell"]) for c in fila] for i, fila in enumerate(filas)]
    t = Table(data, colWidths=[a * inch for a in anchos], repeatRows=1)
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), .9, colors.black), ("LINEBELOW", (0, 0), (-1, 0), .5, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), .9, colors.black), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]))
    story.append(Paragraph(f"Tabla {cont['tab']}. {pie}", S["tcap"]))
    story.append(t)
    story.append(Spacer(1, 8))


# ---------------------------------------------------------------- documento
class Doc(BaseDocTemplate):
    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and f.style.name in ("H1", "H2", "H3"):
            self.notify("TOCEntry", ({"H1": 0, "H2": 1, "H3": 2}[f.style.name], f.getPlainText(), self.page))


def pie_pagina(c, d):
    c.saveState()
    c.setFont("Serif", 8.5); c.setFillColor(colors.HexColor("#444444"))
    c.setStrokeColor(colors.HexColor("#999999")); c.setLineWidth(.4)
    c.line(inch, .75 * inch, letter[0] - inch, .75 * inch)
    c.drawString(inch, .55 * inch, "Métodos Matemáticos Computacionales para Ciencia de Datos")
    c.drawRightString(letter[0] - inch, .55 * inch, str(d.page))
    c.restoreState()


doc = Doc(str(BASE / "documento" / "Proyecto_PCA_Paises.pdf"), pagesize=letter, leftMargin=inch, rightMargin=inch,
          topMargin=inch, bottomMargin=inch, title="Exploración de datos y componentes principales",
          author="De La Cruz Maldonado José Eduardo; López Reyes Jorge")
marco = Frame(inch, inch, letter[0] - 2 * inch, letter[1] - 2 * inch, id="f")
doc.addPageTemplates([PageTemplate(id="portada", frames=[marco]),
                      PageTemplate(id="normal", frames=[marco], onPage=pie_pagina)])
W = 6.5 * inch

# ---------------------------------------------------------------- portada
c = ParagraphStyle("c", fontName="Serif", fontSize=13, leading=18, alignment=TA_CENTER)
story += [Spacer(1, .35 * inch),
          Paragraph("UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICO", ParagraphStyle("u", parent=c, fontName="Serif-B", fontSize=15, leading=20)),
          Paragraph("Instituto de Investigaciones en Matemáticas Aplicadas y en Sistemas", c),
          Paragraph("Licenciatura en Ciencia de Datos", c),
          Spacer(1, .55 * inch),
          Table([[""]], colWidths=[W], rowHeights=[2], style=[("LINEABOVE", (0, 0), (-1, 0), 1.2, colors.black)]),
          Spacer(1, .4 * inch),
          Paragraph("Métodos Matemáticos Computacionales para Ciencia de Datos", ParagraphStyle("m", parent=c, fontSize=14, leading=20)),
          Spacer(1, .35 * inch),
          Paragraph("Exploración de datos y reducción de dimensiones con componentes principales",
                    ParagraphStyle("t", parent=c, fontName="Serif-B", fontSize=21, leading=27)),
          Spacer(1, .18 * inch),
          Paragraph("Indicadores demográficos, económicos y geográficos de 227 países", ParagraphStyle("s", parent=c, fontName="Serif-I", fontSize=13)),
          Spacer(1, .4 * inch),
          Table([[""]], colWidths=[W], rowHeights=[2], style=[("LINEABOVE", (0, 0), (-1, 0), 1.2, colors.black)]),
          Spacer(1, .45 * inch)]
datos_portada = [["Integrantes", "De La Cruz Maldonado José Eduardo<br/>López Reyes Jorge"],
                 ["Profesora", "Nora Isabel Pérez Quezadas"],
                 ["Datos", "Countries of the World (Kaggle, fernandol)"]]
tp = Table([[Paragraph(a, ParagraphStyle("pa", parent=c, fontName="Serif-B", fontSize=11.5, alignment=TA_LEFT)),
             Paragraph(b, ParagraphStyle("pb", parent=c, fontSize=11.5, leading=16, alignment=TA_LEFT))] for a, b in datos_portada],
           colWidths=[1.5 * inch, 4.5 * inch])
tp.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
story += [tp, Spacer(1, .9 * inch), Paragraph("Ciudad Universitaria, Ciudad de México<br/>Noviembre de 2026", c),
          NextPageTemplate("normal"), PageBreak()]

story.append(Paragraph("Resumen", S["H1"].clone("Hx2")))
P(f"Se realiza un análisis exploratorio de {R['n_paises']} países descritos por 18 variables demográficas, económicas y geográficas "
  "(<i>Countries of the World</i>, Kaggle) para saber si pueden resumirse en pocas componentes principales. Se depuró la base (variables redundantes "
  "descartadas, tres territorios eliminados por exceso de faltantes, imputación con la mediana regional y logaritmo en las variables de asimetría extrema) "
  "y se obtuvieron gráficas, medidas descriptivas, valores atípicos y matrices de covarianza y correlación. Luego se aplicó el análisis de componentes "
  "principales (PCA) con y sin estandarización, eligiendo el número de componentes con los criterios de Kaiser, Horn y varianza acumulada. "
  f"Con datos estandarizados, cuatro componentes explican {100 * R['acum_z'][3]:.1f} % de la varianza y la primera ({100 * R['prop_z'][0]:.1f} %) funciona como un eje de nivel de desarrollo; "
  f"sin estandarizar, la primera explica {100 * R['prop_s'][0]:.2f} % pero solo refleja el PIB per cápita por su escala. "
  "Por ello, estandarizar es indispensable cuando las variables tienen unidades distintas.")
P("<b>Palabras clave:</b> análisis exploratorio, componentes principales, estandarización, correlación, indicadores de países.", "small")
story.append(PageBreak())

# ---------------------------------------------------------------- índice
story.append(Paragraph("Contenido", S["H1"].clone("Hx")))
toc = TableOfContents()
toc.levelStyles = [ParagraphStyle("t1", fontName="Serif-B", fontSize=10.5, leading=15, leftIndent=0),
                   ParagraphStyle("t2", fontName="Serif", fontSize=10, leading=13.5, leftIndent=18),
                   ParagraphStyle("t3", fontName="Serif", fontSize=9.5, leading=12.5, leftIndent=36)]
story += [toc, PageBreak()]

# ================================================================ 1
H1("Introducción")
H2("Objetivo e hipótesis de trabajo")
P("El objetivo de este trabajo es realizar un análisis exploratorio del conjunto de datos <i>Countries of the World</i> [1] y, con la base ya depurada, "
  "determinar si los indicadores demográficos, económicos y geográficos de los países pueden resumirse en unas pocas componentes principales sin perder demasiada información. "
  "El análisis sigue el flujo planteado en clase: datos, exploración (gráficas, preprocesamiento, correlaciones, medidas descriptivas y valores atípicos), corrección de los datos cuando hace falta y reducción de dimensiones con PCA.")
P("Partimos de dos hipótesis de trabajo que se retoman en la Discusión. <b>H1:</b> muchas variables miden en el fondo el nivel de desarrollo de un país (salud, ingreso, educación, estructura económica), "
  "por lo que estarán fuertemente correlacionadas y unas pocas componentes bastarán para resumir buena parte de la varianza. "
  "<b>H2:</b> como las variables están en unidades muy distintas, el PCA sin estandarizar quedará dominado por la variable de mayor escala, mientras que con estandarización sí resumirá la estructura de los datos.")
H2("Justificación y antecedentes")
P("Los países se describen con decenas de indicadores y varios de ellos dicen casi lo mismo. Resumirlos en pocas dimensiones permite comparar países, visualizarlos en un plano y usar menos variables en modelos posteriores. "
  "Además, este conjunto es un buen caso para entender el PCA, porque la decisión de estandarizar o no cambia por completo el resultado.")
P("El análisis de componentes principales es una técnica clásica para reducir dimensiones [2], y los criterios para decidir cuántas componentes conservar se han estudiado desde hace décadas [3, 4]. "
  "Como antecedente de la idea de resumir el desarrollo de un país con pocas dimensiones, el Índice de Desarrollo Humano del PNUD [5] combina salud, educación e ingreso en un solo indicador; "
  "a diferencia del PCA, se construye con una fórmula fija y no a partir de la estructura de los datos.")

# ================================================================ 2
H2("Origen y descripción de los datos")
P("Los datos vienen del conjunto <i>Countries of the World</i>, publicado en Kaggle por el usuario fernandol "
  "(https://www.kaggle.com/datasets/fernandol/countries-of-the-world) [1]. Cada fila es un país o territorio y cada columna una "
  "característica. Por los valores que contiene (por ejemplo, China aparece con 1,313,973,713 habitantes), la información corresponde "
  "a mediados de la década de 2000, así que las conclusiones describen ese periodo y no la situación actual.")
P("El archivo usa coma como separador decimal (\"48,0\") y los nombres de país y de región traen espacios al final, por lo que "
  "al leerlo indicamos <i>decimal=\",\"</i> y limpiamos los textos. La Tabla 1 resume las columnas.")
codigo("carga")
tabla([["Variable", "Tipo", "Qué mide"],
       ["País", "texto", "Nombre del país o territorio (se usa como identificador)."],
       ["Región", "categórica (11 niveles)", "Región geográfica definida por la fuente."],
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
       ["Agricultura, industria, servicios", "numéricas", "Fracción del PIB que aporta cada sector."]],
      [1.9, 1.4, 3.2], "Variables del conjunto de datos tal como se usan en este trabajo.")
figura("fig_categoricas.png", W * .92, "Distribución de las dos variables categóricas. Clima tiene 22 países sin dato (s/d).")
P(f"La región con más países es África subsahariana ({R['regiones']['SUB-SAHARAN AFRICA']}), seguida de América Latina y el Caribe "
  f"({R['regiones']['LATIN AMER. & CARIB']}); Países Bálticos ({R['regiones']['BALTICS']}) es la más pequeña. En clima, el tipo 2 concentra "
  f"{R['clima']['2']} países.")

H2("Herramientas y métodos")
P("Todo el análisis se hizo en Python 3 con estos paquetes: pandas [6] (lectura del CSV con <i>read_csv</i>, imputación con <i>groupby/transform</i> y <i>fillna</i>, y los métodos <i>mean, median, var, std, skew, cov</i> y <i>corr</i>); "
  "NumPy [7] (matriz de covarianza con <i>numpy.cov</i>, valores y vectores propios con <i>numpy.linalg.eigh</i> y <i>log10</i>); Matplotlib [8] y seaborn [9] (histogramas, diagramas de caja, dispersión y mapas de calor); "
  "y scikit-learn [10], cuya clase <i>PCA</i> usamos solo para verificar nuestro cálculo. Las herramientas que aparecen en el pizarrón de clase (matrices de covarianza y correlación, PCA y estandarización) se describen a grandes rasgos; "
  "las demás (transformación logarítmica, criterio del rango intercuartílico y simulación de Horn) se explican con más detalle.")
H3("Medidas descriptivas y covarianza")
P("La media, la varianza y la covarianza de dos variables X e Y medidas en <i>n</i> países son:")
ecuacion('$\\bar{x}=\\frac{1}{n}\\sum_{i=1}^{n}x_i\\qquad\\qquad s^2(X)=\\frac{\\sum_{i=1}^{n}(x_i-\\bar{x})^2}{n-1}$', "eq_media_var")
ecuacion('$\\mathrm{Cov}(X,Y)=\\frac{\\sum_{i=1}^{n}(x_i-\\bar{x})(y_i-\\bar{y})}{n-1}$', "eq_cov")
P("Aquí <i>n</i> es el número de países, <i>x<sub>i</sub></i> y <i>y<sub>i</sub></i> son los valores de X y Y en el país <i>i</i>, la barra sobre una letra indica su media y cada suma recorre <i>i</i> = 1, …, <i>n</i>. "
  "La desviación estándar <i>s</i> es la raíz cuadrada de la varianza. La mediana es el valor central de los datos ordenados y, a diferencia de la media, no la afectan los valores extremos.")
H3("Correlación de Pearson")
ecuacion('$r(X,Y)=\\frac{\\mathrm{Cov}(X,Y)}{\\sigma(X)\\,\\sigma(Y)}$', "eq_pearson")
P("donde σ(X) y σ(Y) son las desviaciones estándar de X y de Y. El coeficiente <i>r</i> va de −1 a 1 y no depende de las unidades. La matriz de correlación reúne el valor de <i>r</i> de todos los pares de variables; vale 1 en la diagonal y es simétrica.")
H3("Valores atípicos: rango intercuartílico")
ecuacion('$x<Q_1-1.5\\,\\mathrm{RIC}\\quad\\mathrm{o}\\quad x>Q_3+1.5\\,\\mathrm{RIC},\\qquad \\mathrm{RIC}=Q_3-Q_1$', "eq_iqr")
P("donde Q<sub>1</sub> y Q<sub>3</sub> son el primer y el tercer cuartil de la variable (los valores que dejan por debajo al 25 % y al 75 % de los países) y RIC es el rango intercuartílico. Un valor <i>x</i> que cumple alguna de las dos condiciones se considera atípico. "
  "Es el criterio que dibuja los círculos de los diagramas de caja.")
H3("Transformación logarítmica y estandarización")
ecuacion('$y=\\log_{10}(x+1)\\qquad\\qquad z_i=\\frac{x_i-\\bar{x}}{s}$', "eq_logz")
P("donde <i>x</i> es el valor original, <i>y</i> el valor transformado y <i>z<sub>i</sub></i> el valor estandarizado de la variable en el país <i>i</i>, con media 0 y desviación estándar 1. "
  "El logaritmo comprime las colas derechas largas y conserva el orden de los países; se suma 1 porque hay valores iguales a cero. La estandarización pone todas las variables en la misma escala.")
H3("Componentes principales")
ecuacion('$S\\,v_j=\\lambda_j\\,v_j\\qquad\\qquad \\mathrm{prop}_j=\\frac{\\lambda_j}{\\lambda_1+\\cdots+\\lambda_p}\\qquad\\qquad T=Z\\,V$', "eq_pca")
P("Aquí <i>S</i> es la matriz de covarianza de los datos (de <i>p</i> × <i>p</i>, con <i>p</i> = 13 variables), <i>v<sub>j</sub></i> es el vector propio de la componente <i>j</i> (sus coeficientes) y <i>λ<sub>j</sub></i> su valor propio, que es la varianza de esa componente; "
  "las componentes se ordenan de mayor a menor λ, y prop<sub>j</sub> es la proporción de varianza que explica la componente <i>j</i>. <i>Z</i> es la matriz de datos estandarizados (<i>n</i> × <i>p</i>), <i>V</i> es la matriz cuyas columnas son los vectores propios y <i>T</i> contiene las puntuaciones (<i>scores</i>) de cada país. "
  "Si <i>S</i> se calcula con datos estandarizados, es la matriz de correlación. La carga de la variable <i>i</i> en la componente <i>j</i> es <i>v<sub>ij</sub></i>·√λ<sub>j</sub>, y equivale a la correlación entre ambas cuando se parte de datos estandarizados.")
H3("Cuántas componentes conservar")
P("El criterio de Kaiser [3] conserva las componentes con λ mayor que 1 (con datos estandarizados): las que explican más varianza que una variable original. "
  "La simulación de Horn [4] genera muchas matrices de datos aleatorios sin estructura, del mismo tamaño que la nuestra, calcula sus valores propios y conserva las componentes cuyo λ supera al del azar; aquí usamos 500 simulaciones y el percentil 95. "
  "El criterio de varianza acumulada toma el menor número de componentes que explica al menos 80 %. El gráfico de sedimentación (<i>scree plot</i>) ayuda a ver dónde la curva de valores propios deja de bajar con fuerza.")

# ================================================================ 4
H1("Análisis experimental")
P("Esta sección describe qué se hizo con los datos antes de analizarlos y sobre qué base se obtuvo cada resultado de la sección 3. El tratamiento tiene cuatro pasos: contar y tratar los valores faltantes, decidir qué variables y países se quedan, imputar los vacíos restantes y transformar las variables muy asimétricas. Las gráficas de la sección 3.1 se hicieron con los datos originales, antes de modificar nada, para mostrar la información tal como viene en la fuente.")
H2("Valores faltantes")
nul = sorted(R["nulos"].items(), key=lambda kv: -kv[1])
P("Primero contamos los vacíos de cada columna. Las que más faltan son "
  + ", ".join(f"{k} ({v} países, {100 * v / R['n_paises']:.1f} %)" for k, v in nul[:4])
  + ". Ninguna columna numérica pasa del 8 % de vacíos, así que no hay razón para descartarlas únicamente por faltantes.")
figura("fig_faltantes.png", W * .8, "Porcentaje de países sin dato en cada columna (solo se muestran las que tienen vacíos).")
codigo("faltantes")
H2("Variables que descartamos y por qué")
P("De las 18 columnas distintas de País, 13 numéricas entran al estudio de correlaciones y componentes principales. Las demás se descartan "
  "por las razones de la Tabla 2. Hablamos de variables (columnas): descartar una significa que no participa en las matrices de "
  "covarianza y correlación ni en el PCA, pero sigue visible en las gráficas de la sección 3.1.")
sl, ss = R["corr_suma_suelo"], R["suma_sectores"]
tabla([["Variable", "Decisión", "Razón"],
       ["País", "Índice", "Es un identificador; no es una medición."],
       ["Región", "Fuera del PCA", "Es categórica nominal (11 niveles) y no tiene sentido calcular media o covarianza con ella. La usamos para colorear gráficas y para imputar faltantes."],
       ["Clima", "Se descarta", f"Es una categoría ordinal con 22 países sin dato (9.7 %) y con valores intermedios (1.5 y 2.5) que no son medidas reales. Su media o covarianza no tiene interpretación."],
       ["Otros usos del suelo", "Se descarta", f"Es exactamente 100 menos tierra cultivable menos cultivos permanentes (la suma de las tres va de {sl[0]:.2f} a {sl[1]:.2f}, la diferencia es redondeo). Una variable que es combinación lineal de otras hace singular la matriz de covarianza y no agrega información."],
       ["Industria", "Se descarta", f"Agricultura + industria + servicios suman entre {ss[0]:.3f} y {ss[1]:.3f}, por lo que las tres son casi dependientes. Conservamos agricultura y servicios; industria queda como el resto (su correlación con ellas es {R['corr_industria']['Agricultura']:.2f} y {R['corr_industria']['Servicios']:.2f}) y además tiene 16 vacíos."],
       ["Población y superficie", "Fuera del PCA", "Miden el tamaño del país, no sus condiciones de vida, y su resumen útil ya está en la densidad de población (población entre superficie). Tienen la asimetría más fuerte (9.2 y 6.0) y dominarían las matrices."],
       ],
      [1.35, 1.0, 4.15], "Variables que no entran a las matrices de correlación ni al PCA.")
H2("Países eliminados y valores imputados")
P(f"Para decidir qué hacer con los vacíos de las 13 variables que sí usamos, contamos cuántos le faltan a cada país. Eliminamos a los que "
  f"tienen cuatro o más vacíos (más del 30 % de sus variables): {', '.join(R['eliminados'])}. Quedan {R['n_final']} países. A los "
  f"demás les rellenamos cada vacío con la mediana de su región; usamos la mediana porque no la afectan los valores extremos y la "
  f"región porque agrupa países con condiciones parecidas, de modo que es mejor imputar con ella que con la mediana mundial.")
imp = sorted(R["imputados"].items(), key=lambda kv: -kv[1])
P("Se imputaron " + ", ".join(f"{k} ({v})" for k, v in imp[:4]) + " y pocos valores en el resto. El caso más grande, alfabetización, "
  f"representa {100 * R['imputados']['Alfabetización'] / R['n_final']:.1f} % de los países. Imputar con la mediana reduce un poco la varianza real de esas "
  "variables, lo cual dejamos señalado como limitación.")
codigo("seleccion")
H2("Transformación de variables muy asimétricas")
P("Esta es la flecha de \"corregir datos\" del esquema del pizarrón: los resultados de la sección 3.1 muestran que algunas variables tienen "
  "colas derechas extremas que, al calcular correlaciones y componentes, dejarían que unos pocos países decidan el resultado. "
  "Con un criterio fijo, aplicamos <i>log10(x + 1)</i> a las variables con coeficiente de asimetría mayor o igual a 2 en valor absoluto. "
  "Elegimos el logaritmo porque comprime las colas derechas y respeta el orden de los países, y sumamos 1 porque estas variables tienen "
  f"ceros (por ejemplo, países sin costa). Las variables transformadas son: {', '.join(R['a_log'])}.")
codigo("transformacion")
figura("fig_log.png", W * .92, "Efecto de la transformación logarítmica sobre las tres variables más asimétricas (izquierda: original; derecha: transformada).")
a = R["asim"]
P(f"La asimetría de densidad baja de {a['Densidad de población'][0]:.2f} a {a['Densidad de población'][1]:.2f}, la de costa/área de "
  f"{a['Costa / área'][0]:.2f} a {a['Costa / área'][1]:.2f} y la de cultivos permanentes de {a['Cultivos permanentes'][0]:.2f} a "
  f"{a['Cultivos permanentes'][1]:.2f}. Las demás variables tienen asimetría menor que 2 y se dejan en su escala original para conservar su interpretación.")
H2("Cómo se obtuvo cada resultado")
P("<b>Gráficas de cada variable (3.1).</b> Se hicieron con los datos originales (227 filas, omitiendo los vacíos de cada variable): un histograma de 20 intervalos con líneas de media y mediana, y un diagrama de caja, con la función <i>hist_box</i> del programa.")
P("<b>Medidas descriptivas y covarianza (3.2) y atípicos (3.3).</b> Se calcularon sobre la base depurada (224 países × 13 variables), antes de transformar, con <i>mean, median, var, std</i> y <i>cov</i>. Los atípicos se contaron con el criterio del RIC antes y después de la transformación logarítmica; los diagramas de caja comparativos usan valores z para que las variables sean comparables.")
P("<b>Correlaciones (3.4).</b> Se calcularon sobre la base transformada (224 × 13) con <i>corr(method=\"pearson\")</i>. La clasificación en variables independientes y dependientes se hizo a partir del significado de cada variable y de su mayor correlación con las demás; es una hipótesis razonada, no una prueba.")
P("<b>PCA (3.5).</b> Se aplicó a la base transformada y estandarizada. Calculamos la matriz de covarianza, extrajimos valores y vectores propios con <i>numpy.linalg.eigh</i> y los ordenamos de mayor a menor. El signo de una componente es arbitrario, así que fijamos una convención (CP1 con signo positivo en el PIB per cápita). "
  "Verificamos el cálculo con <i>sklearn.decomposition.PCA</i> (los valores propios coinciden) y comprobamos que las componentes no están correlacionadas. La simulación de Horn usa 500 repeticiones con semilla fija, de modo que el resultado se puede reproducir. "
  "El programa toma como número de componentes la mediana de los tres criterios (4, 2 y 5, por lo que resulta 4); la justificación detallada está en la sección 3.5.")
P("<b>Comparación con y sin estandarización (3.6).</b> Se repite el mismo cálculo sobre la misma base transformada, una vez con los datos solo centrados (matriz de covarianza) y otra con datos estandarizados (matriz de correlación). Por eso, \"sin estandarizar\" significa sin dividir entre la desviación estándar, pero con la transformación logarítmica ya aplicada. "
  "Todo el código está en el archivo <i>exploracion_pca.py</i>.")

# ================================================================ res
H1("Resultados")
P("Los resultados se presentan en el orden del flujo de trabajo: gráficas de cada variable (3.1), medidas descriptivas (3.2), valores atípicos (3.3), correlaciones (3.4), componentes principales (3.5) y comparación con y sin estandarización (3.6). "
  "Cada resultado lleva una lectura breve; la comparación con las hipótesis, las limitaciones y las mejoras posibles se discuten en la sección 4.")

# ================================================================ 3
H2("Gráficas de cada característica")
P("Antes de modificar nada, graficamos cada variable numérica con un histograma y un diagrama de caja. En el histograma la línea "
  "discontinua marca la media y la continua la mediana; cuando están muy separadas, la distribución es asimétrica. En el diagrama "
  "de caja, la caja va del primer al tercer cuartil, los bigotes llegan hasta 1.5 veces el rango intercuartílico y los círculos "
  "son valores atípicos. Las variables se grafican con los datos originales, con los vacíos omitidos en cada una.")
codigo("graficas")
COM = {
    "Population": "Unos pocos países enormes (China, India, Estados Unidos) contrastan con una mayoría de países pequeños.",
    "Area (sq. mi.)": "Pocos países ocupan superficies muy grandes (Russia, Canada, China); la mayoría son pequeños o islas.",
    "Pop. Density (per sq. mi.)": "Casi todos los países tienen pocas centenas de habitantes por milla cuadrada, pero territorios diminutos como Monaco, Macau o Singapore llegan a miles.",
    "Coastline (coast/area ratio)": "La razón vale cero en países sin litoral y es muy alta en islas pequeñas, lo que alarga la cola derecha.",
    "Net migration": "Se concentra alrededor de cero. En 62 de 224 países vale exactamente cero, y es probable que en la fuente ese cero sustituya un dato no disponible.",
    "Infant mortality (per 1000 births)": "La mayoría de los países tiene valores bajos; hay una cola de países africanos con más de 100 muertes por cada 1000 nacimientos.",
    "GDP ($ per capita)": "Muchos países están por debajo de 10,000 USD y solo unos pocos superan los 30,000 (Luxembourg, Norway, United States).",
    "Literacy (%)": "La distribución se carga hacia el 100 %, con una cola de países de baja alfabetización (sesgo a la izquierda).",
    "Phones (per 1000)": "Cola derecha producida por países con muchísimas líneas por habitante, sobre todo Monaco.",
    "Arable (%)": "Casi todos los países destinan menos de 30 % a tierra cultivable; Bangladesh es el extremo.",
    "Crops (%)": "La mayoría dedica menos de 5 % a cultivos permanentes, pero varias islas pasan del 40 %.",
    "Other (%)": "Es el complemento de las dos variables anteriores (se comprueba en la sección 2), por lo que no aporta información nueva.",
    "Birthrate": "Distribución bastante simétrica, sin valores atípicos por el criterio del rango intercuartílico.",
    "Deathrate": "Concentrada entre 5 y 12; los atípicos son países del sur de África (Swaziland, Botswana, Lesotho).",
    "Agriculture": "La mayoría de los países depende poco de la agricultura; los extremos (Liberia, Somalia) superan 60 % del PIB.",
    "Industry": "Distribución con cola derecha moderada; el máximo es Equatorial Guinea.",
    "Service": "Es la más simétrica de todas, sin valores atípicos.",
}
for e in R["estad_eda"]:
    t = (f"{COM[e['var']]} Asimetría {e['asim']:.1f}; media {fmt(e['media'])} frente a mediana {fmt(e['mediana'])}; "
         f"{e['atip']} valores atípicos por el criterio del rango intercuartílico.")
    cont["fig"] += 1
    iw, ih = ImageReader(str(FIG / e["archivo"])).getSize()
    story.append(KeepTogether([Image(str(FIG / e["archivo"]), width=W, height=W * ih / iw),
                               Paragraph(f"Figura {cont['fig']}. {e['nombre']}. {t}", S["cap"])]))
P("En conjunto, casi todas las variables tienen asimetría positiva (la media es mayor que la mediana). Las más asimétricas son "
  "población, superficie, densidad, costa/área y cultivos permanentes, con coeficientes de asimetría de 3.2 a 9.2. Esto anticipa que "
  "algunas necesitarán una transformación antes de calcular correlaciones y componentes principales, algo que se resuelve en la sección 2.")

# ================================================================ 5
H2("Medidas descriptivas")
P("Calculamos las medidas descriptivas con las 13 variables elegidas, ya depuradas pero todavía en su escala original (así se pueden "
  "interpretar). La media resume el centro, pero se mueve con los valores extremos; la mediana no. Por eso comparar ambas dice "
  "si hay asimetría. La varianza mide la dispersión alrededor de la media, y su raíz cuadrada (desviación estándar) está en las mismas unidades que la variable:")
ecuacion('$\\bar{x}=\\frac{1}{n}\\sum_{i=1}^{n}x_i\\qquad\\qquad s^2(X)=\\frac{\\sum_{i=1}^{n}(x_i-\\bar{x})^2}{n-1}$', "eq_media_var")
ecuacion('$\\mathrm{Cov}(X,Y)=\\frac{\\sum_{i=1}^{n}(x_i-\\bar{x})(y_i-\\bar{y})}{n-1}$', "eq_cov")
P("Los símbolos son los definidos en la sección 1.4: <i>n</i> es el número de países, <i>x<sub>i</sub></i> y <i>y<sub>i</sub></i> son los valores de cada variable en el país <i>i</i>, y la barra sobre una letra indica su media.")
codigo("descriptivas")
filas = [["Variable", "Media", "Mediana", "Varianza", "Desv. est.", "Mínimo", "Máximo"]]
for d in R["desc"]:
    filas.append([d["nombre"]] + [fmt(d[k]) for k in ("media", "mediana", "varianza", "desv_est", "minimo", "maximo")])
tabla(filas, [1.75, .75, .75, 1.05, .75, .7, .75], f"Medidas descriptivas de las 13 variables elegidas ({R['n_final']} países, escala original).")
P(f"La media supera a la mediana en {len(R['media_gt_mediana'])} de las 13 variables (todas salvo alfabetización y servicios), lo que confirma "
  "la asimetría derecha. El caso más claro es costa/área, con media 21.0 y mediana 0.73, y también densidad de población (381 contra 79). "
  "En el PIB per cápita la media (9,748) casi duplica a la mediana (5,700): un país \"típico\" tiene un ingreso mucho menor al que sugiere el promedio.")
cv = R["cov_clave"]
filas = [[""] + cv["nombres"]] + [[n] + [fmt(v) for v in fila] for n, fila in zip(cv["nombres"], cv["matriz"])]
tabla(filas, [1.5, .95, 1.05, 1.0, .95, .85], "Matriz de covarianza (escala original) de cinco indicadores de desarrollo. La diagonal contiene las varianzas.")
P("Elegimos estas cinco variables para mostrar la covarianza porque son las que, como veremos en la sección 3.4, más se relacionan entre sí. "
  "Los signos tienen sentido: el PIB per cápita covaría positivamente con los teléfonos y la alfabetización, y negativamente con la mortalidad infantil y la natalidad. "
  "Sin embargo, las magnitudes no son comparables entre pares: la covarianza entre PIB y teléfonos (1,904,505) es enorme solo porque el PIB se mide en miles de dólares, "
  "mientras que la varianza de la natalidad es 124. La covarianza depende de las unidades, y por eso en la sección 3.4 pasamos a la correlación, que no tiene unidades.")

# ================================================================ 6
H2("Datos atípicos")
P("Un valor es atípico por el criterio del rango intercuartílico (RIC) si queda más allá de 1.5 veces el RIC por debajo del primer cuartil o "
  "por encima del tercero. Contamos esos valores en cada variable antes y después de la transformación de la sección 2, y comparamos "
  "las variables en una escala común (valores z) para ver cuáles tienen colas más pesadas.")
codigo("atipicos")
figura("fig_atipicos.png", W, "Diagramas de caja de las 13 variables estandarizadas, con los datos depurados (izquierda) y tras la transformación (derecha).")
filas = [["Variable", "Atípicos antes", "Atípicos después", "Casos más alejados (datos depurados)"]]
for a in R["atipicos"]:
    if a["antes"] > 0:
        filas.append([a["nombre"], a["antes"], a["despues"], ", ".join(a["ejemplos"])])
tabla(filas, [1.5, .9, 1.0, 3.1], "Valores atípicos por el criterio del RIC. Natalidad no tiene ninguno y no aparece.")
P("No eliminamos ningún país por ser atípico. Los casos extremos son valores reales y esperables: Luxembourg tiene el PIB per cápita más alto de la "
  "muestra, Monaco el mayor número de teléfonos por habitante y Macau la mayor densidad, no son errores de captura. Quitarlos haría que el estudio "
  "dejara fuera justamente a los países que más contrastan. En su lugar, reducimos su influencia de dos maneras: la transformación logarítmica "
  "(que baja los atípicos de densidad de 20 a 7, de costa/área de 37 a 1 y de cultivos permanentes de 28 a 0) y la estandarización que se discute en la sección 3.6.")
P("Un caso aparte es migración neta, con 50 atípicos. Aquí el criterio engaña: como 62 países tienen exactamente cero, el rango intercuartílico es muy angosto y valores "
  "de apenas unas unidades quedan señalados. La variable va solo de −21 a 23, de modo que no tiene valores realmente extremos y la dejamos sin cambios. "
  "Mortalidad (16) y alfabetización (16) se mantienen por la misma razón: son países reales con situaciones distintas, como el sur de África con alta mortalidad.")

# ================================================================ 7
H3("Correlaciones y relación entre variables")
H3("Covarianza y correlación de Pearson")
P("Como se vio en la sección 3.2, la covarianza depende de las unidades. El coeficiente de correlación de Pearson la divide entre las desviaciones estándar de ambas variables:")
ecuacion('$r(X,Y)=\\frac{\\mathrm{Cov}(X,Y)}{\\sigma(X)\\,\\sigma(Y)}$', "eq_pearson")
P("Aquí σ(X) y σ(Y) son las desviaciones estándar de X y de Y. Así el resultado queda entre −1 y 1, sin unidades: valores cercanos a 1 indican que las variables crecen juntas, cercanos a −1 que una crece cuando la otra baja y cercanos a 0 que no hay relación lineal. "
  "A partir de aquí trabajamos con la base transformada (la que usaremos en el PCA). La Figura de covarianza muestra por qué la covarianza sola es difícil de leer: el PIB per cápita, "
  "con varianza del orden de 10<super>8</super>, domina todo el mapa de color.")
figura("fig_cov.png", W * .85, "Matriz de covarianza de las 13 variables (escala simétrica logarítmica para que se aprecien todas las magnitudes).")
H3("Matriz de correlación")
codigo("correlacion")
figura("fig_corr.png", W * .95, "Matriz de correlación de Pearson de las 13 variables (base transformada).")
P(f"De los {R['n_pares']} pares distintos de variables, {R['n_pares_05']} tienen correlación de al menos 0.5 en valor absoluto y {R['n_pares_08']} superan 0.8. "
  "La diagonal vale 1 porque cada variable se correlaciona perfectamente consigo misma, y la matriz es simétrica.")
filas = [["Par de variables", "r"]] + [[f"{a} y {b}", f"{r:.2f}"] for a, b, r in R["pares_fuertes"][:8]]
tabla(filas, [4.5, .8], "Los ocho pares con mayor correlación en valor absoluto.")
P("Se forma un bloque claro: la natalidad, la mortalidad infantil y la proporción de agricultura se mueven juntas y en sentido contrario al PIB, los teléfonos, la alfabetización y los servicios. "
  "Es decir, varias columnas están diciendo casi lo mismo, el grado de desarrollo del país. En cambio, la tierra cultivable y los cultivos permanentes casi no se relacionan con ese bloque "
  f"(por ejemplo, |r| = {abs(R['pares_debiles_max'][0][2]):.2f} entre cultivos permanentes y mortalidad infantil). Esta redundancia es lo que hace útil un PCA.")
H3("Variables independientes y dependientes")
P("Para separar variables que actúan como punto de partida de las que parecen depender de otras, usamos dos pistas: el sentido que tiene cada variable (una característica física del territorio "
  "no depende del ingreso de un país; la mortalidad infantil sí puede depender de él) y qué tan fuerte es su correlación con las demás. La Tabla 7 resume la clasificación junto con la mayor correlación de cada variable.")
rol = {"Densidad de población": ("Independiente", "Es una condición de partida (población entre superficie)."),
       "Costa / área": ("Independiente", "Es una característica geográfica fija."),
       "Tierra cultivable": ("Independiente", "Depende del suelo y del clima, no del ingreso."),
       "Cultivos permanentes": ("Independiente", "Depende del suelo y del clima."),
       "Migración neta": ("Dependiente (débil)", "Responde a condiciones económicas, pero su relación lineal es baja."),
       "Mortalidad infantil": ("Dependiente", "Resultado de la salud y el ingreso; muy ligada a la natalidad."),
       "PIB per cápita": ("Dependiente", "Se mueve con la infraestructura (teléfonos) y la educación."),
       "Alfabetización": ("Dependiente", "Resultado de la educación, relacionada con el desarrollo."),
       "Teléfonos": ("Dependiente", "Indicador de infraestructura que acompaña al ingreso."),
       "Natalidad": ("Dependiente", "Cambia con el nivel de desarrollo y educación."),
       "Mortalidad": ("Dependiente", "Depende de la edad de la población y de la salud."),
       "Agricultura": ("Dependiente", "Su peso disminuye al crecer la economía."),
       "Servicios": ("Dependiente", "Su peso aumenta al crecer la economía.")}
filas = [["Variable", "Papel", "Justificación", "Mayor |r| (con)"]]
for d in R["dep"]:
    filas.append([d["nombre"], rol[d["nombre"]][0], rol[d["nombre"]][1], f"{abs(d['r_max']):.2f} ({d['con']})"])
tabla(filas, [1.35, 1.05, 2.5, 1.6], "Clasificación de las variables según su papel y mayor correlación con otra variable.")
P("Las cuatro variables que clasificamos como independientes tienen correlaciones máximas bajas (entre 0.36 y 0.52), lo que es coherente con que no las determine el resto. "
  "Las dependientes forman el bloque con correlaciones de 0.66 a 0.85. La correlación no demuestra causalidad, de modo que la clasificación debe leerse como una hipótesis razonable: "
  "por ejemplo, el PIB y los teléfonos pueden influirse mutuamente. Si más adelante se quisiera ajustar un modelo, buenas variables respuesta serían el PIB per cápita o la mortalidad infantil, "
  "explicadas con las condiciones geográficas y demográficas.")
figura("fig_dependencia.png", W, "Tres relaciones entre variables dependientes, con su recta de ajuste y su coeficiente de correlación.")

# ================================================================ 8
H2("Componentes principales (PCA)")
H3("Qué ventaja ofrece el PCA")
P("Con 13 variables y una estructura de correlación como la de la sección 3.4, trabajar variable por variable es redundante. El PCA construye combinaciones lineales de las variables "
  "(las componentes principales, CP) que están ordenadas por la varianza que explican y no están correlacionadas entre sí. Las ventajas concretas para estos datos son:")
P(f"Primero, la reducción: veremos que 4 componentes conservan alrededor de {100 * R['acum_z'][3]:.0f} % de la información de las 13 variables. Segundo, la eliminación de redundancia: las componentes "
  f"son ortogonales, y lo verificamos numéricamente, pues la mayor covarianza entre dos componentes es {R['off_diag']:.1e}, es decir, cero salvo error de redondeo. Tercero, la visualización: las dos primeras "
  f"componentes ({100 * R['acum_z'][1]:.1f} % de la varianza) permiten dibujar a los países en un plano. Cuarto, en un modelo posterior las componentes evitan la multicolinealidad entre las variables originales. "
  "A cambio, perdemos parte de la información (lo que queda fuera de las componentes elegidas) y las componentes son más difíciles de interpretar que las variables originales.")
H3("Cómo se calculan")
P("El procedimiento es el siguiente. Se centran los datos restando la media de cada variable; se calcula la matriz de covarianza; se obtienen sus valores propios λ y vectores propios; "
  "cada vector propio da los coeficientes de una componente y su valor propio es la varianza de esa componente. La proporción de varianza explicada por la componente i es λ<sub>i</sub> / Σλ, donde λ<sub>i</sub> es el valor propio de la componente <i>i</i> y Σλ es la suma de todos los valores propios (la varianza total). "
  "Las puntuaciones (scores) de cada país se obtienen multiplicando los datos centrados por los vectores propios.")
P("Calculamos el PCA de dos formas: con la matriz de covarianza de los datos sin estandarizar y con la de los datos estandarizados (cada variable dividida entre su desviación estándar). "
  "Como se anota en el pizarrón, la matriz de covarianza de los datos estandarizados es igual a la matriz de correlación; lo comprobamos en el programa. "
  "Programamos el cálculo con los valores propios directamente y lo comparamos con la función PCA de scikit-learn, con coincidencia total en los valores propios"
  + (" (verificado)." if R["sklearn_ok"] else "."))
codigo("pca_matrices")
H3("Por qué elegimos cuatro componentes")
P("El número de componentes no se puede escoger al azar, así que usamos tres criterios sobre el caso estandarizado, que es el que tiene sentido interpretar (la sección 3.6 lo justifica):")
P(f"El criterio de Kaiser conserva las componentes con valor propio mayor que 1, es decir, las que explican más varianza que una variable original estandarizada; da {R['k_kaiser']} componentes. "
  f"La simulación de Horn compara cada valor propio con el que se obtendría por azar con datos sin estructura (percentil 95 de 500 simulaciones); da {R['k_horn']}. "
  f"El criterio de la varianza acumulada pide llegar a una proporción alta, aquí 80 %; da {R['k_80']}. "
  "Además, la gráfica de sedimentación (scree plot) muestra un codo después de la segunda componente.")
codigo("pca_criterios")
figura("fig_scree.png", W, "Izquierda: valores propios, umbral de Kaiser y valores esperados por azar. Derecha: varianza explicada individual y acumulada.")
filas = [["Componente", "Valor propio", "% de varianza", "% acumulado", "Umbral por azar (Horn)"]]
for i in range(6):
    filas.append([f"CP{i + 1}", f"{R['val_z'][i]:.2f}", f"{100 * R['prop_z'][i]:.1f}", f"{100 * R['acum_z'][i]:.1f}", f"{R['horn'][i]:.2f}"])
tabla(filas, [1.0, 1.1, 1.1, 1.1, 1.6], "Valores propios de la matriz de correlación (primeras seis componentes).")
P(f"Los criterios no coinciden. Kaiser pide {R['k_kaiser']}, la simulación de Horn solo {R['k_horn']} y la varianza acumulada {R['k_80']}. Elegimos {R['k']} componentes por tres razones. "
  f"La CP3 y la CP4 tienen valores propios de {R['val_z'][2]:.2f} y {R['val_z'][3]:.2f}, por encima de 1, y juntas aportan {100 * (R['prop_z'][2] + R['prop_z'][3]):.1f} % de la varianza. "
  f"Con {R['k']} componentes se explica {100 * R['acum_z'][3]:.1f} %, cercano al 80 % y mucho más que el {100 * R['acum_z'][1]:.1f} % de dos componentes. Y, como se ve en la siguiente subsección, la CP3 y la CP4 tienen una interpretación geográfica clara. "
  f"La CP5 ({R['val_z'][4]:.2f}) queda por debajo de 1 y no la incluimos aunque con ella se pasaría de 80 %. Reconocemos que la CP3 y la CP4 son marginales (sus valores propios están cerca del umbral), "
  "así que la parte sólida del resultado son las dos primeras componentes.")
H3("Interpretación de las componentes")
P("Los coeficientes de cada componente se interpretan mejor como cargas, es decir, como la correlación entre cada variable original y la componente. "
  "Una carga grande en valor absoluto indica que esa variable pesa mucho en la componente.")
codigo("pca_cargas")
figura("fig_cargas.png", W * .72, "Cargas de las variables en las primeras cinco componentes (rojo: positivas; azul: negativas).")
c1 = R["cargas"]
P(f"La CP1 ({100 * R['prop_z'][0]:.1f} % de la varianza) separa a los países por nivel de desarrollo: pesan a favor el PIB per cápita (0.77), los teléfonos (0.85), la alfabetización (0.79) y los servicios (0.79), "
  "y en contra la mortalidad infantil (−0.91), la natalidad (−0.87), la agricultura (−0.79) y la mortalidad (−0.55). Una puntuación alta indica un país con ingreso, infraestructura y educación altos y una población con baja natalidad.")
P(f"La CP2 ({100 * R['prop_z'][1]:.1f} %) está dominada por los cultivos permanentes (0.87), con aportes de la migración neta (−0.59), la densidad (0.45), el PIB (−0.42) y la costa/área (0.36). "
  "Describe un perfil de territorios pequeños, con mucha costa y densidad, cultivos permanentes y emigración, típico de islas. Esta lectura es nuestra interpretación y no algo que los datos afirmen por sí mismos.")
P(f"La CP3 ({100 * R['prop_z'][2]:.1f} %) mezcla tierra cultivable (0.69) y densidad (0.57), con migración neta y mortalidad: la intensidad del uso agrícola del territorio y su relación con la población. "
  f"La CP4 ({100 * R['prop_z'][3]:.1f} %) contrapone la razón costa/área (0.64) con la tierra cultivable (−0.52): geografía costera frente a tierra de cultivo.")
H3("Los países en el plano de las dos primeras componentes")
codigo("pca_biplot")
figura("fig_biplot.png", W * .95, "Países en el plano de CP1 y CP2, coloreados por grupo de regiones; las flechas son las cargas de las variables.")
gm = R["grupo_medias_cp1"]
P(f"Las regiones se ordenan sobre la CP1 como cabría esperar. Las puntuaciones medias son: Europa {gm['Europa']:.2f}, América {gm['América']:.2f}, Oceanía {gm['Oceanía']:.2f}, "
  f"Asia y Cercano Oriente {gm['Asia y Cercano Oriente']:.2f}, CEI {gm['CEI']:.2f} y África {gm['África']:.2f}. Los puntos más altos en la CP1 son {', '.join(R['cp1_extremos']['alto'])}, y los más bajos "
  f"{', '.join(R['cp1_extremos']['bajo'])}. Que una variable construida solo con números reproduzca la geografía del desarrollo es una señal de que las componentes recogen estructura real y no ruido.")

# ================================================================ 9
H3("Estandarización: con y sin")
H3("Por qué importa la escala")
P("El PCA maximiza la varianza, y la varianza depende de las unidades. Si una variable está en miles de dólares y otra en fracciones entre 0 y 1, la primera aporta varianza varios órdenes de magnitud mayor solo por su escala. "
  "La Tabla 9 muestra el rango y la varianza de cada variable en la base transformada.")
filas = [["Variable", "Mínimo", "Máximo", "Rango", "Varianza"]]
for d in R["rango"]:
    filas.append([d["nombre"], fmt(d["minimo"]), fmt(d["maximo"]), fmt(d["rango"]), fmt(d["varianza"])])
tabla(filas, [1.9, .9, .9, 1.0, 1.4], "Rango y varianza de cada variable antes de estandarizar (base transformada).")
P(f"La varianza del PIB per cápita es {R['var_pib']:,.0f}, y la de {R['var_min'][0].lower()} es {R['var_min'][1]:.3f}. El PIB aporta {100 * R['part_pib']:.2f} % de la varianza total de las 13 variables. "
  "Si no se estandariza, el PCA solo \"ve\" al PIB.")
H3("Qué ocurre sin estandarizar y estandarizando")
codigo("comparacion")
figura("fig_comp_barras.png", W, "Izquierda: coeficientes de la CP1 en ambos casos. Derecha: varianza explicada por las primeras seis componentes.")
figura("fig_comp_scores.png", W, "Países en el plano CP1–CP2 sin estandarizar (izquierda) y estandarizando (derecha).")
n_alta = sum(abs(f[0]) >= .5 for f in c1["m"])
filas = [["Aspecto", "Sin estandarizar", "Estandarizados"],
         ["Matriz usada", "Covarianza", "Correlación (covarianza de los datos estandarizados)"],
         ["Varianza explicada por la CP1", f"{100 * R['prop_s'][0]:.2f} %", f"{100 * R['prop_z'][0]:.1f} %"],
         ["Componentes para llegar a 80 %", f"{R['k_s_80']}", f"{R['k_80']}"],
         ["Variables con peso importante en la CP1", "1 (PIB per cápita, coeficiente 1.00)", f"{n_alta} (|carga| ≥ 0.5)"],
         ["Qué representa la CP1", "El PIB per cápita casi por sí solo", "Un eje de desarrollo con muchas variables"]]
tabla(filas, [2.4, 2.0, 2.1], "Comparación del PCA con y sin estandarización.")
P(f"Sin estandarizar, la CP1 explica {100 * R['prop_s'][0]:.2f} % de la varianza y su vector propio vale {R['vec_s_pib']:.4f} en el PIB per cápita y casi cero en las demás variables. "
  "La componente es, en la práctica, el PIB con otro nombre, y el PCA no reduce nada: ordena a los países por ingreso e ignora la mortalidad infantil, la natalidad o la alfabetización. "
  "El 99.98 % es un artefacto de la escala, no una señal de que la información esté concentrada.")
P(f"Al estandarizar, cada variable tiene varianza 1 y la información se reparte: la CP1 explica {100 * R['prop_z'][0]:.1f} % y recibe peso de {n_alta} variables, las cuatro primeras componentes "
  f"suman {100 * R['acum_z'][3]:.1f} %. Las puntuaciones de la CP1 de ambos casos tienen correlación de {R['r_cp1']:.2f}: ordenan de forma parecida a los países, porque el PIB también forma parte del eje de desarrollo, "
  "pero la versión estandarizada incorpora la información social y demográfica que la otra descarta.")
H3("Conclusión sobre la estandarización")
P("Las variables de este conjunto están en unidades distintas (dólares, porcentajes, fracciones, razones), así que estandarizar es la decisión adecuada y la que usamos para elegir componentes en la sección 3.5. "
  "Solo tendría sentido no estandarizar si todas las variables estuvieran en la misma unidad y la diferencia de varianzas fuera información que se quiere conservar. Aquí no es el caso.")

# ================================================================ disc
H1("Discusión")
H2("Comparación con las hipótesis")
P(f"<b>H1 (las variables miden desarrollo y se pueden resumir).</b> Se cumple en lo esencial. {R['n_pares_05']} de los {R['n_pares']} pares de variables tienen |r| ≥ 0.5 y se forma un bloque claro de desarrollo; la primera componente ({100 * R['prop_z'][0]:.1f} %) ordena a las regiones de África a Europa. "
  f"Sin embargo, la reducción es moderada: hacen falta cuatro componentes para llegar a {100 * R['acum_z'][3]:.1f} %, y la simulación de Horn solo respalda {R['k_horn']} ({100 * R['acum_z'][1]:.1f} %). Es decir, los 13 indicadores no se reducen a una sola dimensión, porque las variables geográficas (tierra cultivable, cultivos permanentes, costa) aportan estructura propia.")
P(f"<b>H2 (la estandarización es necesaria).</b> Se cumple de forma contundente: sin estandarizar, la CP1 explica {100 * R['prop_s'][0]:.2f} % de la varianza y es prácticamente el PIB per cápita; estandarizando, explica {100 * R['prop_z'][0]:.1f} % y recibe peso de siete variables.")
H2("Resultados inesperados y limitaciones")
P(f"Los criterios para elegir componentes no coinciden (Kaiser {R['k_kaiser']}, Horn {R['k_horn']}, varianza acumulada {R['k_80']}). Una explicación es que Horn es el más exigente, pues descuenta lo que se obtendría por azar con {R['n_final']} países y 13 variables, mientras que Kaiser es más permisivo; "
  f"la CP3 y la CP4 tienen valores propios de {R['val_z'][2]:.2f} y {R['val_z'][3]:.2f}, apenas por encima de 1, por lo que son interpretables pero marginales. Por eso las dos primeras componentes son el resultado más firme.")
P("Otras limitaciones: (1) en migración neta, 62 países tienen exactamente cero, y es probable que algunos de esos ceros sean datos no disponibles, lo que debilita su correlación con las demás variables; "
  f"(2) la imputación con la mediana regional reduce algo la varianza de las variables más afectadas (alfabetización, con 16 de {R['n_final']} países imputados); (3) los datos son de mediados de la década de 2000, de modo que las conclusiones describen ese periodo; "
  "(4) la interpretación de la CP2, CP3 y CP4 es nuestra lectura de las cargas; (5) la clasificación en variables independientes y dependientes se apoya en correlaciones, que no prueban causalidad.")
H2("Cómo se podría mejorar el análisis")
P("Con más tiempo se podría: tratar los ceros de migración neta como faltantes y repetir el análisis; comparar la imputación con la mediana regional contra otros métodos de imputación; "
  "repetir el PCA sin los territorios muy pequeños (Monaco, Macau, Singapore) para ver si cambian las componentes; actualizar los datos con fuentes más recientes; y usar las componentes como variables explicativas en un modelo para el PIB per cápita o la mortalidad infantil.")

# ================================================================ 10
H1("Conclusiones")
P(f"Partimos de {R['n_paises']} países y 18 variables. Después de la depuración quedaron {R['n_final']} países y 13 variables numéricas; descartamos las variables categóricas y las redundantes (otros usos del suelo, industria) "
  "con razones explícitas, y transformamos con logaritmo las tres variables de asimetría extrema.")
P("Las correlaciones muestran un bloque de variables que describe el nivel de desarrollo (mortalidad infantil, natalidad, alfabetización, PIB per cápita, teléfonos, agricultura y servicios), mientras que las condiciones geográficas "
  "(tierra cultivable, cultivos permanentes, costa) se relacionan poco con él. Por eso las clasificamos como independientes y el bloque como dependiente, aclarando que se trata de una hipótesis y no de una prueba de causalidad.")
P(f"Con datos estandarizados, cuatro componentes explican {100 * R['acum_z'][3]:.1f} % de la varianza. La primera (el {100 * R['prop_z'][0]:.1f} %) es un eje de desarrollo que ordena a las regiones de forma coherente. "
  "La elección de cuatro componentes se apoya en Kaiser y en la varianza acumulada, aunque la simulación de Horn sugiere solo dos, de modo que las dos primeras son las más firmes.")
P("Sin estandarizar, el PCA se reduce al PIB por la diferencia de escalas y pierde su utilidad. Limitaciones: los datos son de mediados de los años 2000; imputamos con la mediana regional una parte pequeña de los valores; "
  "y el cero de migración neta puede ser un dato faltante disfrazado. Una extensión natural sería ajustar un modelo para el PIB per cápita o la mortalidad infantil usando las componentes como predictores.")

# ================================================================ bib
H1("Bibliografía")
for t in ["[1] fernandol. <i>Countries of the World</i> [conjunto de datos]. Kaggle. https://www.kaggle.com/datasets/fernandol/countries-of-the-world",
          "[2] Jolliffe, I. T. (2002). <i>Principal Component Analysis</i> (2.ª ed.). Springer.",
          "[3] Kaiser, H. F. (1960). The application of electronic computers to factor analysis. <i>Educational and Psychological Measurement</i>, 20(1), 141–151.",
          "[4] Horn, J. L. (1965). A rationale and test for the number of factors in factor analysis. <i>Psychometrika</i>, 30(2), 179–185.",
          "[5] United Nations Development Programme (1990). <i>Human Development Report 1990</i>. Oxford University Press.",
          "[6] McKinney, W. (2010). Data structures for statistical computing in Python. <i>Proceedings of the 9th Python in Science Conference</i>, 51–56.",
          "[7] Harris, C. R. et al. (2020). Array programming with NumPy. <i>Nature</i>, 585, 357–362.",
          "[8] Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. <i>Computing in Science &amp; Engineering</i>, 9(3), 90–95.",
          "[9] Waskom, M. L. (2021). seaborn: statistical data visualization. <i>Journal of Open Source Software</i>, 6(60), 3021.",
          "[10] Pedregosa, F. et al. (2011). Scikit-learn: Machine learning in Python. <i>Journal of Machine Learning Research</i>, 12, 2825–2830."]:
    P(t, "small")

doc.multiBuild(story)
print("PDF listo")
