"""
AGROVISION — Predictie Productie Agricola cu Random Forest Regresie
Ziua 29 | Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu

Scop:
    Model de regresie care estimeaza productia (tone/ha) pe parcele LPIS Gorj
    pe baza: NDVI, precipitatii, temperatura, cultura, suprafata.
    Complementar Zilei 28 (clasificare risc PAC).
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import random

# ─── CONFIGURARE PAGINA ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Predictie Productie | AGROVISION",
    page_icon="RF-R",
    layout="wide"
)

# ─── CONSTANTE ────────────────────────────────────────────────────────────────
CULTURI = ["grau", "porumb", "rapita", "floarea", "lucerna", "pasune"]

# Productie medie realista (tone/ha) per cultura — date agronomice Romania
PRODUCTIE_MEDIE = {
    "grau":    5.2,
    "porumb":  7.8,
    "rapita":  3.1,
    "floarea": 2.8,
    "lucerna": 8.5,
    "pasune":  4.0,
}

CULORI_CULTURI = {
    "grau":    "#F4D03F",
    "porumb":  "#E67E22",
    "rapita":  "#F1C40F",
    "floarea": "#F39C12",
    "lucerna": "#27AE60",
    "pasune":  "#2ECC71",
}


def genereaza_dataset(n: int = 150, seed: int = 42) -> pd.DataFrame:
    """
    Genereaza n parcele sintetice cu date agrometeorologice si productie.
    Productia este calculata dupa o formula agronomica simplificata:
      productie = productie_medie * factor_ndvi * factor_precipitatii * factor_temp + zgomot
    """
    rng = random.Random(seed)
    np.random.seed(seed)

    culturi    = [rng.choice(CULTURI) for _ in range(n)]
    suprafete  = np.round(np.random.exponential(5.0, n).clip(0.5, 25), 2)
    ndvi       = np.round(np.random.normal(0.55, 0.15, n).clip(0.1, 0.9), 3)
    precipitatii = np.round(np.random.normal(480, 80, n).clip(250, 750), 1)  # mm/an
    temperatura  = np.round(np.random.normal(11.5, 1.5, n).clip(8, 16), 1)   # grade C

    productii = []
    for i in range(n):
        baza = PRODUCTIE_MEDIE[culturi[i]]
        f_ndvi   = 0.5 + ndvi[i] * 1.0          # NDVI ridicat = productie mai mare
        f_prec   = 0.7 + (precipitatii[i] - 250) / 500 * 0.6
        f_temp   = 1.0 - abs(temperatura[i] - 11) * 0.02
        prod = baza * f_ndvi * f_prec * f_temp
        prod += np.random.normal(0, 0.3)         # zgomot aleatoriu
        productii.append(round(max(0.5, prod), 2))

    df = pd.DataFrame({
        "cultura":       culturi,
        "suprafata":     suprafete,
        "ndvi":          ndvi,
        "precipitatii":  precipitatii,
        "temperatura":   temperatura,
        "productie_tha": productii
    })
    df["productie_totala"] = (df["productie_tha"] * df["suprafata"]).round(2)
    return df


def antreneaza_regresie(df: pd.DataFrame, n_estimators: int,
                        max_depth, seed: int):
    """Antreneaza Random Forest Regressor. Returneaza model + metrici."""
    le = LabelEncoder()
    df = df.copy()
    df["cultura_enc"] = le.fit_transform(df["cultura"])

    features = ["ndvi", "precipitatii", "temperatura", "suprafata", "cultura_enc"]
    X = df[features].values
    y = df["productie_tha"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=seed
    )

    rf = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=seed
    )
    rf.fit(X_train, y_train)
    y_pred = rf.predict(X_test)

    mae  = round(mean_absolute_error(y_test, y_pred), 3)
    rmse = round(np.sqrt(mean_squared_error(y_test, y_pred)), 3)
    r2   = round(r2_score(y_test, y_pred), 4)
    cv   = cross_val_score(rf, X, y, cv=5, scoring="r2")

    return {
        "model":     rf,
        "features":  features,
        "le":        le,
        "X_test":    X_test,
        "y_test":    y_test,
        "y_pred":    y_pred,
        "mae":       mae,
        "rmse":      rmse,
        "r2":        r2,
        "cv_r2":     round(cv.mean(), 4),
        "cv_std":    round(cv.std(), 4),
        "n_train":   len(X_train),
        "n_test":    len(X_test),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFATA STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════════

st.title("Ziua 29 - Predictie Productie Agricola")
st.markdown(
    "**Regresie cu Random Forest** — estimeaza productia (tone/ha) "
    "pe baza de NDVI, precipitatii, temperatura si cultura."
)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Parametri Model")

    n_estimators = st.slider("Arbori (n_estimators)", 10, 200, 100, 10)
    max_depth = st.selectbox("Adancime maxima", [None, 3, 5, 8, 12], index=2)
    seed = st.number_input("Seed", value=42, step=1)
    n_parcele = st.slider("Parcele dataset", 50, 300, 150, 10)

    st.divider()
    st.markdown("**Clasificare vs. Regresie**")
    st.markdown("- Ziua 28: **Ce risc?** (CONFORM/NECONFORM)")
    st.markdown("- Ziua 29: **Cat produce?** (tone/ha)")
    st.divider()
    st.markdown("**Productii medii Gorj:**")
    for cultura, prod in PRODUCTIE_MEDIE.items():
        st.markdown(f"- {cultura}: {prod} t/ha")

# ─── ANTRENARE ────────────────────────────────────────────────────────────────
df = genereaza_dataset(n=n_parcele, seed=int(seed))
result = antreneaza_regresie(df, n_estimators, max_depth, int(seed))

# ─── KPI-URI ──────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("R² Score", f"{result['r2']:.3f}",
              help="1.0 = predictie perfecta. >0.8 = model bun")
with k2:
    st.metric("MAE", f"{result['mae']} t/ha",
              help="Eroare medie absoluta in tone/ha")
with k3:
    st.metric("RMSE", f"{result['rmse']} t/ha",
              help="Penalizeaza erorile mari")
with k4:
    st.metric("CV R² (5-fold)", f"{result['cv_r2']:.3f}",
              delta=f"±{result['cv_std']:.3f}")
with k5:
    prod_medie = round(df["productie_tha"].mean(), 2)
    st.metric("Productie medie", f"{prod_medie} t/ha")

st.divider()

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Predictii vs. Real",
    "Importanta Variabile",
    "Analiza per Cultura",
    "Predictie Parcela Noua",
    "Teorie Regresie"
])

# ── TAB 1: PREDICTII VS. REAL ─────────────────────────────────────────────────
with tab1:
    st.subheader("Predictii vs. Valori Reale")

    df_pred = pd.DataFrame({
        "Real (t/ha)":    result["y_test"],
        "Prezis (t/ha)":  result["y_pred"]
    })
    df_pred["Eroare"] = (df_pred["Prezis (t/ha)"] - df_pred["Real (t/ha)"]).round(3)
    df_pred["Eroare %"] = (df_pred["Eroare"] / df_pred["Real (t/ha)"] * 100).round(1)

    col_scatter, col_hist = st.columns(2)

    with col_scatter:
        fig_scatter = px.scatter(
            df_pred,
            x="Real (t/ha)", y="Prezis (t/ha)",
            color="Eroare",
            color_continuous_scale="RdYlGn_r",
            title=f"Predictii vs. Real (R²={result['r2']:.3f})",
            opacity=0.7
        )
        # Linia perfecta y=x
        lim = [df_pred["Real (t/ha)"].min() * 0.9,
               df_pred["Real (t/ha)"].max() * 1.05]
        fig_scatter.add_trace(go.Scatter(
            x=lim, y=lim,
            mode="lines",
            name="Predictie perfecta",
            line=dict(color="gray", dash="dash", width=1)
        ))
        fig_scatter.update_layout(height=380, plot_bgcolor="#F8F9FA")
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_hist:
        fig_err = px.histogram(
            df_pred, x="Eroare",
            nbins=20,
            title="Distributia Erorilor (t/ha)",
            color_discrete_sequence=["#3498DB"],
            labels={"Eroare": "Eroare (t/ha)", "count": "Frecventa"}
        )
        fig_err.add_vline(x=0, line_dash="dash", line_color="red",
                          annotation_text="Eroare zero")
        fig_err.update_layout(height=380, plot_bgcolor="#F8F9FA")
        st.plotly_chart(fig_err, use_container_width=True)

    st.markdown("#### Primele 15 predictii")
    st.dataframe(
        df_pred.head(15).style.background_gradient(
            subset=["Eroare %"], cmap="RdYlGn_r", vmin=-30, vmax=30
        ).format({"Real (t/ha)": "{:.2f}", "Prezis (t/ha)": "{:.2f}",
                  "Eroare": "{:.3f}", "Eroare %": "{:.1f}%"}),
        use_container_width=True
    )

# ── TAB 2: IMPORTANTA VARIABILE ───────────────────────────────────────────────
with tab2:
    st.subheader("Importanta Variabilelor in Model")

    labels_ro = {
        "ndvi":          "NDVI",
        "precipitatii":  "Precipitatii (mm)",
        "temperatura":   "Temperatura (C)",
        "suprafata":     "Suprafata (ha)",
        "cultura_enc":   "Cultura"
    }
    importances = result["model"].feature_importances_
    names = [labels_ro[f] for f in result["features"]]
    df_imp = pd.DataFrame({"Variabila": names, "Importanta": importances})
    df_imp = df_imp.sort_values("Importanta", ascending=True)

    fig_imp = px.bar(
        df_imp, x="Importanta", y="Variabila",
        orientation="h",
        color="Importanta",
        color_continuous_scale="Greens",
        title="Contributia fiecarei variabile la predictia productiei",
        text=df_imp["Importanta"].round(3)
    )
    fig_imp.update_traces(textposition="outside")
    fig_imp.update_layout(height=360, plot_bgcolor="#F8F9FA",
                          coloraxis_showscale=False)
    st.plotly_chart(fig_imp, use_container_width=True)

    top = result["features"][int(np.argmax(importances))]
    st.info(
        f"**Variabila dominanta:** {labels_ro[top]} "
        f"({importances.max()*100:.1f}% din decizie). "
        f"Aceasta confirma importanta monitorizarii spectrale (NDVI) "
        f"pentru prognoza productiei agricole."
    )

    # Scatter NDVI vs productie
    fig_ndvi = px.scatter(
        df, x="ndvi", y="productie_tha",
        color="cultura",
        color_discrete_map=CULORI_CULTURI,
        trendline="ols",
        title="NDVI vs. Productie per Cultura",
        labels={"ndvi": "NDVI", "productie_tha": "Productie (t/ha)",
                "cultura": "Cultura"},
        opacity=0.6
    )
    fig_ndvi.update_layout(height=400, plot_bgcolor="#F8F9FA")
    st.plotly_chart(fig_ndvi, use_container_width=True)

# ── TAB 3: ANALIZA PER CULTURA ────────────────────────────────────────────────
with tab3:
    st.subheader("Analiza Productiei per Cultura")

    col_box, col_bar = st.columns(2)

    with col_box:
        fig_box = px.box(
            df, x="cultura", y="productie_tha",
            color="cultura",
            color_discrete_map=CULORI_CULTURI,
            title="Distributia Productiei per Cultura",
            labels={"cultura": "Cultura", "productie_tha": "Productie (t/ha)"}
        )
        fig_box.update_layout(showlegend=False, height=380,
                              plot_bgcolor="#F8F9FA")
        st.plotly_chart(fig_box, use_container_width=True)

    with col_bar:
        df_stat = df.groupby("cultura").agg(
            Productie_medie=("productie_tha", "mean"),
            Suprafata_totala=("suprafata", "sum"),
            Productie_totala=("productie_totala", "sum")
        ).round(2).reset_index()

        fig_bar = px.bar(
            df_stat, x="cultura", y="Productie_medie",
            color="cultura",
            color_discrete_map=CULORI_CULTURI,
            title="Productie Medie per Cultura (t/ha)",
            text="Productie_medie"
        )
        fig_bar.update_traces(textposition="outside")
        fig_bar.update_layout(showlegend=False, height=380,
                              plot_bgcolor="#F8F9FA")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("#### Statistici per cultura")
    st.dataframe(
        df_stat.style.background_gradient(
            subset=["Productie_medie"], cmap="Greens"
        ).format({"Productie_medie": "{:.2f} t/ha",
                  "Suprafata_totala": "{:.1f} ha",
                  "Productie_totala": "{:.1f} t"}),
        use_container_width=True
    )

# ── TAB 4: PREDICTIE NOUA ─────────────────────────────────────────────────────
with tab4:
    st.subheader("Estimeaza Productia pentru o Parcela Noua")

    col1, col2 = st.columns(2)
    with col1:
        inp_cultura = st.selectbox("Cultura", CULTURI)
        inp_suprafata = st.number_input("Suprafata (ha)", 0.5, 25.0, 4.5, 0.1)
        inp_ndvi = st.slider("NDVI", 0.10, 0.90, 0.60, 0.01)
    with col2:
        inp_prec = st.number_input("Precipitatii anuale (mm)", 250, 750, 480, 10)
        inp_temp = st.number_input("Temperatura medie (C)", 8.0, 16.0, 11.5, 0.1)

    le_nou = LabelEncoder().fit(CULTURI)
    cultura_enc = int(le_nou.transform([inp_cultura])[0])

    X_nou = np.array([[inp_ndvi, inp_prec, inp_temp,
                       inp_suprafata, cultura_enc]])
    productie_pred = round(float(result["model"].predict(X_nou)[0]), 2)
    productie_totala_pred = round(productie_pred * inp_suprafata, 2)

    culoare = CULORI_CULTURI.get(inp_cultura, "#3498DB")

    st.markdown("---")
    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        st.metric("Productie estimata", f"{productie_pred} t/ha")
    with col_r2:
        st.metric("Productie totala parcela", f"{productie_totala_pred} tone")
    with col_r3:
        medie_cultura = PRODUCTIE_MEDIE[inp_cultura]
        diferenta = round(productie_pred - medie_cultura, 2)
        st.metric("Fata de media nationala",
                  f"{medie_cultura} t/ha",
                  delta=f"{diferenta:+.2f} t/ha")

    # Bara comparatie cu media
    fig_comp = go.Figure(go.Bar(
        x=[inp_cultura + " (prezis)", inp_cultura + " (medie nationala)"],
        y=[productie_pred, PRODUCTIE_MEDIE[inp_cultura]],
        marker_color=[culoare, "#BDC3C7"],
        text=[f"{productie_pred} t/ha", f"{PRODUCTIE_MEDIE[inp_cultura]} t/ha"],
        textposition="outside"
    ))
    fig_comp.update_layout(
        title="Comparatie: Parcela ta vs. Media nationala",
        yaxis_title="Productie (t/ha)",
        height=300, plot_bgcolor="#F8F9FA", showlegend=False
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    if diferenta > 0.5:
        st.success(f"Parcela are productie PESTE medie cu {diferenta:.2f} t/ha. "
                   f"Conditii agrometeorologice favorabile.")
    elif diferenta < -0.5:
        st.warning(f"Parcela are productie SUB medie cu {abs(diferenta):.2f} t/ha. "
                   f"Verifica conditiile de cultura si irigare.")
    else:
        st.info("Parcela are productie in linie cu media nationala.")

# ── TAB 5: TEORIE ─────────────────────────────────────────────────────────────
with tab5:
    st.subheader("Teorie — Regresie vs. Clasificare in ML")

    st.markdown(
        """
### Clasificare vs. Regresie — Distinctia fundamentala

| Aspect | Clasificare (Ziua 28) | Regresie (Ziua 29) |
|--------|----------------------|-------------------|
| **Output** | Clasa discreta | Valoare continua |
| **Exemplu** | CONFORM / NECONFORM | 5.2 tone/ha |
| **Metrica principala** | Accuracy, F1 | R², MAE, RMSE |
| **Algoritm folosit** | RandomForestClassifier | RandomForestRegressor |
| **Aplicatie APIA** | Selectie parcele control | Estimare subventii |

### Metrici de evaluare pentru regresie

**R² (Coeficientul de determinare)**
$$R^2 = 1 - \\frac{\\sum(y_i - \\hat{y}_i)^2}{\\sum(y_i - \\bar{y})^2}$$
- R² = 1.0 → model perfect
- R² = 0.0 → model egal cu media
- R² < 0 → model mai slab decat media

**MAE (Mean Absolute Error)**
$$MAE = \\frac{1}{n}\\sum|y_i - \\hat{y}_i|$$
Interpretare directa: eroare medie in tone/ha

**RMSE (Root Mean Square Error)**
$$RMSE = \\sqrt{\\frac{1}{n}\\sum(y_i - \\hat{y}_i)^2}$$
Penalizeaza erorile mari mai mult decat MAE

### Aplicatie in prognoza agricola

Modelul de regresie poate fi utilizat de APIA pentru:
- **Estimarea subventiei** bazata pe productia prognozata
- **Detectia supradeclararii** — parcele cu productie declarata
  mult peste maximul prognozat de model
- **Planificarea inspectiilor** — prioritizare parcele cu
  discrepante mari intre declarat si prognozat

### Referinte bibliografice

- Breiman, L. (2001). *Random Forests*. Machine Learning, 45(1), 5-32.
- Van Klompenburg, T. et al. (2020). *Crop yield prediction using
  machine learning: A systematic literature review*.
  Computers and Electronics in Agriculture, 177, 105709.
- Liakos, K.G. et al. (2018). *Machine Learning in Agriculture:
  A Review*. Sensors, 18(8), 2674.
        """
    )

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Ziua 29 - AGROVISION | Random Forest Regresie | "
    "scikit-learn + Plotly | "
    "Prof. Asoc. Dr. Oliviu Mihnea Gamulescu, UCB Targu Jiu 2026"
)
