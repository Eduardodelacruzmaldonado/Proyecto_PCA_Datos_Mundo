# Exploración de datos y PCA — Countries of the World

Proyecto final de *Métodos Matemáticos Computacionales para Ciencia de Datos* (UNAM, IIMAS, Ciencia de Datos).

Integrantes: De La Cruz Maldonado José Eduardo, López Reyes Jorge.
Profesora: Nora Isabel Pérez Quezadas.

## Estructura
- `contexto/`: imágenes del pizarrón, rúbrica, prompt original y CSV de origen. Todo el contexto nuevo se agrega aquí.
- `datos/`: CSV de Kaggle (fernandol/countries-of-the-world).
- `codigo/exploracion_pca.py`: análisis completo (genera `figuras/` y `resultados/`).
- `codigo/construir_pdf.py`: arma el reporte en PDF.
- `documento/Proyecto_PCA_Paises.pdf`: reporte.

## Reproducir
```
python3 codigo/exploracion_pca.py
python3 codigo/construir_pdf.py
```
Requiere pandas, numpy, matplotlib, seaborn, scikit-learn y reportlab.
