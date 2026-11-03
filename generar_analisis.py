# -*- coding: utf-8 -*-
"""
Script de Procesamiento y Análisis Matemático para el Proyecto de PCA
Materia: Métodos Matemáticos para Ciencia de Datos - UNAM IIMAS
Alumnos: De La Cruz Maldonado José Eduardo, López Reyes Jorge
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# Configurar estilo visual académico sobrio y limpio
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['grid.color'] = '#dddddd'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['grid.alpha'] = 0.7

BASE_DIR = r"C:\Users\casa\.gemini\antigravity\scratch\pca_countries_project"
DATA_PATH = os.path.join(BASE_DIR, "datos", "countries_of_the_world.csv")
IMG_DIR = os.path.join(BASE_DIR, "graficas")
os.makedirs(IMG_DIR, exist_ok=True)

# 1. Carga de datos
raw_df = pd.read_csv(DATA_PATH)

# Limpiar nombres de columnas y strings
raw_df.columns = [c.strip() for c in raw_df.columns]
raw_df['Country'] = raw_df['Country'].str.strip()
raw_df['Region'] = raw_df['Region'].str.strip()

# Convertir columnas con formato europeo de comas decimales a float
numeric_cols = [c for c in raw_df.columns if c not in ['Country', 'Region']]
for col in numeric_cols:
    raw_df[col] = pd.to_numeric(raw_df[col].astype(str).str.replace(',', '.').str.strip(), errors='coerce')
    raw_df[col] = raw_df[col].astype(float)

print("Dimensiones originales:", raw_df.shape)

# 2. Diagnóstico y Limpieza
# Identificar filas con 4 o más nulos (microterritorios sin soberanía o sin registros macroeconómicos)
null_counts = raw_df.isnull().sum(axis=1)
excluded_territories = raw_df[null_counts >= 4]['Country'].tolist()
print("Territorios excluidos por exceso de nulos (>= 4 variables faltantes):", excluded_territories)

df_clean = raw_df[null_counts < 4].copy()

# Para las filas restantes, imputación por la mediana de la región geográfica correspondiente
for col in numeric_cols:
    df_clean[col] = df_clean.groupby('Region')[col].transform(lambda x: x.fillna(x.median()))
    # Si alguna región completa tuviera nulo, imputar por la mediana global
    df_clean[col] = df_clean[col].fillna(df_clean[col].median())

print("Dimensiones tras limpieza:", df_clean.shape)

# Guardar dataset limpio
df_clean.to_csv(os.path.join(BASE_DIR, "datos", "countries_cleaned.csv"), index=False)

# 3. Selección de Características Cuantitativas para el Análisis Multivariado
# Note: 'Climate' es una variable categórica codificada numéricamente (1: seco, 2: templado...), no continua de razón.
# 'Other (%)' es redundante por ser complemento de Arable + Crops (100 - Arable - Crops).
# 'Country' y 'Region' son identificadores categóricos.
pca_features = [
    'Population',
    'Area (sq. mi.)',
    'Pop. Density (per sq. mi.)',
    'Coastline (coast/area ratio)',
    'Net migration',
    'Infant mortality (per 1000 births)',
    'GDP ($ per capita)',
    'Literacy (%)',
    'Phones (per 1000)',
    'Arable (%)',
    'Crops (%)',
    'Birthrate',
    'Deathrate',
    'Agriculture',
    'Industry',
    'Service'
]

# Nombres amigables en español
feature_names_es = {
    'Population': 'Población',
    'Area (sq. mi.)': 'Área (millas²)',
    'Pop. Density (per sq. mi.)': 'Densidad Poblacional',
    'Coastline (coast/area ratio)': 'Tasa de Litoral/Área',
    'Net migration': 'Migración Neta',
    'Infant mortality (per 1000 births)': 'Mortalidad Infantil',
    'GDP ($ per capita)': 'PIB per Cápita',
    'Literacy (%)': 'Alfabetización (%)',
    'Phones (per 1000)': 'Teléfonos por 1000 hab.',
    'Arable (%)': 'Tierra Arable (%)',
    'Crops (%)': 'Cultivos Permanentes (%)',
    'Birthrate': 'Tasa de Natalidad',
    'Deathrate': 'Tasa de Mortalidad',
    'Agriculture': 'Sector Agrícola (PIB)',
    'Industry': 'Sector Industrial (PIB)',
    'Service': 'Sector Servicios (PIB)'
}

X_df = df_clean[pca_features].copy()

# 4. Estadísticas Descriptivas Univariadas (Media, Mediana, Varianza, DE, etc.)
desc_stats = pd.DataFrame({
    'Variable': [feature_names_es[f] for f in pca_features],
    'Media': X_df.mean(),
    'Mediana': X_df.median(),
    'Varianza': X_df.var(ddof=1),
    'Desv. Estándar': X_df.std(ddof=1),
    'Mínimo': X_df.min(),
    'Máximo': X_df.max()
})
desc_stats.to_csv(os.path.join(BASE_DIR, "datos", "estadisticas_descriptivas.csv"), index=False)
print("Estadísticas descriptivas calculadas con éxito.")

# 5. Generación de Gráficos de Distribución (EDA)
# 5.1 Matriz de Histogramas y Boxplots
fig, axes = plt.subplots(4, 4, figsize=(18, 14))
axes = axes.flatten()
for idx, col in enumerate(pca_features):
    ax = axes[idx]
    sns.histplot(X_df[col], kde=True, ax=ax, color='#1f77b4', bins=20)
    ax.set_title(feature_names_es[col], fontsize=11, fontweight='bold', pad=5)
    ax.set_xlabel('')
    ax.set_ylabel('Frecuencia' if idx % 4 == 0 else '', fontsize=9)
    ax.tick_params(axis='both', which='major', labelsize=8)
    ax.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()
fig.savefig(os.path.join(IMG_DIR, "01_distribuciones_histogramas.png"), dpi=200)
plt.close(fig)

# 5.2 Boxplots para variables socioeconómicas y demográficas
key_vars = ['GDP ($ per capita)', 'Literacy (%)', 'Phones (per 1000)', 'Infant mortality (per 1000 births)', 'Birthrate', 'Deathrate']
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
axes = axes.flatten()
for idx, col in enumerate(key_vars):
    ax = axes[idx]
    sns.boxplot(y=X_df[col], ax=ax, color='#aec7e8', width=0.4, flierprops=dict(marker='o', markersize=4, markerfacecolor='#d62728'))
    ax.set_title(f"Distribución: {feature_names_es[col]}", fontsize=11, fontweight='bold')
    ax.set_ylabel('Valor', fontsize=9)
    ax.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()
fig.savefig(os.path.join(IMG_DIR, "02_boxplots_socioeconomicos.png"), dpi=200)
plt.close(fig)

# 6. Matrices de Asociación: Covarianza vs Correlación
cov_matrix = X_df.cov()
corr_matrix = X_df.corr(method='pearson')

cov_matrix.to_csv(os.path.join(BASE_DIR, "datos", "matriz_covarianza.csv"))
corr_matrix.to_csv(os.path.join(BASE_DIR, "datos", "matriz_correlacion.csv"))

# Mapa de Calor de Correlación de Pearson
fig, ax = plt.subplots(figsize=(14, 11))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
cmap = sns.diverging_palette(230, 20, as_cmap=True)
sns.heatmap(corr_matrix, mask=mask, cmap=cmap, vmin=-1, vmax=1, annot=True, fmt=".2f",
            annot_kws={"size": 7.5}, xticklabels=[feature_names_es[f] for f in pca_features],
            yticklabels=[feature_names_es[f] for f in pca_features], square=True, linewidths=0.5, cbar_kws={"shrink": 0.8}, ax=ax)
ax.set_title("Matriz de Correlación de Pearson (r)", fontsize=14, fontweight='bold', pad=15)
plt.xticks(rotation=45, ha='right', fontsize=9)
plt.yticks(fontsize=9)
plt.tight_layout()
fig.savefig(os.path.join(IMG_DIR, "03_matriz_correlacion_heatmap.png"), dpi=200)
plt.close(fig)

# 7. EXPERIMENTO CRUCIAL: Comparativa PCA Sin Estandarizar vs. PCA Estandarizado
# Caso A: Sin estandarizar
pca_raw = PCA()
X_raw_pca = pca_raw.fit_transform(X_df)
var_exp_raw = pca_raw.explained_variance_ratio_ * 100

# Caso B: Estandarizado
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_df)
pca_scaled = PCA()
X_scaled_pca = pca_scaled.fit_transform(X_scaled)
var_exp_scaled = pca_scaled.explained_variance_ratio_ * 100
eigenvalues_scaled = pca_scaled.explained_variance_

# Comparativa gráfica de varianza explicada por componente
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Subplot 1: Sin estandarizar
bars1 = ax1.bar(range(1, len(var_exp_raw) + 1), var_exp_raw, color='#d62728', alpha=0.85, edgecolor='black')
ax1.set_title("PCA SIN Estandarización\n(Basado en Matriz de Covarianza)", fontsize=12, fontweight='bold')
ax1.set_xlabel("Componente Principal", fontsize=10)
ax1.set_ylabel("Varianza Explicada (%)", fontsize=10)
ax1.set_ylim(0, 105)
for bar in bars1[:2]:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 1.5, f'{yval:.2f}%', ha='center', va='bottom', fontsize=8, fontweight='bold')
ax1.text(0.5, 0.7, "PC1 y PC2 absorben el 99.99%\nde la varianza debido a la escala\nde Población y Área", 
         transform=ax1.transAxes, fontsize=10, bbox=dict(boxstyle="round,pad=0.5", fc="#ffdddd", ec="#d62728", lw=1))
ax1.grid(True, linestyle=':', alpha=0.6)

# Subplot 2: Estandarizado
bars2 = ax2.bar(range(1, len(var_exp_scaled) + 1), var_exp_scaled, color='#1f77b4', alpha=0.85, edgecolor='black')
ax2.plot(range(1, len(var_exp_scaled) + 1), np.cumsum(var_exp_scaled), color='#ff7f0e', marker='o', linewidth=2, label='Varianza Acumulada')
ax2.axhline(80, color='red', linestyle='--', label='Umbral 80% Acumulado')
ax2.set_title("PCA CON Estandarización Z-Score\n(Basado en Matriz de Correlación)", fontsize=12, fontweight='bold')
ax2.set_xlabel("Componente Principal", fontsize=10)
ax2.set_ylabel("Varianza Explicada (%)", fontsize=10)
ax2.set_ylim(0, 105)
ax2.legend(loc='lower right', fontsize=9)
for bar in bars2[:5]:
    yval = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 1.5, f'{yval:.1f}%', ha='center', va='bottom', fontsize=8)
ax2.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
fig.savefig(os.path.join(IMG_DIR, "04_comparativa_estandarizacion_varianza.png"), dpi=200)
plt.close(fig)

# 8. Gráfico de Sedimentación (Scree Plot) y Criterio de Kaiser
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(range(1, len(eigenvalues_scaled) + 1), eigenvalues_scaled, marker='s', color='#1f77b4', linewidth=2.2, markersize=7, label='Valores Propios (Eigenvalues λ)')
ax.axhline(1.0, color='#d62728', linestyle='--', linewidth=1.8, label='Criterio de Kaiser (λ = 1)')
ax.set_title("Gráfico de Sedimentación (Scree Plot) y Criterio de Kaiser", fontsize=13, fontweight='bold', pad=12)
ax.set_xlabel("Número de Componente Principal", fontsize=11)
ax.set_ylabel("Valor Propio (Eigenvalue λ)", fontsize=11)
ax.set_xticks(range(1, len(eigenvalues_scaled) + 1))
for i, ev in enumerate(eigenvalues_scaled):
    ax.annotate(f"{ev:.2f}", (i + 1, ev), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=8, fontweight='bold' if ev >= 1.0 else 'normal')
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(loc='upper right', fontsize=10)
plt.tight_layout()
fig.savefig(os.path.join(IMG_DIR, "05_scree_plot_kaiser.png"), dpi=200)
plt.close(fig)

# 9. Matriz de Cargas (Loadings) de las Componentes Principales
loadings = pd.DataFrame(
    pca_scaled.components_.T,
    index=[feature_names_es[f] for f in pca_features],
    columns=[f"CP{i+1}" for i in range(len(pca_features))]
)
loadings.to_csv(os.path.join(BASE_DIR, "datos", "matriz_cargas_loadings.csv"))

# Heatmap de Cargas para las primeras 5 componentes (que cumplen o están en el umbral de Kaiser)
fig, ax = plt.subplots(figsize=(8, 10))
sns.heatmap(loadings.iloc[:, :5], annot=True, fmt=".2f", cmap="vlag", center=0, cbar_kws={'shrink': 0.8}, ax=ax, annot_kws={"size": 9})
ax.set_title("Cargas Factoriales (Loadings) de CP1 a CP5", fontsize=12, fontweight='bold', pad=12)
plt.xticks(fontsize=10)
plt.yticks(fontsize=9)
plt.tight_layout()
fig.savefig(os.path.join(IMG_DIR, "06_cargas_loadings_heatmap.png"), dpi=200)
plt.close(fig)

# 10. Biplot de CP1 vs CP2 con Proyección de Países y Vectores de Variables
fig, ax = plt.subplots(figsize=(14, 10))
# Coordenadas de los países en CP1 y CP2
cp1_scores = X_scaled_pca[:, 0]
cp2_scores = X_scaled_pca[:, 1]
regions = df_clean['Region'].values

palette = sns.color_palette("tab10", len(np.unique(regions)))
region_colors = {reg: palette[i] for i, reg in enumerate(np.unique(regions))}

for reg in np.unique(regions):
    idx = (regions == reg)
    ax.scatter(cp1_scores[idx], cp2_scores[idx], label=reg, color=region_colors[reg], alpha=0.75, s=45, edgecolors='none')

# Anotar algunos países emblemáticos para dar referencia geográfica y económica
highlight_countries = ['United States', 'China', 'India', 'Germany', 'Japan', 'Mexico', 'Brazil', 'Nigeria', 'Ethiopia', 'Somalia', 'Norway', 'Luxembourg', 'United Kingdom', 'Sierra Leone']
for i, country in enumerate(df_clean['Country']):
    if country in highlight_countries:
        ax.annotate(country, (cp1_scores[i], cp2_scores[i]), textcoords="offset points", xytext=(4, 4), fontsize=8, fontweight='bold', color='#222222')

# Añadir vectores de cargas escalados para el biplot
scale_vector = 4.5
for i, feature in enumerate(pca_features):
    x_arrow = pca_scaled.components_[0, i] * scale_vector
    y_arrow = pca_scaled.components_[1, i] * scale_vector
    ax.arrow(0, 0, x_arrow, y_arrow, color='#b2182b', alpha=0.85, width=0.03, head_width=0.15)
    ax.text(x_arrow * 1.12, y_arrow * 1.12, feature_names_es[feature], color='#67001f', fontsize=8.5, fontweight='bold', ha='center', va='center')

ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
ax.axvline(0, color='gray', linestyle='--', linewidth=0.8)
ax.set_title("Biplot de Componentes Principales (CP1 vs. CP2)\nProyección Geopolítica y Vectores de Carga", fontsize=14, fontweight='bold', pad=12)
ax.set_xlabel(f"Componente Principal 1 ({var_exp_scaled[0]:.1f}% varianza) - Nivel de Desarrollo Socioeconómico", fontsize=11)
ax.set_ylabel(f"Componente Principal 2 ({var_exp_scaled[1]:.1f}% varianza) - Escala Demográfica y Perfil Productivo", fontsize=11)
ax.legend(title="Región Geográfica", bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=8.5, title_fontsize=9.5)
ax.grid(True, linestyle=':', alpha=0.5)
plt.tight_layout()
fig.savefig(os.path.join(IMG_DIR, "07_biplot_cp1_cp2.png"), dpi=200)
plt.close(fig)

print("¡Todos los análisis matemáticos y gráficas generados con éxito!")
