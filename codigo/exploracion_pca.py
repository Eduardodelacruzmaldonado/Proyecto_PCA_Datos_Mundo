"""Exploración de datos y componentes principales (PCA) con el conjunto
"Countries of the World" (Kaggle, fernandol).

El script genera las figuras en ../figuras y los resultados numéricos en
../resultados. Los bloques marcados con "# >>> nombre" / "# <<< nombre" son los
fragmentos que se muestran en el documento PDF.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import SymLogNorm
from sklearn.decomposition import PCA

BASE = Path(__file__).resolve().parent.parent
FIG = BASE / "figuras"
OUT = BASE / "resultados"
FIG.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)

C1, C2 = "#2f4b6e", "#a0522d"
plt.rcParams.update({
    "font.family": "serif", "font.size": 8, "axes.spines.top": False,
    "axes.spines.right": False, "figure.dpi": 200, "savefig.bbox": "tight",
})

NOMBRES = {
    "Population": "Población", "Area (sq. mi.)": "Superficie",
    "Pop. Density (per sq. mi.)": "Densidad de población",
    "Coastline (coast/area ratio)": "Costa / área",
    "Net migration": "Migración neta",
    "Infant mortality (per 1000 births)": "Mortalidad infantil",
    "GDP ($ per capita)": "PIB per cápita", "Literacy (%)": "Alfabetización",
    "Phones (per 1000)": "Teléfonos", "Arable (%)": "Tierra cultivable",
    "Crops (%)": "Cultivos permanentes", "Other (%)": "Otros usos del suelo",
    "Climate": "Clima", "Birthrate": "Natalidad", "Deathrate": "Mortalidad",
    "Agriculture": "Agricultura", "Industry": "Industria", "Service": "Servicios",
}
UNIDADES = {
    "Population": "habitantes", "Area (sq. mi.)": "millas cuadradas",
    "Pop. Density (per sq. mi.)": "hab. por milla cuadrada",
    "Coastline (coast/area ratio)": "razón costa / área",
    "Net migration": "por cada 1000 hab.",
    "Infant mortality (per 1000 births)": "por cada 1000 nacimientos",
    "GDP ($ per capita)": "USD por habitante", "Literacy (%)": "%",
    "Phones (per 1000)": "líneas por cada 1000 hab.", "Arable (%)": "% de la superficie",
    "Crops (%)": "% de la superficie", "Other (%)": "% de la superficie",
    "Birthrate": "por cada 1000 hab.", "Deathrate": "por cada 1000 hab.",
    "Agriculture": "fracción del PIB", "Industry": "fracción del PIB",
    "Service": "fracción del PIB",
}
GRUPO = {
    "SUB-SAHARAN AFRICA": "África", "NORTHERN AFRICA": "África",
    "LATIN AMER. & CARIB": "América", "NORTHERN AMERICA": "América",
    "ASIA (EX. NEAR EAST)": "Asia y Cercano Oriente", "NEAR EAST": "Asia y Cercano Oriente",
    "C.W. OF IND. STATES": "CEI", "EASTERN EUROPE": "Europa",
    "WESTERN EUROPE": "Europa", "BALTICS": "Europa", "OCEANIA": "Oceanía",
}
COLORES = {"África": "#c0392b", "América": "#1b6ca8", "Asia y Cercano Oriente": "#2e8b57",
           "Europa": "#8e44ad", "CEI": "#d68910", "Oceanía": "#6b6b6b"}
res = {}


def iqr_atipicos(s):
    q1, q3 = s.quantile([.25, .75])
    i = q3 - q1
    return s[(s < q1 - 1.5 * i) | (s > q3 + 1.5 * i)]


# >>> carga
raw = pd.read_csv(BASE / "datos" / "countries_of_the_world.csv", decimal=",")
raw.columns = [c.strip() for c in raw.columns]
raw["Country"] = raw["Country"].str.strip()
raw["Region"] = raw["Region"].str.strip()
raw = raw.set_index("Country")
print(raw.shape)
print(raw.dtypes)
print(raw.isna().sum())
# <<< carga
res["n_paises"], res["n_columnas"] = int(raw.shape[0]), int(raw.shape[1] + 1)
res["nulos"] = {NOMBRES.get(k, k): int(v) for k, v in raw.isna().sum().items() if v > 0}

# >>> graficas
NUMERICAS = [c for c in raw.columns if c not in ("Region", "Climate")]


def hist_box(x, titulo, unidad, ruta):
    x = x.dropna()
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.6, 1.9),
                               gridspec_kw={"width_ratios": [2.6, 1.6]})
    a.hist(x, bins=20, color=C1, edgecolor="white", linewidth=.4)
    a.axvline(x.mean(), color=C2, ls="--", lw=1, label=f"media = {x.mean():.4g}")
    a.axvline(x.median(), color="black", lw=1, label=f"mediana = {x.median():.4g}")
    a.set_xlabel(unidad); a.set_ylabel("países"); a.set_title(titulo, loc="left", fontsize=8.5)
    a.legend(frameon=False, fontsize=6.5)
    b.boxplot(x, vert=False, widths=.5, medianprops=dict(color="black"),
              flierprops=dict(marker="o", ms=2.5, mfc="none", mec=C2))
    b.set_yticks([]); b.set_xlabel(unidad)
    fig.tight_layout(); fig.savefig(ruta); plt.close(fig)


estad = []
for i, v in enumerate(NUMERICAS):
    hist_box(raw[v], NOMBRES[v], UNIDADES[v], FIG / f"hb_{i:02d}.png")
    x = raw[v].dropna()
    estad.append({"var": v, "nombre": NOMBRES[v], "archivo": f"hb_{i:02d}.png", "n": int(x.size),
                  "nulos": int(raw[v].isna().sum()), "media": x.mean(), "mediana": x.median(),
                  "asim": x.skew(), "atip": int(len(iqr_atipicos(x))),
                  "min": x.min(), "max": x.max(), "pais_max": x.idxmax()})
# <<< graficas
res["estad_eda"] = estad

fig, (a, b) = plt.subplots(1, 2, figsize=(6.6, 2.4), gridspec_kw={"width_ratios": [1.6, 1]})
rc = raw["Region"].value_counts().sort_values()
a.barh(rc.index, rc.values, color=C1); a.set_xlabel("países"); a.set_title("Región", loc="left")
a.tick_params(axis="y", labelsize=6.5)
cc = raw["Climate"].value_counts(dropna=False).sort_index()
b.bar([("s/d" if pd.isna(k) else f"{k:g}") for k in cc.index], cc.values, color=C1)
b.set_xlabel("tipo de clima"); b.set_ylabel("países"); b.set_title("Clima", loc="left")
fig.tight_layout(); fig.savefig(FIG / "fig_categoricas.png"); plt.close(fig)
res["regiones"] = rc.sort_values(ascending=False).to_dict()
res["clima"] = {("sin dato" if pd.isna(k) else f"{k:g}"): int(v) for k, v in cc.items()}

# >>> faltantes
nulos = raw.isna().sum()
nulos = (100 * nulos[nulos > 0] / len(raw)).sort_values()
fig, ax = plt.subplots(figsize=(5.6, 2.6))
ax.barh([NOMBRES[v] for v in nulos.index], nulos.values, color=C1)
ax.set_xlabel("% de países sin dato")
fig.tight_layout(); fig.savefig(FIG / "fig_faltantes.png")
# <<< faltantes
plt.close(fig)

# >>> seleccion
VARS = ["Pop. Density (per sq. mi.)", "Coastline (coast/area ratio)", "Net migration",
            "Infant mortality (per 1000 births)", "GDP ($ per capita)", "Literacy (%)",
            "Phones (per 1000)", "Arable (%)", "Crops (%)", "Birthrate", "Deathrate",
            "Agriculture", "Service"]
datos = raw[VARS + ["Region"]].copy()
faltan = datos[VARS].isna().sum(axis=1)
eliminados = datos.index[faltan >= 4].tolist()      # más del 30 % de las variables sin dato
datos = datos[faltan < 4].copy()
med_region = datos.groupby("Region")[VARS].transform("median")
datos[VARS] = datos[VARS].fillna(med_region)
datos[VARS] = datos[VARS].fillna(datos[VARS].median())
print("eliminados:", eliminados, "| quedan:", len(datos), "| nulos:", int(datos[VARS].isna().sum().sum()))
# <<< seleccion
res["eliminados"] = eliminados
res["n_final"] = int(len(datos))
res["imputados"] = {NOMBRES[v]: int(raw.loc[datos.index, v].isna().sum()) for v in VARS
                    if raw.loc[datos.index, v].isna().sum() > 0}
res["corr_suma_suelo"] = [float((raw["Arable (%)"] + raw["Crops (%)"] + raw["Other (%)"]).min()),
                          float((raw["Arable (%)"] + raw["Crops (%)"] + raw["Other (%)"]).max())]
suma = (raw["Agriculture"] + raw["Industry"] + raw["Service"]).dropna()
res["suma_sectores"] = [float(suma.min()), float(suma.max())]
r_ind = raw[["Industry", "Agriculture", "Service"]].corr()
res["corr_industria"] = {"Agricultura": float(r_ind.loc["Industry", "Agriculture"]),
                         "Servicios": float(r_ind.loc["Industry", "Service"])}

# >>> transformacion
asim_antes = datos[VARS].skew()
a_log = asim_antes[asim_antes.abs() >= 2].index.tolist()
trans = datos.copy()
for v in a_log:
    trans[v] = np.log10(trans[v] + 1)
asim_despues = trans[VARS].skew()
print(pd.DataFrame({"antes": asim_antes, "despues": asim_despues}).loc[a_log].round(2))
# <<< transformacion
res["a_log"] = [NOMBRES[v] for v in a_log]
res["asim"] = {NOMBRES[v]: [float(asim_antes[v]), float(asim_despues[v])] for v in VARS}

fig, axs = plt.subplots(len(a_log), 2, figsize=(6.2, 1.55 * len(a_log)))
for fila, v in zip(axs, a_log):
    fila[0].hist(datos[v], bins=25, color=C1, edgecolor="white", linewidth=.3)
    fila[1].hist(trans[v], bins=25, color=C2, edgecolor="white", linewidth=.3)
    fila[0].set_title(f"{NOMBRES[v]} (original), asimetría = {asim_antes[v]:.2f}", loc="left", fontsize=7)
    fila[1].set_title(f"log10(x + 1), asimetría = {asim_despues[v]:.2f}", loc="left", fontsize=7)
    fila[0].set_ylabel("países")
fig.tight_layout(); fig.savefig(FIG / "fig_log.png"); plt.close(fig)

# >>> descriptivas
desc = pd.DataFrame({
    "media": datos[VARS].mean(), "mediana": datos[VARS].median(),
    "varianza": datos[VARS].var(), "desv_est": datos[VARS].std(),
    "minimo": datos[VARS].min(), "maximo": datos[VARS].max()})
cov_orig = datos[VARS].cov()             # covarianza en unidades originales
clave = ["GDP ($ per capita)", "Infant mortality (per 1000 births)", "Literacy (%)",
         "Phones (per 1000)", "Birthrate"]
print(desc.round(3))
print(cov_orig.loc[clave, clave].round(1))
# <<< descriptivas
desc.to_csv(OUT / "descriptivas.csv")
res["desc"] = [{"nombre": NOMBRES[v], **{k: float(desc.loc[v, k]) for k in desc.columns}} for v in VARS]
res["cov_clave"] = {"nombres": [NOMBRES[v] for v in clave],
                    "matriz": cov_orig.loc[clave, clave].to_numpy().tolist()}
res["media_gt_mediana"] = [NOMBRES[v] for v in VARS if desc.loc[v, "media"] > desc.loc[v, "mediana"]]

# >>> atipicos
def zscores(df):
    return (df[VARS] - df[VARS].mean()) / df[VARS].std()

at_antes = {v: iqr_atipicos(datos[v]) for v in VARS}
at_despues = {v: iqr_atipicos(trans[v]) for v in VARS}
fig, (a, b) = plt.subplots(1, 2, figsize=(6.6, 3.2), sharey=True)
for ax, df, t in ((a, datos, "Datos depurados"), (b, trans, "Tras la transformación")):
    ax.boxplot(zscores(df).values, vert=False, widths=.6, medianprops=dict(color="black"),
               flierprops=dict(marker="o", ms=2, mfc="none", mec=C2))
    ax.set_title(t, loc="left", fontsize=8); ax.set_xlabel("valor estandarizado (z)")
a.set_yticks(range(1, len(VARS) + 1))
a.set_yticklabels([NOMBRES[v] for v in VARS], fontsize=6.5)
fig.tight_layout(); fig.savefig(FIG / "fig_atipicos.png")
# <<< atipicos
plt.close(fig)
res["atipicos"] = [{"nombre": NOMBRES[v], "antes": int(len(at_antes[v])), "despues": int(len(at_despues[v])),
                    "ejemplos": list(at_antes[v].reindex(
                        (datos[v] - datos[v].median()).abs().loc[at_antes[v].index].sort_values(ascending=False).index
                    ).index[:3])} for v in VARS]

# >>> correlacion
corr = trans[VARS].corr(method="pearson")
etq = [NOMBRES[v] for v in VARS]
fig, ax = plt.subplots(figsize=(6.4, 5.3))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1, vmax=1, square=True,
            linewidths=.3, annot_kws={"size": 5.5}, cbar_kws={"shrink": .7},
            xticklabels=etq, yticklabels=etq, ax=ax)
ax.tick_params(labelsize=6.5)
fig.tight_layout(); fig.savefig(FIG / "fig_corr.png")
# <<< correlacion
plt.close(fig)
cov_t = trans[VARS].cov()
fig, ax = plt.subplots(figsize=(6.4, 5.0))
M = cov_t.to_numpy()
sns.heatmap(cov_t, cmap="RdBu_r", norm=SymLogNorm(linthresh=1, vmin=-M.max(), vmax=M.max()),
            square=True, linewidths=.3, xticklabels=etq, yticklabels=etq, ax=ax,
            cbar_kws={"shrink": .7, "label": "covarianza (escala simétrica logarítmica)"})
ax.tick_params(labelsize=6.5)
fig.tight_layout(); fig.savefig(FIG / "fig_cov.png"); plt.close(fig)
pares = [(NOMBRES[VARS[i]], NOMBRES[VARS[j]], float(corr.iloc[i, j]))
         for i in range(len(VARS)) for j in range(i)]
pares.sort(key=lambda p: -abs(p[2]))
res["pares_fuertes"] = pares[:10]
res["pares_debiles_max"] = [p for p in pares if abs(p[2]) < 0.1][:5]
res["n_pares_08"] = int(sum(abs(p[2]) >= .8 for p in pares))
res["n_pares_05"] = int(sum(abs(p[2]) >= .5 for p in pares))
res["n_pares"] = len(pares)
res["dep"] = []
for v in VARS:
    o = corr[v].drop(v).abs()
    res["dep"].append({"nombre": NOMBRES[v], "r_max": float(corr[v][o.idxmax()]), "con": NOMBRES[o.idxmax()]})

fig, axs = plt.subplots(1, 3, figsize=(6.6, 2.2))
for ax, (x, y) in zip(axs, [("Phones (per 1000)", "GDP ($ per capita)"),
                            ("Birthrate", "Infant mortality (per 1000 births)"),
                            ("Literacy (%)", "Infant mortality (per 1000 births)")]):
    ax.scatter(trans[x], trans[y], s=7, color=C1, alpha=.55, linewidths=0)
    m, b0 = np.polyfit(trans[x], trans[y], 1)
    xs = np.linspace(trans[x].min(), trans[x].max(), 50)
    ax.plot(xs, m * xs + b0, color=C2, lw=1.1)
    ax.set_xlabel(NOMBRES[x]); ax.set_ylabel(NOMBRES[y]); ax.tick_params(labelsize=6.5)
    ax.set_title(f"r = {corr.loc[x, y]:.2f}", loc="left", fontsize=8)
fig.tight_layout(); fig.savefig(FIG / "fig_dependencia.png"); plt.close(fig)

# >>> pca_matrices
X = trans[VARS].to_numpy(float)
Xc = X - X.mean(axis=0)                       # datos centrados
S = np.cov(Xc, rowvar=False)                  # covarianza sin estandarizar
Z = Xc / X.std(axis=0, ddof=1)                # datos estandarizados
R = np.cov(Z, rowvar=False)                   # covarianza de los estandarizados
print("cov(Z) coincide con la matriz de correlación:", np.allclose(R, np.corrcoef(X, rowvar=False)))


def pca_manual(M):
    valores, vectores = np.linalg.eigh(M)
    orden = np.argsort(valores)[::-1]
    valores, vectores = valores[orden], vectores[:, orden]
    for j in range(vectores.shape[1]):        # signo: CP1 con PIB positivo; en las demás, la mayor carga positiva
        ref = VARS.index("GDP ($ per capita)") if j == 0 else np.abs(vectores[:, j]).argmax()
        if vectores[ref, j] < 0:
            vectores[:, j] *= -1
    return valores, vectores


val_s, vec_s = pca_manual(S)                  # sin estandarizar
val_z, vec_z = pca_manual(R)                  # estandarizados
# <<< pca_matrices
res["cov_igual_corr"] = bool(np.allclose(R, np.corrcoef(X, rowvar=False)))
sk = PCA().fit(Z)
res["sklearn_ok"] = bool(np.allclose(sk.explained_variance_, val_z))
rango = pd.DataFrame({"minimo": X.min(axis=0), "maximo": X.max(axis=0)}, index=VARS)
rango["rango"] = rango["maximo"] - rango["minimo"]
rango["varianza"] = X.var(axis=0, ddof=1)
res["rango"] = [{"nombre": NOMBRES[v], **{k: float(rango.loc[v, k]) for k in rango.columns}} for v in VARS]
res["var_total_s"] = float(val_s.sum())
res["part_pib"] = float(rango.loc["GDP ($ per capita)", "varianza"] / rango["varianza"].sum())
res["var_pib"] = float(rango.loc["GDP ($ per capita)", "varianza"])
res["var_min"] = [NOMBRES[rango["varianza"].idxmin()], float(rango["varianza"].min())]

# >>> pca_criterios
p = len(VARS)
prop_z = val_z / val_z.sum()
acum_z = np.cumsum(prop_z)
rng = np.random.default_rng(0)
sim = np.array([np.sort(np.linalg.eigvalsh(np.corrcoef(rng.standard_normal((len(X), p)), rowvar=False)))[::-1]
                for _ in range(500)])
horn = np.percentile(sim, 95, axis=0)         # simulación de Horn (valores propios esperados por azar)
k_kaiser = int((val_z > 1).sum())
k_horn = int((val_z > horn).sum())
k_80 = int(np.argmax(acum_z >= .80) + 1)
k = int(np.median([k_kaiser, k_horn, k_80]))
print("Kaiser:", k_kaiser, "| Horn:", k_horn, "| 80 %:", k_80, "| elegido:", k)
print(np.round(val_z, 2)); print(np.round(100 * acum_z, 1))
# <<< pca_criterios
res.update(k=k, k_kaiser=k_kaiser, k_horn=k_horn, k_80=k_80,
           val_z=val_z.tolist(), prop_z=prop_z.tolist(), acum_z=acum_z.tolist(), horn=horn.tolist())

fig, (a, b) = plt.subplots(1, 2, figsize=(6.6, 2.5))
comp = np.arange(1, p + 1)
a.plot(comp, val_z, "o-", color=C1, ms=3.5, label="valores propios")
a.plot(comp, horn, "s--", color="gray", ms=3, lw=.9, label="simulación de Horn (p. 95)")
a.axhline(1, color=C2, ls=":", lw=1, label="criterio de Kaiser (λ = 1)")
a.set_xlabel("componente"); a.set_ylabel("valor propio"); a.legend(frameon=False, fontsize=6.5)
b.bar(comp, 100 * prop_z, color=C1, label="individual")
b.plot(comp, 100 * acum_z, "o-", color=C2, ms=3, label="acumulada")
b.axhline(80, color="gray", ls=":", lw=1)
b.set_xlabel("componente"); b.set_ylabel("% de la varianza"); b.legend(frameon=False, fontsize=6.5)
fig.tight_layout(); fig.savefig(FIG / "fig_scree.png"); plt.close(fig)

# >>> pca_cargas
cargas = vec_z * np.sqrt(val_z)               # correlación entre variable y componente
CP = [f"CP{i}" for i in range(1, p + 1)]
tabla_cargas = pd.DataFrame(cargas, index=[NOMBRES[v] for v in VARS], columns=CP)
scores_z = Z @ vec_z
off = np.abs(np.cov(scores_z, rowvar=False) - np.diag(val_z)).max()
print(tabla_cargas.iloc[:, :k + 1].round(2))
print("covarianza entre componentes (máx. fuera de la diagonal):", f"{off:.1e}")
# <<< pca_cargas
res["off_diag"] = float(off)
res["cargas"] = {"nombres": list(tabla_cargas.index), "m": tabla_cargas.iloc[:, :5].to_numpy().tolist()}
fig, ax = plt.subplots(figsize=(4.8, 4.0))
sns.heatmap(tabla_cargas.iloc[:, :k + 1], annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1, vmax=1,
            linewidths=.3, annot_kws={"size": 6.5}, cbar_kws={"shrink": .7}, ax=ax)
ax.tick_params(labelsize=7)
fig.tight_layout(); fig.savefig(FIG / "fig_cargas.png"); plt.close(fig)

# >>> pca_biplot
grupos = trans["Region"].map(GRUPO)
fig, ax = plt.subplots(figsize=(6.4, 4.8))
for g, c in COLORES.items():
    m = (grupos == g).to_numpy()
    ax.scatter(scores_z[m, 0], scores_z[m, 1], s=14, color=c, alpha=.75, linewidths=0, label=g)
esc = 0.85 * np.abs(scores_z[:, :2]).max() / np.abs(cargas[:, :2]).max()
for i, v in enumerate(VARS):
    ax.arrow(0, 0, esc * cargas[i, 0], esc * cargas[i, 1], color="black", lw=.6, head_width=.08)
    ax.text(esc * cargas[i, 0] * 1.07, esc * cargas[i, 1] * 1.07, NOMBRES[v], fontsize=6.2)
ax.axhline(0, color="gray", lw=.4); ax.axvline(0, color="gray", lw=.4)
ax.set_xlabel(f"CP1 ({100 * prop_z[0]:.1f} % de la varianza)")
ax.set_ylabel(f"CP2 ({100 * prop_z[1]:.1f} % de la varianza)")
ax.legend(frameon=False, fontsize=6.5, loc="lower left")
fig.tight_layout(); fig.savefig(FIG / "fig_biplot.png")
# <<< pca_biplot
plt.close(fig)
dist = np.hypot(scores_z[:, 0], scores_z[:, 1])
res["extremos_cp12"] = trans.index[np.argsort(dist)[::-1][:6]].tolist()
res["cp1_extremos"] = {"alto": trans.index[np.argsort(scores_z[:, 0])[::-1][:3]].tolist(),
                       "bajo": trans.index[np.argsort(scores_z[:, 0])[:3]].tolist()}
res["grupo_medias_cp1"] = {g: float(scores_z[(grupos == g).to_numpy(), 0].mean()) for g in COLORES}

# >>> comparacion
prop_s = val_s / val_s.sum()
scores_s = Xc @ vec_s
cargas_s = vec_s * np.sqrt(val_s)
r_cp1 = np.corrcoef(scores_s[:, 0], scores_z[:, 0])[0, 1]
print("varianza de CP1 sin estandarizar: %.2f %%" % (100 * prop_s[0]))
print("varianza de CP1 estandarizando:   %.2f %%" % (100 * prop_z[0]))
print("carga de CP1 (sin estandarizar) sobre el PIB:", round(vec_s[VARS.index("GDP ($ per capita)"), 0], 4))
print("correlación entre las puntuaciones de CP1 de ambos casos:", round(r_cp1, 3))
# <<< comparacion
res.update(prop_s=prop_s.tolist(), r_cp1=float(r_cp1), val_s=val_s.tolist(),
           vec_s_pib=float(vec_s[VARS.index("GDP ($ per capita)"), 0]),
           vec_s_phones=float(vec_s[VARS.index("Phones (per 1000)"), 0]),
           k_s_80=int(np.argmax(np.cumsum(prop_s) >= .80) + 1),
           cp1_s=[[NOMBRES[v], float(vec_s[i, 0])] for i, v in enumerate(VARS)])

fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.7))
y = np.arange(p)
axs[0].barh(y - .2, vec_s[:, 0], .4, color=C2, label="sin estandarizar")
axs[0].barh(y + .2, vec_z[:, 0], .4, color=C1, label="estandarizados")
axs[0].set_yticks(y); axs[0].set_yticklabels(etq, fontsize=6.3); axs[0].invert_yaxis()
axs[0].set_xlabel("coeficiente en CP1"); axs[0].legend(frameon=False, fontsize=6.3)
ncomp = 6
x = np.arange(ncomp)
axs[1].bar(x - .2, 100 * prop_s[:ncomp], .4, color=C2, label="sin estandarizar")
axs[1].bar(x + .2, 100 * prop_z[:ncomp], .4, color=C1, label="estandarizados")
axs[1].set_xticks(x); axs[1].set_xticklabels([f"CP{i + 1}" for i in x])
axs[1].set_ylabel("% de la varianza"); axs[1].legend(frameon=False, fontsize=6.3)
fig.tight_layout(); fig.savefig(FIG / "fig_comp_barras.png"); plt.close(fig)

fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.9))
for ax, sc, pr, t in ((axs[0], scores_s, prop_s, "Sin estandarizar"), (axs[1], scores_z, prop_z, "Estandarizados")):
    for g, c in COLORES.items():
        m = (grupos == g).to_numpy()
        ax.scatter(sc[m, 0], sc[m, 1], s=9, color=c, alpha=.75, linewidths=0, label=g)
    ax.set_title(t, loc="left", fontsize=8)
    ax.set_xlabel(f"CP1 ({100 * pr[0]:.1f} %)"); ax.set_ylabel(f"CP2 ({100 * pr[1]:.1f} %)")
axs[1].legend(frameon=False, fontsize=5.8)
fig.tight_layout(); fig.savefig(FIG / "fig_comp_scores.png"); plt.close(fig)

with open(OUT / "resultados.json", "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1,
              default=lambda o: o.item() if hasattr(o, "item") else str(o))
print("listo")
