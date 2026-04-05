"""
BLOC 3 — Deep Learning YOLOv8, Ziua 1
Arhitectura YOLO — ce este, cum functioneaza, variante, instalare
Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu | UCB Targu Jiu | APIA CJ Gorj

CONCEPT CHEIE:
  YOLO = You Only Look Once — detectie obiecte intr-o singura trecere prin retea
  YOLOv8 = versiunea 8, dezvoltata de Ultralytics (2023)
  from ultralytics import YOLO   — import principal
  model = YOLO("yolov8n.pt")     — incarca model pre-antrenat (n=nano)
  results = model.predict(...)   — ruleaza inferenta pe o imagine
"""

import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from io import BytesIO
import numpy as np

st.set_page_config(page_title="Arhitectura YOLO — Ziua 1", layout="wide")

st.markdown("""
<style>
.titlu { color:#1565c0; font-size:1.05rem; font-weight:700;
         border-bottom:2px solid #1565c0; padding-bottom:4px; margin-bottom:12px; }
.card  { background:#e3f2fd; border-left:4px solid #1565c0;
         border-radius:6px; padding:12px 16px; margin-bottom:8px; }
.card-verde { background:#e8f5e9; border-left:4px solid #2e7d32;
              border-radius:6px; padding:12px 16px; margin-bottom:8px; }
.card-gri   { background:#f5f5f5; border-left:4px solid #757575;
              border-radius:6px; padding:12px 16px; margin-bottom:8px; }
</style>
""", unsafe_allow_html=True)

st.title("Ziua 1 — Arhitectura YOLOv8")
st.markdown("**Ce este YOLO, cum functioneaza si de ce il folosim pentru imagini drone**")
st.markdown("---")

# ─── SECTIUNEA 1: Ce este YOLO ────────────────────────────────────────────────
st.markdown('<p class="titlu">Ce este YOLO?</p>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("""
    <div class="card">
        <strong>YOLO = You Only Look Once</strong><br><br>
        Un algoritm de <strong>detectie obiecte</strong> care analizeaza intreaga imagine
        o singura data si detecteaza simultan <em>toate obiectele</em> din ea,
        impreuna cu pozitia si clasa lor.<br><br>
        Spre deosebire de metodele clasice (care scanau imaginea de sute de ori),
        YOLO este <strong>extrem de rapid</strong> — potrivit pentru analiza
        in timp real a imaginilor drone.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card-verde">
        <strong>De ce YOLOv8 pentru agricultura?</strong><br><br>
        - Detecteaza culturi din imagini drone in < 1 secunda<br>
        - Identifica parcele cu vegetatie lipsa (NDVI scazut)<br>
        - Clasifica tipul de cultura (grau, porumb, rapita...)<br>
        - Detecteaza anomalii vizuale pe parcela<br>
        - Se antreneaza pe date proprii (imagini Gorj/Dolj/Olt)
    </div>
    """, unsafe_allow_html=True)

with col2:
    # Diagrama flux YOLO simpla
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.set_xlim(0, 10); ax.set_ylim(0, 8); ax.axis("off")

    def cutie(ax, x, y, w, h, culoare, text, text2=""):
        rect = mpatches.FancyBboxPatch((x, y), w, h,
                                       boxstyle="round,pad=0.1",
                                       facecolor=culoare, edgecolor="#333",
                                       linewidth=1.2)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2 + (0.2 if text2 else 0),
                text, ha="center", va="center",
                fontsize=9, fontweight="bold", color="white")
        if text2:
            ax.text(x + w/2, y + h/2 - 0.3, text2,
                    ha="center", va="center", fontsize=7, color="#eee")

    cutie(ax, 0.3, 6, 2.5, 1.2, "#1565c0", "Imagine drone", "640x640 px")
    ax.annotate("", xy=(3.5, 6.6), xytext=(2.8, 6.6),
                arrowprops=dict(arrowstyle="->", color="#333"))
    cutie(ax, 3.5, 6, 2.5, 1.2, "#6a1b9a", "Backbone", "CSPDarknet")
    ax.annotate("", xy=(3.5, 5.0), xytext=(4.75, 6.0),
                arrowprops=dict(arrowstyle="->", color="#333"))
    cutie(ax, 2.5, 3.5, 2.5, 1.2, "#2e7d32", "Neck", "FPN + PAN")
    ax.annotate("", xy=(3.5, 2.5), xytext=(3.75, 3.5),
                arrowprops=dict(arrowstyle="->", color="#333"))
    cutie(ax, 2.5, 1.0, 2.5, 1.2, "#c62828", "Head", "Detectie + Cls")
    ax.annotate("", xy=(6.5, 1.6), xytext=(5.0, 1.6),
                arrowprops=dict(arrowstyle="->", color="#333"))
    cutie(ax, 6.5, 0.8, 2.8, 1.6, "#e65100", "Output", "BBox + Clasa\n+ Confidence")

    ax.text(5, 7.5, "Arhitectura YOLOv8", ha="center",
            fontsize=11, fontweight="bold", color="#1565c0")
    plt.tight_layout()
    buf = BytesIO(); fig.savefig(buf, dpi=150, bbox_inches="tight")
    buf.seek(0); plt.close()
    st.image(buf, use_container_width=True)

st.markdown("---")

# ─── SECTIUNEA 2: Variantele YOLOv8 ──────────────────────────────────────────
st.markdown('<p class="titlu">Variantele YOLOv8 — ce alegem?</p>', unsafe_allow_html=True)

import pandas as pd
variante = [
    ("yolov8n", "Nano",   "3.2M",  "80.4",  "< 1s",  "Testare rapida, CPU"),
    ("yolov8s", "Small",  "11.2M", "112.5", "< 1s",  "Balans viteza/acuratete"),
    ("yolov8m", "Medium", "25.9M", "183.2", "1-2s",  "Productie, GPU recomandat"),
    ("yolov8l", "Large",  "43.7M", "165.2", "2-3s",  "Acuratete inalta, GPU"),
    ("yolov8x", "XLarge", "68.2M", "257.8", "3-5s",  "Maxim acuratete, GPU puternic"),
]

df_var = pd.DataFrame(variante, columns=["Model", "Varianta", "Parametri",
                                          "mAP50-95", "Viteza CPU", "Recomandat pentru"])
st.dataframe(df_var, use_container_width=True, hide_index=True)

st.markdown("""
<div class="card-verde">
    <strong>Recomandare pentru proiectul nostru:</strong>
    Incepem cu <strong>yolov8n</strong> (Nano) — cel mai rapid, functioneaza pe orice calculator,
    inclusiv fara GPU. Cand avem datasetul final vom trece la <strong>yolov8s</strong> sau <strong>yolov8m</strong>.
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ─── SECTIUNEA 3: Termeni cheie ───────────────────────────────────────────────
st.markdown('<p class="titlu">Termeni cheie de retinut</p>', unsafe_allow_html=True)

termeni = [
    ("Bounding Box (BBox)", "Dreptunghiul care inconjoara obiectul detectat — definit prin (x, y, latime, inaltime)"),
    ("Confidence Score",    "Probabilitatea ca detectia sa fie corecta — intre 0.0 si 1.0 (ex: 0.87 = 87%)"),
    ("IoU",                 "Intersection over Union — cat de mult se suprapune BBox prezis cu cel real"),
    ("mAP50",               "mean Average Precision la IoU=0.5 — metrica principala de evaluare"),
    ("Clasa (Class)",       "Categoria obiectului detectat — ex: 'grau', 'porumb', 'vegetatie_lipsa'"),
    ("Backbone",            "Reteaua neuronala care extrage caracteristici din imagine (CSPDarknet)"),
    ("Epoch",               "O trecere completa prin intregul dataset de antrenare"),
    ("Batch size",          "Cate imagini sunt procesate simultan la antrenare (ex: 16 sau 32)"),
    ("Inferenta",           "Rularea modelului pe imagini noi pentru a face predictii"),
]

col_t1, col_t2 = st.columns(2)
for i, (termen, definitie) in enumerate(termeni):
    col = col_t1 if i % 2 == 0 else col_t2
    with col:
        st.markdown(f"""
        <div class="card-gri">
            <strong>{termen}</strong><br>
            <small style="color:#444">{definitie}</small>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ─── SECTIUNEA 4: Instalare si verificare ─────────────────────────────────────
st.markdown('<p class="titlu">Instalare si verificare ultralytics</p>', unsafe_allow_html=True)

st.code("pip install ultralytics", language="bash")

try:
    import ultralytics
    ver = ultralytics.__version__
    st.success(f"ultralytics {ver} este instalat si functional!")

    st.code(f"""
from ultralytics import YOLO

# Incarca model pre-antrenat (se descarca automat prima data ~6MB)
model = YOLO("yolov8n.pt")

# Informatii despre model
print(model.info())

# Versiune ultralytics instalata: {ver}
    """, language="python")

except ImportError:
    st.error("ultralytics nu este inca instalat. Ruleaza: pip install ultralytics")

st.markdown("---")

# ─── SECTIUNEA 5: Comparatie cu alte metode ───────────────────────────────────
st.markdown('<p class="titlu">De ce YOLO si nu alte metode?</p>', unsafe_allow_html=True)

comp = pd.DataFrame([
    ("YOLO",              "O singura trecere",   "Foarte rapid",  "Bun",     "Da — simplu"),
    ("Faster R-CNN",      "Doua etape",          "Mediu",         "Excelent","Mai complex"),
    ("SSD",               "O singura trecere",   "Rapid",         "Mediu",   "Da"),
    ("Clasificare CNN",   "Nu detecteaza BBox",  "Rapid",         "—",       "Nu detecteaza pozitie"),
], columns=["Metoda", "Mod functionare", "Viteza", "Acuratete", "Antrenare custom"])

st.dataframe(comp, use_container_width=True, hide_index=True)

st.markdown("---")

# ─── Concept Ziua 1 ───────────────────────────────────────────────────────────
with st.expander("Conceptul Zilei 1 — YOLO: You Only Look Once"):
    st.markdown("""
**Problema clasica:** detectia obiectelor in imagini necesita sute de evaluari ale
aceleiasi imagini (sliding window) — extrem de lent.

**Solutia YOLO:** imparte imaginea intr-o grila NxN, fiecare celula prezice
simultan: existenta unui obiect, pozitia BBox si clasa.
**O singura trecere = toate detectiile.**
""")
    st.code("""
from ultralytics import YOLO

# 1. Incarca model pre-antrenat pe COCO (80 clase generale)
model = YOLO("yolov8n.pt")

# 2. Inferenta pe o imagine
results = model.predict("imagine_drone.jpg", conf=0.5)

# 3. Acceseaza rezultatele
for r in results:
    boxes  = r.boxes          # bounding boxes
    classes = r.boxes.cls     # clasele detectate (index)
    confs  = r.boxes.conf     # confidence scores
    names  = r.names          # dictionar {index: "nume_clasa"}

# 4. Salveaza imaginea cu detectiile desenate
results[0].save("rezultat.jpg")
    """, language="python")
    st.info("La Ziua 2 vom rula prima detectie reala pe o imagine incarcata din browser.")
