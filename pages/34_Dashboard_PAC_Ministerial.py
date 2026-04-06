"""
AGROVISION — Dashboard PAC Ministerial
Ziua 34 | Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu

Scop:
    Dashboard de nivel ministerial/judetean cu KPI-uri PAC,
    statistici culturi, conformitate si plati simulate
    pentru judetul Gorj — campania 2024.

    Util pentru:
    - Raportare APIA Gorj → APIA Central
    - Prezentari Prefectura / Consiliu Judetean
    - Cercetare academica UCB (date reprezentative)

Sursa date: simulate pe baza structurii reale LPIS Gorj.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from folium import plugins
from streamlit_folium import st_folium
from datetime import date
import io

# ─── CONFIGURARE PAGINA ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard PAC Ministerial | AGROVISION",
    page_icon="PAC",
    layout="wide"
)

# ─── DATE SIMULATE GORJ — CAMPANIA 2024 ───────────────────────────────────────
# Structura reala a judetului Gorj: 70 UAT-uri, ~18.000 fermieri
# Date reprezentative, scala redusa pentru demo

np.random.seed(42)

UAT_GORJ = [
    {"uat": "Targu Jiu",     "lat": 45.042, "lon": 23.272, "tip": "municipiu"},
    {"uat": "Rovinari",      "lat": 44.918, "lon": 23.165, "tip": "oras"},
    {"uat": "Motru",         "lat": 44.807, "lon": 22.988, "tip": "oras"},
    {"uat": "Bumbesti-Jiu",  "lat": 45.182, "lon": 23.391, "tip": "oras"},
    {"uat": "Novaci",        "lat": 45.301, "lon": 23.673, "tip": "oras"},
    {"uat": "Turceni",       "lat": 44.873, "lon": 23.401, "tip": "comuna"},
    {"uat": "Aninoasa",      "lat": 45.087, "lon": 23.522, "tip": "comuna"},
    {"uat": "Balesti",       "lat": 44.971, "lon": 23.489, "tip": "comuna"},
    {"uat": "Carbunesti",    "lat": 44.956, "lon": 23.527, "tip": "oras"},
    {"uat": "Tismana",       "lat": 45.033, "lon": 22.992, "tip": "comuna"},
    {"uat": "Sacelele",      "lat": 45.118, "lon": 23.197, "tip": "comuna"},
    {"uat": "Vladuleni",     "lat": 44.842, "lon": 23.317, "tip": "comuna"},
]

CULTURI = ["grau", "porumb", "rapita", "floarea_soarelui",
           "lucerna", "pasune", "orz", "triticale"]

PLATII_BAZA = {   # EUR/ha — plata de baza PAC 2024 (simulate)
    "grau":             185,
    "porumb":           175,
    "rapita":           190,
    "floarea_soarelui": 172,
    "lucerna":          160,
    "pasune":           110,
    "orz":              178,
    "triticale":        165,
}

def genereaza_date_campanie(an: int) -> pd.DataFrame:
    """Genereaza date simulate pentru campania PAC a anului dat."""
    np.random.seed(an)           # seed diferit per an pentru variatie
    rand = np.random.RandomState(an)

    rows = []
    fermier_id = 1
    for uat_info in UAT_GORJ:
        n_fermieri = rand.randint(40, 120)
        for _ in range(n_fermieri):
            cultura = rand.choice(CULTURI, p=[0.25,0.22,0.08,0.07,0.12,0.15,0.07,0.04])
            suprafata = round(rand.uniform(0.5, 25.0), 2)
            ndvi      = round(rand.uniform(0.2, 0.85), 3)
            conform   = rand.random() > 0.18   # 82% rata conformitate
            risc      = rand.choice([1, 2, 3], p=[0.55, 0.30, 0.15])

            plata_baza  = suprafata * PLATII_BAZA[cultura]
            plata_verde = suprafata * rand.uniform(40, 65) if conform else 0
            plata_totala = plata_baza + plata_verde if conform else plata_baza * 0.3

            rows.append({
                "fermier_id":    f"GJ{an}-{fermier_id:05d}",
                "uat":           uat_info["uat"],
                "lat":           uat_info["lat"] + rand.uniform(-0.05, 0.05),
                "lon":           uat_info["lon"] + rand.uniform(-0.05, 0.05),
                "cultura":       cultura,
                "suprafata":     suprafata,
                "ndvi":          ndvi,
                "conform":       conform,
                "risc":          risc,
                "plata_baza":    round(plata_baza, 2),
                "plata_verde":   round(plata_verde, 2),
                "plata_totala":  round(plata_totala, 2),
                "an":            an,
            })
            fermier_id += 1

    return pd.DataFrame(rows)


# ─── CACHE DATE ───────────────────────────────────────────────────────────────
@st.cache_data
def date_campanie(an: int) -> pd.DataFrame:
    return genereaza_date_campanie(an)


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFATA STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════════

st.title("Ziua 34 - Dashboard PAC Ministerial")
st.markdown(
    "**Statistici judetene Gorj** — campanie PAC, plati, conformitate, "
    "culturi. Date simulate reprezentative, structura reala LPIS."
)

# ─── SIDEBAR FILTRE ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtre Dashboard")

    an_ales = st.selectbox(
        "Campania agricola",
        options=[2024, 2023, 2022],
        index=0
    )

    st.divider()

    uaturi_disp = ["Toate"] + [u["uat"] for u in UAT_GORJ]
    uat_ales = st.selectbox("UAT", options=uaturi_disp)

    culturi_disp = ["Toate"] + CULTURI
    cultura_aleasa = st.selectbox("Cultura", options=culturi_disp)

    st.divider()
    arata_neconforme = st.checkbox("Evidentiaza neconforme", value=True)
    st.divider()
    st.caption(f"Date simulate Gorj — Campania {an_ales}")
    st.caption("Structura reala LPIS, valori reprezentative")

# ─── INCARCA SI FILTREAZA DATE ────────────────────────────────────────────────
df_full = date_campanie(an_ales)

df = df_full.copy()
if uat_ales != "Toate":
    df = df[df["uat"] == uat_ales]
if cultura_aleasa != "Toate":
    df = df[df["cultura"] == cultura_aleasa]

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "KPI Judetean",
    "Culturi & Suprafete",
    "Plati PAC",
    "Conformitate & Risc",
    "Harta UAT"
])


# ── TAB 1: KPI JUDETEAN ───────────────────────────────────────────────────────
with tab1:
    st.subheader(f"Indicatori Cheie — Campania PAC {an_ales} | Gorj")

    total_fermieri   = len(df)
    sup_totala       = df["suprafata"].sum()
    plata_totala_jud = df["plata_totala"].sum()
    rata_conform     = df["conform"].mean() * 100
    nr_neconforme    = (~df["conform"]).sum()
    plata_medie_ha   = df["plata_totala"].sum() / df["suprafata"].sum() if sup_totala > 0 else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div style='background:white;border-radius:10px;padding:18px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.08);
                    border-top:4px solid #0052A5;text-align:center;'>
            <div style='font-size:32px;font-weight:800;color:#0052A5;'>
                {total_fermieri:,}
            </div>
            <div style='font-size:13px;color:#666;'>Fermieri inregistrati</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style='background:white;border-radius:10px;padding:18px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.08);
                    border-top:4px solid #28a745;text-align:center;'>
            <div style='font-size:32px;font-weight:800;color:#28a745;'>
                {sup_totala:,.0f}
            </div>
            <div style='font-size:13px;color:#666;'>Hectare declarate</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div style='background:white;border-radius:10px;padding:18px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.08);
                    border-top:4px solid #fd7e14;text-align:center;'>
            <div style='font-size:32px;font-weight:800;color:#fd7e14;'>
                {plata_totala_jud:,.0f}
            </div>
            <div style='font-size:13px;color:#666;'>EUR plati totale PAC</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    c4, c5, c6 = st.columns(3)
    with c4:
        culoare_conf = "#28a745" if rata_conform >= 80 else "#dc3545"
        st.markdown(f"""
        <div style='background:white;border-radius:10px;padding:18px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.08);
                    border-top:4px solid {culoare_conf};text-align:center;'>
            <div style='font-size:32px;font-weight:800;color:{culoare_conf};'>
                {rata_conform:.1f}%
            </div>
            <div style='font-size:13px;color:#666;'>Rata conformitate PAC</div>
        </div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div style='background:white;border-radius:10px;padding:18px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.08);
                    border-top:4px solid #dc3545;text-align:center;'>
            <div style='font-size:32px;font-weight:800;color:#dc3545;'>
                {nr_neconforme:,}
            </div>
            <div style='font-size:13px;color:#666;'>Cereri neconforme</div>
        </div>""", unsafe_allow_html=True)
    with c6:
        st.markdown(f"""
        <div style='background:white;border-radius:10px;padding:18px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.08);
                    border-top:4px solid #6f42c1;text-align:center;'>
            <div style='font-size:32px;font-weight:800;color:#6f42c1;'>
                {plata_medie_ha:.0f}
            </div>
            <div style='font-size:13px;color:#666;'>EUR/ha plata medie</div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    # Comparatie inter-anuala
    st.subheader("Comparatie inter-anuala (2022-2024)")
    ani_comp = [2022, 2023, 2024]
    comp_rows = []
    for an in ani_comp:
        df_an = date_campanie(an)
        comp_rows.append({
            "An": str(an),
            "Fermieri": len(df_an),
            "Suprafata (ha)": round(df_an["suprafata"].sum(), 0),
            "Plati EUR": round(df_an["plata_totala"].sum(), 0),
            "Conformitate (%)": round(df_an["conform"].mean() * 100, 1),
        })

    df_comp = pd.DataFrame(comp_rows)

    fig_comp = make_subplots(
        rows=1, cols=3,
        subplot_titles=["Fermieri", "Suprafata (ha)", "Plati (EUR)"]
    )
    culori_ani = ["#adb5bd", "#6c757d", "#0052A5"]
    for i, (coloana, row, col) in enumerate([
        ("Fermieri", 1, 1), ("Suprafata (ha)", 1, 2), ("Plati EUR", 1, 3)
    ]):
        fig_comp.add_trace(
            go.Bar(
                x=df_comp["An"],
                y=df_comp[coloana],
                marker_color=culori_ani,
                name=coloana,
                showlegend=False,
                text=df_comp[coloana].apply(lambda v: f"{v:,.0f}"),
                textposition="outside"
            ),
            row=row, col=col
        )

    fig_comp.update_layout(height=350, margin=dict(t=40, b=10))
    st.plotly_chart(fig_comp, use_container_width=True)

    st.dataframe(
        df_comp.style.highlight_max(axis=0, color="#d4edda",
                                     subset=["Fermieri","Suprafata (ha)","Plati EUR"]),
        use_container_width=True,
        hide_index=True
    )


# ── TAB 2: CULTURI & SUPRAFETE ────────────────────────────────────────────────
with tab2:
    st.subheader("Distributia Culturilor si Suprafetelor")

    # Sumar per cultura
    df_cultura = (
        df.groupby("cultura")
        .agg(
            nr_fermieri=("fermier_id", "count"),
            suprafata_ha=("suprafata", "sum"),
            ndvi_mediu=("ndvi", "mean"),
            plata_totala=("plata_totala", "sum")
        )
        .reset_index()
        .sort_values("suprafata_ha", ascending=False)
    )

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        fig_pie = px.pie(
            df_cultura,
            values="suprafata_ha",
            names="cultura",
            title="Distributie suprafata pe culturi (ha)",
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.35
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(showlegend=True, height=380)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_g2:
        fig_bar_c = px.bar(
            df_cultura,
            x="cultura",
            y="suprafata_ha",
            color="cultura",
            title="Suprafata totala pe cultura (ha)",
            color_discrete_sequence=px.colors.qualitative.Set2,
            text_auto=".0f"
        )
        fig_bar_c.update_layout(showlegend=False, height=380,
                                  xaxis_title="Cultura",
                                  yaxis_title="Suprafata (ha)")
        st.plotly_chart(fig_bar_c, use_container_width=True)

    st.divider()

    # Suprafata per UAT
    df_uat = (
        df.groupby("uat")
        .agg(
            nr_fermieri=("fermier_id", "count"),
            suprafata_ha=("suprafata", "sum"),
            plata_totala=("plata_totala", "sum"),
            rata_conform=("conform", "mean")
        )
        .reset_index()
        .sort_values("suprafata_ha", ascending=False)
    )
    df_uat["rata_conform"] = (df_uat["rata_conform"] * 100).round(1)
    df_uat["suprafata_ha"] = df_uat["suprafata_ha"].round(1)
    df_uat["plata_totala"] = df_uat["plata_totala"].round(0)

    fig_uat = px.bar(
        df_uat,
        x="uat",
        y="suprafata_ha",
        color="rata_conform",
        color_continuous_scale=["#dc3545", "#ffc107", "#28a745"],
        title="Suprafata declarata per UAT — colorat dupa rata conformitate (%)",
        text_auto=".0f"
    )
    fig_uat.update_layout(height=400, xaxis_tickangle=-30,
                           coloraxis_colorbar_title="Conform %")
    st.plotly_chart(fig_uat, use_container_width=True)

    # Tabel sumar per UAT
    st.markdown("#### Tabel sumar per UAT")
    st.dataframe(
        df_uat.rename(columns={
            "uat": "UAT",
            "nr_fermieri": "Fermieri",
            "suprafata_ha": "Suprafata (ha)",
            "plata_totala": "Plati (EUR)",
            "rata_conform": "Conform (%)"
        }).style.background_gradient(
            subset=["Conform (%)"],
            cmap="RdYlGn",
            vmin=60, vmax=100
        ).format({
            "Suprafata (ha)": "{:.1f}",
            "Plati (EUR)": "{:,.0f}",
            "Conform (%)": "{:.1f}%"
        }),
        use_container_width=True,
        hide_index=True
    )


# ── TAB 3: PLATI PAC ──────────────────────────────────────────────────────────
with tab3:
    st.subheader("Analiza Plati PAC")

    col_p1, col_p2 = st.columns(2)

    with col_p1:
        # Distributie plata totala per fermier
        fig_hist = px.histogram(
            df,
            x="plata_totala",
            nbins=40,
            title="Distributia platilor per fermier (EUR)",
            color_discrete_sequence=["#0052A5"],
            labels={"plata_totala": "Plata totala (EUR)", "count": "Nr. fermieri"}
        )
        fig_hist.update_layout(height=380)
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_p2:
        # Plata medie per cultura
        df_plata_c = (
            df.groupby("cultura")["plata_totala"]
            .mean()
            .reset_index()
            .sort_values("plata_totala", ascending=True)
        )
        fig_plata_bar = px.bar(
            df_plata_c,
            x="plata_totala",
            y="cultura",
            orientation="h",
            title="Plata medie per fermier/cultura (EUR)",
            color="plata_totala",
            color_continuous_scale=["#adb5bd", "#0052A5"],
            text_auto=".0f"
        )
        fig_plata_bar.update_layout(height=380, showlegend=False,
                                     coloraxis_showscale=False)
        st.plotly_chart(fig_plata_bar, use_container_width=True)

    st.divider()

    # Plata totala per UAT
    df_plata_uat = (
        df.groupby("uat")
        .agg(
            plata_baza=("plata_baza", "sum"),
            plata_verde=("plata_verde", "sum"),
            plata_totala=("plata_totala", "sum")
        )
        .reset_index()
        .sort_values("plata_totala", ascending=False)
    )

    fig_stacked = px.bar(
        df_plata_uat,
        x="uat",
        y=["plata_baza", "plata_verde"],
        title="Structura platilor per UAT — Plata de baza vs. Plata verde (EUR)",
        barmode="stack",
        color_discrete_map={
            "plata_baza":  "#0052A5",
            "plata_verde": "#28a745"
        },
        labels={"value": "EUR", "variable": "Tip plata"},
        text_auto=False
    )
    fig_stacked.update_layout(height=400, xaxis_tickangle=-30)
    st.plotly_chart(fig_stacked, use_container_width=True)

    # Metrici cheie plati
    st.divider()
    mp1, mp2, mp3, mp4 = st.columns(4)
    with mp1:
        st.metric("Plata de baza totala",
                  f"{df['plata_baza'].sum():,.0f} EUR")
    with mp2:
        st.metric("Plata verde totala",
                  f"{df['plata_verde'].sum():,.0f} EUR")
    with mp3:
        st.metric("Plata medie / fermier",
                  f"{df['plata_totala'].mean():,.0f} EUR")
    with mp4:
        st.metric("Plata maxima / fermier",
                  f"{df['plata_totala'].max():,.0f} EUR")


# ── TAB 4: CONFORMITATE & RISC ────────────────────────────────────────────────
with tab4:
    st.subheader("Conformitate si Risc PAC")

    col_r1, col_r2 = st.columns(2)

    with col_r1:
        # Pie conformitate
        conf_counts = df["conform"].value_counts().reset_index()
        conf_counts["conform"] = conf_counts["conform"].map(
            {True: "CONFORM", False: "NECONFORM"}
        )
        fig_conf = px.pie(
            conf_counts,
            values="count",
            names="conform",
            title="Conformitate cereri PAC",
            color="conform",
            color_discrete_map={
                "CONFORM":    "#28a745",
                "NECONFORM":  "#dc3545"
            },
            hole=0.4
        )
        fig_conf.update_layout(height=360)
        st.plotly_chart(fig_conf, use_container_width=True)

    with col_r2:
        # Distributie risc
        risc_map = {1: "SCAZUT", 2: "MEDIU", 3: "RIDICAT"}
        df_risc = df.copy()
        df_risc["risc_label"] = df_risc["risc"].map(risc_map)
        risc_counts = df_risc["risc_label"].value_counts().reset_index()

        fig_risc = px.bar(
            risc_counts,
            x="risc_label",
            y="count",
            color="risc_label",
            title="Distributia riscului PAC",
            color_discrete_map={
                "SCAZUT":   "#28a745",
                "MEDIU":    "#ffc107",
                "RIDICAT":  "#dc3545"
            },
            text_auto=True,
            category_orders={"risc_label": ["SCAZUT", "MEDIU", "RIDICAT"]}
        )
        fig_risc.update_layout(height=360, showlegend=False,
                                 xaxis_title="Nivel risc",
                                 yaxis_title="Nr. cereri")
        st.plotly_chart(fig_risc, use_container_width=True)

    st.divider()

    # Neconforme per cultura
    df_neconf = (
        df[~df["conform"]]
        .groupby("cultura")
        .agg(nr=("fermier_id", "count"), sup=("suprafata", "sum"))
        .reset_index()
        .sort_values("nr", ascending=False)
    )

    if not df_neconf.empty:
        fig_nc = px.scatter(
            df_neconf,
            x="cultura",
            y="nr",
            size="sup",
            color="sup",
            title="Cereri NECONFORME per cultura (marime bulb = suprafata afectata ha)",
            color_continuous_scale=["#ffc107", "#dc3545"],
            labels={"nr": "Nr. cereri", "sup": "Suprafata (ha)"},
            text="nr"
        )
        fig_nc.update_traces(textposition="top center")
        fig_nc.update_layout(height=380)
        st.plotly_chart(fig_nc, use_container_width=True)

    # Tabel risc per UAT
    df_risc_uat = (
        df.groupby("uat")
        .agg(
            total=("fermier_id", "count"),
            neconforme=("conform", lambda x: (~x).sum()),
            risc_ridicat=("risc", lambda x: (x == 3).sum()),
        )
        .reset_index()
    )
    df_risc_uat["% neconf"] = (
        df_risc_uat["neconforme"] / df_risc_uat["total"] * 100
    ).round(1)
    df_risc_uat["% risc rid"] = (
        df_risc_uat["risc_ridicat"] / df_risc_uat["total"] * 100
    ).round(1)

    st.markdown("#### Risc per UAT")

    def color_pct(val):
        if val > 25:
            return "background-color:#f8d7da;color:#721c24;font-weight:bold"
        if val > 15:
            return "background-color:#fff3cd;color:#856404"
        return "background-color:#d4edda;color:#155724"

    st.dataframe(
        df_risc_uat.rename(columns={
            "uat": "UAT", "total": "Total cereri",
            "neconforme": "Neconforme", "risc_ridicat": "Risc ridicat",
            "% neconf": "% Neconf.", "% risc rid": "% Risc rid."
        })
        .sort_values("% Neconf.", ascending=False)
        .style
        .map(color_pct, subset=["% Neconf.", "% Risc rid."])
        .format({"% Neconf.": "{:.1f}%", "% Risc rid.": "{:.1f}%"}),
        use_container_width=True,
        hide_index=True
    )

    if arata_neconforme:
        with st.expander("Lista cereri NECONFORME cu risc RIDICAT"):
            df_alert = df[(~df["conform"]) & (df["risc"] == 3)][
                ["fermier_id", "uat", "cultura", "suprafata", "ndvi", "plata_totala"]
            ].sort_values("suprafata", ascending=False)
            st.dataframe(
                df_alert.rename(columns={
                    "fermier_id": "ID Fermier", "uat": "UAT",
                    "cultura": "Cultura", "suprafata": "Sup. (ha)",
                    "ndvi": "NDVI", "plata_totala": "Plata (EUR)"
                }).style.format({"Sup. (ha)": "{:.2f}", "Plata (EUR)": "{:,.0f}"}),
                use_container_width=True,
                hide_index=True
            )


# ── TAB 5: HARTA UAT ──────────────────────────────────────────────────────────
with tab5:
    st.subheader("Harta Statistica per UAT — Gorj")

    # Sumar pentru harta
    df_harta = (
        df_full.groupby("uat")   # folosim df_full (toate UAT-urile)
        .agg(
            fermieri=("fermier_id", "count"),
            suprafata=("suprafata", "sum"),
            plata=("plata_totala", "sum"),
            conform_pct=("conform", "mean"),
        )
        .reset_index()
    )
    df_harta["conform_pct"] = df_harta["conform_pct"] * 100

    # Adauga coordonate
    uat_coords = {u["uat"]: (u["lat"], u["lon"]) for u in UAT_GORJ}
    df_harta["lat"] = df_harta["uat"].map(lambda u: uat_coords.get(u, (45.04, 23.27))[0])
    df_harta["lon"] = df_harta["uat"].map(lambda u: uat_coords.get(u, (45.04, 23.27))[1])

    # Metrica de colorat
    metrica = st.selectbox(
        "Coloreaza dupa",
        ["Conformitate (%)", "Suprafata (ha)", "Plati (EUR)", "Nr. fermieri"]
    )
    metrica_col = {
        "Conformitate (%)": "conform_pct",
        "Suprafata (ha)":   "suprafata",
        "Plati (EUR)":      "plata",
        "Nr. fermieri":     "fermieri"
    }[metrica]

    # Construieste harta Folium
    m_uat = folium.Map(
        location=[45.05, 23.28],
        zoom_start=9,
        tiles="CartoDB positron"
    )

    val_min = df_harta[metrica_col].min()
    val_max = df_harta[metrica_col].max()

    for _, row in df_harta.iterrows():
        # Normalizare 0-1 pentru marime cerc
        norm = (row[metrica_col] - val_min) / (val_max - val_min + 1e-9)
        radius = 12 + norm * 20

        # Culoare dupa rata conformitate
        conf = row["conform_pct"]
        if conf >= 85:
            culoare = "#28a745"
        elif conf >= 75:
            culoare = "#ffc107"
        else:
            culoare = "#dc3545"

        popup_html = f"""
        <div style="font-family:Arial;font-size:12px;min-width:190px;">
            <b style="color:#0052A5">{row['uat']}</b><br>
            Fermieri: <b>{row['fermieri']}</b><br>
            Suprafata: <b>{row['suprafata']:.0f} ha</b><br>
            Plati: <b>{row['plata']:,.0f} EUR</b><br>
            Conformitate: <b style="color:{culoare}">{row['conform_pct']:.1f}%</b>
        </div>
        """
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=culoare,
            fill=True,
            fill_color=culoare,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"{row['uat']} — {row[metrica_col]:,.1f} {metrica}"
        ).add_to(m_uat)

    plugins.Fullscreen(position="topright").add_to(m_uat)
    st_folium(m_uat, width=None, height=500, returned_objects=[])

    st.caption(
        "Marimea cercului = valoarea metricii selectate. "
        "Culoarea = rata conformitate (verde ≥85%, galben ≥75%, rosu <75%)"
    )

    st.divider()

    # Export date agregate
    buf_excel = io.BytesIO()
    with pd.ExcelWriter(buf_excel, engine="openpyxl") as writer:
        df_harta[["uat", "fermieri", "suprafata", "plata", "conform_pct"]].rename(
            columns={
                "uat": "UAT",
                "fermieri": "Nr Fermieri",
                "suprafata": "Suprafata ha",
                "plata": "Plati EUR",
                "conform_pct": "Conformitate pct"
            }
        ).to_excel(writer, sheet_name="Sumar UAT", index=False)

        df_full.to_excel(writer, sheet_name="Date Complete", index=False)

    st.download_button(
        label="Descarca Excel — Date agregate UAT",
        data=buf_excel.getvalue(),
        file_name=f"Dashboard_PAC_Gorj_{an_ales}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )


# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Ziua 34 - AGROVISION | Dashboard PAC Ministerial | "
    "Date simulate reprezentative Gorj | Campania PAC 2022-2024 | "
    "Prof. Asoc. Dr. Oliviu Mihnea Gamulescu, UCB Targu Jiu 2026"
)
