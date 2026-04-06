"""
AGROVISION — QGIS & WMS Live
Ziua 31 | Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu

Scop:
    Afisare straturi WMS oficiale (ANCPI, ortofoto, cadastru)
    direct in Streamlit folosind Folium.
    Parcele LPIS Gorj suprapuse pe harti oficiale.
    Direct utilizabil la APIA pentru inspectii teren.

WMS = Web Map Service — standard OGC pentru harti raster online.
ANCPI ofera WMS public gratuit pentru Romania.
"""

import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
import pandas as pd
import json
import io
import zipfile

# ─── CONFIGURARE PAGINA ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="QGIS WMS Live | AGROVISION",
    page_icon="GIS",
    layout="wide"
)

# ─── DATE LPIS GORJ ───────────────────────────────────────────────────────────
PARCELE = [
    {"cod": "GJ_78258-1675", "fermier": "Popescu Ion",      "suprafata": 4.32,
     "cultura": "grau",    "uat": "Targu Jiu",    "lat": 45.0421, "lon": 23.2718,
     "status": "CONFORM"},
    {"cod": "GJ_78301-0892", "fermier": "Ionescu Maria",    "suprafata": 6.78,
     "cultura": "porumb",  "uat": "Rovinari",     "lat": 44.9183, "lon": 23.1645,
     "status": "CONFORM"},
    {"cod": "GJ_78445-2341", "fermier": "Dumitrescu Gh.",   "suprafata": 3.15,
     "cultura": "rapita",  "uat": "Motru",        "lat": 44.8067, "lon": 22.9876,
     "status": "NECONFORM"},
    {"cod": "GJ_78512-0077", "fermier": "Stanescu Petre",   "suprafata": 8.90,
     "cultura": "grau",    "uat": "Bumbesti-Jiu", "lat": 45.1823, "lon": 23.3912,
     "status": "CONFORM"},
    {"cod": "GJ_78634-1129", "fermier": "Olteanu Vasile",   "suprafata": 2.44,
     "cultura": "lucerna", "uat": "Novaci",       "lat": 45.3012, "lon": 23.6734,
     "status": "CONFORM"},
    {"cod": "GJ_78720-3388", "fermier": "Marinescu Ana",    "suprafata": 5.67,
     "cultura": "floarea", "uat": "Targu Jiu",    "lat": 45.0198, "lon": 23.2456,
     "status": "NECONFORM"},
    {"cod": "GJ_79001-0445", "fermier": "Petrescu Dan",     "suprafata": 7.23,
     "cultura": "grau",    "uat": "Turceni",      "lat": 44.8734, "lon": 23.4012,
     "status": "CONFORM"},
    {"cod": "GJ_79234-1876", "fermier": "Constantin Gh.",   "suprafata": 1.98,
     "cultura": "lucerna", "uat": "Aninoasa",     "lat": 45.0867, "lon": 23.5219,
     "status": "CONFORM"},
    {"cod": "GJ_79567-2290", "fermier": "Florescu Elena",   "suprafata": 9.45,
     "cultura": "porumb",  "uat": "Rovinari",     "lat": 44.9045, "lon": 23.1823,
     "status": "NECONFORM"},
    {"cod": "GJ_80980-2611", "fermier": "Draghici Marin",   "suprafata": 6.64,
     "cultura": "lucerna", "uat": "Targu Jiu",    "lat": 45.0534, "lon": 23.2901,
     "status": "CONFORM"},
]

# ─── STRATURI HARTA ───────────────────────────────────────────────────────────
STRATURI_TILES = {
    "OpenStreetMap": {
        "tiles": "OpenStreetMap",
        "descriere": "Harta standard OpenStreetMap — drumuri, localitati, relief"
    },
    "Satelit Esri": {
        "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attr": "Esri World Imagery",
        "descriere": "Imagini satelit Esri — rezolutie ridicata"
    },
    "CartoDB Positron": {
        "tiles": "CartoDB positron",
        "descriere": "Harta minimalista alba — ideal pentru date suprapuse"
    },
    "CartoDB Dark": {
        "tiles": "CartoDB dark_matter",
        "descriere": "Harta inchisa — contrast ridicat pentru date"
    },
    "OpenTopoMap": {
        "tiles": "https://tile.opentopomap.org/{z}/{x}/{y}.png",
        "attr": "OpenTopoMap",
        "descriere": "Harta topografica cu curbe de nivel — util pentru teren accidentat"
    },
    "Stamen Terrain": {
        "tiles": "https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}{r}.png",
        "attr": "Stadia Maps",
        "descriere": "Relief si vegetatie — vizualizare naturala"
    },
}

# WMS public INSPIRE Romania (geoportal.gov.ro)
WMS_INSPIRE = {
    "Ortofoto Romania (ANCPI)": {
        "url": "https://geoportal.ancpi.ro/maps/rest/services/ortofoto2012/MapServer/WMSServer",
        "layers": "0",
        "descriere": "Ortofotoplan Romania 2012 — ANCPI (gratuit, public)"
    },
    "Limite administrative": {
        "url": "https://geoportal.gov.ro/arcgis/services/INSPIRE/AU/MapServer/WmsServer",
        "layers": "0",
        "descriere": "Limite administrative INSPIRE Romania"
    },
}


def construieste_harta(strat_ales: str, zoom: int,
                       arata_lpis: bool, arata_wms: bool,
                       wms_ales: str) -> folium.Map:
    """Construieste harta Folium cu stratul ales si parcelele LPIS."""

    centru_lat = sum(p["lat"] for p in PARCELE) / len(PARCELE)
    centru_lon = sum(p["lon"] for p in PARCELE) / len(PARCELE)

    # Stratul de baza
    info_strat = STRATURI_TILES[strat_ales]
    if strat_ales == "OpenStreetMap":
        m = folium.Map(location=[centru_lat, centru_lon],
                       zoom_start=zoom, tiles="OpenStreetMap")
    elif strat_ales == "CartoDB Positron":
        m = folium.Map(location=[centru_lat, centru_lon],
                       zoom_start=zoom, tiles="CartoDB positron")
    elif strat_ales == "CartoDB Dark":
        m = folium.Map(location=[centru_lat, centru_lon],
                       zoom_start=zoom, tiles="CartoDB dark_matter")
    else:
        m = folium.Map(location=[centru_lat, centru_lon],
                       zoom_start=zoom, tiles=None)
        folium.TileLayer(
            tiles=info_strat["tiles"],
            attr=info_strat.get("attr", strat_ales),
            name=strat_ales
        ).add_to(m)

    # Strat WMS optional
    if arata_wms and wms_ales in WMS_INSPIRE:
        wms_info = WMS_INSPIRE[wms_ales]
        try:
            folium.WmsTileLayer(
                url=wms_info["url"],
                layers=wms_info["layers"],
                name=wms_ales,
                fmt="image/png",
                transparent=True,
                opacity=0.7
            ).add_to(m)
        except Exception:
            pass  # WMS poate fi offline

    # Strat LPIS
    if arata_lpis:
        grup_lpis = folium.FeatureGroup(name="Parcele LPIS Gorj")
        for p in PARCELE:
            culoare = "#28a745" if p["status"] == "CONFORM" else "#dc3545"
            popup_html = f"""
            <div style="font-family:Arial;font-size:13px;min-width:200px;">
                <b style="color:#0052A5">{p['cod']}</b><br>
                <b>Fermier:</b> {p['fermier']}<br>
                <b>UAT:</b> {p['uat']}<br>
                <b>Cultura:</b> {p['cultura']}<br>
                <b>Suprafata:</b> {p['suprafata']} ha<br>
                <b>Status PAC:</b>
                <span style="color:{culoare};font-weight:bold">
                    {p['status']}
                </span>
            </div>
            """
            folium.CircleMarker(
                location=[p["lat"], p["lon"]],
                radius=10 + p["suprafata"] * 0.5,
                color=culoare,
                fill=True,
                fill_color=culoare,
                fill_opacity=0.7,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{p['fermier']} | {p['suprafata']} ha | {p['status']}"
            ).add_to(grup_lpis)
        grup_lpis.add_to(m)

    # Plugin fullscreen
    plugins.Fullscreen(position="topright").add_to(m)

    # Plugin masurare distanta
    plugins.MeasureControl(position="bottomleft",
                            primary_length_unit="meters",
                            secondary_length_unit="kilometers").add_to(m)

    # Control straturi
    folium.LayerControl().add_to(m)

    return m


def exporta_geojson(parcele: list) -> str:
    """Exporta parcelele ca GeoJSON pentru import in QGIS."""
    features = []
    for p in parcele:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [p["lon"], p["lat"]]
            },
            "properties": {
                "cod_lpis":  p["cod"],
                "fermier":   p["fermier"],
                "uat":       p["uat"],
                "cultura":   p["cultura"],
                "suprafata": p["suprafata"],
                "status":    p["status"]
            }
        })
    return json.dumps({
        "type": "FeatureCollection",
        "crs": {"type": "name",
                "properties": {"name": "EPSG:4326"}},
        "features": features
    }, ensure_ascii=False, indent=2)


def exporta_shapefile_stereo70(parcele: list) -> bytes:
    """
    Exporta parcelele ca Shapefile Point in Stereo 70 (EPSG:31700).
    Returneaza un ZIP cu fisierele .shp, .shx, .dbf, .prj.
    Stereo 70 = sistemul national de coordonate Romania, obligatoriu APIA/ANCPI.
    """
    try:
        import shapefile
        from pyproj import Transformer
    except ImportError:
        return b""

    # Transformator WGS84 (EPSG:4326) → Stereo 70 (EPSG:31700)
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:31700", always_xy=True)

    shp_buf = io.BytesIO()
    shx_buf = io.BytesIO()
    dbf_buf = io.BytesIO()

    w = shapefile.Writer(
        shp=shp_buf, shx=shx_buf, dbf=dbf_buf,
        shapeType=shapefile.POINT
    )

    # Campuri atribute (DBF)
    w.field("COD_LPIS",  "C", 25)
    w.field("FERMIER",   "C", 50)
    w.field("UAT",       "C", 30)
    w.field("CULTURA",   "C", 20)
    w.field("SUPRAFATA", "N", 10, 2)
    w.field("STATUS",    "C", 15)
    w.field("X_STEREO",  "N", 12, 2)
    w.field("Y_STEREO",  "N", 12, 2)

    for p in parcele:
        # Conversie lon/lat → X/Y Stereo 70
        x_stereo, y_stereo = transformer.transform(p["lon"], p["lat"])
        w.point(x_stereo, y_stereo)
        w.record(
            p["cod"], p["fermier"], p["uat"],
            p["cultura"], p["suprafata"], p["status"],
            round(x_stereo, 2), round(y_stereo, 2)
        )

    w.close()

    # Fisier .prj — definitia Stereo 70 in format WKT
    prj_stereo70 = (
        'PROJCS["Stereo70",'
        'GEOGCS["Dealul Piscului 1970",'
        'DATUM["Dealul_Piscului_1970",'
        'SPHEROID["Krassowsky 1940",6378245,298.3]],'
        'PRIMEM["Greenwich",0],'
        'UNIT["degree",0.0174532925199433]],'
        'PROJECTION["Oblique_Stereographic"],'
        'PARAMETER["latitude_of_origin",46],'
        'PARAMETER["central_meridian",25],'
        'PARAMETER["scale_factor",0.99975],'
        'PARAMETER["false_easting",500000],'
        'PARAMETER["false_northing",500000],'
        'UNIT["metre",1]]'
    )

    # Impacheteaza intr-un ZIP
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Parcele_LPIS_Gorj_Stereo70.shp", shp_buf.getvalue())
        zf.writestr("Parcele_LPIS_Gorj_Stereo70.shx", shx_buf.getvalue())
        zf.writestr("Parcele_LPIS_Gorj_Stereo70.dbf", dbf_buf.getvalue())
        zf.writestr("Parcele_LPIS_Gorj_Stereo70.prj", prj_stereo70)
        # Fisier LISEZ-MOI
        nota = (
            "Shapefile Parcele LPIS Gorj\n"
            "Sistem coordonate: Stereo 70 (EPSG:31700)\n"
            "Tip geometrie: Point\n"
            "Campuri: COD_LPIS, FERMIER, UAT, CULTURA, SUPRAFATA, STATUS, X_STEREO, Y_STEREO\n"
            "Generat de: AGROVISION — Ziua 31\n"
            "Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu, UCB Targu Jiu 2026\n"
        )
        zf.writestr("CITESTE.txt", nota)

    return zip_buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFATA STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════════

st.title("Ziua 31 - QGIS & WMS Live")
st.markdown(
    "**Harti oficiale in browser** — straturi WMS ANCPI, ortofoto si "
    "parcele LPIS Gorj suprapuse. Fara QGIS instalat, direct din aplicatie."
)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Configurare Harta")

    strat_ales = st.selectbox(
        "Strat de baza",
        options=list(STRATURI_TILES.keys()),
        index=1,
        help="Alege fundalul hartii"
    )
    st.caption(STRATURI_TILES[strat_ales]["descriere"])

    zoom = st.slider("Zoom initial", 7, 15, 10)

    st.divider()
    arata_lpis = st.checkbox("Afiseaza parcele LPIS", value=True)
    arata_wms  = st.checkbox("Afiseaza strat WMS oficial", value=False,
                              help="Necesita conexiune la internet si server WMS activ")

    if arata_wms:
        wms_ales = st.selectbox(
            "Strat WMS",
            options=list(WMS_INSPIRE.keys())
        )
        st.caption(WMS_INSPIRE[wms_ales]["descriere"])
        st.warning(
            "Straturile WMS depind de serverele ANCPI/INSPIRE. "
            "Daca nu se incarca, serverul este offline momentan."
        )
    else:
        wms_ales = list(WMS_INSPIRE.keys())[0]

    st.divider()
    st.markdown("**Legenda:**")
    st.markdown(
        '<span style="color:#28a745;font-size:16px;">●</span> CONFORM PAC',
        unsafe_allow_html=True
    )
    st.markdown(
        '<span style="color:#dc3545;font-size:16px;">●</span> NECONFORM PAC',
        unsafe_allow_html=True
    )

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Harta Live",
    "Parcele LPIS",
    "Export QGIS",
    "Ghid WMS"
])

# ── TAB 1: HARTA ──────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Harta Interactiva cu Straturi Oficiale")

    # KPI rapid
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Parcele LPIS", len(PARCELE))
    with k2:
        conforme = sum(1 for p in PARCELE if p["status"] == "CONFORM")
        st.metric("Conforme PAC", conforme)
    with k3:
        neconf = len(PARCELE) - conforme
        st.metric("Neconforme PAC", neconf)
    with k4:
        sup_total = sum(p["suprafata"] for p in PARCELE)
        st.metric("Suprafata totala", f"{sup_total:.1f} ha")

    st.divider()

    m = construieste_harta(strat_ales, zoom, arata_lpis, arata_wms, wms_ales)
    rezultat = st_folium(m, width=None, height=520, returned_objects=["last_object_clicked"])

    # Afiseaza detalii parcela click
    if rezultat and rezultat.get("last_object_clicked"):
        click = rezultat["last_object_clicked"]
        lat_click = click.get("lat")
        lon_click = click.get("lng")
        if lat_click and lon_click:
            # Gaseste parcela cea mai apropiata de click
            import math
            min_dist = float("inf")
            parcela_click = None
            for p in PARCELE:
                dist = math.sqrt(
                    (p["lat"] - lat_click)**2 + (p["lon"] - lon_click)**2
                )
                if dist < min_dist:
                    min_dist = dist
                    parcela_click = p
            if parcela_click and min_dist < 0.05:
                culoare = "#d4edda" if parcela_click["status"] == "CONFORM" else "#f8d7da"
                st.markdown(
                    f'<div style="background:{culoare};border-radius:8px;'
                    f'padding:12px 16px;margin-top:8px;">'
                    f'<b>{parcela_click["cod"]}</b> | '
                    f'{parcela_click["fermier"]} | '
                    f'{parcela_click["uat"]} | '
                    f'{parcela_click["cultura"]} | '
                    f'{parcela_click["suprafata"]} ha | '
                    f'<b>{parcela_click["status"]}</b>'
                    f'</div>',
                    unsafe_allow_html=True
                )

# ── TAB 2: PARCELE ────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Tabel Parcele LPIS Gorj")

    df = pd.DataFrame(PARCELE)

    # Filtru UAT
    uaturi = ["Toate"] + sorted(df["uat"].unique().tolist())
    uat_filtru = st.selectbox("Filtreaza dupa UAT", uaturi)
    if uat_filtru != "Toate":
        df = df[df["uat"] == uat_filtru]

    def color_status(val):
        if val == "CONFORM":
            return "background-color: #d4edda; color: #155724"
        return "background-color: #f8d7da; color: #721c24"

    st.dataframe(
        df[["cod", "fermier", "uat", "cultura", "suprafata", "status"]]
        .style.map(color_status, subset=["status"])
        .format({"suprafata": "{:.2f} ha"}),
        use_container_width=True,
        height=380
    )

    st.markdown(f"**{len(df)}** parcele afisate | "
                f"Suprafata: **{df['suprafata'].sum():.1f} ha**")

# ── TAB 3: EXPORT QGIS ────────────────────────────────────────────────────────
with tab3:
    st.subheader("Export pentru QGIS")
    st.markdown(
        "Descarca parcelele LPIS in format **GeoJSON** (WGS84 EPSG:4326) "
        "pentru import direct in QGIS sau ArcGIS."
    )

    geojson_str = exporta_geojson(PARCELE)

    col_exp1, col_exp2, col_exp3 = st.columns(3)
    with col_exp1:
        st.download_button(
            label="Descarca GeoJSON (WGS84)",
            data=geojson_str.encode("utf-8"),
            file_name="Parcele_LPIS_Gorj_WGS84.geojson",
            mime="application/geo+json",
            use_container_width=True,
            type="primary"
        )
        st.caption(
            "EPSG:4326 — WGS84 (GPS global). "
            "Deschide in QGIS: Layer → Add Vector Layer"
        )

    with col_exp2:
        # CSV cu coordonate
        df_exp = pd.DataFrame(PARCELE)
        csv_data = df_exp.to_csv(index=False, encoding="utf-8")
        st.download_button(
            label="Descarca CSV (coordonate GPS)",
            data=csv_data.encode("utf-8"),
            file_name="Parcele_LPIS_Gorj_GPS.csv",
            mime="text/csv",
            use_container_width=True
        )
        st.caption(
            "Importa in QGIS: Layer → Add Delimited Text Layer → "
            "X field: lon, Y field: lat"
        )

    with col_exp3:
        shp_zip = exporta_shapefile_stereo70(PARCELE)
        if shp_zip:
            st.download_button(
                label="Descarca Shapefile Stereo 70",
                data=shp_zip,
                file_name="Parcele_LPIS_Gorj_Stereo70.zip",
                mime="application/zip",
                use_container_width=True,
                type="secondary"
            )
            st.caption(
                "EPSG:31700 — Stereo 70 (sistemul national Romania). "
                "ZIP cu .shp .shx .dbf .prj — import direct QGIS/ANCPI"
            )
        else:
            st.warning("pyshp sau pyproj nu este instalat.")

    st.divider()
    st.markdown("#### Previzualizare GeoJSON")
    with st.expander("Vezi continutul GeoJSON"):
        st.code(geojson_str[:800] + "\n...", language="json")

    st.divider()
    st.markdown("#### Ce este Stereo 70?")
    st.markdown("""
<div style='background:#e8f4fd; border-radius:8px; padding:14px 18px;
            border-left:4px solid #0052A5; font-size:13px;'>
<b>Stereo 70 (EPSG:31700)</b> — sistemul national de coordonate al Romaniei.<br><br>
- Proiectie: <b>Oblique Stereographic</b> (stereografica oblicua)<br>
- Meridian central: <b>25° E</b>, Paralela origine: <b>46° N</b><br>
- Elipsoid: <b>Krassovsky 1940</b> (6.378.245 m)<br>
- Unitate: <b>metri</b><br>
- False Easting: 500.000 m | False Northing: 500.000 m<br><br>
<b>De ce Stereo 70?</b> Toate hartile oficiale ANCPI, LPIS, cadastru si APIA
folosesc Stereo 70. Datele GPS sunt in WGS84 — conversie necesara inainte
de suprapunere pe harile oficiale.
</div>
""", unsafe_allow_html=True)

    st.markdown("#### Pasi import in QGIS")
    pasi = [
        ("1. Deschide QGIS", "QGIS Desktop 3.x — gratuit de pe qgis.org"),
        ("2. Incarca fisierul", "Drag & drop fisierul .geojson in fereastra QGIS"),
        ("3. Sistem coordonate", "QGIS detecteaza automat EPSG:4326 (WGS84)"),
        ("4. Simbolizare", "Click dreapta layer → Properties → Symbology → Categorized pe campul 'status'"),
        ("5. Adauga WMS ANCPI", "Layer → Add WMS/WMTS Layer → URL server ANCPI"),
        ("6. Etichete", "Properties → Labels → Single Labels → campul 'cod_lpis'"),
    ]
    for pas, desc in pasi:
        st.markdown(f"**{pas}** — {desc}")

# ── TAB 4: GHID WMS ───────────────────────────────────────────────────────────
with tab4:
    st.subheader("Ghid WMS — Harti Oficiale Romania")

    st.markdown(
        """
### Ce este WMS?

**Web Map Service (WMS)** este un standard OGC (Open Geospatial Consortium)
care permite accesarea hartilor raster de pe servere remote direct in
aplicatii GIS sau web, fara a descarca datele local.

### Serverele WMS disponibile in Romania

| Furnizor | URL WMS | Continut | Cost |
|---------|---------|---------|------|
| **ANCPI** | geoportal.ancpi.ro | Ortofoto, cadastru, LPIS | Gratuit |
| **INSPIRE Romania** | geoportal.gov.ro | Limite administrative, retea rutiera | Gratuit |
| **INS** | statistici.insse.ro | Date statistice geografice | Gratuit |
| **ANIF** | anif.ro | Sisteme de irigatii | Gratuit |

### URL-uri WMS utile pentru APIA Gorj

```
Ortofoto 2012 ANCPI:
https://geoportal.ancpi.ro/maps/rest/services/ortofoto2012/MapServer/WMSServer

Unitati Administrativ-Teritoriale:
https://geoportal.gov.ro/arcgis/services/INSPIRE/AU/MapServer/WmsServer

Retea Hidro:
https://geoportal.gov.ro/arcgis/services/INSPIRE/HY/MapServer/WmsServer
```

### Cum adaugi WMS in QGIS

```
1. Layer → Add Layer → Add WMS/WMTS Layer
2. Click "New" → introdu URL-ul serverului
3. Click "Connect" → selecteaza stratul dorit
4. Click "Add" → stratul apare in proiect
```

### Cum adaugi WMS in Folium (Python)

```python
folium.WmsTileLayer(
    url="https://geoportal.ancpi.ro/maps/rest/services/ortofoto2012/MapServer/WMSServer",
    layers="0",
    fmt="image/png",
    transparent=True,
    name="Ortofoto ANCPI"
).add_to(m)
```

### Avantajele WMS pentru APIA

- **Date oficiale** — aceleasi date ca LPIS oficial
- **Actualizate** — serverul furnizeaza intotdeauna versiunea curenta
- **Fara stocare locala** — nu descarci date voluminoase
- **Legal** — surse oficiale, acceptate in rapoarte de control
        """
    )

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Ziua 31 - AGROVISION | QGIS & WMS Live | "
    "Folium + WMS + GeoJSON | "
    "Prof. Asoc. Dr. Oliviu Mihnea Gamulescu, UCB Targu Jiu 2026"
)
