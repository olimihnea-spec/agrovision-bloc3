"""
BLOC 3 — Deep Learning YOLOv8, Ziua 5
Format Dataset YOLO — structura, adnotari .txt, data.yaml, dataset minimal
Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu | UCB Targu Jiu | APIA CJ Gorj

CONCEPT CHEIE:
  Dataset YOLO = imagini + fisiere .txt cu adnotari normalizate [0,1]
  Format adnotare: class_id x_center y_center width height (per linie, per obiect)
  data.yaml = fisierul de configurare: cai, nr. clase, nume clase
  Split recomandat: 70% train / 20% val / 10% test
  Acest modul genereaza un dataset sintetic minimal gata de antrenare
"""

import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
import json
import zipfile
import os
from datetime import date

# ─── Configurare pagina ───────────────────────────────────────────────────────
st.set_page_config(page_title="Format Dataset YOLO — Ziua 5", layout="wide")

st.markdown("""
<style>
.titlu { color:#e65100; font-size:1.05rem; font-weight:700;
         border-bottom:2px solid #e65100; padding-bottom:4px; margin-bottom:12px; }
.card  { background:#fff3e0; border-left:4px solid #e65100;
         border-radius:6px; padding:12px 16px; margin-bottom:8px; }
.card-verde { background:#e8f5e9; border-left:4px solid #2e7d32;
              border-radius:6px; padding:12px 16px; margin-bottom:8px; }
.card-cod   { background:#1e1e1e; border-radius:6px; padding:14px 18px;
              font-family:monospace; font-size:0.85rem; color:#d4d4d4; margin-bottom:10px; }
</style>
""", unsafe_allow_html=True)

st.title("Ziua 5 — Format Dataset YOLOv8")
st.markdown("**Structura, adnotari, data.yaml si generare dataset sintetic pentru culturi agricole**")
st.markdown("---")

# ─── SECTIUNEA 1: Structura dataset ──────────────────────────────────────────
st.markdown('<p class="titlu">1. Structura unui dataset YOLO</p>',
            unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("""
    <div class="card">
        <strong>Structura de foldere obligatorie:</strong>
    </div>
    """, unsafe_allow_html=True)

    st.code("""
dataset_culturi/
├── images/
│   ├── train/        ← 70% din imagini
│   │   ├── img001.jpg
│   │   ├── img002.jpg
│   │   └── ...
│   ├── val/          ← 20% din imagini
│   │   ├── img201.jpg
│   │   └── ...
│   └── test/         ← 10% din imagini
│       └── ...
├── labels/
│   ├── train/        ← adnotarile .txt pentru train
│   │   ├── img001.txt
│   │   ├── img002.txt
│   │   └── ...
│   ├── val/
│   └── test/
└── data.yaml         ← configurare model
    """, language="text")

with col2:
    st.markdown("""
    <div class="card">
        <strong>Regula de aur:</strong> pentru fiecare imagine <code>img001.jpg</code>
        exista un fisier <code>img001.txt</code> cu EXACT acelasi nume in folderul
        corespunzator din <code>labels/</code>.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card-verde">
        <strong>Split recomandat pentru agricultura:</strong><br>
        - <strong>Train (70%)</strong> — modelul invata din aceste imagini<br>
        - <strong>Val (20%)</strong> — evaluare in timpul antrenarii<br>
        - <strong>Test (10%)</strong> — evaluare finala, dupa antrenare<br><br>
        Pentru un dataset mic (< 200 imagini): 80% train / 20% val, fara test separat.
    </div>
    """, unsafe_allow_html=True)

    # Pie split
    fig_pie, ax_pie = plt.subplots(figsize=(4, 2.5))
    ax_pie.pie([70, 20, 10], labels=["Train 70%", "Val 20%", "Test 10%"],
               colors=["#1565c0", "#2e7d32", "#e65100"],
               autopct="%1.0f%%", startangle=90)
    ax_pie.set_title("Split dataset recomandat", fontsize=9)
    plt.tight_layout()
    buf_pie = BytesIO(); fig_pie.savefig(buf_pie, dpi=120, bbox_inches="tight")
    buf_pie.seek(0); plt.close()
    st.image(buf_pie, use_container_width=True)

st.markdown("---")

# ─── SECTIUNEA 2: Formatul adnotarilor ───────────────────────────────────────
st.markdown('<p class="titlu">2. Formatul adnotarilor YOLO (.txt)</p>',
            unsafe_allow_html=True)

col3, col4 = st.columns([1, 1])

with col3:
    st.markdown("""
    **Fiecare linie = un obiect detectat:**
    """)
    st.code("""
# Format: class_id x_center y_center width height
# Toate valorile sunt NORMALIZATE intre 0.0 si 1.0
# (impartite la latimea/inaltimea imaginii)

0 0.512 0.347 0.234 0.189
1 0.731 0.612 0.156 0.204
0 0.123 0.789 0.098 0.112

# Linia 1: clasa 0 (grau), centrat la (51.2%, 34.7%)
#           latime=23.4%, inaltime=18.9% din imagine
# Linia 2: clasa 1 (porumb), etc.
# Linia 3: alta parcela de grau
    """, language="text")

    st.markdown("""
    **Clasele sunt definite in data.yaml:**
    """)
    st.code("""
# data.yaml
path: ./dataset_culturi    # calea la dataset
train: images/train
val:   images/val
test:  images/test

nc: 4                      # number of classes
names:
  0: grau
  1: porumb
  2: rapita
  3: vegetatie_lipsa
    """, language="yaml")

with col4:
    # Diagrama vizuala BBox normalizat
    fig_bbox, ax_bbox = plt.subplots(figsize=(5, 4))
    ax_bbox.set_xlim(0, 1); ax_bbox.set_ylim(0, 1)
    ax_bbox.set_aspect("equal")
    ax_bbox.invert_yaxis()

    # Imagine simulata
    ax_bbox.add_patch(patches.Rectangle((0,0), 1, 1,
                      facecolor="#c8e6c9", edgecolor="#333", linewidth=2))

    # BBox 1 — grau
    x_c, y_c, w, h = 0.512, 0.347, 0.234, 0.189
    x1 = x_c - w/2; y1 = y_c - h/2
    ax_bbox.add_patch(patches.Rectangle((x1,y1), w, h,
                      facecolor="none", edgecolor="#1565c0", linewidth=2))
    ax_bbox.plot(x_c, y_c, "bo", markersize=6)
    ax_bbox.annotate("0 (grau)\n0.512 0.347 0.234 0.189",
                     (x_c, y_c), (x_c+0.05, y_c-0.12),
                     fontsize=7, color="#1565c0",
                     arrowprops=dict(arrowstyle="->", color="#1565c0"))

    # BBox 2 — porumb
    x_c2, y_c2, w2, h2 = 0.731, 0.612, 0.156, 0.204
    x12 = x_c2 - w2/2; y12 = y_c2 - h2/2
    ax_bbox.add_patch(patches.Rectangle((x12,y12), w2, h2,
                      facecolor="none", edgecolor="#e65100", linewidth=2))
    ax_bbox.plot(x_c2, y_c2, "o", color="#e65100", markersize=6)
    ax_bbox.annotate("1 (porumb)\n0.731 0.612 0.156 0.204",
                     (x_c2, y_c2), (x_c2-0.35, y_c2+0.15),
                     fontsize=7, color="#e65100",
                     arrowprops=dict(arrowstyle="->", color="#e65100"))

    ax_bbox.set_xlabel("x (0=stanga → 1=dreapta)", fontsize=8)
    ax_bbox.set_ylabel("y (0=sus → 1=jos)", fontsize=8)
    ax_bbox.set_title("Coordonate YOLO normalizate [0,1]", fontsize=9)
    ax_bbox.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax_bbox.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax_bbox.grid(True, alpha=0.3)
    plt.tight_layout()
    buf_bbox = BytesIO(); fig_bbox.savefig(buf_bbox, dpi=150, bbox_inches="tight")
    buf_bbox.seek(0); plt.close()
    st.image(buf_bbox, use_container_width=True)

st.markdown("---")

# ─── SECTIUNEA 3: Convertor coordonate ────────────────────────────────────────
st.markdown('<p class="titlu">3. Convertor coordonate — pixel → YOLO normalizat</p>',
            unsafe_allow_html=True)

st.markdown("Daca stii coordonatele in pixeli ale unui BBox, converteste-le la formatul YOLO:")

col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
    img_w = st.number_input("Latimea imaginii (px)", value=4608, min_value=1)
    img_h = st.number_input("Inaltimea imaginii (px)", value=3456, min_value=1)
with col_c2:
    px_x1 = st.number_input("X1 (stanga)", value=500, min_value=0)
    px_y1 = st.number_input("Y1 (sus)", value=300, min_value=0)
with col_c3:
    px_x2 = st.number_input("X2 (dreapta)", value=1200, min_value=0)
    px_y2 = st.number_input("Y2 (jos)", value=800, min_value=0)

if px_x2 > px_x1 and px_y2 > px_y1:
    x_c_n = ((px_x1 + px_x2) / 2) / img_w
    y_c_n = ((px_y1 + px_y2) / 2) / img_h
    w_n   = (px_x2 - px_x1) / img_w
    h_n   = (px_y2 - px_y1) / img_h

    clasa_conv = st.selectbox("Clasa obiect", ["0 (grau)","1 (porumb)","2 (rapita)","3 (vegetatie_lipsa)"])
    cls_id = int(clasa_conv[0])

    st.success(f"**Format YOLO:** `{cls_id} {x_c_n:.6f} {y_c_n:.6f} {w_n:.6f} {h_n:.6f}`")
    st.caption(f"x_center={x_c_n:.4f} | y_center={y_c_n:.4f} | width={w_n:.4f} | height={h_n:.4f}")

st.markdown("---")

# ─── SECTIUNEA 4: Generator dataset sintetic ──────────────────────────────────
st.markdown('<p class="titlu">4. Genereaza dataset sintetic minimal</p>',
            unsafe_allow_html=True)

st.markdown("""
<div class="card">
    Generam un dataset sintetic cu imagini colorate (simuland parcele agricole)
    si adnotarile .txt corespunzatoare. Gata de antrenat cu <code>yolo train</code>.
</div>
""", unsafe_allow_html=True)

CLASE = {0: "grau", 1: "porumb", 2: "rapita", 3: "vegetatie_lipsa"}
CULORI_CLASE = {
    0: (180, 200, 100),   # grau — verde-galben
    1: (50,  160, 50),    # porumb — verde intens
    2: (220, 200, 30),    # rapita — galben
    3: (140, 100, 60),    # vegetatie lipsa — maro
}

col_g1, col_g2 = st.columns(2)
with col_g1:
    n_imagini  = st.slider("Nr. imagini de generat", 10, 100, 30)
    img_size   = st.selectbox("Rezolutie imagini", [320, 416, 640], index=1)
with col_g2:
    clase_sel  = st.multiselect("Clase incluse", list(CLASE.values()),
                                default=list(CLASE.values()))
    n_obiecte  = st.slider("Max obiecte per imagine", 1, 8, 3)

clase_ids = [k for k, v in CLASE.items() if v in clase_sel]

def genereaza_imagine_sintetica(size, n_obj, clase_ids, seed):
    rng = np.random.default_rng(seed)
    img = Image.new("RGB", (size, size), color=(120, 150, 80))
    draw = ImageDraw.Draw(img)

    # Fundal gradient simulat
    for y in range(size):
        verde = int(100 + 50 * np.sin(y / size * np.pi))
        for x in range(0, size, 4):
            r_val = int(80 + rng.integers(-10, 10))
            draw.rectangle([x, y, x+3, y], fill=(r_val, verde, 60))

    adnotari = []
    for _ in range(rng.integers(1, n_obj + 1)):
        cls_id = int(rng.choice(clase_ids))
        culoare = tuple(int(c + rng.integers(-20, 20)) for c in CULORI_CLASE[cls_id])
        culoare = tuple(max(0, min(255, c)) for c in culoare)

        w_box = rng.integers(size//8, size//3)
        h_box = rng.integers(size//8, size//3)
        x1    = rng.integers(0, size - w_box)
        y1    = rng.integers(0, size - h_box)

        draw.rectangle([x1, y1, x1+w_box, y1+h_box], fill=culoare)
        draw.rectangle([x1, y1, x1+w_box, y1+h_box],
                       outline=(0,0,0), width=2)

        # Coordonate YOLO normalizate
        x_c = (x1 + w_box/2) / size
        y_c = (y1 + h_box/2) / size
        w_n = w_box / size
        h_n = h_box / size
        adnotari.append(f"{cls_id} {x_c:.6f} {y_c:.6f} {w_n:.6f} {h_n:.6f}")

    return img, adnotari

if st.button("Genereaza Dataset ZIP", type="primary") and clase_ids:
    with st.spinner(f"Se genereaza {n_imagini} imagini..."):
        rng_main = np.random.default_rng(42)

        # Split
        idx_all   = list(range(n_imagini))
        rng_main.shuffle(idx_all)
        n_train   = int(n_imagini * 0.70)
        n_val     = int(n_imagini * 0.20)
        splits    = {
            "train": idx_all[:n_train],
            "val":   idx_all[n_train:n_train+n_val],
            "test":  idx_all[n_train+n_val:]
        }

        # data.yaml
        yaml_content = (
            f"path: ./dataset_culturi_gorj\n"
            f"train: images/train\n"
            f"val:   images/val\n"
            f"test:  images/test\n\n"
            f"nc: {len(clase_ids)}\n"
            f"names:\n"
        )
        for i, cls_id in enumerate(clase_ids):
            yaml_content += f"  {i}: {CLASE[cls_id]}\n"

        # ZIP
        buf_zip = BytesIO()
        with zipfile.ZipFile(buf_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("dataset_culturi_gorj/data.yaml", yaml_content)

            for split_name, indices in splits.items():
                for idx in indices:
                    img, adnotari = genereaza_imagine_sintetica(
                        img_size, n_obiecte, clase_ids, seed=idx*100
                    )
                    # Imagine
                    buf_img = BytesIO()
                    img.save(buf_img, format="JPEG", quality=90)
                    zf.writestr(
                        f"dataset_culturi_gorj/images/{split_name}/img_{idx:04d}.jpg",
                        buf_img.getvalue()
                    )
                    # Adnotare
                    zf.writestr(
                        f"dataset_culturi_gorj/labels/{split_name}/img_{idx:04d}.txt",
                        "\n".join(adnotari)
                    )

            # README
            readme = (
                f"DATASET CULTURI AGRICOLE — Sintetic\n"
                f"Generat: {date.today().strftime('%d.%m.%Y')}\n"
                f"Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu | UCB Targu Jiu\n\n"
                f"Imagini: {n_imagini} ({img_size}x{img_size} px)\n"
                f"Split: {n_train} train / {n_val} val / {n_imagini-n_train-n_val} test\n"
                f"Clase: {', '.join([CLASE[c] for c in clase_ids])}\n\n"
                f"ANTRENARE:\n"
                f"  yolo train model=yolov8n.pt data=dataset_culturi_gorj/data.yaml "
                f"epochs=50 imgsz={img_size}\n\n"
                f"NOTA: Datele sunt sintetice (imagini generate, nu reale).\n"
                f"Inlocuieste cu imagini drone reale pentru model de productie.\n"
            )
            zf.writestr("dataset_culturi_gorj/README.txt", readme)

        buf_zip.seek(0)

        # Previzualizare 4 imagini
        st.markdown("**Previzualizare 4 imagini generate:**")
        prev_cols = st.columns(4)
        for i in range(4):
            img_prev, _ = genereaza_imagine_sintetica(img_size, n_obiecte, clase_ids, seed=i*100)
            with prev_cols[i]:
                st.image(img_prev, use_container_width=True, caption=f"img_{i:04d}.jpg")

        # Statistici
        st.markdown(f"""
        <div class="card-verde">
            <strong>Dataset generat:</strong> {n_imagini} imagini {img_size}x{img_size} px<br>
            Train: {n_train} | Val: {n_val} | Test: {n_imagini-n_train-n_val}<br>
            Clase: {', '.join([CLASE[c] for c in clase_ids])}
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            "Descarca Dataset ZIP",
            data=buf_zip,
            file_name=f"dataset_culturi_gorj_{img_size}px.zip",
            mime="application/zip"
        )

elif not clase_ids:
    st.warning("Selecteaza cel putin o clasa.")

st.markdown("---")

# ─── Concept Ziua 5 ───────────────────────────────────────────────────────────
with st.expander("Conceptul Zilei 5 — Format dataset YOLO complet"):
    st.markdown("""
**Reguli de baza pentru un dataset YOLO valid:**

1. Fiecare imagine `.jpg` → un fisier `.txt` cu acelasi nume in `labels/`
2. Fisierul `.txt` gol = imagine fara obiecte (negativ pur)
3. Coordonatele sunt INTOTDEAUNA normalizate [0, 1]
4. Clasa incepe de la 0 (nu 1!)
5. `data.yaml` trebuie sa aiba `nc` = numarul exact de clase
""")
    st.code("""
# Conversia coordonate pixeli → YOLO normalizat
def pixeli_la_yolo(x1, y1, x2, y2, img_w, img_h):
    x_center = ((x1 + x2) / 2) / img_w
    y_center = ((y1 + y2) / 2) / img_h
    width    = (x2 - x1) / img_w
    height   = (y2 - y1) / img_h
    return x_center, y_center, width, height

# Exemplu pentru imagine 4608x3456 px
x_c, y_c, w, h = pixeli_la_yolo(500, 300, 1200, 800, 4608, 3456)
linie_txt = f"0 {x_c:.6f} {y_c:.6f} {w:.6f} {h:.6f}"
# → "0 0.184635 0.159722 0.151910 0.144676"
    """, language="python")
    st.info("La Ziua 6 vom adnota imagini drone reale cu LabelImg — "
            "tool gratuit care genereaza automat fisierele .txt in format YOLO.")
