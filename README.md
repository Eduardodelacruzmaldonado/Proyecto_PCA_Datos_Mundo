# Análisis Multivariado y PCA: Países del Mundo
**Materia:** Métodos Matemáticos para Ciencia de Datos  
**Institución:** Universidad Nacional Autónoma de México (UNAM)  
**Facultad / Instituto:** Instituto de Investigaciones en Matemáticas Aplicadas y en Sistemas (IIMAS)  
**Licenciatura:** Ciencia de Datos  
**Profesora:** Mtra. Nora Isabel Pérez Quezadas  
**Integrantes:**
- De La Cruz Maldonado José Eduardo
- López Reyes Jorge

---

## 📌 Descripción del Proyecto
Este repositorio contiene el análisis matemático, preprocesamiento de datos, análisis exploratorio multivariado y la reducción de dimensionalidad mediante **Análisis de Componentes Principales (PCA)** aplicado al conjunto de datos mundial *Countries of the World* (Kaggle / CIA World Factbook).

Se investiga y fundamenta de manera formal:
1. **La justificación matemática de la estandarización:** Demostración empírica de cómo la omisión de la estandarización colapsa las componentes en las magnitudes de mayor escala (Población y Área), ocultando las dimensiones de desarrollo socioeconómico.
2. **Selección objetiva de componentes:** Aplicación formal del Criterio de Kaiser ($\lambda > 1.0$), gráfico de sedimentación (*Scree Plot*) y análisis de varianza explicada acumulada.
3. **Interpretación factorial y Biplot:** Proyección de las naciones y vectores directores en el espacio factorial bidimensional ($CP_1$ vs. $CP_2$).

---

## 📁 Estructura del Repositorio
```text
├── contexto/                 # Fotografías de notas y requerimientos del pizarrón de clase
│   ├── pizarron_1.png
│   ├── pizarron_2.png
│   └── pizarron_3.png
├── datos/                    # Conjuntos de datos y matrices calculadas
│   ├── countries_of_the_world.csv     # Dataset original
│   ├── countries_cleaned.csv          # Dataset depurado e imputado (N = 216)
│   ├── estadisticas_descriptivas.csv  # Medidas de tendencia central y dispersión
│   ├── matriz_covarianza.csv          # Matriz de covarianzas muestral
│   ├── matriz_correlacion.csv         # Matriz de correlación de Pearson
│   └── matriz_cargas_loadings.csv     # Cargas factoriales de las componentes
├── graficas/                 # Visualizaciones generadas en alta resolución
│   ├── 01_distribuciones_histogramas.png
│   ├── 02_boxplots_socioeconomicos.png
│   ├── 03_matriz_correlacion_heatmap.png
│   ├── 04_comparativa_estandarizacion_varianza.png
│   ├── 05_scree_plot_kaiser.png
│   ├── 06_cargas_loadings_heatmap.png
│   └── 07_biplot_cp1_cp2.png
├── reporte/                  # Reporte académico formal
│   ├── Reporte_PCA_Countries_UNAM_IIMAS.pdf
│   └── preview/              # Renders de comprobación de páginas
├── prompt_usuario.txt        # Registro del requerimiento original
├── generar_analisis.py       # Script principal de análisis estadístico y graficación
├── generar_pdf_reporte.py    # Generador de documento PDF (ReportLab)
├── requirements.txt          # Dependencias de Python
└── README.md
```

---

## ⚙️ Requisitos e Instalación
Se requiere Python 3.10 o superior y las siguientes bibliotecas:
```bash
pip install -r requirements.txt
```

### Ejecución
1. Para regenerar todos los análisis estadísticos, matrices y gráficas:
```bash
python generar_analisis.py
```
2. Para compilar el reporte académico en PDF:
```bash
python generar_pdf_reporte.py
```

---

## 📄 Reporte Académico Final
El documento final formal con la portada institucional, tablas completas, justificaciones matemáticas, figuras integradas y fragmentos de código se encuentra en:
👉 `reporte/Reporte_PCA_Countries_UNAM_IIMAS.pdf`
