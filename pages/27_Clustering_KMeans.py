"""
AGROVISION — Clustering Spatial K-Means
Ziua 27 | Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu

Scop:
    Aplica K-Means clustering pe parcelele LPIS Gorj
    dupa coordonate geografice + suprafata + vegetatie.
    Identifica zone cu profil de risc PAC similar.
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import io
import random

# ─── CONFIGURARE PAGINA ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Clustering K-Means | AGROVISION",
    page_icon="Clustering",
    layout="wide"
)

# ─── DATE LPIS GORJ ───────────────────────────────────────────────────────────
PARCELE = [
    {"cod": "GJ_78258-1675", "fermier": "Popescu Ion",      "suprafata": 4.32,
     "cultura": "grau",       "uat": "Targu Jiu",      "lat": 45.0421, "lon": 23.2718},
    {"cod": "GJ_78301-0892", "fermier": "Ionescu Maria",    "suprafata": 6.78,
     "cultura": "porumb",     "uat": "Rovinari",       "lat": 44.9183, "lon": 23.1645},
    {"cod": "GJ_78445-2341", "fermier": "Dumitrescu Gh.",   "suprafata": 3.15,
     "cultura": "rapita",     "uat": "Motru",          "lat": 44.8067, "lon": 22.9876},
    {"cod": "GJ_78512-0077", "fermier": "Stanescu Petre",   "suprafata": 8.90,
     "cultura": "grau",       "uat": "Bumbesti-Jiu",   "lat": 45.1823, "lon": 23.3912},
    {"cod": "GJ_78634-1129", "fermier": "Olteanu Vasile",   "suprafata": 2.44,
     "cultura": "lucerna",    "uat": "Novaci",         "lat": 45.3012, "lon": 23.6734},
    {"cod": "GJ_78720-3388", "fermier": "Marinescu Ana",    "suprafata": 5.67,
     "cultura": "floarea",    "uat": "Targu Jiu",      "lat": 45.0198, "lon": 23.2456},
    {"cod": "GJ_79001-0445", "fermier": "Petrescu Dan",     "suprafata": 7.23,
     "cultura": "grau",       "uat": "Turceni",        "lat": 44.8734, "lon": 23.4012},
    {"cod": "GJ_79234-1876", "fermier": "Constantin Gh.",   "suprafata": 1.98,
     "cultura": "lucerna",    "uat": "Aninoasa",       "lat": 45.0867, "lon": 23.5219},
    {"cod": "GJ_79567-2290", "fermier": "Florescu Elena",   "suprafata": 9.45,
     "cultura": "porumb",     "uat": "Rovinari",       "lat": 44.9045, "lon": 23.1823},
    {"cod": "GJ_80980-2611", "fermier": "Draghici Marin",   "suprafata": 6.64,
     "cultura": "lucerna",    "uat": "Targu Jiu",      "lat": 45.0534, "lon": 23.2901},
]

CULORI_CLUSTER = [
    "#E74C3C",  # rosu
    "#3498DB",  # albastru
    "#2ECC71",  # verde
    "#F39C12",  # portocaliu
    "#9B59B6",  # violet
]

CULTURI_ICON = {
    "grau":    "[grau]",
    "porumb":  "[porumb]",
    "rapita":  "[rapita]",
    "floarea": "[floarea-soarelui]",
    "pasune":  "[pasune]",
    "lucerna": "[lucerna]",
}


def genereaza_date(seed: int = 42) -> pd.DataFrame:
    """Adauga coloane simulate: vegetatie, sol_gol, apa, ndvi_sim."""
    rng = random.Random(seed)
    df = pd.DataFrame(PARCELE)
    df["vegetatie"] = [round(rng.uniform(30, 85), 1) for _ in range(len(df))]
    df["sol_gol"]   = [round(rng.uniform(5, 35), 1)  for _ in range(len(df))]
    df["apa"]       = (100 - df["vegetatie"] - df["sol_gol"]).clip(0).round(1)
    df["ndvi_sim"]  = ((df["vegetatie"] - 30) / 55 * 0.6 + 0.2).round(3)
    df["status"]    = df["vegetatie"].apply(lambda v: "CONFORM" if v >= 50 else "NECONFORM")
    return df


def aplica_kmeans(df: pd.DataFrame, k: int, features: list) -> pd.DataFrame:
    """Scalare + K-Means. Returneaza df cu coloana 'cluster'."""
    X = df[features].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    df = df.copy()
    df["cluster"] = km.fit_predict(X_scaled)
    if k >= 2 and len(df) > k:
        df.attrs["silhouette"] = round(silhouette_score(X_scaled, df["cluster"]), 3)
    else:
        df.attrs["silhouette"] = None
    df.attrs["inertia"] = round(km.inertia_, 2)
    return df


def harta_clustere(df: pd.DataFrame) -> folium.Map:
    """Harta Folium cu marcatori colorati dupa cluster."""
    centru_lat = df["lat"].mean()
    centru_lon = df["lon"].mean()
    m = folium.Map(location=[centru_lat, centru_lon], zoom_start=10,
                   tiles="CartoDB positron")

    for _, row in df.iterrows():
        culoare = CULORI_CLUSTER[int(row["cluster"]) % len(CULORI_CLUSTER)]
        popup_text = (
            f"<b>{row['cod']}</b><br>"
            f"Fermier: {row['fermier']}<br>"
            f"Cultura: {row['cultura']}<br>"
            f"Suprafata: {row['suprafata']} ha<br>"
            f"Vegetatie: {row['vegetatie']}%<br>"
            f"Cluster: <b>{int(row['cluster'])}</b><br>"
            f"Status: {row['status']}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=12,
            color=culoare,
            fill=True,
            fill_color=culoare,
            fill_opacity=0.8,
            popup=folium.Popup(popup_text, max_width=250),
            tooltip=f"Cluster {int(row['cluster'])} - {row['fermier']}"
        ).add_to(m)

    # Legenda simpla (HTML)
    clustere_unice = sorted(df["cluster"].unique())
    legenda_html = (
        '<div style="position:fixed;bottom:30px;left:30px;z-index:1000;'
        'background:white;padding:10px;border-radius:6px;'
        'border:1px solid #ccc;font-size:13px;">'
        "<b>Clustere K-Means</b><br>"
    )
    for c in clustere_unice:
        culoare = CULORI_CLUSTER[int(c) % len(CULORI_CLUSTER)]
        n = int((df["cluster"] == c).sum())
        legenda_html += (
            f'<span style="color:{culoare};font-size:16px;">&#9679;</span>'
            f" Cluster {c} ({n} parcele)<br>"
        )
    legenda_html += "</div>"
    m.get_root().html.add_child(folium.Element(legenda_html))

    return m


def grafic_scatter(df: pd.DataFrame, x_col: str, y_col: str) -> go.Figure:
    """Scatter plot interactiv cu clustere colorate."""
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        color=df["cluster"].astype(str),
        color_discrete_sequence=CULORI_CLUSTER,
        text="fermier",
        symbol="cultura",
        size="suprafata",
        size_max=20,
        hover_data=["cod", "uat", "status"],
        labels={x_col: x_col.replace("_", " ").title(),
                y_col: y_col.replace("_", " ").title(),
                "color": "Cluster"},
        title=f"Clustering K-Means: {x_col} vs {y_col}"
    )
    fig.update_traces(textposition="top center", textfont_size=9)
    fig.update_layout(
        plot_bgcolor="#F8F9FA",
        paper_bgcolor="white",
        font_family="Arial",
        height=420,
        legend_title_text="Cluster"
    )
    return fig


def grafic_elbow(df_orig: pd.DataFrame, features: list) -> go.Figure:
    """Metoda cotului pentru alegerea k optim (k=2..6)."""
    X = df_orig[features].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    inertii = []
    silhouettes = []
    ks = list(range(2, min(7, len(df_orig))))
    for k in ks:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertii.append(km.inertia_)
        silhouettes.append(silhouette_score(X_scaled, labels))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ks, y=inertii,
        mode="lines+markers",
        name="Inertie (WCSS)",
        line=dict(color="#E74C3C", width=2),
        marker=dict(size=8)
    ))
    fig.add_trace(go.Scatter(
        x=ks, y=[s * max(inertii) for s in silhouettes],
        mode="lines+markers",
        name="Silhouette (scalat)",
        line=dict(color="#3498DB", width=2, dash="dash"),
        marker=dict(size=8),
        yaxis="y2"
    ))
    fig.update_layout(
        title="Metoda Cotului - Alegerea k Optim",
        xaxis_title="Numar clustere (k)",
        yaxis_title="Inertie (WCSS)",
        yaxis2=dict(title="Silhouette Score", overlaying="y", side="right",
                    range=[0, 1]),
        height=380,
        legend=dict(x=0.6, y=0.95),
        plot_bgcolor="#F8F9FA"
    )
    return fig


def export_excel(df: pd.DataFrame) -> bytes:
    """Export DataFrame cu clustere in Excel."""
    buf = io.BytesIO()
    cols = ["cod", "fermier", "uat", "cultura", "suprafata",
            "vegetatie", "sol_gol", "apa", "ndvi_sim", "status", "cluster"]
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df[cols].to_excel(writer, sheet_name="Clustere_LPIS", index=False)
        rezumat = df.groupby("cluster").agg(
            n_parcele=("cod", "count"),
            suprafata_totala=("suprafata", "sum"),
            vegetatie_medie=("vegetatie", "mean"),
            ndvi_mediu=("ndvi_sim", "mean")
        ).round(2)
        rezumat.to_excel(writer, sheet_name="Rezumat_Clustere")
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFATA STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════════

st.title("Ziua 27 - Clustering Spatial K-Means")
st.markdown(
    "**Identificare zone cu profil de risc PAC similar** "
    "folosind Machine Learning nesupervizat pe parcelele LPIS Gorj."
)

# ─── SIDEBAR CONFIGURARE ──────────────────────────────────────────────────────
with st.sidebar:
    st.header("Configurare K-Means")

    k = st.slider(
        "Numar clustere (k)",
        min_value=2, max_value=5, value=3,
        help="Cate grupuri vrei sa formezi?"
    )

    toate_features = ["lat", "lon", "suprafata", "vegetatie", "ndvi_sim"]
    features_alese = st.multiselect(
        "Variabile pentru clustering",
        options=toate_features,
        default=["lat", "lon", "vegetatie"],
        help="Selecteaza ce caracteristici foloseste K-Means"
    )
    if len(features_alese) < 2:
        st.warning("Selecteaza minim 2 variabile.")
        features_alese = ["lat", "lon", "vegetatie"]

    seed = st.number_input("Seed date simulate", value=42, step=1)

    st.divider()
    st.markdown("**Culturi prezente:**")
    st.markdown("- Grau, Porumb, Rapita")
    st.markdown("- Floarea-soarelui, Lucerna")
    st.caption(
        "Lucerna este frecventa in judetul Gorj "
        "ca furaj pentru cresterea animalelor."
    )

# ─── DATE SI CLUSTERING ───────────────────────────────────────────────────────
df_baza = genereaza_date(int(seed))
df = aplica_kmeans(df_baza, k, features_alese)

# KPI-uri
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Parcele totale", len(df))
with col2:
    st.metric("Clustere formate", k)
with col3:
    sil = df.attrs.get("silhouette")
    st.metric("Silhouette Score", f"{sil:.3f}" if sil else "N/A",
              help="Valori aproape de 1 = clustere bine separate")
with col4:
    neconf = int((df["status"] == "NECONFORM").sum())
    st.metric("Neconforme PAC", neconf,
              delta=f"-{neconf} din {len(df)}")

st.divider()

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab_harta, tab_scatter, tab_elbow, tab_tabel, tab_teorie = st.tabs([
    "Harta Clustere",
    "Scatter Plot",
    "Metoda Cotului",
    "Tabel & Export",
    "Teorie ML"
])

# ── TAB 1: HARTA ──────────────────────────────────────────────────────────────
with tab_harta:
    st.subheader("Harta Parcelelor pe Clustere")
    st.caption(
        "Fiecare culoare reprezinta un cluster. "
        "Click pe un marcator pentru detalii."
    )
    m = harta_clustere(df)
    st_folium(m, width=None, height=480)

    st.markdown("#### Compozitie clustere")
    rezumat_cols = st.columns(k)
    for idx, c in enumerate(sorted(df["cluster"].unique())):
        sub = df[df["cluster"] == c]
        culoare = CULORI_CLUSTER[int(c) % len(CULORI_CLUSTER)]
        with rezumat_cols[idx % k]:
            fermieri = ", ".join(sub["fermier"].tolist())
            st.markdown(
                f'<div style="border-left:4px solid {culoare};'
                f'padding:8px 12px;margin-bottom:6px;'
                f'background:#FAFAFA;border-radius:4px">'
                f"<b>Cluster {c}</b><br>"
                f"{sub['uat'].nunique()} UAT-uri | "
                f"{sub['suprafata'].sum():.1f} ha<br>"
                f"<small>{fermieri}</small>"
                f"</div>",
                unsafe_allow_html=True
            )

# ── TAB 2: SCATTER ────────────────────────────────────────────────────────────
with tab_scatter:
    st.subheader("Scatter Plot Interactiv")

    col_x, col_y = st.columns(2)
    with col_x:
        x_var = st.selectbox(
            "Axa X", options=toate_features,
            index=toate_features.index("vegetatie")
        )
    with col_y:
        y_var = st.selectbox(
            "Axa Y", options=toate_features,
            index=toate_features.index("suprafata")
        )

    if x_var == y_var:
        st.warning("Alege variabile diferite pentru cele doua axe.")
    else:
        fig_scatter = grafic_scatter(df, x_var, y_var)
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("#### Vegetatie medie per cluster")
    fig_bar = px.bar(
        df.groupby("cluster")["vegetatie"].mean().reset_index(),
        x="cluster", y="vegetatie",
        color="cluster",
        color_discrete_sequence=CULORI_CLUSTER,
        labels={"cluster": "Cluster", "vegetatie": "Vegetatie medie (%)"},
        text_auto=".1f"
    )
    fig_bar.add_hline(y=50, line_dash="dash", line_color="red",
                      annotation_text="Prag PAC 50%")
    fig_bar.update_layout(showlegend=False, height=320,
                          plot_bgcolor="#F8F9FA")
    st.plotly_chart(fig_bar, use_container_width=True)

# ── TAB 3: ELBOW ──────────────────────────────────────────────────────────────
with tab_elbow:
    st.subheader("Metoda Cotului - Alegerea k Optim")
    st.markdown(
        """
**Cum citesti graficul?**
- **Inertia (WCSS)** scade pe masura ce k creste
- **Silhouette Score** masoara cat de bine separate sunt clusterele (0-1)
- **k optim** = punctul de 'cot' din curba inertiei
        """
    )
    fig_elbow = grafic_elbow(df_baza, features_alese)
    st.plotly_chart(fig_elbow, use_container_width=True)

    st.info(
        f"Pentru setul curent de date (10 parcele, {len(features_alese)} variabile): "
        f"**k recomandat = 3** (compromis intre granularitate si interpretabilitate)."
    )

# ── TAB 4: TABEL & EXPORT ─────────────────────────────────────────────────────
with tab_tabel:
    st.subheader("Tabel Parcele cu Clustere Asignate")

    clustere_disponibile = sorted(df["cluster"].unique().tolist())
    cluster_filtru = st.multiselect(
        "Filtreaza dupa cluster",
        options=clustere_disponibile,
        default=clustere_disponibile
    )
    df_filtrat = df[df["cluster"].isin(cluster_filtru)]

    cols_afisate = ["cod", "fermier", "uat", "cultura",
                    "suprafata", "vegetatie", "status", "cluster"]

    def color_row(row):
        culoare_hex = CULORI_CLUSTER[int(row["cluster"]) % len(CULORI_CLUSTER)]
        r = int(culoare_hex[1:3], 16)
        g = int(culoare_hex[3:5], 16)
        b = int(culoare_hex[5:7], 16)
        return [f"background-color: rgba({r},{g},{b},0.15)"] * len(row)

    st.dataframe(
        df_filtrat[cols_afisate]
        .style.apply(color_row, axis=1)
        .format({"suprafata": "{:.2f} ha", "vegetatie": "{:.1f}%"}),
        use_container_width=True,
        height=360
    )

    st.markdown(f"**{len(df_filtrat)}** parcele afisate din {len(df)} total.")

    st.markdown("#### Export rezultate")
    excel_data = export_excel(df)
    st.download_button(
        label="Descarca Excel (clustere + rezumat)",
        data=excel_data,
        file_name="agrovision_clustere_kmeans.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    st.markdown("#### Statistici per cluster")
    rezumat_stat = df.groupby("cluster").agg(
        Parcele=("cod", "count"),
        Suprafata_ha=("suprafata", "sum"),
        Vegetatie_medie=("vegetatie", "mean"),
        NDVI_mediu=("ndvi_sim", "mean"),
        Neconforme=("status", lambda x: (x == "NECONFORM").sum())
    ).round(2)
    st.dataframe(rezumat_stat, use_container_width=True)

# ── TAB 5: TEORIE ─────────────────────────────────────────────────────────────
with tab_teorie:
    st.subheader("Teorie - K-Means in Agricultura de Precizie")

    st.markdown(
        """
### Ce este K-Means?

K-Means este un algoritm de **clustering nesupervizat** care grupeaza
observatii in **k clustere** astfel incat suma patratelor distantelor
de la fiecare punct la centrul clusterului sau (WCSS) sa fie minima.

### Algoritmul (5 pasi)

1. **Initializare** - alege k centroizi aleatoriu (sau cu K-Means++)
2. **Asignare** - fiecare punct se asigneaza la cel mai apropiat centroid
3. **Actualizare** - recalculeaza centroizii ca medie a punctelor din cluster
4. **Repetare** - repeta pasii 2-3 pana convergenta
5. **Evaluare** - calculeaza WCSS si Silhouette Score

### Aplicatii in agricultura

| Aplicatie | Variabile de clustering | Utilitate APIA |
|-----------|------------------------|----------------|
| Zone cu risc PAC similar | lat, lon, vegetatie | Prioritizare control teren |
| Profile de cultura | suprafata, NDVI, sol | Grupare parcele similare |
| Zone furajere | lat, lon, lucerna % | Planificare subventii zootehnie |
| Harte de productivitate | NDVI_sim, suprafata | Estimare subventii |

### Nota privind lucerna in judetul Gorj

Lucerna (*Medicago sativa*) este cultivata frecvent in Gorj ca furaj
pentru bovine si ovine. In contextul PAC, parcelele cu lucerna se
incadreaza la **pajisti temporare** sau **culturi furajere**, cu
cerinte specifice de conformitate GAEC (Bunele Conditii Agricole
si de Mediu).

### Referinte bibliografice

- MacQueen, J.B. (1967). *Some methods for classification and analysis
  of multivariate observations*. Proceedings of 5th Berkeley Symposium,
  University of California Press, pp. 281-297.
- Rousseeuw, P.J. (1987). *Silhouettes: A graphical aid to the
  interpretation and validation of cluster analysis*. Journal of
  Computational and Applied Mathematics, 20, 53-65.
- Liakos, K.G. et al. (2018). *Machine Learning in Agriculture: A
  Review*. Sensors, 18(8), 2674.
- Pedregosa, F. et al. (2011). *Scikit-learn: Machine Learning in
  Python*. JMLR 12, pp. 2825-2830.
        """
    )

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Ziua 27 - AGROVISION | K-Means Clustering | "
    "scikit-learn + Folium + Plotly | "
    "Prof. Asoc. Dr. Oliviu Mihnea Gamulescu, UCB Targu Jiu 2026"
)
