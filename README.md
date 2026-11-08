# Exploración de datos y reducción de dimensiones con componentes principales

**Materia:** Métodos Matemáticos Computacionales para Ciencia de Datos
**Institución:** Universidad Nacional Autónoma de México (UNAM), Instituto de Investigaciones en Matemáticas Aplicadas y en Sistemas (IIMAS)
**Licenciatura:** Ciencia de Datos
**Profesora:** Nora Isabel Pérez Quezadas
**Integrantes:**
- De La Cruz Maldonado José Eduardo
- López Reyes Jorge

---

## Descripción

Análisis exploratorio del conjunto de datos *Countries of the World* (Kaggle, fernandol) y reducción de dimensiones con análisis de componentes principales (PCA). El reporte completo está en `reporte/Proyecto_PCA_Paises.pdf`.

El flujo de trabajo es el planteado en clase:

1. **Depuración.** Se descartan las variables categóricas y redundantes (clima, otros usos del suelo, industria, población y superficie), se eliminan 3 territorios con 4 o más datos faltantes (quedan 224 países) y se imputan los vacíos restantes con la mediana de la región.
2. **Exploración.** Histograma y diagrama de caja de cada variable, medidas descriptivas, matriz de covarianza, valores atípicos (criterio del rango intercuartílico) y transformación logarítmica de las variables con asimetría extrema.
3. **Correlaciones.** Matriz de correlación de Pearson de las 13 variables, pares más y menos relacionados, comparación gráfica de las 4 variables más correlacionadas (natalidad, mortalidad infantil, agricultura y alfabetización) y contraste con las 2 menos correlacionadas (tierra cultivable y migración neta).
4. **PCA.** Valores y vectores propios calculados con `numpy.linalg.eigh` (verificados con scikit-learn). El número de componentes se elige con los criterios de Kaiser, Horn (500 simulaciones) y varianza acumulada; con 4 componentes se explica 76.7 % de la varianza.
5. **Estandarización.** Comparación del PCA con y sin estandarizar: sin estandarizar, la primera componente explica 99.98 % de la varianza porque solo refleja el PIB per cápita.
6. **Reconstrucción.** Se regresa de las componentes a la matriz original con *k* componentes, se deshacen la estandarización y el logaritmo y se mide el error; con 4 componentes se deja de recuperar 23.3 % de la varianza y en países extremos aparecen valores imposibles (por ejemplo, PIB negativo en Níger).

---

## Estructura del repositorio

```text
├── exploracion_pca.py        # Todo el análisis: depuración, gráficas, correlaciones y PCA
├── generar_pdf_reporte.py    # Arma el reporte PDF con los resultados del análisis
├── datos/
│   └── countries_of_the_world.csv
├── contexto/                 # Fotos del pizarrón, rúbrica del proyecto y contexto adicional
├── fuentes/                  # Tipografías Liberation Serif y DejaVu Sans Mono (licencias libres)
├── graficas/                 # Gráficas generadas por exploracion_pca.py (y fórmulas del reporte)
├── resultados/               # Tablas y resultados numéricos (CSV y JSON)
├── reporte/
│   └── Proyecto_PCA_Paises.pdf
├── prompt_usuario.txt
├── requirements.txt
└── README.md
```

Los fragmentos de código que aparecen en el reporte se copian directamente de `exploracion_pca.py` (bloques marcados con `# >>> nombre` y `# <<< nombre`), y todos los números del texto se leen de la carpeta `resultados`, de modo que el PDF siempre corresponde al análisis ejecutado.

---

## Instalación y ejecución

Se requiere Python 3.10 o superior. Las rutas se construyen con `pathlib` a partir de la carpeta del proyecto y las tipografías del PDF vienen incluidas, así que el proyecto funciona igual en **Windows**, **macOS** y **Linux** sin modificar nada.

**macOS / Linux (Terminal):**
```bash
cd Proyecto_PCA_Datos_Mundo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 exploracion_pca.py
python3 generar_pdf_reporte.py
```

**Windows (PowerShell):**
```powershell
cd Proyecto_PCA_Datos_Mundo
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python exploracion_pca.py
python generar_pdf_reporte.py
```

`exploracion_pca.py` crea las carpetas `graficas` y `resultados`; `generar_pdf_reporte.py` escribe `reporte/Proyecto_PCA_Paises.pdf`. El análisis completo tarda unos segundos.

---

## Nota sobre los datos

En el archivo original de Kaggle, la fracción del PIB de la industria de Países Bajos (Netherlands) aparece como `04,244`, lo que se lee como 4.244 y es imposible para una fracción (los tres sectores sumarían 5.0). En `datos/countries_of_the_world.csv` ese valor está corregido a `0,244`, con lo que agricultura + industria + servicios suman 1.001, como en el resto de los países.
