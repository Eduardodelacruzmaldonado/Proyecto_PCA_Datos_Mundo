# -*- coding: utf-8 -*-
"""
Convierte exploracion_pca.py en el notebook analisis_pca.ipynb y lo ejecuta.

exploracion_pca.py está escrito por celdas: "# %%" inicia una celda de código y "# %% [markdown]" una
celda de texto. Este programa arma el notebook con esas celdas y lo ejecuta para que queden guardadas
las tablas y las gráficas. Así el notebook y el programa siempre tienen exactamente el mismo código.

Uso (desde la carpeta del proyecto):
    python crear_notebook.py        # en macOS / Linux: python3
"""
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent
ORIGEN = BASE / "exploracion_pca.py"
DESTINO = BASE / "analisis_pca.ipynb"

celdas, tipo, lineas = [], None, []


def cerrar():
    """Agrega al notebook la celda que se estaba leyendo."""
    texto = "\n".join(lineas).strip("\n")
    if tipo == "markdown":
        texto = "\n".join(l[2:] if l.startswith("# ") else l[1:] for l in texto.split("\n"))
        celdas.append(nbformat.v4.new_markdown_cell(texto))
    elif tipo == "code" and texto.strip():
        celdas.append(nbformat.v4.new_code_cell(texto))


for linea in ORIGEN.read_text(encoding="utf-8").splitlines():
    if linea.startswith("# %%"):
        cerrar()                                   # lo que está antes de la primera celda no se copia
        tipo = "markdown" if "[markdown]" in linea else "code"
        lineas = []
    else:
        lineas.append(linea)
cerrar()

nb = nbformat.v4.new_notebook(cells=celdas, metadata={
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"}})
print(f"Ejecutando {len(celdas)} celdas...")
NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(BASE)}}).execute()
nbformat.write(nb, DESTINO)
print("Notebook generado en:", DESTINO.name)
