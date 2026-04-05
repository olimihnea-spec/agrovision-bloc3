"""
BLOC 3 — Deep Learning YOLOv8, Ziua 3
Detectie imagini drone — analiza adaptata pentru vederea de sus
Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu | UCB Targu Jiu | APIA CJ Gorj

CONCEPT CHEIE:
  Modelul COCO nu detecteaza culturi din aer — avem nevoie de alta abordare
  SOLUTIE 1: Segmentare prin culoare (HSV) — identifica zone verzi/galbene/maronii
  SOLUTIE 2: Indici spectrale (ExG, VARI) — vegetatie vs sol gol
  SOLUTIE 3: YOLOv8-seg — segmentare semantica (vom antrena in Zilele 11-15)
  Aceasta pagina = analiza completa imagine drone FARA model antrenat custom
"""

import streamlit as st
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from io import BytesIO

try:
    import cv2
    CV2_OK = True
except ImportError:
    CV2_OK = False

# ─── Configurare pagina ───────────────────────────────────────────────────────
st.set_page_config(page_title="Detectie Drone — Ziua 3", layout="wide")

st.markdown("""
<style>
.titlu { color:#2e7d32; font-size:1.05rem; font-weight:700;
         border-bottom:2px solid #2e7d32; padding-bottom:4px; margin-bottom:12px; }
.card  { background:#e8f5e9; border-left:4px solid #2e7d32;
         border-radius:6px; padding:12px 16px; margin-bottom:8px; }
.card-portocaliu { background:#fff3e0; border-left:4px solid #e65100;
                   border-radius:6px; padding:12px 16px; margin-bottom:8px; }
.card-albastru { background:#e3f2fd; border-left:4px solid #1565c0;
                 border-radius:6px; padding:12px 16px; margin-bottom:8px; }
</style>
""", unsafe_allow_html=True)

st.title("Ziua 3 — Detectie Imagini Drone")
st.markdown("**Analiza adaptata pentru vederea de sus — segmentare culoare + indici spectrale**")
st.markdown("---")

# ─── Explicatie problema ──────────────────────────────────────────────────────
st.markdown("""
<div class="card-portocaliu">
    <strong>De ce COCO nu merge pe drone?</strong><br>
    Modelul pre-antrenat YOLOv8 (COCO) a fost antrenat pe fotografii la nivel de sol.
    Dintr-o drona, obiectele apar <em>de sus</em> — forme complet diferite.
    Un camp de grau vazut de la 100m nu seamana cu nimic din COCO.<br><br>
    <strong>Solutia pe termen scurt:</strong> analiza prin culoare + indici spectrale.<br>
    <strong>Solutia pe termen lung:</strong> antrenare YOLOv8 pe dataset propriu (Zilele 6-15).
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ─── UPLOAD ───────────────────────────────────────────────────────────────────
st.markdown('<p class="titlu">Incarca imaginea drone</p>', unsafe_allow_html=True)

fisier = st.file_uploader(
    "Imagine drone (JPG, PNG, TIF)",
    type=["jpg", "jpeg", "png", "tif", "tiff"]
)

if fisier is None:
    st.markdown("""
    <div class="card-albastru">
        Incarca orice imagine drone sau fotografie aeriana color.<br>
        Functioneaza si cu fotografii RGB normale — indicii ExG si VARI
        detecteaza vegetatia din orice unghi.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

img_pil = Image.open(fisier).convert("RGB")
img_np  = np.array(img_pil, dtype=np.float32)
h, w    = img_np.shape[:2]

R = img_np[:,:,0] / 255.0
G = img_np[:,:,1] / 255.0
B = img_np[:,:,2] / 255.0

st.markdown("---")

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
st.sidebar.markdown("### Parametri analiza")

metoda = st.sidebar.radio(
    "Metoda de analiza",
    ["Indici spectrale (ExG/VARI/GLI)", "Segmentare culoare HSV", "Ambele"]
)

prag_vegetatie = st.sidebar.slider(
    "Prag vegetatie (indice)",
    min_value=0.0, max_value=0.5, value=0.1, step=0.01,
    help="Pixelii cu indice > prag sunt considerati vegetatie"
)

if metoda in ["Segmentare culoare HSV", "Ambele"]:
    st.sidebar.markdown("**Parametri HSV verde:**")
    h_min = st.sidebar.slider("H min (nuanta verde)", 25, 60, 35)
    h_max = st.sidebar.slider("H max", 60, 100, 85)
    s_min = st.sidebar.slider("S min (saturatie)", 20, 80, 30)
    v_min = st.sidebar.slider("V min (luminozitate)", 20, 100, 40)

# ─── CALCUL INDICI ────────────────────────────────────────────────────────────
eps = 1e-6

ExG  = 2*G - R - B
VARI = (G - R) / (G + R - B + eps)
GLI  = (2*G - R - B) / (2*G + R + B + eps)

# Clip pentru vizualizare
ExG_viz  = np.clip(ExG,  -1, 1)
VARI_viz = np.clip(VARI, -1, 1)
GLI_viz  = np.clip(GLI,  -1, 1)

# Masti vegetatie
masca_ExG  = ExG  > prag_vegetatie
masca_VARI = VARI > prag_vegetatie
masca_GLI  = GLI  > prag_vegetatie
masca_indici = masca_ExG & masca_VARI   # combinatie ExG + VARI

# Segmentare HSV
masca_hsv = np.zeros((h, w), dtype=bool)
if metoda in ["Segmentare culoare HSV", "Ambele"] and CV2_OK:
    img_uint8 = (img_np).astype(np.uint8)
    img_hsv   = cv2.cvtColor(img_uint8, cv2.COLOR_RGB2HSV)
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, 255, 255])
    masca_hsv = cv2.inRange(img_hsv, lower, upper).astype(bool)

# ─── TABS REZULTATE ───────────────────────────────────────────────────────────
tab_indici, tab_hsv, tab_sinteza = st.tabs([
    "Indici spectrale", "Segmentare HSV", "Sinteza & Statistici"
])

# ══════════════════════════════════════════════════════
# TAB 1 — INDICI
# ══════════════════════════════════════════════════════
with tab_indici:
    st.markdown('<p class="titlu">Indici spectrale din banda RGB</p>',
                unsafe_allow_html=True)

    fig, axes = plt.subplots(2, 3, figsize=(12, 6))

    # Rand 1: imaginile indici
    for ax, indice, titlu, cmap in zip(
        axes[0],
        [ExG_viz, VARI_viz, GLI_viz],
        ["ExG = 2G-R-B", "VARI = (G-R)/(G+R-B)", "GLI = (2G-R-B)/(2G+R+B)"],
        ["RdYlGn", "RdYlGn", "RdYlGn"]
    ):
        im = ax.imshow(indice, cmap=cmap, vmin=-0.5, vmax=0.5)
        ax.set_title(titlu, fontsize=9)
        ax.axis("off")
        plt.colorbar(im, ax=ax, fraction=0.046)

    # Rand 2: mastile
    for ax, masca, titlu, culoare in zip(
        axes[1],
        [masca_ExG, masca_VARI, masca_GLI],
        [f"Vegetatie ExG (>{prag_vegetatie})",
         f"Vegetatie VARI (>{prag_vegetatie})",
         f"Vegetatie GLI (>{prag_vegetatie})"],
        ["#2e7d32", "#1565c0", "#6a1b9a"]
    ):
        overlay = img_np.astype(np.uint8).copy()
        overlay[masca] = [0, 200, 0]   # verde pentru vegetatie
        ax.imshow(overlay)
        pct = masca.mean() * 100
        ax.set_title(f"{titlu}\n{pct:.1f}% vegetatie", fontsize=9)
        ax.axis("off")

    plt.suptitle(f"Analiza indici spectrale — {fisier.name}", fontsize=11, y=1.01)
    plt.tight_layout()
    buf1 = BytesIO(); fig.savefig(buf1, dpi=150, bbox_inches="tight")
    buf1.seek(0); plt.close()
    st.image(buf1, use_container_width=True)

    # Statistici indici
    st.markdown("**Statistici indici:**")
    import pandas as pd
    df_stats = pd.DataFrame({
        "Indice": ["ExG", "VARI", "GLI"],
        "Medie":  [f"{ExG.mean():.3f}",  f"{VARI.mean():.3f}",  f"{GLI.mean():.3f}"],
        "Std":    [f"{ExG.std():.3f}",   f"{VARI.std():.3f}",   f"{GLI.std():.3f}"],
        "Min":    [f"{ExG.min():.3f}",   f"{VARI.min():.3f}",   f"{GLI.min():.3f}"],
        "Max":    [f"{ExG.max():.3f}",   f"{VARI.max():.3f}",   f"{GLI.max():.3f}"],
        "% Vegetatie": [f"{masca_ExG.mean()*100:.1f}%",
                        f"{masca_VARI.mean()*100:.1f}%",
                        f"{masca_GLI.mean()*100:.1f}%"],
    })
    st.dataframe(df_stats, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════
# TAB 2 — HSV
# ══════════════════════════════════════════════════════
with tab_hsv:
    st.markdown('<p class="titlu">Segmentare prin culoare (spatiu HSV)</p>',
                unsafe_allow_html=True)

    st.markdown("""
    <div class="card-albastru">
        <strong>Spatiul HSV</strong> (Hue-Saturation-Value) separa culoarea (H)
        de luminozitate (V) — mult mai robust decat RGB pentru detectia vegetatiei
        in conditii diferite de iluminare.
    </div>
    """, unsafe_allow_html=True)

    if not CV2_OK:
        st.warning("Instaleaza opencv-python: pip install opencv-python")
    else:
        fig2, axes2 = plt.subplots(1, 3, figsize=(12, 4))

        # Original
        axes2[0].imshow(img_np.astype(np.uint8))
        axes2[0].set_title("Original", fontsize=10); axes2[0].axis("off")

        # Masca HSV
        axes2[1].imshow(masca_hsv, cmap="Greens")
        axes2[1].set_title(f"Masca verde HSV\n{masca_hsv.mean()*100:.1f}% din imagine",
                           fontsize=10)
        axes2[1].axis("off")

        # Overlay
        overlay_hsv = img_np.astype(np.uint8).copy()
        overlay_hsv[masca_hsv] = [0, 220, 0]
        axes2[2].imshow(overlay_hsv)
        axes2[2].set_title("Overlay vegetatie (verde)", fontsize=10)
        axes2[2].axis("off")

        plt.tight_layout()
        buf2 = BytesIO(); fig2.savefig(buf2, dpi=150, bbox_inches="tight")
        buf2.seek(0); plt.close()
        st.image(buf2, use_container_width=True)

        st.markdown("""
        **Cum functioneaza HSV:**
        - **H (Hue):** nuanta culorii — verde = 35-85
        - **S (Saturation):** saturatia — valori mici = culori sterse (sol uscat)
        - **V (Value):** luminozitatea — valori mici = zone intunecate (umbra)
        """)

# ══════════════════════════════════════════════════════
# TAB 3 — SINTEZA
# ══════════════════════════════════════════════════════
with tab_sinteza:
    st.markdown('<p class="titlu">Sinteza si clasificare parcela</p>',
                unsafe_allow_html=True)

    pct_exg  = float(masca_ExG.mean()  * 100)
    pct_vari = float(masca_VARI.mean() * 100)
    pct_hsv  = float(masca_hsv.mean()  * 100) if CV2_OK else 0.0
    pct_comb = float(masca_indici.mean() * 100)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Vegetatie ExG",    f"{pct_exg:.1f}%")
    c2.metric("Vegetatie VARI",   f"{pct_vari:.1f}%")
    c3.metric("Vegetatie HSV",    f"{pct_hsv:.1f}%")
    c4.metric("Vegetatie combinat", f"{pct_comb:.1f}%")

    # Clasificare risc PAC
    pct_ref = pct_comb if pct_comb > 0 else pct_exg
    st.markdown("**Clasificare risc PAC (prag 20% vegetatie minima):**")

    if pct_ref >= 60:
        st.success(f"CONFORM — {pct_ref:.1f}% vegetatie detectata. Parcela eligibila PAC.")
    elif pct_ref >= 20:
        st.warning(f"RISC MEDIU — {pct_ref:.1f}% vegetatie. Verificare recomandata.")
    else:
        st.error(f"RISC RIDICAT — {pct_ref:.1f}% vegetatie. Sub pragul PAC de 20%.")

    # Histograma indici
    fig3, axes3 = plt.subplots(1, 3, figsize=(10, 3))
    for ax, vals, titlu, culoare in zip(
        axes3,
        [ExG.flatten(), VARI.flatten(), GLI.flatten()],
        ["ExG", "VARI", "GLI"],
        ["#2e7d32", "#1565c0", "#6a1b9a"]
    ):
        ax.hist(np.clip(vals, -1, 1), bins=60, color=culoare, alpha=0.75, edgecolor="none")
        ax.axvline(prag_vegetatie, color="#c62828", linestyle="--",
                   linewidth=1.5, label=f"Prag={prag_vegetatie}")
        ax.set_title(f"Distributie {titlu}", fontsize=9)
        ax.set_xlabel("Valoare indice"); ax.set_ylabel("Nr. pixeli")
        ax.legend(fontsize=8); ax.spines[["top","right"]].set_visible(False)

    plt.tight_layout()
    buf3 = BytesIO(); fig3.savefig(buf3, dpi=150, bbox_inches="tight")
    buf3.seek(0); plt.close()
    st.image(buf3, use_container_width=True)

    # Export imagine adnotata
    fig4, ax4 = plt.subplots(figsize=(8, 5))
    ax4.imshow(img_np.astype(np.uint8))
    overlay_final = img_np.astype(np.uint8).copy()
    overlay_final[masca_indici] = [0, 200, 0]
    overlay_final[~masca_indici] = (overlay_final[~masca_indici] * 0.6 +
                                     np.array([180, 80, 0]) * 0.4).clip(0,255).astype(np.uint8)
    ax4.imshow(overlay_final)
    verde_patch = mpatches.Patch(color="#00c800", label=f"Vegetatie ({pct_comb:.1f}%)")
    maro_patch  = mpatches.Patch(color="#b45000", label=f"Sol/lipsa veg. ({100-pct_comb:.1f}%)")
    ax4.legend(handles=[verde_patch, maro_patch], loc="upper right", fontsize=9)
    ax4.set_title(f"Harta vegetatie — {fisier.name}", fontsize=10)
    ax4.axis("off")
    plt.tight_layout()
    buf4 = BytesIO(); fig4.savefig(buf4, dpi=150, bbox_inches="tight")
    buf4.seek(0); plt.close()

    st.image(buf4, use_container_width=True)
    st.download_button(
        "Descarca harta vegetatie (PNG)",
        data=buf4,
        file_name=f"harta_vegetatie_{fisier.name.split('.')[0]}.png",
        mime="image/png"
    )

st.markdown("---")

# ─── Concept Ziua 3 ───────────────────────────────────────────────────────────
with st.expander("Conceptul Zilei 3 — De ce COCO nu merge pe drone + solutia"):
    st.markdown("""
**Problema:** YOLOv8 pre-antrenat pe COCO nu detecteaza nimic in imagini drone agricole.

**De ce?**
- COCO = 80 clase la nivel de sol (persoane, masini, animale)
- Imaginile drone = vedere de sus, culturi, sol — complet diferit vizual
- Un camp de grau la 100m nu seamana cu NIMIC din COCO

**Solutii:**
1. **Pe termen scurt (Ziua 3):** indici spectrale (ExG, VARI) + HSV — detectie prin culoare
2. **Pe termen mediu (Zilele 6-10):** construim propriul dataset cu imagini drone adnotate
3. **Pe termen lung (Zilele 11-15):** antrenam YOLOv8 pe datasetul nostru → detectie reala

**Fluxul corect pentru drone:**
""")
    st.code("""
import cv2
import numpy as np

# Imagine drone RGB
img = np.array(Image.open("drone.jpg")) / 255.0
R, G, B = img[:,:,0], img[:,:,1], img[:,:,2]

# Calcul indici
ExG  = 2*G - R - B
VARI = (G - R) / (G + R - B + 1e-6)

# Masca vegetatie
masca = (ExG > 0.1) & (VARI > 0.1)
pct_vegetatie = masca.mean() * 100
print(f"Vegetatie: {pct_vegetatie:.1f}%")

# Clasificare risc PAC
if pct_vegetatie < 20:
    print("RISC RIDICAT — sub pragul PAC")
    """, language="python")
