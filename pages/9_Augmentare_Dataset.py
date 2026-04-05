"""
BLOC 3 — Deep Learning YOLOv8, Ziua 9
Augmentare dataset — rotatie, flip, brightness, contrast, mosaic
Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu | UCB Targu Jiu | APIA CJ Gorj

CONCEPT CHEIE:
  Augmentarea = generare variante artificiale ale imaginilor existente
  Scopul: mareste datasetul fara a adnota imagini noi
  PIL.ImageEnhance — brightness, contrast, sharpness
  Image.transpose() — flip orizontal/vertical
  Image.rotate() — rotatie cu unghi arbitrar
  Adnotarile se transforma odata cu imaginea (flip/rotatie schimba coordonatele!)
"""

import streamlit as st
import numpy as np
from PIL import Image, ImageEnhance
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from io import BytesIO
import zipfile
import random
from datetime import date

st.set_page_config(page_title="Augmentare Dataset — Ziua 9", layout="wide")

st.markdown("""
<style>
.titlu { color:#e65100; font-size:1.05rem; font-weight:700;
         border-bottom:2px solid #e65100; padding-bottom:4px; margin-bottom:12px; }
.card  { background:#fff3e0; border-left:4px solid #e65100;
         border-radius:6px; padding:12px 16px; margin-bottom:8px; }
.card-verde { background:#e8f5e9; border-left:4px solid #2e7d32;
              border-radius:6px; padding:12px 16px; margin-bottom:8px; }
</style>
""", unsafe_allow_html=True)

st.title("Ziua 9 — Augmentare Dataset")
st.markdown("**Multiplica datele fara adnotare noua: flip, rotatie, brightness, contrast**")
st.markdown("---")

st.markdown("""
<div class="card">
    <strong>De ce augmentare?</strong> Un dataset mic (50 imagini/clasa) poate fi
    transformat in 200-400 imagini prin augmentare — modelul invata mai bine
    si generalizeaza mai corect pe imagini noi din drone.
</div>
""", unsafe_allow_html=True)

# ─── UPLOAD ───────────────────────────────────────────────────────────────────
st.markdown('<p class="titlu">Incarca imaginea + adnotarile</p>', unsafe_allow_html=True)

col_u1, col_u2 = st.columns(2)
with col_u1:
    fisier_img = st.file_uploader("Imagine (.jpg/.png)", type=["jpg","jpeg","png","tif"])
with col_u2:
    fisier_txt = st.file_uploader("Adnotari YOLO (.txt)", type=["txt"])

clase_input = st.text_input("Clase:", "grau, porumb, rapita, vegetatie_lipsa")
clase_lista = [c.strip() for c in clase_input.split(",")]

# ─── SIDEBAR — augmentari ─────────────────────────────────────────────────────
st.sidebar.markdown("### Augmentari active")
do_flip_h   = st.sidebar.checkbox("Flip orizontal",    value=True)
do_flip_v   = st.sidebar.checkbox("Flip vertical",     value=True)
do_rot90    = st.sidebar.checkbox("Rotatie 90°",       value=True)
do_rot180   = st.sidebar.checkbox("Rotatie 180°",      value=True)
do_bright   = st.sidebar.checkbox("Brightness",        value=True)
do_contrast = st.sidebar.checkbox("Contrast",          value=True)
do_noise    = st.sidebar.checkbox("Zgomot gaussian",   value=False)

bright_factor  = st.sidebar.slider("Brightness factor", 0.5, 2.0, 1.4, 0.1)
contrast_factor= st.sidebar.slider("Contrast factor",   0.5, 2.0, 1.3, 0.1)
noise_std      = st.sidebar.slider("Zgomot std",        1,   30,  10,  1)

# ─── FUNCTII AUGMENTARE ───────────────────────────────────────────────────────

def transforma_adnotari_flip_h(adnotari):
    """Flip orizontal: x_center → 1 - x_center"""
    return [(c, 1.0 - x, y, w, h) for c, x, y, w, h in adnotari]

def transforma_adnotari_flip_v(adnotari):
    """Flip vertical: y_center → 1 - y_center"""
    return [(c, x, 1.0 - y, w, h) for c, x, y, w, h in adnotari]

def transforma_adnotari_rot90(adnotari):
    """Rotatie 90° sens orar: (x,y,w,h) → (1-y, x, h, w)"""
    return [(c, 1.0 - y, x, h, w) for c, x, y, w, h in adnotari]

def transforma_adnotari_rot180(adnotari):
    """Rotatie 180°: (x,y) → (1-x, 1-y)"""
    return [(c, 1.0 - x, 1.0 - y, w, h) for c, x, y, w, h in adnotari]

def augmenteaza(img_pil, adnotari):
    """Genereaza toate variantele active. Returneaza lista (img, adnotari, nume_aug)."""
    variante = [("original", img_pil, adnotari)]

    if do_flip_h:
        img_fh = img_pil.transpose(Image.FLIP_LEFT_RIGHT)
        variante.append(("flip_h", img_fh, transforma_adnotari_flip_h(adnotari)))

    if do_flip_v:
        img_fv = img_pil.transpose(Image.FLIP_TOP_BOTTOM)
        variante.append(("flip_v", img_fv, transforma_adnotari_flip_v(adnotari)))

    if do_rot90:
        img_r90 = img_pil.transpose(Image.ROTATE_90)
        variante.append(("rot90", img_r90, transforma_adnotari_rot90(adnotari)))

    if do_rot180:
        img_r180 = img_pil.transpose(Image.ROTATE_180)
        variante.append(("rot180", img_r180, transforma_adnotari_rot180(adnotari)))

    if do_bright:
        img_br = ImageEnhance.Brightness(img_pil).enhance(bright_factor)
        variante.append(("bright", img_br, adnotari))

    if do_contrast:
        img_ct = ImageEnhance.Contrast(img_pil).enhance(contrast_factor)
        variante.append(("contrast", img_ct, adnotari))

    if do_noise:
        arr = np.array(img_pil, dtype=np.float32)
        noise = np.random.normal(0, noise_std, arr.shape)
        arr_n = np.clip(arr + noise, 0, 255).astype(np.uint8)
        img_ns = Image.fromarray(arr_n)
        variante.append(("noise", img_ns, adnotari))

    return variante

def adnotari_la_txt(adnotari):
    return "\n".join([f"{c} {x:.6f} {y:.6f} {w:.6f} {h:.6f}"
                      for c, x, y, w, h in adnotari])

def deseneaza_bbox(ax, img, adnotari, titlu):
    ax.imshow(img)
    W, H = img.width, img.height
    culori = ["#c62828","#1565c0","#2e7d32","#e65100"]
    for cls_id, xc, yc, w, h in adnotari:
        x1 = (xc - w/2) * W; y1 = (yc - h/2) * H
        col = culori[cls_id % len(culori)]
        ax.add_patch(mpatches.Rectangle((x1, y1), w*W, h*H,
                     facecolor="none", edgecolor=col, linewidth=2))
        nm = clase_lista[cls_id] if cls_id < len(clase_lista) else str(cls_id)
        ax.text(x1+2, y1+14, nm, fontsize=7, color="white", fontweight="bold",
                bbox=dict(facecolor=col, alpha=0.8, pad=1))
    ax.set_title(titlu, fontsize=8)
    ax.axis("off")

# ─── PROCESARE ────────────────────────────────────────────────────────────────
if fisier_img:
    img_pil = Image.open(fisier_img).convert("RGB")

    # Citire adnotari
    adnotari = []
    if fisier_txt:
        for linie in fisier_txt.read().decode("utf-8").strip().split("\n"):
            parti = linie.strip().split()
            if len(parti) == 5:
                try:
                    adnotari.append((int(parti[0]),
                                     *[float(p) for p in parti[1:]]))
                except ValueError:
                    pass

    variante = augmenteaza(img_pil, adnotari)
    n_aug = len(variante)

    c1, c2, c3 = st.columns(3)
    c1.metric("Imagine originala", "1")
    c2.metric("Variante generate", n_aug)
    c3.metric("Factor multiplicare", f"{n_aug}x")

    st.markdown(f"""
    <div class="card-verde">
        Din <strong>1 imagine</strong> am generat <strong>{n_aug} variante</strong>.
        Daca ai 50 imagini adnotate → dupa augmentare vei avea
        <strong>{50 * n_aug} imagini</strong> pentru antrenare!
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p class="titlu">Previzualizare variante generate</p>',
                unsafe_allow_html=True)

    # Grid previzualizare
    n_cols_viz = min(4, n_aug)
    n_rows_viz = (n_aug + n_cols_viz - 1) // n_cols_viz
    fig, axes = plt.subplots(n_rows_viz, n_cols_viz,
                              figsize=(4 * n_cols_viz, 3.5 * n_rows_viz))
    if n_aug == 1:
        axes = [[axes]]
    elif n_rows_viz == 1:
        axes = [axes]

    for i, (nume, img_v, adt_v) in enumerate(variante):
        r, c = divmod(i, n_cols_viz)
        ax = axes[r][c] if n_rows_viz > 1 else axes[0][c]
        deseneaza_bbox(ax, img_v, adt_v, nume)

    # Ascunde axele neutilizate
    for i in range(n_aug, n_rows_viz * n_cols_viz):
        r, c = divmod(i, n_cols_viz)
        ax = axes[r][c] if n_rows_viz > 1 else axes[0][c]
        ax.axis("off")

    plt.suptitle(f"Augmentare dataset — {n_aug} variante din 1 imagine",
                 fontsize=10, y=1.01)
    plt.tight_layout()
    buf_fig = BytesIO()
    fig.savefig(buf_fig, dpi=130, bbox_inches="tight")
    buf_fig.seek(0); plt.close()
    st.image(buf_fig, use_container_width=True)

    st.markdown("---")

    # ─── EXPORT ZIP ───────────────────────────────────────────────────────────
    st.markdown('<p class="titlu">Export variante augmentate in ZIP</p>',
                unsafe_allow_html=True)

    import os
    nume_baza = os.path.splitext(fisier_img.name)[0]

    if st.button("Genereaza ZIP augmentat", type="primary"):
        with st.spinner(f"Se genereaza {n_aug} variante..."):
            buf_zip = BytesIO()
            with zipfile.ZipFile(buf_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                for nume_aug, img_v, adt_v in variante:
                    # Imagine
                    buf_i = BytesIO()
                    img_v.save(buf_i, format="JPEG", quality=92)
                    zf.writestr(
                        f"augmentat/images/{nume_baza}_{nume_aug}.jpg",
                        buf_i.getvalue()
                    )
                    # Adnotare
                    zf.writestr(
                        f"augmentat/labels/{nume_baza}_{nume_aug}.txt",
                        adnotari_la_txt(adt_v)
                    )
            buf_zip.seek(0)

        st.success(f"{n_aug} variante exportate!")
        st.download_button(
            "Descarca ZIP augmentat",
            data=buf_zip,
            file_name=f"augmentat_{nume_baza}_{date.today().strftime('%Y%m%d')}.zip",
            mime="application/zip"
        )

else:
    st.markdown("""
    <div class="card">
        Incarca o imagine drone (si optional fisierul .txt cu adnotari)
        pentru a vedea augmentarea in actiune.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

with st.expander("Conceptul Zilei 9 — Augmentare si transformarea adnotarilor"):
    st.markdown("""
**Regula esentiala:** orice transformare geometrica (flip, rotatie) schimba
si coordonatele BBox! Brightness/contrast/zgomot NU schimba coordonatele.
""")
    st.code("""
from PIL import Image, ImageEnhance
import numpy as np

img = Image.open("parcela.jpg")

# Flip orizontal — x_center devine 1 - x_center
img_flip = img.transpose(Image.FLIP_LEFT_RIGHT)
# Adnotare (0, 0.3, 0.5, 0.2, 0.1) → (0, 0.7, 0.5, 0.2, 0.1)

# Flip vertical — y_center devine 1 - y_center
img_flipv = img.transpose(Image.FLIP_TOP_BOTTOM)

# Rotatie 90° — (x,y,w,h) → (1-y, x, h, w)
img_rot90 = img.transpose(Image.ROTATE_90)

# Brightness (adnotarile NU se schimba)
img_bright = ImageEnhance.Brightness(img).enhance(1.4)

# Contrast
img_contrast = ImageEnhance.Contrast(img).enhance(1.3)

# Zgomot gaussian
arr = np.array(img, dtype=np.float32)
arr_noise = np.clip(arr + np.random.normal(0, 10, arr.shape), 0, 255)
img_noise = Image.fromarray(arr_noise.astype(np.uint8))
    """, language="python")
    st.info("YOLOv8 face augmentare automata la antrenare (mosaic, HSV, flip). "
            "Augmentarea manuala e utila cand datasetul e foarte mic (< 50 imagini/clasa).")
