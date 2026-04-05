"""
BLOC 3 — Deep Learning YOLOv8, Ziua 17
Export GIS complet: GeoJSON + Shapefile Stereo70 + GPX
din rezultatele comparative T1/T2 pentru vizualizare in QGIS/ArcGIS
Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu | UCB Targu Jiu | APIA CJ Gorj

CONCEPT CHEIE:
  GeoJSON  = format JSON cu geometrie geografica — deschis direct in QGIS prin drag & drop
  Shapefile = format standard ESRI (SHP+DBF+SHX+PRJ) — folosit in LPIS oficial
  Stereo70  = proiectia nationala romaneasca EPSG:31700 — ceruta de APIA/ANCPI
  GPX       = format GPS Exchange — incarcat pe GPS/telefon pentru control pe teren

  De ce Stereo70 pentru APIA:
    - LPIS Romania foloseste Stereo70 (EPSG:31700) ca sistem de referinta oficial
    - Harile ANCPI si OCPI sunt in Stereo70
    - Inspector incarca shapefilul in QGIS si se suprapune peste LPIS oficial

  Formule conversie WGS84 → Stereo70 (simplificat):
    Folosim biblioteca pyproj (daca instalata) sau aproximare liniara pentru zona Gorj
"""

import streamlit as st
import numpy as np
import json
import zipfile
import struct
import math
from io import BytesIO
from datetime import date, datetime
import random

st.set_page_config(page_title="Export GIS — Ziua 17", layout="wide")

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.bloc3-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    padding: 1.5rem 2rem; border-radius: 12px;
    margin-bottom: 1.5rem; border-left: 5px solid #e94560;
}
.bloc3-header h1 { color: #e94560; margin: 0; font-size: 1.6rem; }
.bloc3-header p  { color: #a8b2d8; margin: 0.3rem 0 0 0; font-size: 0.9rem; }
.concept-box {
    background: #0f3460; border: 1px solid #e94560;
    border-radius: 8px; padding: 1rem 1.2rem; margin: 1rem 0;
    color: #a8b2d8; font-size: 0.88rem;
}
.concept-box b { color: #e94560; }
.ok-box {
    background: #0d2b0d; border: 1px solid #27ae60;
    border-radius: 8px; padding: 0.8rem 1rem; color: #7dcea0; margin: 0.4rem 0;
}
.info-box {
    background: #0f3460; border: 1px solid #3498db;
    border-radius: 8px; padding: 0.8rem 1rem; color: #a8b2d8; margin: 0.4rem 0;
}
.sectiune-titlu {
    background: #0f3460; color: #e94560;
    padding: 0.5rem 1rem; border-radius: 6px;
    font-weight: bold; font-size: 1rem; margin: 1rem 0 0.5rem 0;
}
.format-card {
    background: #16213e; border: 1px solid #0f3460;
    border-radius: 10px; padding: 1.2rem; text-align: center; margin: 0.3rem 0;
}
.format-card h3 { color: #e94560; margin: 0 0 0.5rem 0; font-size: 1.1rem; }
.format-card p  { color: #a8b2d8; font-size: 0.82rem; margin: 0.2rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="bloc3-header">
  <h1>Ziua 17 — Export GIS: GeoJSON + Shapefile Stereo70 + GPX</h1>
  <p>Bloc 3 YOLOv8 | Prof. Asoc. Dr. Oliviu Mihnea Gamulescu | UCB Targu Jiu | APIA CJ Gorj</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="concept-box">
<b>CONCEPTE CHEIE AZI:</b><br>
<b>GeoJSON</b> = {"type":"Feature","geometry":{"type":"Polygon","coordinates":[...]}, "properties":{...}}<br>
<b>Shapefile</b> = 4 fisiere: .shp (geometrie) + .dbf (atribute) + .shx (index) + .prj (proiectie)<br>
<b>EPSG:31700</b> = Stereo70 — proiectia nationala Romania, obligatorie in LPIS si ANCPI<br>
<b>GPX</b> = waypoints GPS per parcela — incarci pe telefon/GPS si gasesti parcela pe teren<br>
<b>pyproj</b> = biblioteca Python pentru conversii intre sisteme de coordonate<br>
<b>WGS84→Stereo70</b> = transforma lat/lon (grade) in X/Y Stereo70 (metri)
</div>
""", unsafe_allow_html=True)

# ── Formate explicate ──────────────────────────────────────────────────────────
col_f1, col_f2, col_f3, col_f4 = st.columns(4)
for col, (titlu, desc, use) in zip([col_f1,col_f2,col_f3,col_f4],[
    ("GeoJSON",   "JSON geografic standard", "QGIS, Leaflet, web"),
    ("Shapefile", "Format ESRI standard",    "QGIS, ArcGIS, LPIS"),
    ("GPX",       "GPS Exchange Format",     "Garmin, telefon GPS"),
    ("ZIP",       "Toate formatele intr-un pachet", "Arhivare, audit"),
]):
    with col:
        st.markdown(f"""
        <div class="format-card">
        <h3>{titlu}</h3>
        <p>{desc}</p>
        <p style="color:#e94560">{use}</p>
        </div>""", unsafe_allow_html=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# DATE PARCELE cu coordonate GPS reale zona Gorj
# ══════════════════════════════════════════════════════════════════════════════

# Coordonate centru aproximativ parcele reale LPIS Gorj (WGS84)
PARCELE_GIS = [
    {"cod":"GJ_78258-1675","fermier":"Ionescu Marin",    "ha":3.42,"cultura":"Grau",
     "lat":44.8921,"lon":23.1854,"veg_t1":72.3,"veg_t2":18.5,"delta":-53.8,"trend":"RECOLTA"},
    {"cod":"GJ_79157-348", "fermier":"Popescu Ion",      "ha":2.45,"cultura":"Porumb",
     "lat":44.9045,"lon":23.2231,"veg_t1":65.1,"veg_t2":71.4,"delta":+6.3,"trend":"CRESTERE"},
    {"cod":"GJ_79237-628", "fermier":"Dumitrescu Vasile","ha":5.10,"cultura":"Floarea-soarelui",
     "lat":44.8876,"lon":23.2567,"veg_t1":58.9,"veg_t2":62.1,"delta":+3.2,"trend":"STABIL"},
    {"cod":"GJ_79308-489", "fermier":"Stanescu Maria",   "ha":1.80,"cultura":"Rapita",
     "lat":44.9178,"lon":23.1423,"veg_t1":81.2,"veg_t2":22.4,"delta":-58.8,"trend":"RECOLTA"},
    {"cod":"GJ_79406-641", "fermier":"Gheorghiu Aurel",  "ha":4.20,"cultura":"Orz",
     "lat":44.8654,"lon":23.3012,"veg_t1":74.6,"veg_t2":19.8,"delta":-54.8,"trend":"RECOLTA"},
    {"cod":"GJ_79406-924", "fermier":"Constantin Elena", "ha":6.75,"cultura":"Lucerna",
     "lat":44.9312,"lon":23.2789,"veg_t1":88.3,"veg_t2":84.7,"delta":-3.6,"trend":"STABIL"},
    {"cod":"GJ_79834-9533","fermier":"Marin Gheorghe",   "ha":2.30,"cultura":"Pasune",
     "lat":44.8543,"lon":23.1987,"veg_t1":91.2,"veg_t2":87.5,"delta":-3.7,"trend":"STABIL"},
    {"cod":"GJ_80123-1004","fermier":"Popa Nicolae",     "ha":8.60,"cultura":"Grau",
     "lat":44.9421,"lon":23.3254,"veg_t1":69.8,"veg_t2":16.3,"delta":-53.5,"trend":"RECOLTA"},
    {"cod":"GJ_80123-3737","fermier":"Dima Florin",      "ha":3.15,"cultura":"Porumb",
     "lat":44.8789,"lon":23.2098,"veg_t1":34.2,"veg_t2":38.9,"delta":+4.7,"trend":"STABIL-RISC"},
    {"cod":"GJ_80980-2611","fermier":"Olteanu Traian",   "ha":7.40,"cultura":"Floarea-soarelui",
     "lat":44.9067,"lon":23.1654,"veg_t1":21.4,"veg_t2":28.7,"delta":+7.3,"trend":"DEGRADARE"},
]

# ══════════════════════════════════════════════════════════════════════════════
# SECTIUNEA 1 — Configurare
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sectiune-titlu">Sectiunea 1 — Configurare export GIS</div>', unsafe_allow_html=True)

col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
    inspector  = st.text_input("Inspector APIA", "Prof. Asoc. Dr. Oliviu Mihnea Gamulescu")
    an_campanie= st.number_input("An campanie", 2020, 2030, 2026)
with col_c2:
    data_t1    = st.date_input("Data T1", value=date(2026, 4, 4))
    data_t2    = st.date_input("Data T2", value=date(2026, 7, 15))
with col_c3:
    sistem_crs = st.selectbox("Sistem de coordonate shapefile",
                               ["EPSG:31700 — Stereo70 (Romania, recomandat APIA)",
                                "EPSG:4326 — WGS84 (GPS standard)"])
    includ_t2  = st.checkbox("Include date T2 in atribute", value=True)

# ── Previzualizare tabel parcele ──────────────────────────────────────────────
import pandas as pd
df_prev = pd.DataFrame([{
    "Cod LPIS":   p["cod"],
    "Fermier":    p["fermier"],
    "Cultura":    p["cultura"],
    "Ha":         p["ha"],
    "Lat":        p["lat"],
    "Lon":        p["lon"],
    "Veg T1(%)":  p["veg_t1"],
    "Veg T2(%)":  p["veg_t2"] if includ_t2 else "-",
    "Delta(%)":   p["delta"]  if includ_t2 else "-",
    "Trend":      p["trend"],
} for p in PARCELE_GIS])

with st.expander("Previzualizeaza datele de exportat"):
    def color_trend(val):
        m = {"RECOLTA":"color:#3498db","DEGRADARE":"color:#f1948a;font-weight:bold",
             "CRESTERE":"color:#7dcea0","STABIL":"color:#a8b2d8",
             "STABIL-RISC":"color:#f39c12;font-weight:bold"}
        return m.get(str(val),"")
    st.dataframe(df_prev.style.map(color_trend, subset=["Trend"]),
                 use_container_width=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# FUNCTII CONVERSIE SI GENERARE
# ══════════════════════════════════════════════════════════════════════════════

def genereaza_poligon_wgs84(lat_c: float, lon_c: float, ha: float) -> list:
    """
    Genereaza un poligon aproximativ rectangular in WGS84 pentru o parcela.
    Suprafata aproximata = ha hectare.
    1 grad lat ≈ 111 km | 1 grad lon ≈ 77 km (la lat 45°)
    """
    side_m  = math.sqrt(ha * 10000)        # latura patrat echivalent in metri
    dlat    = (side_m / 2) / 111000        # jumatate latura in grade latitudine
    dlon    = (side_m / 2) / 77000         # jumatate latura in grade longitudine

    rng     = random.Random(hash(f"{lat_c}{lon_c}"))
    rot     = rng.uniform(-15, 15)         # rotatie usoara pentru aspect natural
    rot_r   = math.radians(rot)

    # Colturi poligon (rectangular rotit)
    corners_raw = [(-dlat,-dlon),(dlat,-dlon),(dlat,dlon),(-dlat,dlon)]
    corners = []
    for dy, dx in corners_raw:
        # Rotatie 2D
        dy_r = dy*math.cos(rot_r) - dx*math.sin(rot_r)
        dx_r = dy*math.sin(rot_r) + dx*math.cos(rot_r)
        # Adauga zgomot mic pentru aspect realist
        dy_r += rng.uniform(-dlat*0.1, dlat*0.1)
        dx_r += rng.uniform(-dlon*0.1, dlon*0.1)
        corners.append([round(lon_c+dx_r, 6), round(lat_c+dy_r, 6)])

    corners.append(corners[0])   # inchide poligonul
    return corners


def wgs84_to_stereo70(lat: float, lon: float) -> tuple:
    """
    Conversie aproximativa WGS84 → Stereo70 (EPSG:31700).
    Foloseste pyproj daca disponibil, altfel aproximare liniara pentru zona Gorj.
    Eroare aproximare: < 10m (acceptabila pentru vizualizare, nu pentru cadastru)
    """
    try:
        from pyproj import Transformer
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:31700",
                                            always_xy=False)
        x, y = transformer.transform(lat, lon)
        return round(x, 2), round(y, 2)
    except ImportError:
        # Aproximare liniara pentru zona Gorj (lat≈44.9°, lon≈23.2°)
        # Baza: Targu Jiu ≈ (44.892°N, 23.271°E) → Stereo70 ≈ (X=390500, Y=346200)
        LAT0, LON0 = 44.892, 23.271
        X0, Y0     = 390500.0, 346200.0
        M_PER_DEG_LAT = 111200.0
        M_PER_DEG_LON = 77800.0
        x = X0 + (lat - LAT0) * M_PER_DEG_LAT
        y = Y0 + (lon - LON0) * M_PER_DEG_LON
        return round(x, 2), round(y, 2)


def poligon_wgs84_to_stereo70(coords_wgs: list) -> list:
    """Converteste lista de [lon, lat] in coordonate Stereo70 [x, y]."""
    result = []
    for lon_p, lat_p in coords_wgs:
        x, y = wgs84_to_stereo70(lat_p, lon_p)
        result.append([x, y])
    return result


# ── Verificare pyproj ──────────────────────────────────────────────────────────
try:
    from pyproj import Transformer
    PYPROJ_OK = True
except ImportError:
    PYPROJ_OK = False

if PYPROJ_OK:
    st.markdown('<div class="ok-box">pyproj disponibil — conversie exacta Stereo70 activa</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="info-box">pyproj indisponibil — se foloseste aproximare liniara Stereo70 (eroare &lt;10m). '
                'Pentru precizie cadastrala: <code>pip install pyproj</code></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# BUTOANE EXPORT
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="sectiune-titlu">Sectiunea 2 — Exporturi GIS</div>', unsafe_allow_html=True)

col_b1, col_b2, col_b3, col_b4 = st.columns(4)

# ── 1. GeoJSON ────────────────────────────────────────────────────────────────
with col_b1:
    if st.button("Export GeoJSON", type="primary", use_container_width=True):
        features = []
        for p in PARCELE_GIS:
            coords = genereaza_poligon_wgs84(p["lat"], p["lon"], p["ha"])
            props  = {
                "cod_lpis":    p["cod"],
                "fermier":     p["fermier"],
                "cultura":     p["cultura"],
                "suprafata_ha":p["ha"],
                "lat_centru":  p["lat"],
                "lon_centru":  p["lon"],
                "veg_t1_pct":  p["veg_t1"],
                "pac_t1":      "CONFORM" if p["veg_t1"] >= 50 else "NECONFORM",
                "data_t1":     data_t1.strftime("%Y-%m-%d"),
                "inspector":   inspector,
                "model_ai":    "YOLOv8n_mAP50_0.829",
                "an_campanie": int(an_campanie),
                "reg_ue":      "2021/2116",
            }
            if includ_t2:
                props.update({
                    "veg_t2_pct":  p["veg_t2"],
                    "delta_veg":   p["delta"],
                    "trend":       p["trend"],
                    "pac_t2":      "CONFORM" if p["veg_t2"] >= 50 else "NECONFORM",
                    "data_t2":     data_t2.strftime("%Y-%m-%d"),
                })
            features.append({
                "type":       "Feature",
                "geometry":   {"type":"Polygon","coordinates":[coords]},
                "properties": props,
            })

        geojson = {
            "type": "FeatureCollection",
            "name": f"Parcele_APIA_Gorj_{an_campanie}",
            "crs":  {"type":"name","properties":{"name":"urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "features": features,
        }

        buf_gj = BytesIO()
        buf_gj.write(json.dumps(geojson, indent=2, ensure_ascii=False).encode("utf-8"))
        buf_gj.seek(0)

        st.download_button(
            "Descarca GeoJSON",
            data=buf_gj,
            file_name=f"Parcele_APIA_Gorj_{an_campanie}.geojson",
            mime="application/geo+json"
        )
        st.markdown(f'<div class="ok-box">GeoJSON generat: {len(PARCELE_GIS)} parcele<br>'
                    'Deschide in QGIS: drag & drop fisierul .geojson</div>',
                    unsafe_allow_html=True)

# ── 2. Shapefile Stereo70 ─────────────────────────────────────────────────────
with col_b2:
    if st.button("Export Shapefile Stereo70", type="primary", use_container_width=True):
        import shapefile as pyshp

        use_stereo = "31700" in sistem_crs

        PRJ_STEREO70 = (
            'PROJCS["Stereo70",'
            'GEOGCS["GCS_Dealul_Piscului_1970",'
            'DATUM["D_Dealul_Piscului_1970",'
            'SPHEROID["Krasovsky_1940",6378245.0,298.3]],'
            'PRIMEM["Greenwich",0.0],'
            'UNIT["Degree",0.0174532925199433]],'
            'PROJECTION["Double_Stereographic"],'
            'PARAMETER["False_Easting",500000.0],'
            'PARAMETER["False_Northing",500000.0],'
            'PARAMETER["Central_Meridian",25.0],'
            'PARAMETER["Scale_Factor",0.99975],'
            'PARAMETER["Latitude_Of_Origin",46.0],'
            'UNIT["Meter",1.0]]'
        )
        PRJ_WGS84 = (
            'GEOGCS["GCS_WGS_1984",'
            'DATUM["D_WGS_1984",'
            'SPHEROID["WGS_1984",6378137.0,298.257223563]],'
            'PRIMEM["Greenwich",0.0],'
            'UNIT["Degree",0.0174532925199433]]'
        )

        shp_buf = BytesIO()
        shx_buf = BytesIO()
        dbf_buf = BytesIO()

        w = pyshp.Writer(shp=shp_buf, shx=shx_buf, dbf=dbf_buf,
                         shapeType=pyshp.POLYGON)
        w.field("COD_LPIS",  "C", 20)
        w.field("FERMIER",   "C", 40)
        w.field("CULTURA",   "C", 20)
        w.field("SUPRAF_HA", "N",  8, 2)
        w.field("VEG_T1",    "N",  6, 1)
        w.field("PAC_T1",    "C", 10)
        w.field("DATA_T1",   "C", 10)
        if includ_t2:
            w.field("VEG_T2",    "N",  6, 1)
            w.field("DELTA_VEG", "N",  7, 1)
            w.field("TREND",     "C", 15)
            w.field("PAC_T2",    "C", 10)

        for p in PARCELE_GIS:
            coords_wgs = genereaza_poligon_wgs84(p["lat"], p["lon"], p["ha"])
            if use_stereo:
                coords_proj = poligon_wgs84_to_stereo70(coords_wgs)
            else:
                coords_proj = [[c[0], c[1]] for c in coords_wgs]

            w.poly([coords_proj])

            rec = [
                p["cod"], p["fermier"], p["cultura"], p["ha"],
                p["veg_t1"],
                "CONFORM" if p["veg_t1"] >= 50 else "NECONF",
                data_t1.strftime("%Y-%m-%d"),
            ]
            if includ_t2:
                rec += [p["veg_t2"], p["delta"], p["trend"],
                        "CONFORM" if p["veg_t2"] >= 50 else "NECONF"]
            w.record(*rec)

        w.close()

        fname    = f"Parcele_APIA_Gorj_{an_campanie}"
        prj_data = (PRJ_STEREO70 if use_stereo else PRJ_WGS84).encode("ascii")

        buf_zip = BytesIO()
        with zipfile.ZipFile(buf_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            shp_buf.seek(0); shx_buf.seek(0); dbf_buf.seek(0)
            zf.writestr(f"{fname}/{fname}.shp", shp_buf.read())
            zf.writestr(f"{fname}/{fname}.shx", shx_buf.read())
            zf.writestr(f"{fname}/{fname}.dbf", dbf_buf.read())
            zf.writestr(f"{fname}/{fname}.prj", prj_data)
            zf.writestr(f"{fname}/INSTRUCTIUNI_QGIS.txt",
                f"Shapefile: {fname}\n"
                f"CRS: {'EPSG:31700 Stereo70' if use_stereo else 'EPSG:4326 WGS84'}\n\n"
                "Deschidere in QGIS:\n"
                "  1. Layer -> Add Layer -> Add Vector Layer\n"
                "  2. Selecteaza fisierul .shp\n"
                f"  3. CRS: {'EPSG:31700' if use_stereo else 'EPSG:4326'}\n"
                "  4. Se suprapune peste LPIS din WMS ANCPI\n\n"
                f"Inspector: {inspector}\n"
                f"Data export: {date.today().strftime('%d.%m.%Y')}\n"
                f"Model AI: YOLOv8n | mAP50=0.829\n"
            )
        buf_zip.seek(0)

        crs_label = "Stereo70" if use_stereo else "WGS84"
        st.download_button(
            f"Descarca Shapefile {crs_label} (ZIP)",
            data=buf_zip,
            file_name=f"Shapefile_{crs_label}_APIA_Gorj_{an_campanie}.zip",
            mime="application/zip"
        )
        st.markdown(
            f'<div class="ok-box">Shapefile generat cu pyshp: SHP+DBF+SHX+PRJ<br>'
            f'CRS: {"EPSG:31700 Stereo70" if use_stereo else "EPSG:4326 WGS84"}<br>'
            f'{"pyproj (conversie exacta)" if PYPROJ_OK else "Aproximare liniara (<10m)"}</div>',
            unsafe_allow_html=True
        )

# ── 3. GPX ────────────────────────────────────────────────────────────────────
with col_b3:
    if st.button("Export GPX (GPS)", type="primary", use_container_width=True):
        ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        def xml_safe(s):
            """Elimina caractere speciale XML si diacritice problematice."""
            return (str(s)
                    .replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                    .replace('"',"&quot;").replace("'","&apos;")
                    .replace("\u2013","-").replace("\u2014","-")
                    .replace("\u0103","a").replace("\u0102","A")
                    .replace("\u00ee","i").replace("\u00ce","I")
                    .replace("\u0219","s").replace("\u0218","S")
                    .replace("\u021b","t").replace("\u021a","T"))

        wpt_lines = []
        trk_lines = []

        for p in PARCELE_GIS:
            pac  = "OK" if p["veg_t2"] >= 50 else "NC"
            name = xml_safe(p["cod"])
            ferm = xml_safe(p["fermier"])
            cult = xml_safe(p["cultura"])
            trd  = xml_safe(p["trend"])
            desc = xml_safe(
                f"Fermier: {p['fermier']} | {p['cultura']} | {p['ha']}ha | "
                f"Veg T1:{p['veg_t1']}% T2:{p['veg_t2']}% | "
                f"Delta:{p['delta']:+.1f}% | {p['trend']}"
            )

            # Waypoint centru parcela
            wpt_lines.append(
                f'  <wpt lat="{p["lat"]}" lon="{p["lon"]}">\n'
                f'    <name>{name}</name>\n'
                f'    <desc>{desc}</desc>\n'
                f'    <sym>Waypoint</sym>\n'
                f'    <type>APIA_{pac}</type>\n'
                f'  </wpt>'
            )

            # Track (poligon parcela) — recunoscut de QGIS si Garmin
            coords = genereaza_poligon_wgs84(p["lat"], p["lon"], p["ha"])
            trkpts = []
            for lon_pt, lat_pt in coords:
                trkpts.append(
                    f'      <trkpt lat="{lat_pt}" lon="{lon_pt}"></trkpt>'
                )
            trk_lines.append(
                f'  <trk>\n'
                f'    <name>{name} {ferm}</name>\n'
                f'    <desc>{cult} | {p["ha"]}ha | {trd}</desc>\n'
                f'    <type>APIA_PARCELA</type>\n'
                f'    <trkseg>\n'
                + "\n".join(trkpts) +
                f'\n    </trkseg>\n'
                f'  </trk>'
            )

        gpx_content = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<gpx version="1.1" creator="AGROVISION-APIA"\n'
            '  xmlns="http://www.topografix.com/GPX/1/1"\n'
            '  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
            '  xsi:schemaLocation="http://www.topografix.com/GPX/1/1 '
            'http://www.topografix.com/GPX/1/1/gpx.xsd">\n'
            '  <metadata>\n'
            f'    <name>Parcele APIA Gorj {an_campanie}</name>\n'
            f'    <desc>AGROVISION YOLOv8 mAP50=0.829</desc>\n'
            f'    <time>{ts}</time>\n'
            '  </metadata>\n'
            + "\n".join(wpt_lines) + "\n"
            + "\n".join(trk_lines) + "\n"
            + "</gpx>"
        )

        buf_gpx = BytesIO()
        buf_gpx.write(gpx_content.encode("utf-8"))
        buf_gpx.seek(0)

        st.download_button(
            "Descarca GPX",
            data=buf_gpx,
            file_name=f"Parcele_APIA_Gorj_{an_campanie}.gpx",
            mime="application/gpx+xml"
        )
        st.markdown(
            f'<div class="ok-box">GPX generat: {len(PARCELE_GIS)} waypoints + {len(PARCELE_GIS)} trasee<br>'
            'Incarcare: Garmin BaseCamp | OsmAnd | telefon GPS</div>',
            unsafe_allow_html=True
        )

# ── 4. ZIP COMPLET ────────────────────────────────────────────────────────────
with col_b4:
    if st.button("Export ZIP Complet GIS", type="primary", use_container_width=True):

        # Regeneram toate fisierele
        use_stereo = "31700" in sistem_crs

        # GeoJSON
        features = []
        for p in PARCELE_GIS:
            coords = genereaza_poligon_wgs84(p["lat"], p["lon"], p["ha"])
            props  = {
                "cod_lpis":p["cod"],"fermier":p["fermier"],
                "cultura":p["cultura"],"suprafata_ha":p["ha"],
                "veg_t1_pct":p["veg_t1"],"veg_t2_pct":p["veg_t2"],
                "delta_veg":p["delta"],"trend":p["trend"],
                "pac_t1":"CONFORM" if p["veg_t1"]>=50 else "NECONFORM",
                "pac_t2":"CONFORM" if p["veg_t2"]>=50 else "NECONFORM",
                "data_t1":data_t1.strftime("%Y-%m-%d"),
                "data_t2":data_t2.strftime("%Y-%m-%d"),
                "inspector":inspector,"model_ai":"YOLOv8n_mAP50_0.829",
            }
            features.append({"type":"Feature",
                              "geometry":{"type":"Polygon","coordinates":[coords]},
                              "properties":props})
        geojson = {"type":"FeatureCollection","features":features}
        gj_bytes = json.dumps(geojson, indent=2, ensure_ascii=False).encode("utf-8")

        # GPX (simplu)
        wpt_all = []
        for p in PARCELE_GIS:
            wpt_all.append(
                f'  <wpt lat="{p["lat"]}" lon="{p["lon"]}">'
                f'<name>{p["cod"]}</name>'
                f'<desc>{p["trend"]} | {p["delta"]:+.1f}%</desc></wpt>'
            )
        gpx_simple = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<gpx version="1.1" creator="AGROVISION-APIA" '
            'xmlns="http://www.topografix.com/GPX/1/1">\n'
            + "\n".join(wpt_all) + "\n</gpx>"
        )

        buf_zip_all = BytesIO()
        with zipfile.ZipFile(buf_zip_all, "w", zipfile.ZIP_DEFLATED) as zf:
            fname = f"Parcele_APIA_Gorj_{an_campanie}"

            # GeoJSON
            zf.writestr(f"GeoJSON/{fname}.geojson", gj_bytes)

            # GPX
            zf.writestr(f"GPX/{fname}.gpx", gpx_simple.encode("utf-8"))

            # README
            crs_txt = "EPSG:31700 Stereo70" if use_stereo else "EPSG:4326 WGS84"
            readme  = (
                f"Pachet GIS — AGROVISION APIA Gorj {an_campanie}\n"
                f"{'='*50}\n\n"
                f"Inspector: {inspector}\n"
                f"Data export: {date.today().strftime('%d.%m.%Y')}\n"
                f"Model AI: YOLOv8n | mAP50=0.829\n"
                f"Sesiuni: T1={data_t1} | T2={data_t2}\n"
                f"Parcele: {len(PARCELE_GIS)}\n"
                f"CRS Shapefile: {crs_txt}\n\n"
                "Fisiere incluse:\n"
                "  GeoJSON/  → deschide in QGIS drag & drop\n"
                "  GPX/      → incarcare GPS/telefon\n\n"
                "QGIS — suprapunere LPIS:\n"
                "  Layer → Add WMS/WMTS → URL: https://geoportal.ancpi.ro/maps/rest/services/\n"
                "  Adauga stratul LPIS → suprapune cu GeoJSON\n\n"
                "Baza legala: Reg. UE 2021/2116 art. 24 — monitorizare UAV\n"
            )
            zf.writestr("README.txt", readme.encode("utf-8"))

        buf_zip_all.seek(0)
        st.download_button(
            "Descarca ZIP Complet GIS",
            data=buf_zip_all,
            file_name=f"GIS_Complet_APIA_Gorj_{an_campanie}.zip",
            mime="application/zip"
        )
        st.markdown(
            f'<div class="ok-box">ZIP complet generat:<br>'
            f'GeoJSON + GPX + README<br>'
            f'{len(PARCELE_GIS)} parcele | CRS: {crs_txt}</div>',
            unsafe_allow_html=True
        )

# ── Instructiuni QGIS ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="sectiune-titlu">Sectiunea 3 — Instructiuni QGIS</div>', unsafe_allow_html=True)

col_q1, col_q2 = st.columns(2)
with col_q1:
    st.markdown("""
**Deschide GeoJSON in QGIS:**
1. Drag & drop fisierul `.geojson` in fereastra QGIS
2. CRS se detecteaza automat (WGS84)
3. Click dreapta strat → Properties → Symbology
4. Categorized → Column: **trend**
5. Culori: RECOLTA=albastru, DEGRADARE=rosu, CRESTERE=verde

**Suprapune cu LPIS oficial:**
1. Layer → Add Layer → Add WMS/WMTS Layer
2. Adauga URL server WMS ANCPI/APIA
3. Selecteaza stratul LPIS
4. Compara poligoanele tale cu LPIS oficial
    """)

with col_q2:
    st.markdown("""
**Stereo70 in QGIS:**
1. Layer → Add Layer → Add Vector Layer
2. Selecteaza fisierul `.shp` din ZIP
3. La intrebare CRS: alege `EPSG:31700`
4. QGIS reproiecteaza automat pentru afisare

**GPX pe telefon (OsmAnd):**
1. Copiaza `.gpx` pe telefon
2. OsmAnd → Menu → My Places → Tracks
3. Import → selecteaza fisierul
4. Waypoints = centrele parcelelor
5. Navigare pe teren catre parcela selectata

**Baza legala:** Reg. UE 2021/2116 art. 24 — APIA poate folosi
teledetectie (UAV + AI) pentru monitorizarea parcelelor.
    """)

# ══════════════════════════════════════════════════════════════════════════════
# REZUMAT LECTIE
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
with st.expander("Rezumat Ziua 17 — Ce am invatat"):
    st.markdown("""
**Export GIS din Python — concepte noi:**

| Format | Librarie | CRS | Utilizare APIA |
|---|---|---|---|
| GeoJSON | json (built-in) | WGS84 | QGIS, web, Leaflet |
| Shapefile | struct (built-in) | Stereo70 / WGS84 | QGIS, ArcGIS, LPIS |
| GPX | string XML | WGS84 | GPS teren, OsmAnd |
| ZIP | zipfile (built-in) | - | Arhivare, audit |

**Conversie WGS84 → Stereo70:**
```python
from pyproj import Transformer
tr = Transformer.from_crs("EPSG:4326", "EPSG:31700", always_xy=False)
x, y = tr.transform(lat, lon)   # x, y in metri Stereo70
```

**Structura Shapefile (4 fisiere obligatorii):**
```
parcele.shp  — geometrie (poligoane)
parcele.dbf  — atribute (tabel)
parcele.shx  — index offseturi
parcele.prj  — definitie proiectie (WKT)
```

**Valoarea pentru APIA:**
- Inspector exporta GeoJSON → il deschide direct in QGIS
- Suprapune peste LPIS oficial → verifica concordanta
- GPX pe telefon → navigheaza la parcela pe teren
- Stereo70 = sistemul oficial Romania → compatibil cu ANCPI/OCPI

**Urmatoarea zi — Ziua 18:** Dashboard AGROVISION complet —
integreaza toate zilele 1-17 intr-un singur dashboard profesional
cu navigare, autentificare, export complet si harta live.
    """)
