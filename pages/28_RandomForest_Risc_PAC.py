"""
AGROVISION — Random Forest pentru Detectia Riscului PAC
Ziua 28 | Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu

Scop:
    Antrenare model Random Forest care clasifica parcelele LPIS
    in 3 categorii de risc PAC: CONFORM / RISC MEDIU / RISC RIDICAT.
    Bazat pe: suprafata, vegetatie, NDVI, cultura, cluster K-Means.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    classification_report, confusion_matrix,
    accuracy_score, ConfusionMatrixDisplay
)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import random

# ─── CONFIGURARE PAGINA ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Random Forest Risc PAC | AGROVISION",
    page_icon="RF",
    layout="wide"
)

# ─── CONSTANTE ────────────────────────────────────────────────────────────────
CULTURI = ["grau", "porumb", "rapita", "floarea", "lucerna", "pasune"]
CLASE_RISC = ["CONFORM", "RISC MEDIU", "RISC RIDICAT"]
CULORI_RISC = {
    "CONFORM":      "#2ECC71",
    "RISC MEDIU":   "#F39C12",
    "RISC RIDICAT": "#E74C3C"
}


# ─── GENERARE DATE SINTETICE ──────────────────────────────────────────────────
def genereaza_dataset(n: int = 120, seed: int = 42) -> pd.DataFrame:
    """
    Genereaza n parcele sintetice cu caracteristici realiste.
    Eticheta 'risc_pac' este derivata din reguli APIA:
      - vegetatie < 40% SAU ndvi < 0.25              → RISC RIDICAT
      - vegetatie 40-55% SAU suprafata > 15 ha        → RISC MEDIU
      - altfel                                         → CONFORM
    """
    rng = random.Random(seed)
    np.random.seed(seed)

    suprafete  = np.round(np.random.exponential(scale=5.0, size=n).clip(0.5, 25), 2)
    vegetatii  = np.round(np.random.normal(loc=58, scale=18, size=n).clip(10, 95), 1)
    sol_gol    = np.round(np.random.uniform(3, 30, size=n), 1)
    apa        = np.round((100 - vegetatii - sol_gol).clip(0, 30), 1)
    ndvi       = np.round((vegetatii - 10) / 85 * 0.7 + 0.1 + np.random.normal(0, 0.05, n), 3).clip(0.05, 0.9)
    culturi    = [rng.choice(CULTURI) for _ in range(n)]
    clustere   = [rng.randint(0, 2) for _ in range(n)]

    def clasifica_risc(veg, ndvi_val, sup):
        if veg < 40 or ndvi_val < 0.25:
            return "RISC RIDICAT"
        elif veg < 55 or sup > 15:
            return "RISC MEDIU"
        return "CONFORM"

    risc = [clasifica_risc(v, d, s)
            for v, d, s in zip(vegetatii, ndvi, suprafete)]

    df = pd.DataFrame({
        "suprafata":  suprafete,
        "vegetatie":  vegetatii,
        "sol_gol":    sol_gol,
        "apa":        apa,
        "ndvi_sim":   ndvi,
        "cultura":    culturi,
        "cluster":    clustere,
        "risc_pac":   risc
    })
    return df


def pregateste_features(df: pd.DataFrame):
    """Encode cultura (text→numar) + selectie coloane X si y."""
    df = df.copy()
    le = LabelEncoder()
    df["cultura_enc"] = le.fit_transform(df["cultura"])
    feature_cols = ["suprafata", "vegetatie", "sol_gol", "ndvi_sim",
                    "cultura_enc", "cluster"]
    X = df[feature_cols].values
    le_risc = LabelEncoder()
    le_risc.fit(CLASE_RISC)
    y = le_risc.transform(df["risc_pac"])
    return X, y, feature_cols, le_risc


@st.cache_resource
def antreneaza_model(n_estimators: int, max_depth, seed: int):
    """Antrenare Random Forest pe 120 parcele sintetice (cached)."""
    df = genereaza_dataset(n=120, seed=seed)
    X, y, feature_cols, le_risc = pregateste_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=seed, stratify=y
    )

    rf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=seed,
        class_weight="balanced"
    )
    rf.fit(X_train, y_train)

    y_pred = rf.predict(X_test)
    acc    = accuracy_score(y_test, y_pred)
    cv     = cross_val_score(rf, X, y, cv=5, scoring="accuracy")
    report = classification_report(y_test, y_pred,
                                   target_names=le_risc.classes_,
                                   output_dict=True)
    cm     = confusion_matrix(y_test, y_pred)

    return {
        "model":        rf,
        "feature_cols": feature_cols,
        "le_risc":      le_risc,
        "X_test":       X_test,
        "y_test":       y_test,
        "y_pred":       y_pred,
        "accuracy":     round(acc, 4),
        "cv_mean":      round(cv.mean(), 4),
        "cv_std":       round(cv.std(), 4),
        "report":       report,
        "cm":           cm,
        "n_train":      len(X_train),
        "n_test":       len(X_test),
        "df_train":     df
    }


def figura_importanta_features(result: dict) -> go.Figure:
    """Grafic importanta variabilelor (feature importance)."""
    importances = result["model"].feature_importances_
    labels_ro = {
        "suprafata":    "Suprafata (ha)",
        "vegetatie":    "Vegetatie (%)",
        "sol_gol":      "Sol gol (%)",
        "ndvi_sim":     "NDVI simulat",
        "cultura_enc":  "Cultura",
        "cluster":      "Cluster K-Means"
    }
    names = [labels_ro.get(f, f) for f in result["feature_cols"]]
    df_imp = pd.DataFrame({"feature": names, "importance": importances})
    df_imp = df_imp.sort_values("importance", ascending=True)

    fig = px.bar(
        df_imp, x="importance", y="feature",
        orientation="h",
        color="importance",
        color_continuous_scale="Blues",
        title="Importanta Variabilelor in Random Forest",
        labels={"importance": "Importanta", "feature": "Variabila"}
    )
    fig.update_layout(
        height=360, showlegend=False,
        plot_bgcolor="#F8F9FA",
        coloraxis_showscale=False
    )
    return fig


def figura_confuzie_matplotlib(cm: np.ndarray, clase: list) -> bytes:
    """Matrice de confuzie ca imagine PNG (300 DPI)."""
    fig, ax = plt.subplots(figsize=(5, 4))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm,
                                  display_labels=clase)
    disp.plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title("Matrice de Confuzie")
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def figura_distributie_risc(df: pd.DataFrame) -> go.Figure:
    """Grafic distributie clase risc in dataset."""
    counts = df["risc_pac"].value_counts().reindex(CLASE_RISC, fill_value=0)
    fig = px.bar(
        x=counts.index,
        y=counts.values,
        color=counts.index,
        color_discrete_map=CULORI_RISC,
        title="Distributia Claselor de Risc in Dataset",
        labels={"x": "Clasa Risc", "y": "Nr. Parcele", "color": "Risc"},
        text=counts.values
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False, height=340,
                      plot_bgcolor="#F8F9FA")
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFATA STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════════

st.title("Ziua 28 - Random Forest pentru Detectia Riscului PAC")
st.markdown(
    "**Model de clasificare supervizat** care prezice riscul PAC "
    "al parcelelor LPIS Gorj: CONFORM / RISC MEDIU / RISC RIDICAT."
)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Parametri Random Forest")

    n_estimators = st.slider(
        "Numar de arbori (n_estimators)",
        min_value=10, max_value=200, value=100, step=10,
        help="Mai multi arbori = model mai robust, dar mai lent"
    )
    max_depth = st.selectbox(
        "Adancime maxima (max_depth)",
        options=[None, 3, 5, 8, 12],
        index=2,
        help="None = arbori complet dezvoltati"
    )
    seed = st.number_input("Seed reproductibil", value=42, step=1)
    n_parcele = st.slider(
        "Parcele in dataset",
        min_value=50, max_value=300, value=120, step=10
    )

    st.divider()
    st.markdown("**Reguli clasificare risc APIA:**")
    st.markdown("- Vegetatie < 40% → RISC RIDICAT")
    st.markdown("- NDVI < 0.25 → RISC RIDICAT")
    st.markdown("- Vegetatie 40-55% → RISC MEDIU")
    st.markdown("- Suprafata > 15 ha → RISC MEDIU")
    st.markdown("- Altfel → CONFORM")

# ─── ANTRENARE MODEL ──────────────────────────────────────────────────────────
with st.spinner("Antrenez modelul Random Forest..."):
    # Rebuild dataset cu n_parcele selectat de utilizator
    df_full = genereaza_dataset(n=n_parcele, seed=int(seed))
    X_all, y_all, feature_cols, le_risc = pregateste_features(df_full)
    X_train, X_test, y_train, y_test = train_test_split(
        X_all, y_all, test_size=0.25, random_state=int(seed), stratify=y_all
    )
    rf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=int(seed),
        class_weight="balanced"
    )
    rf.fit(X_train, y_train)
    y_pred   = rf.predict(X_test)
    acc      = accuracy_score(y_test, y_pred)
    cv       = cross_val_score(rf, X_all, y_all, cv=5, scoring="accuracy")
    report   = classification_report(y_test, y_pred,
                                     target_names=le_risc.classes_,
                                     output_dict=True)
    cm       = confusion_matrix(y_test, y_pred)

result = {
    "model": rf, "feature_cols": feature_cols, "le_risc": le_risc,
    "X_test": X_test, "y_test": y_test, "y_pred": y_pred,
    "accuracy": round(acc, 4), "cv_mean": round(cv.mean(), 4),
    "cv_std": round(cv.std(), 4), "report": report, "cm": cm,
    "n_train": len(X_train), "n_test": len(X_test), "df_train": df_full
}

# ─── KPI-URI ──────────────────────────────────────────────────────────────────
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    st.metric("Acuratete Test", f"{result['accuracy']*100:.1f}%")
with kpi2:
    st.metric("CV Accuracy (5-fold)", f"{result['cv_mean']*100:.1f}%",
              delta=f"±{result['cv_std']*100:.1f}%")
with kpi3:
    st.metric("Arbori", n_estimators)
with kpi4:
    st.metric("Parcele antrenament", result["n_train"])
with kpi5:
    st.metric("Parcele test", result["n_test"])

st.divider()

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab_pred, tab_eval, tab_feat, tab_pred_noua, tab_teorie = st.tabs([
    "Date & Distributie",
    "Evaluare Model",
    "Importanta Variabile",
    "Predictie Parcela Noua",
    "Teorie RF"
])

# ── TAB 1: DATE & DISTRIBUTIE ─────────────────────────────────────────────────
with tab_pred:
    st.subheader("Datele de Antrenament")

    col_dist, col_culturi = st.columns(2)
    with col_dist:
        st.plotly_chart(figura_distributie_risc(df_full),
                        use_container_width=True)
    with col_culturi:
        fig_cult = px.histogram(
            df_full, x="cultura", color="risc_pac",
            color_discrete_map=CULORI_RISC,
            barmode="group",
            title="Risc PAC per Cultura",
            labels={"cultura": "Cultura", "count": "Nr. Parcele",
                    "risc_pac": "Risc"}
        )
        fig_cult.update_layout(height=340, plot_bgcolor="#F8F9FA")
        st.plotly_chart(fig_cult, use_container_width=True)

    st.markdown("#### Primele 20 parcele din dataset")
    st.dataframe(
        df_full.head(20).style.map(
            lambda v: f"background-color: {CULORI_RISC.get(v, 'white')}22",
            subset=["risc_pac"]
        ).format({"suprafata": "{:.2f}", "vegetatie": "{:.1f}",
                  "ndvi_sim": "{:.3f}"}),
        use_container_width=True, height=380
    )

# ── TAB 2: EVALUARE ───────────────────────────────────────────────────────────
with tab_eval:
    st.subheader("Evaluarea Performantei Modelului")

    col_cm, col_report = st.columns([1, 1])

    with col_cm:
        st.markdown("**Matrice de Confuzie**")
        cm_img = figura_confuzie_matplotlib(result["cm"],
                                            list(le_risc.classes_))
        st.image(cm_img, use_container_width=True)
        st.caption(
            "Diagonala principala = predictii corecte. "
            "Valorile in afara diagonalei = erori."
        )

    with col_report:
        st.markdown("**Raport per clasa**")
        df_report = pd.DataFrame(result["report"]).T
        df_report = df_report.drop(index=["accuracy", "macro avg",
                                           "weighted avg"], errors="ignore")
        df_report = df_report[["precision", "recall", "f1-score", "support"]]
        df_report.columns = ["Precizie", "Recall", "F1", "Nr. probe"]
        df_report = df_report.round(3)

        def culoare_f1(val):
            if val >= 0.80:
                return "background-color: #d5f5e3"
            elif val >= 0.60:
                return "background-color: #fef9e7"
            else:
                return "background-color: #fadbd8"

        st.dataframe(
            df_report.style.map(culoare_f1, subset=["F1"]),
            use_container_width=True
        )
        st.markdown("---")
        st.markdown(f"**Acuratete globala:** {result['accuracy']*100:.1f}%")
        st.markdown(
            f"**Cross-validation 5-fold:** "
            f"{result['cv_mean']*100:.1f}% "
            f"(±{result['cv_std']*100:.1f}%)"
        )
        st.caption(
            "CV accuracy mai mica decat test accuracy = model robust. "
            "Diferenta mare intre train/test = overfitting."
        )

    # Grafic CV
    st.markdown("#### Stabilitate Cross-Validation")
    cv_scores = cross_val_score(rf, X_all, y_all, cv=5, scoring="accuracy")
    fig_cv = go.Figure(go.Bar(
        x=[f"Fold {i+1}" for i in range(5)],
        y=(cv_scores * 100).round(1),
        text=(cv_scores * 100).round(1),
        textposition="outside",
        marker_color=["#3498DB" if s >= result["cv_mean"] else "#E74C3C"
                      for s in cv_scores]
    ))
    fig_cv.add_hline(y=result["cv_mean"]*100, line_dash="dash",
                     line_color="gray",
                     annotation_text=f"Medie {result['cv_mean']*100:.1f}%")
    fig_cv.update_layout(
        title="Acuratete per Fold (Cross-Validation)",
        yaxis_title="Acuratete (%)", yaxis_range=[0, 105],
        height=320, plot_bgcolor="#F8F9FA", showlegend=False
    )
    st.plotly_chart(fig_cv, use_container_width=True)

# ── TAB 3: IMPORTANTA VARIABILE ───────────────────────────────────────────────
with tab_feat:
    st.subheader("Importanta Variabilelor (Feature Importance)")
    st.markdown(
        "**Gini Importance** — cat de mult reduce fiecare variabila "
        "impuritatea in arbori."
    )
    st.plotly_chart(figura_importanta_features(result),
                    use_container_width=True)

    st.markdown("#### Interpretare")
    importances = rf.feature_importances_
    labels_ro = {
        "suprafata": "Suprafata",
        "vegetatie": "Vegetatie",
        "sol_gol": "Sol gol",
        "ndvi_sim": "NDVI",
        "cultura_enc": "Cultura",
        "cluster": "Cluster K-Means"
    }
    top_feature = feature_cols[int(np.argmax(importances))]
    st.info(
        f"Variabila cea mai importanta: **{labels_ro.get(top_feature, top_feature)}** "
        f"({importances.max()*100:.1f}% din puterea de decizie). "
        f"Aceasta confirma ca informatia spectral-vegetativa este "
        f"decisiva pentru evaluarea conformitatii PAC."
    )

    # Scatter: variabila top vs risc
    fig_top = px.scatter(
        df_full,
        x=top_feature, y="vegetatie",
        color="risc_pac",
        color_discrete_map=CULORI_RISC,
        title=f"Distributia parcelelor: {labels_ro.get(top_feature, top_feature)} vs Vegetatie",
        labels={top_feature: labels_ro.get(top_feature, top_feature),
                "vegetatie": "Vegetatie (%)", "risc_pac": "Risc PAC"},
        opacity=0.7
    )
    fig_top.add_hline(y=40, line_dash="dash", line_color="#E74C3C",
                      annotation_text="Prag risc ridicat 40%")
    fig_top.add_hline(y=55, line_dash="dot", line_color="#F39C12",
                      annotation_text="Prag risc mediu 55%")
    fig_top.update_layout(height=400, plot_bgcolor="#F8F9FA")
    st.plotly_chart(fig_top, use_container_width=True)

# ── TAB 4: PREDICTIE NOUA ─────────────────────────────────────────────────────
with tab_pred_noua:
    st.subheader("Prezice Riscul PAC pentru o Parcela Noua")
    st.markdown(
        "Introdu caracteristicile parcelei si modelul va prezice "
        "nivelul de risc PAC in timp real."
    )

    col_in1, col_in2 = st.columns(2)
    with col_in1:
        inp_suprafata  = st.number_input("Suprafata (ha)", 0.5, 25.0, 4.5, 0.1)
        inp_vegetatie  = st.number_input("Vegetatie detectata (%)", 10.0, 95.0, 62.0, 0.5)
        inp_sol_gol    = st.number_input("Sol gol (%)", 1.0, 40.0, 15.0, 0.5)
    with col_in2:
        inp_ndvi       = st.number_input("NDVI simulat", 0.05, 0.90, 0.55, 0.01)
        inp_cultura    = st.selectbox("Cultura", options=CULTURI)
        inp_cluster    = st.selectbox("Cluster K-Means", options=[0, 1, 2])

    le_cult = LabelEncoder().fit(CULTURI)
    inp_cultura_enc = int(le_cult.transform([inp_cultura])[0])

    X_nou = np.array([[
        inp_suprafata, inp_vegetatie, inp_sol_gol,
        inp_ndvi, inp_cultura_enc, inp_cluster
    ]])

    proba = rf.predict_proba(X_nou)[0]
    clasa_idx = int(np.argmax(proba))
    clasa_pred = le_risc.classes_[clasa_idx]
    culoare_pred = CULORI_RISC[clasa_pred]
    confidenta = round(proba[clasa_idx] * 100, 1)

    st.markdown("---")
    st.markdown(
        f'<div style="background-color:{culoare_pred}33;'
        f'border-left:6px solid {culoare_pred};'
        f'padding:16px 20px;border-radius:6px;">'
        f'<h3 style="color:{culoare_pred};margin:0">Predictie: {clasa_pred}</h3>'
        f'<p style="margin:4px 0 0 0">Confidenta: <b>{confidenta}%</b></p>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Probabilitati per clasa
    st.markdown("#### Probabilitati per clasa")
    fig_proba = go.Figure(go.Bar(
        x=list(le_risc.classes_),
        y=(proba * 100).round(1),
        text=(proba * 100).round(1),
        textposition="outside",
        marker_color=[CULORI_RISC[c] for c in le_risc.classes_]
    ))
    fig_proba.update_layout(
        yaxis_title="Probabilitate (%)", yaxis_range=[0, 110],
        height=300, plot_bgcolor="#F8F9FA", showlegend=False
    )
    st.plotly_chart(fig_proba, use_container_width=True)

    # Recomandare inspector
    recomandari = {
        "CONFORM":      "Parcela nu necesita control prioritar. "
                        "Mentineti in planul de monitorizare standard.",
        "RISC MEDIU":   "Parcela necesita verificare documentara. "
                        "Solicitati fotografii georeferentiate fermierului.",
        "RISC RIDICAT": "Parcela necesita CONTROL PE TEREN urgent. "
                        "Initiati procedura conform Reg. UE 2021/2116 art. 68."
    }
    st.warning(f"**Recomandare APIA:** {recomandari[clasa_pred]}")

# ── TAB 5: TEORIE ─────────────────────────────────────────────────────────────
with tab_teorie:
    st.subheader("Teorie - Random Forest in Agricultura de Precizie")

    st.markdown(
        """
### Ce este Random Forest?

**Random Forest** (Breiman, 2001) este un ansamblu de **arbori de decizie**
antrenati independent pe subseturi aleatorii ale datelor (bootstrap).
Predictia finala = **votul majoritatii** arborilor (clasificare)
sau media (regresie).

### Avantaje fata de un singur arbore de decizie

| Proprietate | Arbore unic | Random Forest |
|-------------|-------------|---------------|
| Varianta | Ridicata (overfitting) | Scazuta (bagging) |
| Bias | Scazut | Scazut |
| Interpretabilitate | Mare | Medie (feature importance) |
| Robustete la outlieri | Slaba | Buna |
| Performanta | Medie | Ridicata |

### Hiperparametri principali

- **n_estimators** — numarul de arbori (recomandare: 100-300)
- **max_depth** — adancimea maxima; None = arbori complet crescuti
- **class_weight="balanced"** — corecteaza dezechilibrul de clase
  (important cand avem mai multe parcele CONFORM decat RISC RIDICAT)
- **random_state** — reproductibilitate rezultate

### Feature Importance (Gini)

$$FI_j = \\sum_{t: split on j} p(t) \\cdot \\Delta I(t)$$

unde $p(t)$ = proportia probelor ce ajung in nodul $t$
si $\\Delta I$ = scaderea impuritatii Gini.

### Aplicatie directa APIA Gorj

Modelul antrenat poate fi utilizat pentru **selectia automata** a parcelelor
cu prioritate de control, reducand costurile de inspectie si concentrand
resursele inspectorilor pe parcelele cu risc PAC real.

In conformitate cu **Regulamentul (UE) 2021/2116**, statele membre
pot utiliza instrumente de analize bazate pe date (RPAS/UAV + AI)
pentru selectia parcelelor la control.

### Referinte bibliografice

- Breiman, L. (2001). *Random Forests*. Machine Learning, 45(1), 5-32.
- Liakos, K.G. et al. (2018). *Machine Learning in Agriculture: A Review*.
  Sensors, 18(8), 2674.
- European Commission (2021). Regulation (EU) 2021/2116 on the financing,
  management and monitoring of the common agricultural policy.
  Official Journal of the European Union, L 435.
- Pedregosa, F. et al. (2011). *Scikit-learn: Machine Learning in Python*.
  JMLR 12, pp. 2825-2830.
        """
    )

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Ziua 28 - AGROVISION | Random Forest Risc PAC | "
    "scikit-learn + Plotly + matplotlib | "
    "Prof. Asoc. Dr. Oliviu Mihnea Gamulescu, UCB Targu Jiu 2026"
)
