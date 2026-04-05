"""
BLOC 3 — Deep Learning YOLOv8, Ziua 8
Tiling imagini mari — 4608px → patch-uri 640px cu overlap
Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu | UCB Targu Jiu | APIA CJ Gorj

CONCEPT CHEIE:
  Tiling = taiere imagine mare in patch-uri mici pentru YOLOv8
  Overlap = suprapunere intre patch-uri (evita pierderea obiectelor la margini)
  Recalculare adnotari = coordonatele BBox se recalculeaza relativ la fiecare patch
  Formula: x_patch = (x_global - patch_x1) / patch_w  (normalizat in patch)
  Rezultat: N patch-uri + N fisiere .txt cu adnotari recalculate
"""

import streamlit as st
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
import zipfile
import os
from datetime import date

# ─── Configurare pagina ───────────────────────────────────────────────────────
st.set_page_config(page_title="Tiling Imagini — Ziua 8", layout="wide")

st.markdown("""
<style>
.titlu { color:#6a1b9a; font-size:1.05rem; font-weight:700;
         border-bottom:2px solid #6a1b9a; padding-bottom:4px; margin-bottom:12px; }
.card  { background:#f3e5f5; border-left:4px solid #6a1b9a;
         border-radius:6px; padding:12px 16px; margin-bottom:8px; }
.card-verde { background:#e8f5e9; border-left:4px solid #2e7d32;
              border-radius:6px; padding:12px 16px; margin-bottom:8px; }
.card-albastru { background:#e3f2fd; border-left:4px solid #1565c0;
                 border-radius:6px; padding:12px 16px; margin-bottom:8px; }
</style>
""", unsafe_allow_html=True)

st.title("Ziua 8 — Tiling Imagini Drone Mari")
st.markdown("**De la 4608x3456 px la sute de patch-uri 640x640 px gata de antrenat**")
st.markdown("---")

# ─── SECTIUNEA 1: De ce tiling? ───────────────────────────────────────────────
st.markdown('<p class="titlu">De ce avem nevoie de tiling?</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    <div class="card">
        <strong>Problema:</strong> imaginile drone sunt uriase (4608x3456 px).
        YOLOv8 redimensioneaza automat la 640px — obiectele mici (parcele,
        culturi) devin pixeli si nu mai pot fi detectate.<br><br>
        <strong>Solutia:</strong> taiem imaginea in patch-uri de 640x640 px
        cu un overlap de 10-20% — fiecare patch e procesat separat,
        pastrandu-se detaliile fine.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card-verde">
        <strong>Calcul nr. patch-uri:</strong><br>
        Imagine 4608x3456 | patch 640 | overlap 10% (64px)<br>
        Pas efectiv = 640 - 64 = 576 px<br>
        Nr. coloane = ceil(4608 / 576) = <strong>8</strong><br>
        Nr. randuri  = ceil(3456 / 576) = <strong>6</strong><br>
        <strong>Total = 48 patch-uri dintr-o singura imagine!</strong>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # Diagrama tiling
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.set_xlim(0, 10); ax.set_ylim(0, 8); ax.axis("off")

    # Imagine originala
    ax.add_patch(patches.FancyBboxPatch((0.2, 0.5), 9.6, 7.0,
                 boxstyle="round,pad=0.1",
                 facecolor="#a5d6a7", edgecolor="#2e7d32", linewidth=2))
    ax.text(5, 7.2, "Imagine drone originala: 4608 x 3456 px",
            ha="center", fontsize=8, color="#1b5e20", fontweight="bold")

    # Grid patch-uri
    cols_p, rows_p = 6, 4
    pw = 9.6 / cols_p; ph = 7.0 / rows_p
    for r in range(rows_p):
        for c in range(cols_p):
            x = 0.2 + c * pw; y = 0.5 + r * ph
            culoare = "#c8e6c9" if (r + c) % 2 == 0 else "#a5d6a7"
            ax.add_patch(patches.Rectangle((x+0.04, y+0.04), pw-0.08, ph-0.08,
                         facecolor=culoare, edgecolor="#1565c0",
                         linewidth=1, linestyle="--"))
            ax.text(x + pw/2, y + ph/2, f"{r*cols_p+c+1}",
                    ha="center", va="center", fontsize=6, color="#1565c0")

    ax.text(5, 0.2, f"{cols_p * rows_p} patch-uri 640x640 px",
            ha="center", fontsize=8, color="#1565c0", fontweight="bold")
    plt.tight_layout()
    buf_d = BytesIO(); fig.savefig(buf_d, dpi=150, bbox_inches="tight")
    buf_d.seek(0); plt.close()
    st.image(buf_d, use_container_width=True)

st.markdown("---")

# ─── SECTIUNEA 2: Tiling interactiv ──────────────────────────────────────────
st.markdown('<p class="titlu">Tiling interactiv — upload imagine drone</p>',
            unsafe_allow_html=True)

# Sidebar parametri
st.sidebar.markdown("### Parametri tiling")
patch_size  = st.sidebar.selectbox("Marime patch (px)", [320, 416, 512, 640, 1024], index=3)
overlap_pct = st.sidebar.slider("Overlap (%)", 0, 30, 10, 5)
min_vizibil = st.sidebar.slider("Vizibilitate minima BBox (%)", 10, 80, 30, 10,
    help="BBox-urile cu mai putin de X% in patch sunt ignorate")
clasa_input = st.sidebar.text_input("Clase:", "grau, porumb, rapita, vegetatie_lipsa")
clase_lista = [c.strip() for c in clasa_input.split(",")]

overlap_px  = int(patch_size * overlap_pct / 100)
pas         = patch_size - overlap_px

fisier_img = st.file_uploader("Imagine drone (JPG, PNG, TIF)",
                               type=["jpg","jpeg","png","tif","tiff"])
fisier_txt = st.file_uploader("Adnotari .txt (optional — daca ai adnotat imaginea)",
                               type=["txt"])

def recalculeaza_adnotari(adnotari, img_w, img_h, px1, py1, patch_w, patch_h, min_viz):
    """Recalculeaza coordonatele BBox pentru un patch."""
    adnotari_patch = []
    for cls_id, xc, yc, w, h in adnotari:
        # Coordonate absolute in imaginea originala
        x1_g = (xc - w/2) * img_w
        y1_g = (yc - h/2) * img_h
        x2_g = (xc + w/2) * img_w
        y2_g = (yc + h/2) * img_h

        # Intersectie cu patch-ul
        ix1 = max(x1_g, px1); iy1 = max(y1_g, py1)
        ix2 = min(x2_g, px1 + patch_w)
        iy2 = min(y2_g, py1 + patch_h)

        if ix2 <= ix1 or iy2 <= iy1:
            continue  # BBox complet in afara patch-ului

        # Procent vizibil din BBox original
        aria_orig  = (x2_g - x1_g) * (y2_g - y1_g)
        aria_inter = (ix2 - ix1) * (iy2 - iy1)
        pct_viz    = aria_inter / max(aria_orig, 1) * 100

        if pct_viz < min_viz:
            continue  # prea putin vizibil

        # Coordonate normalizate relativ la patch
        xc_p = ((ix1 + ix2) / 2 - px1) / patch_w
        yc_p = ((iy1 + iy2) / 2 - py1) / patch_h
        w_p  = (ix2 - ix1) / patch_w
        h_p  = (iy2 - iy1) / patch_h

        adnotari_patch.append((cls_id, xc_p, yc_p, w_p, h_p))
    return adnotari_patch

if fisier_img:
    img_pil  = Image.open(fisier_img).convert("RGB")
    img_np   = np.array(img_pil)
    W, H     = img_pil.width, img_pil.height

    # Calcul grid patch-uri
    import math
    n_cols = math.ceil((W - overlap_px) / pas)
    n_rows = math.ceil((H - overlap_px) / pas)
    n_total = n_cols * n_rows

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Imagine originala", f"{W}x{H} px")
    c2.metric("Marime patch", f"{patch_size}x{patch_size} px")
    c3.metric("Overlap", f"{overlap_px} px ({overlap_pct}%)")
    c4.metric("Total patch-uri", n_total)

    # Citire adnotari (daca exista)
    adnotari_globale = []
    if fisier_txt:
        continut = fisier_txt.read().decode("utf-8").strip()
        for linie in continut.split("\n"):
            parti = linie.strip().split()
            if len(parti) == 5:
                try:
                    cls_id = int(parti[0])
                    xc, yc, w, h = [float(p) for p in parti[1:]]
                    adnotari_globale.append((cls_id, xc, yc, w, h))
                except ValueError:
                    pass
        st.info(f"{len(adnotari_globale)} adnotari incarcate din fisierul .txt")

    # Vizualizare grid pe imagine
    st.markdown("**Previzualizare grid patch-uri pe imagine:**")
    scale = min(800 / W, 600 / H)
    W_viz = int(W * scale); H_viz = int(H * scale)
    img_viz = img_pil.resize((W_viz, H_viz), Image.LANCZOS)

    fig2, ax2 = plt.subplots(figsize=(10, 6))
    ax2.imshow(img_viz)

    for r in range(n_rows):
        for c in range(n_cols):
            x1 = c * pas; y1 = r * pas
            x2 = min(x1 + patch_size, W)
            y2 = min(y1 + patch_size, H)
            ax2.add_patch(patches.Rectangle(
                (x1 * scale, y1 * scale),
                (x2 - x1) * scale, (y2 - y1) * scale,
                facecolor="none", edgecolor="#1565c0",
                linewidth=0.8, alpha=0.7
            ))
            ax2.text(
                (x1 + (x2-x1)/2) * scale,
                (y1 + (y2-y1)/2) * scale,
                f"{r*n_cols+c+1}",
                ha="center", va="center",
                fontsize=5, color="white",
                bbox=dict(boxstyle="round,pad=0.1",
                          facecolor="#1565c0", alpha=0.6)
            )

    # Deseneaza si adnotarile originale
    for cls_id, xc, yc, w, h in adnotari_globale:
        x1_g = (xc - w/2) * W * scale
        y1_g = (yc - h/2) * H * scale
        w_g  = w * W * scale
        h_g  = h * H * scale
        ax2.add_patch(patches.Rectangle(
            (x1_g, y1_g), w_g, h_g,
            facecolor="none", edgecolor="#c62828", linewidth=1.5
        ))

    ax2.set_title(f"Grid {n_rows}x{n_cols} = {n_total} patch-uri "
                  f"| {patch_size}px | overlap {overlap_pct}%", fontsize=9)
    ax2.axis("off")
    plt.tight_layout()
    buf2 = BytesIO(); fig2.savefig(buf2, dpi=150, bbox_inches="tight")
    buf2.seek(0); plt.close()
    st.image(buf2, use_container_width=True)

    st.markdown("---")

    # Previzualizare primul patch
    st.markdown('<p class="titlu">Previzualizare patch-uri individuale</p>',
                unsafe_allow_html=True)

    idx_patch = st.slider("Selecteaza patch-ul", 0, n_total - 1, 0)
    r_sel = idx_patch // n_cols
    c_sel = idx_patch  % n_cols
    px1 = c_sel * pas; py1 = r_sel * pas
    px2 = min(px1 + patch_size, W)
    py2 = min(py1 + patch_size, H)

    patch_img = img_pil.crop((px1, py1, px2, py2))
    patch_w   = px2 - px1; patch_h = py2 - py1

    adnotari_patch = recalculeaza_adnotari(
        adnotari_globale, W, H, px1, py1, patch_w, patch_h, min_vizibil
    )

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        fig3, ax3 = plt.subplots(figsize=(5, 5))
        ax3.imshow(patch_img)
        for cls_id, xc_p, yc_p, w_p, h_p in adnotari_patch:
            px1b = (xc_p - w_p/2) * patch_w
            py1b = (yc_p - h_p/2) * patch_h
            ax3.add_patch(patches.Rectangle(
                (px1b, py1b), w_p * patch_w, h_p * patch_h,
                facecolor="none", edgecolor="#c62828", linewidth=2
            ))
            cls_name = clase_lista[cls_id] if cls_id < len(clase_lista) else str(cls_id)
            ax3.text(px1b + 3, py1b + 14, cls_name,
                     fontsize=8, color="white", fontweight="bold",
                     bbox=dict(facecolor="#c62828", alpha=0.8, pad=1))
        ax3.set_title(f"Patch #{idx_patch+1} ({px1},{py1})→({px2},{py2})\n"
                      f"{len(adnotari_patch)} adnotari in acest patch", fontsize=9)
        ax3.axis("off")
        plt.tight_layout()
        buf3 = BytesIO(); fig3.savefig(buf3, dpi=150, bbox_inches="tight")
        buf3.seek(0); plt.close()
        st.image(buf3, use_container_width=True)

    with col_p2:
        st.markdown(f"**Patch #{idx_patch+1}:**")
        st.markdown(f"- Pozitie: ({px1}, {py1}) → ({px2}, {py2})")
        st.markdown(f"- Dimensiune: {patch_w}x{patch_h} px")
        st.markdown(f"- Adnotari in patch: **{len(adnotari_patch)}**")

        if adnotari_patch:
            import pandas as pd
            df_p = pd.DataFrame([{
                "Nr.":    i+1,
                "Clasa":  clase_lista[c] if c < len(clase_lista) else str(c),
                "x_c":    round(x, 4),
                "y_c":    round(y, 4),
                "w":      round(w, 4),
                "h":      round(h, 4),
            } for i,(c,x,y,w,h) in enumerate(adnotari_patch)])
            st.dataframe(df_p, use_container_width=True, hide_index=True)

            txt_patch = "\n".join(
                [f"{c} {x:.6f} {y:.6f} {w:.6f} {h:.6f}"
                 for c,x,y,w,h in adnotari_patch]
            )
            st.code(txt_patch, language="text")
        else:
            if adnotari_globale:
                st.info("Nicio adnotare in acest patch "
                        f"(vizibilitate minima {min_vizibil}%). "
                        "Incearca alt patch sau scade pragul de vizibilitate.")
            else:
                st.info("Incarca un fisier .txt cu adnotari pentru a vedea "
                        "recalcularea coordonatelor per patch.")

    st.markdown("---")

    # Export ZIP patch-uri
    st.markdown('<p class="titlu">Export toate patch-urile in ZIP</p>',
                unsafe_allow_html=True)

    max_patch_export = st.slider(
        "Nr. maxim patch-uri de exportat",
        min_value=5, max_value=min(n_total, 100), value=min(n_total, 20)
    )

    st.markdown(f"""
    <div class="card-albastru">
        Se vor exporta <strong>{max_patch_export}</strong> din {n_total} patch-uri totale,
        impreuna cu fisierele .txt recalculate. Gata de adaugat in dataset pentru antrenare.
    </div>
    """, unsafe_allow_html=True)

    if st.button("Genereaza ZIP patch-uri", type="primary"):
        with st.spinner(f"Se genereaza {max_patch_export} patch-uri..."):
            progres = st.progress(0)
            buf_zip = BytesIO()
            nume_baza = os.path.splitext(fisier_img.name)[0]

            with zipfile.ZipFile(buf_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                count = 0
                for r in range(n_rows):
                    for c in range(n_cols):
                        if count >= max_patch_export:
                            break
                        px1_e = c * pas; py1_e = r * pas
                        px2_e = min(px1_e + patch_size, W)
                        py2_e = min(py1_e + patch_size, H)
                        pw_e  = px2_e - px1_e; ph_e = py2_e - py1_e

                        patch = img_pil.crop((px1_e, py1_e, px2_e, py2_e))

                        # Redimensionare la patch_size exact
                        if pw_e < patch_size or ph_e < patch_size:
                            patch_pad = Image.new("RGB", (patch_size, patch_size),
                                                  color=(0,0,0))
                            patch_pad.paste(patch, (0,0))
                            patch = patch_pad

                        buf_p = BytesIO()
                        patch.save(buf_p, format="JPEG", quality=92)
                        nume_patch = f"{nume_baza}_r{r:02d}_c{c:02d}"
                        zf.writestr(f"patches/images/{nume_patch}.jpg",
                                    buf_p.getvalue())

                        # Adnotari recalculate
                        adt_p = recalculeaza_adnotari(
                            adnotari_globale, W, H, px1_e, py1_e,
                            patch_size, patch_size, min_vizibil
                        )
                        txt_p = "\n".join(
                            [f"{cl} {x:.6f} {y:.6f} {w:.6f} {h:.6f}"
                             for cl,x,y,w,h in adt_p]
                        )
                        zf.writestr(f"patches/labels/{nume_patch}.txt", txt_p)

                        count += 1
                        progres.progress(count / max_patch_export)
                    else:
                        continue
                    break

            buf_zip.seek(0)
            progres.empty()

        st.success(f"{max_patch_export} patch-uri generate!")
        st.download_button(
            "Descarca ZIP patch-uri",
            data=buf_zip,
            file_name=f"patches_{nume_baza}_{patch_size}px.zip",
            mime="application/zip"
        )

else:
    st.markdown("""
    <div class="card-albastru">
        Incarca o imagine drone pentru a vedea tiling-ul in actiune.<br>
        Recomandat: imaginea ta reala <strong>GJ_78258-1675...jpg</strong> (4608x3456 px).
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ─── Concept Ziua 8 ───────────────────────────────────────────────────────────
with st.expander("Conceptul Zilei 8 — Tiling si recalcularea adnotarilor"):
    st.markdown("""
**De ce recalculam coordonatele?**
O adnotare `0 0.50 0.50 0.20 0.15` e relativa la imaginea originala (4608x3456).
Dupa tiling, patch-ul are alta origine si alta dimensiune — coordonatele se schimba.
""")
    st.code("""
# Recalculare coordonate BBox pentru un patch
def recalculeaza(xc, yc, w, h, img_W, img_H, px1, py1, patch_size):
    # Coordonate absolute in imaginea originala
    x1_g = (xc - w/2) * img_W
    y1_g = (yc - h/2) * img_H
    x2_g = (xc + w/2) * img_W
    y2_g = (yc + h/2) * img_H

    # Intersectie cu patch-ul
    ix1 = max(x1_g, px1)
    iy1 = max(y1_g, py1)
    ix2 = min(x2_g, px1 + patch_size)
    iy2 = min(y2_g, py1 + patch_size)

    if ix2 <= ix1 or iy2 <= iy1:
        return None  # BBox in afara patch-ului

    # Coordonate normalizate relativ la patch
    xc_p = ((ix1 + ix2) / 2 - px1) / patch_size
    yc_p = ((iy1 + iy2) / 2 - py1) / patch_size
    w_p  = (ix2 - ix1) / patch_size
    h_p  = (iy2 - iy1) / patch_size

    return xc_p, yc_p, w_p, h_p

# Pas efectiv intre patch-uri (cu overlap 10%)
patch_size  = 640
overlap_px  = int(640 * 0.10)   # 64 px
pas         = patch_size - overlap_px  # 576 px
    """, language="python")
    st.info("Overlap-ul asigura ca obiectele de la marginea unui patch "
            "apar complet in patch-ul vecin — esential pentru detectie corecta.")
