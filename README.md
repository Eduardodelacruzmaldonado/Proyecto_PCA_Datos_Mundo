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

1. **Depuración.** Se descartan las variables categóricas y redundantes (clima, otros usos del suelo, industria, población y superficie) y se eliminan 3 territorios con 4 o más datos faltantes (quedan 224 países). Los vacíos restantes no se rellenan con la mediana: se estiman por **interpolación lineal** entre nodos (medianas de grupos de países) a partir de la variable más correlacionada con cada una.
2. **Exploración.** Histograma y diagrama de caja de cada variable, medidas descriptivas, matriz de covarianza, valores atípicos (criterio del rango intercuartílico) y transformación logarítmica de las variables con asimetría extrema.
3. **Correlaciones.** Matriz de correlación de Pearson de las 13 variables, pares más y menos relacionados y comparación de los valores y vectores propios de las variables más y menos correlacionadas.
4. **PCA.** Valores y vectores propios calculados con `numpy.linalg.eigh` (verificados con scikit-learn). El número de componentes se elige con el criterio de Kaiser (valores propios mayores que 1); con 4 componentes se explica 76.9 % de la varianza.
5. **Estandarización.** Comparación del PCA con y sin estandarizar: sin estandarizar, la primera componente explica 99.98 % de la varianza porque solo refleja el PIB per cápita.
6. **Reconstrucción.** Se regresa de las componentes a la matriz original con *k* componentes, se deshacen la estandarización y el logaritmo y se mide el error.
7. **Predicción con splines cúbicos.** Con los países de la base se construye un spline cúbico natural de la mortalidad infantil en función del PIB per cápita y se predice la de 45 países que no se usaron para construirlo (error 37 % menor que sin usar el PIB). La derivada del spline muestra cuánto cambia la mortalidad por cada 1,000 dólares.
8. **Hipótesis H2 (rendimientos decrecientes).** Con los mismos nodos se mide cuánto cambian la alfabetización, la mortalidad infantil y el peso de la agricultura por cada 100 teléfonos: en el primer tramo la pendiente es entre 93 y 477 veces la del último.

El reporte no incluye código: todo el código, con su explicación, sus tablas y sus gráficas, está en el notebook `analisis_pca.ipynb`. La copia `analisis_pca_reporte.ipynb` contiene solo el análisis del reporte y lo calcula y muestra todo dentro del notebook, sin crear carpetas ni escribir archivos; solo necesita `datos/countries_of_the_world.csv`.

---

## Estructura del repositorio

```text
├── analisis_pca.ipynb        # Notebook con todo el código explicado, las tablas y las gráficas
├── analisis_pca_reporte.ipynb  # Copia autocontenida: solo el análisis del reporte, sin crear carpetas ni archivos
├── exploracion_pca.py        # El mismo análisis como programa (escrito por celdas)
├── crear_notebook.py         # Convierte exploracion_pca.py en los dos notebooks y los ejecuta
├── generar_pdf_reporte.py    # Arma el reporte PDF con los resultados del análisis
├── datos/
│   └── countries_of_the_world.csv
├── contexto/                 # Fotos del pizarrón, rúbrica del proyecto y contexto adicional
├── fuentes/                  # Tipografías Liberation Serif y DejaVu Sans Mono (licencias libres)
├── graficas/                 # Gráficas generadas por el análisis (y fórmulas del reporte)
├── resultados/               # Tablas y resultados numéricos (CSV y JSON)
├── reporte/
│   └── Proyecto_PCA_Paises.pdf
├── prompt_usuario.txt
├── requirements.txt
└── README.md
```

`exploracion_pca.py` está escrito por celdas (`# %%` para código y `# %% [markdown]` para texto) y `crear_notebook.py` lo convierte tal cual en `analisis_pca.ipynb`, así que el programa y el notebook siempre tienen el mismo código. Todos los números del reporte se leen de la carpeta `resultados`, de modo que el PDF siempre corresponde al análisis ejecutado.

---

## Instalación y ejecución

Se requiere Python 3.10 o superior. Las rutas se construyen con `pathlib` a partir de la carpeta del proyecto y las tipografías del PDF vienen incluidas, así que el proyecto funciona igual en **Windows**, **macOS** y **Linux** sin modificar nada.

**macOS / Linux (Terminal):**
```bash
cd Proyecto_PCA_Datos_Mundo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 crear_notebook.py
python3 generar_pdf_reporte.py
```

**Windows (PowerShell):**
```powershell
cd Proyecto_PCA_Datos_Mundo
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python crear_notebook.py
python generar_pdf_reporte.py
```

`crear_notebook.py` ejecuta todo el análisis dentro del notebook `analisis_pca.ipynb` y crea las carpetas `graficas` y `resultados`; `generar_pdf_reporte.py` escribe `reporte/Proyecto_PCA_Paises.pdf`. También se puede abrir el notebook y ejecutarlo celda por celda, o correr solo el análisis con `python exploracion_pca.py`. Todo tarda menos de un minuto.

---

## Nota sobre los datos

En el archivo original de Kaggle, la fracción del PIB de la industria de Países Bajos (Netherlands) aparece como `04,244`, lo que se lee como 4.244 y es imposible para una fracción (los tres sectores sumarían 5.0). En `datos/countries_of_the_world.csv` ese valor está corregido a `0,244`, con lo que agricultura + industria + servicios suman 1.001, como en el resto de los países.
