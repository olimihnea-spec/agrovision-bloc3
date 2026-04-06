"""
AGROVISION — Analiza Spatiala Avansata
Ziua 32 | Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu

Scop:
    Analiza spatiala a parcelelor LPIS Gorj:
    - Heatmap densitate parcele neconforme
    - Calcul distante GPS intre parcele
    - Clustering spatial pentru planificarea rutei de inspectie
    - Zone de risc PAC identificate pe harta
    Direct utilizabil la APIA pentru prioritizarea inspectiilor teren.
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium import plugins
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import math
import json
import io

# ─── CONFIGURARE PAGINA ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Analiza Spatiala | AGROVISION",
    page_icon="SA",
    layout="wide"
)

# ─── DATE LPIS GORJ (extinse cu risc si NDVI) ────────────────────────────────
PARCELE = [
    {"cod": "GJ_78258-1675", "fermier": "Popescu Ion",      "suprafata": 4.32,
     "cultura": "grau",    "uat": "Targu Jiu",    "lat": 45.0421, "lon": 23.2718,
     "vegetatie": 72.3, "ndvi": 0.61, "status": "CONFORM",   "risc": 1},
    {"cod": "GJ_78301-0892", "fermier": "Ionescu Maria",    "suprafata": 6.78,
     "cultura": "porumb",  "uat": "Rovinari",     "lat": 44.9183, "lon": 23.1645,
     "vegetatie": 65.1, "ndvi": 0.54, "status": "CONFORM",   "risc": 1},
    {"cod": "GJ_78445-2341", "fermier": "Dumitrescu Gh.",   "suprafata": 3.15,
     "cultura": "rapita",  "uat": "Motru",        "lat": 44.8067, "lon": 22.9876,
     "vegetatie": 31.2, "ndvi": 0.22, "status": "NECONFORM", "risc": 3},
    {"cod": "GJ_78512-0077", "fermier": "Stanescu Petre",   "suprafata": 8.90,
     "cultura": "grau",    "uat": "Bumbesti-Jiu", "lat": 45.1823, "lon": 23.3912,
     "vegetatie": 78.4, "ndvi": 0.68, "status": "CONFORM",   "risc": 1},
    {"cod": "GJ_78634-1129", "fermier": "Olteanu Vasile",   "suprafata": 2.44,
     "cultura": "lucerna", "uat": "Novaci",       "lat": 45.3012, "lon": 23.6734,
     "vegetatie": 82.1, "ndvi": 0.73, "status": "CONFORM",   "risc": 1},
    {"cod": "GJ_78720-3388", "fermier": "Marinescu Ana",    "suprafata": 5.67,
     "cultura": "floarea", "uat": "Targu Jiu",    "lat": 45.0198, "lon": 23.2456,
     "vegetatie": 43.7, "ndvi": 0.31, "status": "NECONFORM", "risc": 3},
    {"cod": "GJ_79001-0445", "fermier": "Petrescu Dan",     "suprafata": 7.23,
     "cultura": "grau",    "uat": "Turceni",      "lat": 44.8734, "lon": 23.4012,
     "vegetatie": 58.9, "ndvi": 0.48, "status": "CONFORM",   "risc": 2},
    {"cod": "GJ_79234-1876", "fermier": "Constantin Gh.",   "suprafata": 1.98,
     "cultura": "lucerna", "uat": "Aninoasa",     "lat": 45.0867, "lon": 23.5219,
     "vegetatie": 76.2, "ndvi": 0.65, "status": "CONFORM",   "risc": 1},
    {"cod": "GJ_79567-2290", "fermier": "Florescu Elena",   "suprafata": 9.45,
     "cultura": "porumb",  "uat": "Rovinari",     "lat": 44.9045, "lon": 23.1823,
     "vegetatie": 37.8, "ndvi": 0.26, "status": "NECONFORM", "risc": 3},
    {"cod": "GJ_80980-2611", "fermier": "Draghici Marin",   "suprafata": 6.64,
     "cultura": "lucerna", "uat": "Targu Jiu",    "lat": 45.0534, "lon": 23.2901,
     "vegetatie": 69.5, "ndvi": 0.58, "status": "CONFORM",   "risc": 1},
]

CULORI_RISC = {1: "#28a745", 2: "#ffc107", 3: "#dc3545"}
ETICHETE_RISC = {1: "SCAZUT", 2: "MEDIU", 3: "RIDICAT"}


def distanta_km(lat1, lon1, lat2, lon2) -> float:
    """Calculeaza distanta Haversine intre doua puncte GPS (km)."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)
    return round(R * 2 * math.asin(math.sqrt(a)), 2)


def matrice_distante(parcele: list) -> pd.DataFrame:
    """Calculeaza matricea de distante intre toate parcelele."""
    n = len(parcele)
    mat = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                mat[i][j] = distanta_km(
                    parcele[i]["lat"], parcele[i]["lon"],
                    parcele[j]["lat"], parcele[j]["lon"]
                )
    coduri = [p["cod"].split("-")[0] for p in parcele]
    return pd.DataFrame(mat, index=coduri, columns=coduri)


def ruta_optima_greedy(parcele_risc: list) -> list:
    """
    Calculeaza o ruta de inspectie greedy:
    porneste de la prima parcela si merge mereu la cea mai apropiata nevizitata.
    """
    if not parcele_risc:
        return []
    nevizitate = list(range(len(parcele_risc)))
    ruta = [nevizitate.pop(0)]
    while nevizitate:
        curent = ruta[-1]
        cel_mai_aproape = min(
            nevizitate,
            key=lambda j: distanta_km(
                parcele_risc[curent]["lat"], parcele_risc[curent]["lon"],
                parcele_risc[j]["lat"], parcele_risc[j]["lon"]
            )
        )
        ruta.append(cel_mai_aproape)
        nevizitate.remove(cel_mai_aproape)
    return ruta


def harta_zone_risc(parcele: list, tip_harta: str) -> folium.Map:
    """Harta cu zone de risc, heatmap si ruta optima de inspectie."""
    centru_lat = sum(p["lat"] for p in parcele) / len(parcele)
    centru_lon = sum(p["lon"] for p in parcele) / len(parcele)

    m = folium.Map(
        location=[centru_lat, centru_lon],
        zoom_start=10,
        tiles="CartoDB positron"
    )

    # Strat satelit optional
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satelit Esri", overlay=False
    ).add_to(m)

    if tip_harta in ("Marcatori risc", "Toate straturile"):
        grup_marcatori = folium.FeatureGroup(name="Parcele LPIS")
        for p in parcele:
            culoare = CULORI_RISC[p["risc"]]
            raza = 8 + p["suprafata"] * 0.8
            popup_html = f"""
            <div style="font-family:Arial;font-size:12px;min-width:210px;">
                <b style="color:#0052A5">{p['cod']}</b><br>
                <b>Fermier:</b> {p['fermier']}<br>
                <b>UAT:</b> {p['uat']} | <b>Cultura:</b> {p['cultura']}<br>
                <b>Suprafata:</b> {p['suprafata']} ha<br>
                <b>Vegetatie:</b> {p['vegetatie']}% |
                <b>NDVI:</b> {p['ndvi']}<br>
                <b>Risc PAC:</b>
                <span style="color:{culoare};font-weight:bold">
                    {ETICHETE_RISC[p['risc']]}
                </span>
            </div>
            """
            folium.CircleMarker(
                location=[p["lat"], p["lon"]],
                radius=raza,
                color=culoare,
                fill=True,
                fill_color=culoare,
                fill_opacity=0.75,
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=f"Risc {ETICHETE_RISC[p['risc']]} — {p['fermier']}"
            ).add_to(grup_marcatori)
        grup_marcatori.add_to(m)

    if tip_harta in ("Heatmap neconforme", "Toate straturile"):
        neconforme = [p for p in parcele if p["risc"] == 3]
        if neconforme:
            heat_data = [[p["lat"], p["lon"], p["risc"]] for p in neconforme]
            plugins.HeatMap(
                heat_data,
                name="Heatmap zone risc",
                min_opacity=0.4,
                radius=40,
                blur=25,
                gradient={0.4: "blue", 0.65: "yellow", 1: "red"}
            ).add_to(m)

    if tip_harta in ("Ruta inspectie", "Toate straturile"):
        # Ruta pentru parcelele cu risc ridicat + mediu
        prioritare = [p for p in parcele if p["risc"] >= 2]
        if len(prioritare) >= 2:
            ruta_idx = ruta_optima_greedy(prioritare)
            ruta_coords = [[prioritare[i]["lat"], prioritare[i]["lon"]]
                           for i in ruta_idx]
            grup_ruta = folium.FeatureGroup(name="Ruta inspectie")
            folium.PolyLine(
                ruta_coords,
                color="#E74C3C",
                weight=3,
                dash_array="8 4",
                tooltip="Ruta optima inspectie"
            ).add_to(grup_ruta)
            dist_totala = sum(
                distanta_km(
                    prioritare[ruta_idx[i]]["lat"],
                    prioritare[ruta_idx[i]]["lon"],
                    prioritare[ruta_idx[i+1]]["lat"],
                    prioritare[ruta_idx[i+1]]["lon"]
                )
                for i in range(len(ruta_idx)-1)
            )
            for rank, idx in enumerate(ruta_idx):
                p = prioritare[idx]
                folium.Marker(
                    location=[p["lat"], p["lon"]],
                    icon=folium.DivIcon(
                        html=f'<div style="background:#E74C3C;color:white;'
                             f'border-radius:50%;width:24px;height:24px;'
                             f'text-align:center;line-height:24px;'
                             f'font-weight:bold;font-size:12px;">'
                             f'{rank+1}</div>',
                        icon_size=(24, 24),
                        icon_anchor=(12, 12)
                    ),
                    tooltip=f"Stop {rank+1}: {p['fermier']}"
                ).add_to(grup_ruta)
            grup_ruta.add_to(m)

    plugins.Fullscreen(position="topright").add_to(m)
    plugins.MeasureControl(position="bottomleft",
                           primary_length_unit="kilometers").add_to(m)
    folium.LayerControl().add_to(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFATA STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════════

st.title("Ziua 32 - Analiza Spatiala Avansata")
st.markdown(
    "**Zone de risc PAC, heatmap, ruta optima de inspectie** — "
    "analiza spatiala pentru planificarea eficienta a controalelor APIA."
)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Configurare")
    tip_harta = st.radio(
        "Tip vizualizare",
        ["Marcatori risc", "Heatmap neconforme",
         "Ruta inspectie", "Toate straturile"],
        index=3
    )
    st.divider()
    st.markdown("**Legenda risc:**")
    for nivel, culoare in CULORI_RISC.items():
        st.markdown(
            f'<span style="color:{culoare};font-size:16px;">●</span> '
            f'Risc {ETICHETE_RISC[nivel]}',
            unsafe_allow_html=True
        )
    st.divider()
    st.markdown("**Formula Haversine:**")
    st.latex(r"d = 2R \arcsin\sqrt{\sin^2\frac{\Delta\phi}{2} + \cos\phi_1\cos\phi_2\sin^2\frac{\Delta\lambda}{2}}")
    st.caption("R = 6371 km (raza Pamantului)")

# ─── KPI ──────────────────────────────────────────────────────────────────────
df = pd.DataFrame(PARCELE)
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("Total parcele", len(PARCELE))
with k2:
    st.metric("Risc ridicat", int((df["risc"]==3).sum()),
              delta=f"{int((df['risc']==3).sum())} prioritare")
with k3:
    st.metric("Risc mediu", int((df["risc"]==2).sum()))
with k4:
    st.metric("Risc scazut", int((df["risc"]==1).sum()))
with k5:
    prioritare = df[df["risc"] >= 2]
    if len(prioritare) >= 2:
        ruta_idx = ruta_optima_greedy(prioritare.to_dict("records"))
        coords = prioritare.to_dict("records")
        dist_ruta = sum(
            distanta_km(
                coords[ruta_idx[i]]["lat"], coords[ruta_idx[i]]["lon"],
                coords[ruta_idx[i+1]]["lat"], coords[ruta_idx[i+1]]["lon"]
            )
            for i in range(len(ruta_idx)-1)
        )
        st.metric("Km ruta inspectie", f"{dist_ruta:.1f} km")

st.divider()

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Harta Zone Risc",
    "Matrice Distante",
    "Ruta Inspectie",
    "Analiza Spatiala"
])

# ── TAB 1: HARTA ──────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Harta Zone de Risc PAC — Gorj")
    m = harta_zone_risc(PARCELE, tip_harta)
    st_folium(m, width=None, height=520)

# ── TAB 2: MATRICE DISTANTE ───────────────────────────────────────────────────
with tab2:
    st.subheader("Matrice Distante GPS intre Parcele (km)")
    st.markdown(
        "Distantele sunt calculate prin formula **Haversine** — "
        "distanta reala pe suprafata Pamantului, nu in linie dreapta pe harta plana."
    )

    mat_df = matrice_distante(PARCELE)

    fig_heatmap = px.imshow(
        mat_df.values,
        x=mat_df.columns.tolist(),
        y=mat_df.index.tolist(),
        color_continuous_scale="Blues",
        title="Matrice distante GPS (km) — parcele LPIS Gorj",
        text_auto=".1f",
        aspect="auto"
    )
    fig_heatmap.update_layout(height=480)
    st.plotly_chart(fig_heatmap, use_container_width=True)

    st.markdown("#### Cele mai apropiate perechi de parcele")
    perechi = []
    for i in range(len(PARCELE)):
        for j in range(i+1, len(PARCELE)):
            d = distanta_km(
                PARCELE[i]["lat"], PARCELE[i]["lon"],
                PARCELE[j]["lat"], PARCELE[j]["lon"]
            )
            perechi.append({
                "Parcela 1": PARCELE[i]["cod"],
                "Fermier 1": PARCELE[i]["fermier"],
                "Parcela 2": PARCELE[j]["cod"],
                "Fermier 2": PARCELE[j]["fermier"],
                "Distanta (km)": d
            })
    df_perechi = pd.DataFrame(perechi).sort_values("Distanta (km)")
    st.dataframe(df_perechi.head(8).style.background_gradient(
        subset=["Distanta (km)"], cmap="Blues_r"
    ).format({"Distanta (km)": "{:.2f}"}),
    use_container_width=True)

# ── TAB 3: RUTA INSPECTIE ────────────────────────────────────────────────────
with tab3:
    st.subheader("Ruta Optima de Inspectie — Algoritm Greedy")
    st.markdown(
        "Porneste de la prima parcela cu risc si merge mereu la cea mai "
        "**apropiata parcela nevizitata** cu risc mediu sau ridicat. "
        "Minimizeaza kilometrii parcursi de inspector."
    )

    prioritare_list = [p for p in PARCELE if p["risc"] >= 2]
    if len(prioritare_list) >= 2:
        ruta_idx = ruta_optima_greedy(prioritare_list)
        ruta_ordonata = [prioritare_list[i] for i in ruta_idx]

        # Tabel ruta
        ruta_data = []
        dist_cumulata = 0
        for rank, p in enumerate(ruta_ordonata):
            if rank > 0:
                prev = ruta_ordonata[rank-1]
                d = distanta_km(prev["lat"], prev["lon"],
                                p["lat"], p["lon"])
                dist_cumulata += d
            else:
                d = 0
            ruta_data.append({
                "Stop": rank + 1,
                "Cod LPIS": p["cod"],
                "Fermier": p["fermier"],
                "UAT": p["uat"],
                "Cultura": p["cultura"],
                "Risc": ETICHETE_RISC[p["risc"]],
                "Dist. de la precedenta (km)": round(d, 2),
                "Dist. cumulata (km)": round(dist_cumulata, 2)
            })

        df_ruta = pd.DataFrame(ruta_data)

        def color_risc_col(val):
            if val == "RIDICAT":
                return "background-color:#f8d7da;color:#721c24"
            elif val == "MEDIU":
                return "background-color:#fff3cd;color:#856404"
            return ""

        st.dataframe(
            df_ruta.style.map(color_risc_col, subset=["Risc"]),
            use_container_width=True
        )

        dist_totala = df_ruta["Dist. de la precedenta (km)"].sum()
        st.success(
            f"Ruta optima: **{len(ruta_ordonata)} parcele** de vizitat | "
            f"Distanta totala: **{dist_totala:.1f} km** | "
            f"Timp estimat la 60 km/h: **{dist_totala/60*60:.0f} minute**"
        )

        # Export ruta ca CSV
        csv_ruta = df_ruta.to_csv(index=False, encoding="utf-8")
        st.download_button(
            "Descarca ruta inspectie (CSV)",
            data=csv_ruta.encode("utf-8"),
            file_name="Ruta_Inspectie_APIA_Gorj.csv",
            mime="text/csv"
        )

# ── TAB 4: ANALIZA SPATIALA ───────────────────────────────────────────────────
with tab4:
    st.subheader("Analiza Spatiala per UAT si Cultura")

    col1, col2 = st.columns(2)

    with col1:
        # Risc per UAT
        df_uat = df.groupby("uat").agg(
            Parcele=("cod", "count"),
            Risc_mediu=("risc", "mean"),
            Suprafata=("suprafata", "sum"),
            Neconforme=("status", lambda x: (x == "NECONFORM").sum())
        ).round(2).reset_index()
        df_uat["Rata neconf %"] = (
            df_uat["Neconforme"] / df_uat["Parcele"] * 100
        ).round(1)

        fig_uat = px.bar(
            df_uat.sort_values("Rata neconf %", ascending=False),
            x="uat", y="Rata neconf %",
            color="Rata neconf %",
            color_continuous_scale="RdYlGn_r",
            title="Rata neconformitate per UAT (%)",
            text="Rata neconf %"
        )
        fig_uat.update_traces(textposition="outside")
        fig_uat.update_layout(height=360, plot_bgcolor="#F8F9FA",
                              coloraxis_showscale=False)
        st.plotly_chart(fig_uat, use_container_width=True)

    with col2:
        # NDVI per cultura
        fig_ndvi = px.box(
            df, x="cultura", y="ndvi",
            color="status",
            color_discrete_map={"CONFORM": "#28a745", "NECONFORM": "#dc3545"},
            title="Distributia NDVI per cultura",
            labels={"cultura": "Cultura", "ndvi": "NDVI",
                    "status": "Status PAC"}
        )
        fig_ndvi.add_hline(y=0.25, line_dash="dash", line_color="red",
                           annotation_text="Prag risc NDVI < 0.25")
        fig_ndvi.update_layout(height=360, plot_bgcolor="#F8F9FA")
        st.plotly_chart(fig_ndvi, use_container_width=True)

    # Scatter spatial
    fig_scatter = px.scatter(
        df,
        x="lon", y="lat",
        color="status",
        size="suprafata",
        size_max=20,
        symbol="cultura",
        color_discrete_map={"CONFORM": "#28a745", "NECONFORM": "#dc3545"},
        hover_data=["fermier", "uat", "vegetatie", "ndvi"],
        title="Distributia spatiala a parcelelor (lon/lat)",
        labels={"lon": "Longitudine", "lat": "Latitudine",
                "status": "Status PAC"}
    )
    fig_scatter.update_layout(height=420, plot_bgcolor="#F8F9FA")
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("#### Statistici per UAT")
    st.dataframe(
        df_uat.style.background_gradient(
            subset=["Rata neconf %"], cmap="RdYlGn_r", vmin=0, vmax=100
        ).format({
            "Suprafata": "{:.1f} ha",
            "Risc_mediu": "{:.2f}",
            "Rata neconf %": "{:.1f}%"
        }),
        use_container_width=True
    )

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Ziua 32 - AGROVISION | Analiza Spatiala | "
    "Haversine + Greedy routing + Heatmap | "
    "Prof. Asoc. Dr. Oliviu Mihnea Gamulescu, UCB Targu Jiu 2026"
)
