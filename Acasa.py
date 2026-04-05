"""
BLOC 3 — Deep Learning YOLOv8
Pagina principala — progres real, 21 zile parcurse
Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu | UCB Targu Jiu | APIA CJ Gorj
"""

import streamlit as st
from datetime import date

st.set_page_config(
    page_title="AGROVISION — YOLOv8 Drone",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.zi-completa {
    background: #d4edda;
    border-left: 4px solid #28a745;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 4px 0;
    font-size: 13px;
}
.zi-urmatoare {
    background: #fff3cd;
    border-left: 4px solid #ffc107;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 4px 0;
    font-size: 13px;
}
.zi-planificata {
    background: #f8f9fa;
    border-left: 4px solid #dee2e6;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 4px 0;
    font-size: 13px;
    color: #999;
}
.bloc-titlu {
    background: #0052A5;
    color: white;
    border-radius: 8px;
    padding: 10px 16px;
    font-weight: 700;
    font-size: 14px;
    margin: 16px 0 8px 0;
}
.kpi-card {
    background: white;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border-top: 4px solid #0052A5;
}
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
st.sidebar.markdown("""
<div style='text-align:center; padding:10px 0;'>
    <div style='font-size:40px;'>🌾</div>
    <div style='font-size:18px; font-weight:700; color:#0052A5;'>AGROVISION</div>
    <div style='font-size:11px; color:#666;'>YOLOv8 | Detectie Culturi Drone</div>
</div>
""", unsafe_allow_html=True)
st.sidebar.caption("Prof. Asoc. Dr. Oliviu Mihnea Gamulescu")
st.sidebar.caption("UCB Targu Jiu | APIA CJ Gorj")
st.sidebar.divider()
st.sidebar.markdown(f"**Progres:** 21 / 40 zile")
st.sidebar.progress(21/40)
st.sidebar.markdown(f"**Data:** {date.today().strftime('%d.%m.%Y')}")
st.sidebar.divider()
st.sidebar.markdown("**Model activ:**")
st.sidebar.code("best_v1_mAP083_20260403.pt\nmAP50 = 0.829")

# ─── TITLU PRINCIPAL ──────────────────────────────────────────────────────────
st.markdown("""
<div style='display:flex; align-items:center; gap:16px; margin-bottom:16px;'>
    <div style='font-size:56px;'>🌾</div>
    <div>
        <h1 style='margin:0; font-size:32px; color:#0052A5; font-weight:800;'>
            AGROVISION v1.0
        </h1>
        <p style='margin:0; color:#546e7a; font-size:15px;'>
            Sistem AI de detectie culturi agricole din imagini drone
            &nbsp;|&nbsp; YOLOv8 &nbsp;|&nbsp; Streamlit &nbsp;|&nbsp;
            UCB Targu Jiu &nbsp;|&nbsp; APIA CJ Gorj
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── KPI-URI PROGRES ──────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown("""<div class="kpi-card">
        <div style='font-size:28px; font-weight:800; color:#0052A5;'>21</div>
        <div style='font-size:12px; color:#666;'>Zile parcurse</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown("""<div class="kpi-card">
        <div style='font-size:28px; font-weight:800; color:#28a745;'>19</div>
        <div style='font-size:12px; color:#666;'>Module active</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown("""<div class="kpi-card">
        <div style='font-size:28px; font-weight:800; color:#dc3545;'>0.829</div>
        <div style='font-size:12px; color:#666;'>mAP50 model</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown("""<div class="kpi-card">
        <div style='font-size:28px; font-weight:800; color:#fd7e14;'>10</div>
        <div style='font-size:12px; color:#666;'>Parcele LPIS Gorj</div>
    </div>""", unsafe_allow_html=True)
with c5:
    st.markdown("""<div class="kpi-card">
        <div style='font-size:28px; font-weight:800; color:#6f42c1;'>3</div>
        <div style='font-size:12px; color:#666;'>Clase detectate</div>
    </div>""", unsafe_allow_html=True)

st.divider()

# ─── PROGRES ZILE ─────────────────────────────────────────────────────────────
st.subheader("Progres Bloc 3 — 40 de zile YOLOv8")

col_s1, col_s2 = st.columns(2)

# ── COLOANA STANGA: Zilele 1-14 (Fundamente + Dataset + Antrenament) ──────────
with col_s1:

    st.markdown('<div class="bloc-titlu">Zilele 1-5 — Fundamente YOLOv8</div>',
                unsafe_allow_html=True)
    zile_1_5 = [
        ("1", "Arhitectura YOLO — variante n/s/m/l/x, termeni cheie"),
        ("2", "Prima detectie — model.predict(), BBox, tabel rezultate"),
        ("3", "Detectie drone — ExG/VARI/GLI, segmentare HSV, risc PAC"),
        ("4", "Batch analiza — upload multiple, progres, Excel 4 sheet-uri"),
        ("5", "Format Dataset YOLO — structura, adnotari .txt, data.yaml"),
    ]
    for nr, desc in zile_1_5:
        st.markdown(f'<div class="zi-completa">✅ <strong>Ziua {nr}</strong> — {desc}</div>',
                    unsafe_allow_html=True)

    st.markdown('<div class="bloc-titlu">Zilele 6-10 — Dataset & Adnotare</div>',
                unsafe_allow_html=True)
    zile_6_10 = [
        ("6",  "Adnotare LabelImg — ghid instalare, verificator .txt"),
        ("7",  "Split dataset — shuffle, train/val/test 70/20/10, ZIP"),
        ("8",  "Tiling imagini mari — 4608px → patch 640px cu overlap"),
        ("9",  "Augmentare — flip, rot90, brightness, zgomot gaussian"),
        ("10", "Validare dataset — perechi complete, BBox, class imbalance"),
    ]
    for nr, desc in zile_6_10:
        st.markdown(f'<div class="zi-completa">✅ <strong>Ziua {nr}</strong> — {desc}</div>',
                    unsafe_allow_html=True)

    st.markdown('<div class="bloc-titlu">Zilele 11-14 — Antrenament & Evaluare</div>',
                unsafe_allow_html=True)
    zile_11_14 = [
        ("11", "Antrenament YOLOv8 — transfer learning, epochs, loss curves"),
        ("12", "Inferenta — conf, IoU, NMS, vizualizare BBox, export Word"),
        ("13", "Evaluare model — Confusion Matrix, PR Curve, F1, mAP"),
        ("14", "Pipeline APIA — imagine → detectie → raport Word oficial"),
    ]
    for nr, desc in zile_11_14:
        st.markdown(f'<div class="zi-completa">✅ <strong>Ziua {nr}</strong> — {desc}</div>',
                    unsafe_allow_html=True)

# ── COLOANA DREAPTA: Zilele 15-21 (Aplicatie completa) + Urmatoarele ─────────
with col_s2:

    st.markdown('<div class="bloc-titlu">Zilele 15-21 — Aplicatie Completa</div>',
                unsafe_allow_html=True)
    zile_15_21 = [
        ("15", "Batch procesare — progress bar, ZIP cu rapoarte multiple"),
        ("16", "Comparatie temporala T1/T2 — delta vegetatie, trend"),
        ("17", "Export GIS — GeoJSON, Shapefile Stereo70, GPX tracks"),
        ("18", "Dashboard AGROVISION — KPI, harta Folium, live detection"),
        ("19", "Autentificare + Roluri — inspector/admin/viewer, SHA-256"),
        ("20", "Rapoarte PDF — fpdf2, antet APIA, tabel colorat, semnatura"),
        ("21", "Deployment Cloud — GitHub privat, Streamlit Cloud, gratuit"),
    ]
    for nr, desc in zile_15_21:
        st.markdown(f'<div class="zi-completa">✅ <strong>Ziua {nr}</strong> — {desc}</div>',
                    unsafe_allow_html=True)

    st.markdown('<div class="bloc-titlu" style="background:#28a745;">Zilele 22-25 — Urmatoarele</div>',
                unsafe_allow_html=True)
    zile_urm = [
        ("22", "Baza de date SQLite — istoric detecții, cautare, filtrare"),
        ("23", "Notificari email — alerta automata neconformitati APIA"),
        ("24", "API REST FastAPI — AGROVISION ca serviciu web"),
        ("25", "Integrare model Hugging Face — best.pt pe cloud"),
    ]
    for nr, desc in zile_urm:
        stil = "zi-urmatoare" if nr == "22" else "zi-planificata"
        prefix = "▶" if nr == "22" else "○"
        st.markdown(f'<div class="{stil}">{prefix} <strong>Ziua {nr}</strong> — {desc}</div>',
                    unsafe_allow_html=True)

    st.markdown('<div class="bloc-titlu" style="background:#6c757d;">Zilele 26-40 — Planificate</div>',
                unsafe_allow_html=True)
    zile_plan = [
        ("26-28", "Analiza avansata — statistici ISI, NDVI integrat"),
        ("29-32", "Multi-utilizatori — baza de date fermieri reali"),
        ("33-36", "Integrare QGIS — WMS live, harti oficiale"),
        ("37-40", "Articol ISI complet — date reale, figuri, submisie"),
    ]
    for perioada, desc in zile_plan:
        st.markdown(f'<div class="zi-planificata">○ <strong>Zilele {perioada}</strong> — {desc}</div>',
                    unsafe_allow_html=True)

st.divider()

# ─── INFO MODEL + ARTICOL ────────────────────────────────────────────────────
col_m1, col_m2 = st.columns(2)

with col_m1:
    st.markdown("""
    <div style='background:#e8f4fd; border-radius:10px; padding:16px; border-left:4px solid #0052A5;'>
        <strong style='color:#0052A5;'>Model antrenat real — best.pt</strong><br><br>
        Fisier: best_v1_mAP083_20260403.pt<br>
        mAP50: <strong>0.829</strong> (82.9%)<br>
        Precision: 0.641 | Recall: 0.667<br>
        Clase: vegetatie / sol_gol / apa<br>
        Dataset: 7 imagini Gorj, augmentat 7x<br>
        Antrenat: 3 aprilie 2026 | 50 epoch-uri
    </div>
    """, unsafe_allow_html=True)

with col_m2:
    st.markdown("""
    <div style='background:#fff3cd; border-radius:10px; padding:16px; border-left:4px solid #ffc107;'>
        <strong style='color:#856404;'>Articol stiintific depus</strong><br><br>
        Conferinta: <strong>IEEE FINE 2026</strong>, Osaka, Japonia<br>
        Paper ID: paper_28<br>
        Track: IoT, Vehicular & Industrial Networking<br>
        Status: <strong>In asteptare review</strong><br>
        Depus: 4 aprilie 2026, ora 16:45<br>
        Termen decizie: ~4-6 saptamani
    </div>
    """, unsafe_allow_html=True)

st.divider()
st.info("""
Selecteaza o zi din **meniul lateral stang** pentru a accesa modulul dorit.
Zilele marcate cu ✅ sunt complete si functionale.
""")
