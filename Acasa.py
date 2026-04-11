"""
BLOC 3 — Deep Learning YOLOv8
Pagina principala — FINALIZAT 40/40 zile (9 aprilie 2026)
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
st.sidebar.markdown(f"**Progres:** 40 / 40 zile — COMPLET")
st.sidebar.progress(1.0)
st.sidebar.markdown(f"**Data:** {date.today().strftime('%d.%m.%Y')}")
st.sidebar.divider()
st.sidebar.markdown("**Model activ:**")
st.sidebar.code("best_v1_mAP083_20260403.pt\nmAP50 = 0.829")
st.sidebar.divider()
st.sidebar.markdown("**Live pe internet:**")
st.sidebar.caption("agrovision-bloc3-8qydbmd2z3zgmpqk4ygtsg\n.streamlit.app")

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
        <div style='font-size:28px; font-weight:800; color:#0052A5;'>40</div>
        <div style='font-size:12px; color:#666;'>Zile parcurse</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown("""<div class="kpi-card">
        <div style='font-size:28px; font-weight:800; color:#28a745;'>40</div>
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
st.subheader("Bloc 3 FINALIZAT — 40/40 zile YOLOv8 (9 aprilie 2026)")

col_s1, col_s2 = st.columns(2)

# ── COLOANA STANGA ────────────────────────────────────────────────────────────
with col_s1:

    st.markdown('<div class="bloc-titlu">Zilele 1-5 — Fundamente YOLOv8</div>',
                unsafe_allow_html=True)
    for nr, desc in [
        ("1", "Arhitectura YOLO — variante n/s/m/l/x, termeni cheie"),
        ("2", "Prima detectie — model.predict(), BBox, tabel rezultate"),
        ("3", "Detectie drone — ExG/VARI/GLI, segmentare HSV, risc PAC"),
        ("4", "Batch analiza — upload multiple, progres, Excel 4 sheet-uri"),
        ("5", "Format Dataset YOLO — structura, adnotari .txt, data.yaml"),
    ]:
        st.markdown(f'<div class="zi-completa">✅ <b>Ziua {nr}</b> — {desc}</div>',
                    unsafe_allow_html=True)

    st.markdown('<div class="bloc-titlu">Zilele 6-10 — Dataset & Adnotare</div>',
                unsafe_allow_html=True)
    for nr, desc in [
        ("6",  "Adnotare LabelImg — ghid instalare, verificator .txt"),
        ("7",  "Split dataset — shuffle, train/val/test 70/20/10, ZIP"),
        ("8",  "Tiling imagini mari — 4608px → patch 640px cu overlap"),
        ("9",  "Augmentare — flip, rot90, brightness, zgomot gaussian"),
        ("10", "Validare dataset — perechi complete, BBox, class imbalance"),
    ]:
        st.markdown(f'<div class="zi-completa">✅ <b>Ziua {nr}</b> — {desc}</div>',
                    unsafe_allow_html=True)

    st.markdown('<div class="bloc-titlu">Zilele 11-14 — Antrenament & Evaluare</div>',
                unsafe_allow_html=True)
    for nr, desc in [
        ("11", "Antrenament YOLOv8 — transfer learning, epochs, loss curves"),
        ("12", "Inferenta — conf, IoU, NMS, vizualizare BBox, export Word"),
        ("13", "Evaluare model — Confusion Matrix, PR Curve, F1, mAP"),
        ("14", "Pipeline APIA — imagine → detectie → raport Word oficial"),
    ]:
        st.markdown(f'<div class="zi-completa">✅ <b>Ziua {nr}</b> — {desc}</div>',
                    unsafe_allow_html=True)

    st.markdown('<div class="bloc-titlu">Zilele 15-20 — Aplicatie Completa</div>',
                unsafe_allow_html=True)
    for nr, desc in [
        ("15", "Batch procesare — progress bar, ZIP cu rapoarte multiple"),
        ("16", "Comparatie temporala T1/T2 — delta vegetatie, trend"),
        ("17", "Export GIS — GeoJSON, Shapefile Stereo70, GPX tracks"),
        ("18", "Dashboard AGROVISION — KPI, harta Folium, live detection"),
        ("19", "Autentificare + Roluri — inspector/admin/viewer, SHA-256"),
        ("20", "Rapoarte PDF — fpdf2, antet APIA, tabel colorat, semnatura"),
    ]:
        st.markdown(f'<div class="zi-completa">✅ <b>Ziua {nr}</b> — {desc}</div>',
                    unsafe_allow_html=True)

# ── COLOANA DREAPTA ───────────────────────────────────────────────────────────
with col_s2:

    st.markdown('<div class="bloc-titlu">Zilele 21-25 — Cloud & API</div>',
                unsafe_allow_html=True)
    for nr, desc in [
        ("21", "Deployment Cloud — GitHub + Streamlit Cloud, gratuit"),
        ("22", "Baza date SQLite — sesiuni, detectii, filtrare, export"),
        ("23", "Notificari email — SMTP_SSL, Gmail App Password, HTML"),
        ("24", "API REST FastAPI — 7 endpoint-uri, Swagger UI, CORS"),
        ("25", "Hugging Face Hub — best.pt pe cloud, download automat"),
    ]:
        st.markdown(f'<div class="zi-completa">✅ <b>Ziua {nr}</b> — {desc}</div>',
                    unsafe_allow_html=True)

    st.markdown('<div class="bloc-titlu">Zilele 26-30 — ML & Sinteza</div>',
                unsafe_allow_html=True)
    for nr, desc in [
        ("26", "Analiza NDVI Spectral — ExG, VARI, GLI, NGRDI, NDVI_sim"),
        ("27", "Clustering K-Means — 10 parcele LPIS, Silhouette, Folium"),
        ("28", "Random Forest Clasificare — risc PAC, Confusion Matrix"),
        ("29", "Random Forest Regresie — productie t/ha, R², MAE, RMSE"),
        ("30", "Sinteza Bloc 3 — certificat Word, demo live, roadmap"),
    ]:
        st.markdown(f'<div class="zi-completa">✅ <b>Ziua {nr}</b> — {desc}</div>',
                    unsafe_allow_html=True)

    st.markdown('<div class="bloc-titlu">Zilele 31-33 — GIS & QGIS</div>',
                unsafe_allow_html=True)
    for nr, desc in [
        ("31", "QGIS WMS Live — straturi oficiale ANCPI, ortofoto, cadastru"),
        ("32", "Analiza Spatiala — Haversine, matrice distante, ruta greedy, heatmap risc"),
        ("33", "Raport Control Teren — Word oficial APIA, Stereo 70, ruta inspectie"),
    ]:
        st.markdown(f'<div class="zi-completa">✅ <b>Ziua {nr}</b> — {desc}</div>',
                    unsafe_allow_html=True)

    st.markdown('<div class="bloc-titlu">Zilele 34-36 — Nivel Ministerial</div>',
                unsafe_allow_html=True)
    for nr, desc in [
        ("34", "Dashboard PAC Ministerial — KPI, culturi, plati, conformitate, harta UAT"),
        ("35", "Export Excel Multi-Sheet — date ministeriale, 4 sheet-uri, formatare"),
        ("36", "Raport PDF Ministerial — multi-pagina, grafice, tabel UAT, fpdf2"),
    ]:
        st.markdown(f'<div class="zi-completa">✅ <b>Ziua {nr}</b> — {desc}</div>',
                    unsafe_allow_html=True)

    st.markdown('<div class="bloc-titlu">Zilele 37-40 — Agenti AI & Finalizare</div>',
                unsafe_allow_html=True)
    for nr, desc in [
        ("37", "Multi-Agenti Simulare — orchestrator + 4 agenti specializati, st.status()"),
        ("38", "Multi-Agenti Avansat — paralelism threading, orchestrator dinamic, retry, SQLite"),
        ("39", "Generator Articol ISI — draft Word MDPI, IMRaD, date reale mAP50=0.829"),
        ("40", "Sinteza Finala — timeline, radar competente, certificat UCB, roadmap"),
    ]:
        st.markdown(f'<div class="zi-completa">✅ <b>Ziua {nr}</b> — {desc}</div>',
                    unsafe_allow_html=True)

st.divider()

# ─── INFO MODEL + ARTICOL + LIVE ─────────────────────────────────────────────
col_m1, col_m2, col_m3 = st.columns(3)

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
        Conferinta: <strong>IEEE FINE 2026</strong>, Osaka<br>
        Paper ID: paper_28<br>
        Track: IoT, Vehicular & Industrial<br>
        Status: <strong>In asteptare review</strong><br>
        Depus: 4 aprilie 2026, ora 16:45<br>
        Termen decizie: ~4-6 saptamani
    </div>
    """, unsafe_allow_html=True)

with col_m3:
    st.markdown("""
    <div style='background:#d4edda; border-radius:10px; padding:16px; border-left:4px solid #28a745;'>
        <strong style='color:#155724;'>Aplicatie Live pe Internet</strong><br><br>
        GitHub: olimihnea-spec/agrovision-bloc3<br>
        Model HF: oliviu-gamulescu/agrovision-yolov8<br>
        Status: <strong>ONLINE 24/7</strong><br>
        Cost: <strong>0 RON</strong><br>
        Deploy: 6 aprilie 2026<br>
        Stack: Streamlit Cloud + HuggingFace
    </div>
    """, unsafe_allow_html=True)

st.divider()
st.success("""
**BLOC 3 COMPLET — 40/40 zile finalizate (9 aprilie 2026)**
Selecteaza orice zi din **meniul lateral stang** pentru a accesa modulul dorit.
Toate cele 40 de module sunt complete si functionale.
""")
