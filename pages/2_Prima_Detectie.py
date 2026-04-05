"""
BLOC 3 — Deep Learning YOLOv8, Ziua 2
Prima detectie pe imagine — upload → YOLOv8 → bounding boxes → rezultate
Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu | UCB Targu Jiu | APIA CJ Gorj

CONCEPT CHEIE:
  model = YOLO("yolov8n.pt")          — incarca model pre-antrenat COCO (80 clase)
  results = model.predict(img, conf)  — ruleaza inferenta
  results[0].boxes                    — lista bounding boxes detectate
  results[0].plot()                   — imagine cu BBox desenate (numpy array BGR)
  cv2.cvtColor(img, cv2.COLOR_BGR2RGB) — conversie BGR→RGB pentru Streamlit
"""

import streamlit as st
import numpy as np
from PIL import Image
from io import BytesIO

try:
    from ultralytics import YOLO
    YOLO_OK = True
except ImportError:
    YOLO_OK = False

try:
    import cv2
    CV2_OK = True
except ImportError:
    CV2_OK = False

# ─── Configurare pagina ───────────────────────────────────────────────────────
st.set_page_config(page_title="Prima Detectie YOLOv8 — Ziua 2", layout="wide")

st.markdown("""
<style>
.titlu { color:#1565c0; font-size:1.05rem; font-weight:700;
         border-bottom:2px solid #1565c0; padding-bottom:4px; margin-bottom:12px; }
.card  { background:#e3f2fd; border-left:4px solid #1565c0;
         border-radius:6px; padding:12px 16px; margin-bottom:8px; }
.card-verde { background:#e8f5e9; border-left:4px solid #2e7d32;
              border-radius:6px; padding:12px 16px; margin-bottom:8px; }
.card-rosu  { background:#ffebee; border-left:4px solid #c62828;
              border-radius:6px; padding:12px 16px; margin-bottom:8px; }
</style>
""", unsafe_allow_html=True)

st.title("Ziua 2 — Prima Detectie YOLOv8")
st.markdown("**Upload imagine → model pre-antrenat → bounding boxes → rezultate**")
st.markdown("---")

if not YOLO_OK:
    st.error("Instaleaza ultralytics: pip install ultralytics")
    st.stop()

# ─── SIDEBAR — parametri ──────────────────────────────────────────────────────
st.sidebar.markdown("### Parametri detectie")

model_ales = st.sidebar.selectbox(
    "Model YOLOv8",
    ["yolov8n.pt", "yolov8s.pt"],
    index=0,
    help="n=Nano (rapid, ~6MB) | s=Small (mai precis, ~22MB)"
)

conf_prag = st.sidebar.slider(
    "Confidence threshold",
    min_value=0.10, max_value=0.95, value=0.25, step=0.05,
    help="Detectiile sub acest prag sunt ignorate"
)

iou_prag = st.sidebar.slider(
    "IoU threshold (NMS)",
    min_value=0.1, max_value=0.9, value=0.45, step=0.05,
    help="Elimina bounding boxes suprapuse peste acest prag"
)

max_det = st.sidebar.number_input(
    "Max detectii per imagine",
    min_value=1, max_value=300, value=50
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Model COCO — 80 clase:**
persoana, masina, camion, avion, pasare,
caine, pisica, vaca, oaie, cal, etc.

*La Ziua 5+ vom antrena pe clase agricole proprii.*
""")

# ─── INCARCARE MODEL ─────────────────────────────────────────────────────────
@st.cache_resource
def incarca_model(nume_model):
    return YOLO(nume_model)

with st.spinner(f"Se incarca modelul {model_ales}..."):
    model = incarca_model(model_ales)

st.markdown(f"""
<div class="card-verde">
    Model <strong>{model_ales}</strong> incarcat.
    Antrenat pe <strong>COCO dataset</strong> — 80 clase, 118.000 imagini.
    Confidence: <strong>{conf_prag}</strong> | IoU: <strong>{iou_prag}</strong>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ─── UPLOAD IMAGINE ───────────────────────────────────────────────────────────
st.markdown('<p class="titlu">Pas 1 — Incarca imaginea</p>', unsafe_allow_html=True)

fisier = st.file_uploader(
    "Selecteaza o imagine (JPG, PNG)",
    type=["jpg", "jpeg", "png"],
    help="Poti folosi orice fotografie. La Ziua 3 vom testa pe imagini drone reale."
)

if fisier is None:
    st.markdown("""
    <div class="card">
        <strong>Nu ai o imagine la indemana?</strong><br>
        Foloseste orice fotografie color — strada, curte, animale, masini.
        Modelul pre-antrenat pe COCO detecteaza 80 de clase generale.<br><br>
        La <strong>Ziua 3</strong> vom testa pe imagini drone reale din parcele agricole.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Citire imagine
img_pil = Image.open(fisier).convert("RGB")
img_np  = np.array(img_pil)

col_orig, col_det = st.columns(2)

with col_orig:
    st.markdown('<p class="titlu">Imaginea originala</p>', unsafe_allow_html=True)
    st.image(img_pil, use_container_width=True,
             caption=f"{fisier.name} — {img_pil.width}x{img_pil.height} px")

# ─── DETECTIE ─────────────────────────────────────────────────────────────────
with st.spinner("Se ruleaza detectia YOLOv8..."):
    results = model.predict(
        img_np,
        conf=conf_prag,
        iou=iou_prag,
        max_det=int(max_det),
        verbose=False
    )

result  = results[0]
n_det   = len(result.boxes)

# Imagine cu BBox desenate (BGR → RGB)
img_det_bgr = result.plot()
if CV2_OK:
    img_det_rgb = cv2.cvtColor(img_det_bgr, cv2.COLOR_BGR2RGB)
else:
    img_det_rgb = img_det_bgr[:, :, ::-1]   # BGR→RGB fara opencv

with col_det:
    st.markdown('<p class="titlu">Rezultat detectie</p>', unsafe_allow_html=True)
    st.image(img_det_rgb, use_container_width=True,
             caption=f"YOLOv8 — {n_det} detectii (conf >= {conf_prag})")

st.markdown("---")

# ─── TABEL REZULTATE ─────────────────────────────────────────────────────────
st.markdown('<p class="titlu">Detectii detaliate</p>', unsafe_allow_html=True)

if n_det == 0:
    st.markdown(f"""
    <div class="card-rosu">
        <strong>Nicio detectie gasita</strong> cu confidence >= {conf_prag}.<br>
        Incearca sa scazi pragul de confidence din sidebar (ex: 0.10).
    </div>
    """, unsafe_allow_html=True)
else:
    import pandas as pd

    boxes  = result.boxes
    names  = result.names

    rows = []
    for i in range(len(boxes)):
        cls_id  = int(boxes.cls[i].item())
        conf_v  = float(boxes.conf[i].item())
        xyxy    = boxes.xyxy[i].tolist()
        x1,y1,x2,y2 = [round(v) for v in xyxy]
        w = x2 - x1; h = y2 - y1
        rows.append({
            "Nr.":        i + 1,
            "Clasa":      names[cls_id],
            "Confidence": f"{conf_v:.2%}",
            "X1":  x1, "Y1": y1, "X2": x2, "Y2": y2,
            "Lat. (px)":  w,
            "Inalt. (px)": h,
            "Aria (px²)": w * h,
        })

    df_det = pd.DataFrame(rows)
    st.dataframe(df_det, use_container_width=True, hide_index=True)

    # Statistici rapide
    st.markdown("**Statistici detectie:**")
    dist_clase = df_det["Clasa"].value_counts().reset_index()
    dist_clase.columns = ["Clasa", "Nr. detectii"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Total detectii", n_det)
    c2.metric("Clase unice", df_det["Clasa"].nunique())
    c3.metric("Confidence maxim",
              df_det["Confidence"].iloc[0] if len(df_det) > 0 else "—")

    st.dataframe(dist_clase, use_container_width=True, hide_index=True)

    # Descarca imaginea cu detectii
    img_pil_det = Image.fromarray(img_det_rgb)
    buf_img = BytesIO()
    img_pil_det.save(buf_img, format="JPEG", quality=95)
    buf_img.seek(0)

    st.download_button(
        "Descarca imaginea cu detectii (JPG)",
        data=buf_img,
        file_name=f"detectie_{fisier.name}",
        mime="image/jpeg"
    )

st.markdown("---")

# ─── Concept Ziua 2 ───────────────────────────────────────────────────────────
with st.expander("Conceptul Zilei 2 — Prima detectie YOLOv8"):
    st.markdown("""
**Fluxul complet al unei detectii YOLOv8:**
""")
    st.code("""
from ultralytics import YOLO
from PIL import Image
import numpy as np

# 1. Incarca modelul (se descarca automat prima data)
model = YOLO("yolov8n.pt")   # ~6MB

# 2. Incarca imaginea
img = np.array(Image.open("imagine.jpg").convert("RGB"))

# 3. Ruleaza detectia
results = model.predict(
    img,
    conf=0.25,    # ignora detectii sub 25% confidence
    iou=0.45,     # NMS: elimina BBox suprapuse
    max_det=50,   # max 50 detectii per imagine
    verbose=False # fara output in terminal
)

# 4. Acceseaza rezultatele
result = results[0]
for i in range(len(result.boxes)):
    cls_id = int(result.boxes.cls[i])
    conf   = float(result.boxes.conf[i])
    x1,y1,x2,y2 = result.boxes.xyxy[i].tolist()
    print(f"{result.names[cls_id]}: {conf:.1%} la ({x1:.0f},{y1:.0f})")

# 5. Imagine cu BBox desenate (array BGR)
img_cu_bbox = result.plot()
    """, language="python")
    st.info("**@st.cache_resource** — modelul se incarca o singura data si ramane in memorie "
            "pe toata durata sesiunii. Fara el, s-ar reincarca la fiecare interactiune.")
