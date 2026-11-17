# -*- coding: utf-8 -*-
"""
Convierte exploracion_pca.py en dos notebooks y los ejecuta.

exploracion_pca.py está escrito por celdas: "# %%" inicia una celda de código y "# %% [markdown]" una
celda de texto. Este programa arma con esas celdas:

- analisis_pca.ipynb: el mismo código del programa. Además de mostrar tablas y figuras, guarda las
  gráficas en "graficas" y los resultados en "resultados", que usa generar_pdf_reporte.py.
- analisis_pca_reporte.ipynb: una copia autocontenida con solo el análisis del reporte. No crea carpetas
  ni escribe archivos: todas las tablas y figuras se muestran dentro del notebook. Solo necesita el archivo
  de datos datos/countries_of_the_world.csv.

Los dos se ejecutan para que queden guardadas las tablas y las gráficas, y los dos se generan del mismo
archivo, así que siempre tienen el mismo análisis.

Uso (desde la carpeta del proyecto):
    python crear_notebook.py        # en macOS / Linux: python3
"""
import re
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent
ORIGEN = BASE / "exploracion_pca.py"


def celdas_de(texto):
    """Separa el texto del programa en celdas de notebook."""
    celdas, tipo, lineas = [], None, []

    def cerrar():
        bloque = "\n".join(lineas).strip("\n")
        if tipo == "markdown":
            bloque = "\n".join(l[2:] if l.startswith("# ") else l[1:] for l in bloque.split("\n"))
            celdas.append(nbformat.v4.new_markdown_cell(bloque))
        elif tipo == "code" and bloque.strip():
            celdas.append(nbformat.v4.new_code_cell(bloque))

    for linea in texto.splitlines():
        if linea.startswith("# %%"):
            cerrar()                                # lo que está antes de la primera celda no se copia
            tipo = "markdown" if "[markdown]" in linea else "code"
            lineas = []
        else:
            lineas.append(linea)
    cerrar()
    return celdas


def autocontenido(texto):
    """Quita del programa todo lo relacionado con carpetas y archivos de salida."""
    def rep(viejo, nuevo):
        nonlocal texto
        assert texto.count(viejo) == 1, viejo[:80]
        texto = texto.replace(viejo, nuevo)

    # Presentación del notebook
    a = texto.index("# Este notebook contiene todo el código del reporte")
    b = texto.index("# ## Preparación")
    texto = texto[:a] + (
        "# Este notebook reúne el análisis del reporte `Proyecto_PCA_Paises.pdf`: la depuración de los datos,\n"
        "# el cálculo de los valores de las tablas y las figuras. Las secciones llevan la misma numeración que el\n"
        "# reporte. Todo se calcula y se muestra aquí mismo: no se crean carpetas ni se escriben archivos. Solo\n"
        "# se necesita el archivo de datos `datos/countries_of_the_world.csv`.\n#\n") + texto[b:]
    rep("# Paquetes, carpetas de salida, estilo de las gráficas y nombres en español de las variables.",
        "# Paquetes, estilo de las gráficas, nombres en español de las variables y funciones auxiliares. El\n"
        "# diccionario `RESULTADOS` reúne en memoria algunas cifras que se citan en el reporte.")

    # Paquetes: sin json ni rutas; las figuras se muestran en el notebook
    rep("import json\n", "")
    rep("from pathlib import Path\n", "")
    rep('matplotlib.use("Agg")                       # genera los PNG sin abrir ventanas en cualquier sistema\n', "")
    rep("import warnings\n", "import warnings\nfrom IPython.display import Markdown, display\n")
    a = texto.index("if hasattr(sys.stdout, \"reconfigure\"):")
    b = texto.index("C1, C2 = ")
    texto = texto[:a] + texto[b:]
    rep("import sys\n", "")
    rep('''"legend.fontsize": 7, "savefig.dpi": 200,
    "savefig.bbox": "tight", "figure.dpi": 100,''', '''"legend.fontsize": 7, "figure.dpi": 100,''')

    # Funciones para mostrar figuras y tablas
    a = texto.index("def guardar(fig, nombre):")
    b = texto.index("def iqr_atipicos(x):")
    texto = texto[:a] + '''def mostrar(tabla, titulo):
    """Muestra una tabla con su título."""
    display(Markdown(f"**{titulo}**"))
    display(tabla)


''' + texto[b:]
    texto, n = re.subn(r'guardar\(fig, [^)\n]+\)', "plt.show()", texto)
    assert n >= 18, n
    rep("def hist_box(x, titulo, unidad, ruta):", "def hist_box(x, titulo, unidad):")
    rep('hist_box(raw[v], NOMBRES[v], UNIDADES[v], FIG / f"hb_{i:02d}.png")', "hist_box(raw[v], NOMBRES[v], UNIDADES[v])")
    rep('"archivo": f"hb_{i:02d}.png", ', "")
    rep('estad.drop(columns=["archivo", "var"])', 'estad.drop(columns=["var"])')

    # Lectura de los datos
    rep('raw = pd.read_csv(BASE / "datos" / "countries_of_the_world.csv", decimal=",")',
        'raw = pd.read_csv("datos/countries_of_the_world.csv", decimal=",")')

    # Sin archivos de salida
    rep('''pd.DataFrame({"valor_propio": val_z, "proporcion": prop_z, "acumulada": acum_z},
             index=[f"CP{i}" for i in range(1, p + 1)]).to_csv(RES / "valores_propios.csv", encoding="utf-8")
''', "")
    texto, n = re.subn(r"\n[^\n]*\.to_csv\(RES / [^\n]*", "", texto)
    assert n >= 8, n
    a = texto.index("# %% [markdown]\n# ## Resultados para el reporte")
    texto = texto[:a].rstrip("\n") + "\n"

    for palabra in ("BASE", "FIG", "RES /", "EN_NOTEBOOK", "guardar(", "json", "to_csv"):
        assert palabra not in texto, palabra
    return texto


def construir(texto, destino):
    nb = nbformat.v4.new_notebook(cells=celdas_de(texto), metadata={
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"}})
    print(f"{destino}: ejecutando {len(nb.cells)} celdas...")
    NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(BASE)}}).execute()
    nbformat.write(nb, BASE / destino)
    print("Notebook generado en:", destino)


programa = ORIGEN.read_text(encoding="utf-8")
construir(programa, "analisis_pca.ipynb")
construir(autocontenido(programa), "analisis_pca_reporte.ipynb")
