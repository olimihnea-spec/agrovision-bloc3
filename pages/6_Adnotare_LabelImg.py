"""
BLOC 3 — Deep Learning YOLOv8, Ziua 6
Adnotare imagini drone cu LabelImg — ghid + verificator adnotari
Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu | UCB Targu Jiu | APIA CJ Gorj

CONCEPT CHEIE:
  LabelImg = tool grafic gratuit pentru adnotare imagini (genereaza .txt YOLO automat)
  Verificator adnotari = upload imagine + .txt → deseneaza BBox-urile pe imagine
  Acest modul = ghid instalare + verificator interactiv + statistici adnotari
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

# ─── Configurare pagina ───────────────────────────────────────────────────────
st.set_page_config(page_title="Adnotare LabelImg — Ziua 6", layout="wide")

st.markdown("""
<style>
.titlu { color:#1565c0; font-size:1.05rem; font-weight:700;
         border-bottom:2px solid #1565c0; padding-bottom:4px; margin-bottom:12px; }
.card  { background:#e3f2fd; border-left:4px solid #1565c0;
         border-radius:6px; padding:12px 16px; margin-bottom:8px; }
.card-verde { background:#e8f5e9; border-left:4px solid #2e7d32;
              border-radius:6px; padding:12px 16px; margin-bottom:8px; }
.card-galben { background:#fff8e1; border-left:4px solid #f9a825;
               border-radius:6px; padding:12px 16px; margin-bottom:8px; }
.pas { background:#e8eaf6; border-left:4px solid #3949ab;
       border-radius:6px; padding:10px 14px; margin-bottom:6px; }
</style>
""", unsafe_allow_html=True)

st.title("Ziua 6 — Adnotare cu LabelImg")
st.markdown("**Ghid instalare + utilizare + verificator interactiv adnotari YOLO**")
st.markdown("---")

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab_ghid, tab_verificator, tab_statistici = st.tabs([
    "Ghid LabelImg", "Verificator adnotari", "Statistici dataset"
])

# ══════════════════════════════════════════════════════
# TAB 1 — GHID
# ══════════════════════════════════════════════════════
with tab_ghid:
    st.markdown('<p class="titlu">Ce este LabelImg si cum il instalezi</p>',
                unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("""
        <div class="card">
            <strong>LabelImg</strong> este un tool grafic gratuit, open-source,
            pentru adnotarea imaginilor. Deseneaza dreptunghiuri (BBox) pe imagini
            si salveaza automat fisierele <code>.txt</code> in format YOLO.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Instalare (o singura data):**")
        st.code("pip install labelImg", language="bash")

        st.markdown("**Pornire:**")
        st.code("labelImg", language="bash")

        st.markdown("""
        <div class="card-galben">
            <strong>Alternativa recomandata:</strong> daca LabelImg nu porneste,
            foloseste <strong>Label Studio</strong> (interfata web mai moderna):<br>
            <code>pip install label-studio</code><br>
            <code>label-studio start</code>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Diagrama interfata LabelImg
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.set_xlim(0, 10); ax.set_ylim(0, 8); ax.axis("off")

        # Fereastra principala
        ax.add_patch(patches.FancyBboxPatch((0.2,0.2), 9.6, 7.6,
                     boxstyle="round,pad=0.1", facecolor="#f5f5f5",
                     edgecolor="#333", linewidth=1.5))

        # Bara meniu
        ax.add_patch(patches.Rectangle((0.2,7.3), 9.6, 0.5,
                     facecolor="#2196f3", edgecolor="none"))
        ax.text(5, 7.55, "LabelImg — imagine_drone.jpg",
                ha="center", va="center", fontsize=8, color="white", fontweight="bold")

        # Panel stanga
        ax.add_patch(patches.Rectangle((0.2,0.2), 2, 7.1,
                     facecolor="#eceff1", edgecolor="#bbb"))
        for y, txt in [(6.8,"Open Dir"),(6.3,"Save"),(5.8,"YOLO format"),
                       (5.3,"Create RectBox"),(4.8,"Classes:")]:
            ax.text(1.2, y, txt, ha="center", va="center", fontsize=7, color="#333")
        for i, cls in enumerate(["grau","porumb","rapita","veg_lipsa"]):
            ax.text(1.2, 4.2-i*0.4, cls, ha="center", va="center",
                    fontsize=7, color="#1565c0")

        # Imagine centrala
        ax.add_patch(patches.Rectangle((2.3,0.3), 7.4, 6.9,
                     facecolor="#a5d6a7", edgecolor="#555"))

        # BBox desenate
        ax.add_patch(patches.Rectangle((3.0,1.5), 2.5, 2.0,
                     facecolor="none", edgecolor="#c62828", linewidth=2))
        ax.text(3.1, 3.6, "grau (0)", fontsize=7, color="#c62828", fontweight="bold")

        ax.add_patch(patches.Rectangle((6.5,3.0), 2.0, 2.5,
                     facecolor="none", edgecolor="#1565c0", linewidth=2))
        ax.text(6.6, 5.6, "porumb (1)", fontsize=7, color="#1565c0", fontweight="bold")

        ax.set_title("Interfata LabelImg (simulata)", fontsize=9)
        plt.tight_layout()
        buf = BytesIO(); fig.savefig(buf, dpi=150, bbox_inches="tight")
        buf.seek(0); plt.close()
        st.image(buf, use_container_width=True)

    st.markdown("---")
    st.markdown('<p class="titlu">Pasi pentru adnotare imagine drone</p>',
                unsafe_allow_html=True)

    pasi = [
        ("Pas 1", "Porneste LabelImg",
         "Ruleaza <code>labelImg</code> in terminal. Se deschide o fereastra grafica."),
        ("Pas 2", "Seteaza format YOLO",
         "Click pe butonul <strong>PascalVOC</strong> din stanga pana apare <strong>YOLO</strong>."),
        ("Pas 3", "Deschide folderul cu imagini",
         "<strong>Open Dir</strong> → selecteaza folderul cu imagini drone."),
        ("Pas 4", "Seteaza folderul de salvare",
         "<strong>Change Save Dir</strong> → selecteaza <code>labels/train/</code>."),
        ("Pas 5", "Adnoteaza prima imagine",
         "Apasa <strong>W</strong> sau click <strong>Create RectBox</strong> → deseneaza un dreptunghi."),
        ("Pas 6", "Alege clasa",
         "Apare o fereastra → scrie clasa (ex: <code>grau</code>) sau selecteaz-o din lista."),
        ("Pas 7", "Salveaza",
         "Apasa <strong>Ctrl+S</strong>. Se creeaza automat fisierul <code>imagine.txt</code>."),
        ("Pas 8", "Treci la urmatoarea",
         "Apasa <strong>D</strong> (next) sau <strong>A</strong> (previous)."),
    ]

    col_p1, col_p2 = st.columns(2)
    for i, (pas, titlu, desc) in enumerate(pasi):
        col = col_p1 if i % 2 == 0 else col_p2
        with col:
            st.markdown(f"""
            <div class="pas">
                <strong>{pas}: {titlu}</strong><br>
                <small>{desc}</small>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p class="titlu">Scurtaturi tastatura LabelImg</p>',
                unsafe_allow_html=True)

    shortcuts = pd.DataFrame([
        ("W",       "Creeaza BBox nou"),
        ("D",       "Urmatoarea imagine"),
        ("A",       "Imaginea anterioara"),
        ("Ctrl+S",  "Salveaza adnotarile"),
        ("Del",     "Sterge BBox selectat"),
        ("Ctrl+Z",  "Undo"),
        ("Scroll",  "Zoom in/out"),
        ("Ctrl+R",  "Schimba directorul de salvare"),
    ], columns=["Tasta", "Actiune"])
    st.dataframe(shortcuts, use_container_width=False, hide_index=True)

    st.markdown("""
    <div class="card-verde">
        <strong>Sfat pentru imagini drone mari (4608x3456):</strong>
        Taie imaginile in patch-uri de 640x640 sau 1024x1024 inainte de adnotare.
        YOLOv8 proceseaza implicit la 640px — imaginile mari sunt redimensionate automat,
        pierzand detalii fine. Vom face acest lucru la Ziua 8 (tiling).
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# TAB 2 — VERIFICATOR
# ══════════════════════════════════════════════════════
with tab_verificator:
    st.markdown('<p class="titlu">Verificator adnotari — upload imagine + .txt</p>',
                unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        Incarca o imagine si fisierul <code>.txt</code> cu adnotarile YOLO.
        Aplicatia deseneaza BBox-urile si verifica daca sunt corecte.
    </div>
    """, unsafe_allow_html=True)

    # Clase configurabile
    clase_input = st.text_input(
        "Clasele tale (separate prin virgula, in ordinea ID-urilor):",
        value="grau, porumb, rapita, vegetatie_lipsa"
    )
    clase_lista = [c.strip() for c in clase_input.split(",")]
    CULORI_VIZ = ["#c62828","#1565c0","#2e7d32","#e65100","#6a1b9a","#00838f"]

    col_up1, col_up2 = st.columns(2)
    with col_up1:
        fisier_img = st.file_uploader("Imaginea (.jpg/.png)", type=["jpg","jpeg","png","tif"])
    with col_up2:
        fisier_txt = st.file_uploader("Adnotarile (.txt)", type=["txt"])

    if fisier_img and fisier_txt:
        img_pil = Image.open(fisier_img).convert("RGB")
        W, H    = img_pil.width, img_pil.height

        # Citire adnotari
        continut = fisier_txt.read().decode("utf-8").strip()
        linii    = [l.strip() for l in continut.split("\n") if l.strip()]

        adnotari = []
        erori    = []
        for i, linie in enumerate(linii):
            parti = linie.split()
            if len(parti) != 5:
                erori.append(f"Linia {i+1}: format invalid — {linie}")
                continue
            try:
                cls_id = int(parti[0])
                x_c, y_c, w_n, h_n = [float(p) for p in parti[1:]]
                if not all(0 <= v <= 1 for v in [x_c, y_c, w_n, h_n]):
                    erori.append(f"Linia {i+1}: valori in afara [0,1] — {linie}")
                    continue
                adnotari.append((cls_id, x_c, y_c, w_n, h_n))
            except ValueError:
                erori.append(f"Linia {i+1}: valori non-numerice — {linie}")

        if erori:
            for e in erori:
                st.error(e)

        # Vizualizare
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.imshow(img_pil)

        for cls_id, x_c, y_c, w_n, h_n in adnotari:
            # Conversie la pixeli
            px_w = w_n * W; px_h = h_n * H
            px_x1 = (x_c - w_n/2) * W
            px_y1 = (y_c - h_n/2) * H

            culoare = CULORI_VIZ[cls_id % len(CULORI_VIZ)]
            ax.add_patch(patches.Rectangle(
                (px_x1, px_y1), px_w, px_h,
                facecolor="none", edgecolor=culoare, linewidth=2.5
            ))

            cls_name = clase_lista[cls_id] if cls_id < len(clase_lista) else str(cls_id)
            ax.text(px_x1 + 4, px_y1 + 16, cls_name,
                    fontsize=9, color="white", fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor=culoare, alpha=0.85))

        ax.set_title(f"{fisier_img.name} — {len(adnotari)} adnotari verificate",
                     fontsize=10)
        ax.axis("off")
        plt.tight_layout()
        buf_v = BytesIO(); fig.savefig(buf_v, dpi=150, bbox_inches="tight")
        buf_v.seek(0); plt.close()
        st.image(buf_v, use_container_width=True)

        # Tabel adnotari
        if adnotari:
            df_adt = pd.DataFrame([{
                "Nr.": i+1,
                "Clasa ID": cls_id,
                "Clasa": clase_lista[cls_id] if cls_id < len(clase_lista) else "?",
                "x_center": round(x_c, 4),
                "y_center": round(y_c, 4),
                "width":    round(w_n, 4),
                "height":   round(h_n, 4),
                "Aria (%)": round(w_n * h_n * 100, 2),
            } for i, (cls_id, x_c, y_c, w_n, h_n) in enumerate(adnotari)])

            st.dataframe(df_adt, use_container_width=True, hide_index=True)

            c1, c2, c3 = st.columns(3)
            c1.metric("Total adnotari", len(adnotari))
            c2.metric("Clase unice", len(set(a[0] for a in adnotari)))
            c3.metric("Erori format", len(erori))

            if not erori:
                st.success("Adnotarile sunt valide — gata pentru antrenare YOLOv8!")
    else:
        # Demo cu adnotari simulate
        st.markdown("""
        <div class="card-galben">
            Nu ai inca adnotari? Incarca imaginea drone si creeaza manual un fisier .txt
            cu adnotarile de test. Exemplu de continut pentru fisierul .txt:
        </div>
        """, unsafe_allow_html=True)
        st.code("""
0 0.512 0.347 0.234 0.189
1 0.731 0.612 0.156 0.204
0 0.123 0.789 0.098 0.112
2 0.456 0.234 0.312 0.201
        """, language="text")

# ══════════════════════════════════════════════════════
# TAB 3 — STATISTICI DATASET
# ══════════════════════════════════════════════════════
with tab_statistici:
    st.markdown('<p class="titlu">Statistici dataset — analiza adnotari multiple</p>',
                unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        Incarca mai multe fisiere <code>.txt</code> de adnotari pentru a vedea
        statistica intregului dataset: distributia claselor, dimensiunea medie a BBox-urilor,
        echilibrul intre clase.
    </div>
    """, unsafe_allow_html=True)

    fisiere_txt = st.file_uploader(
        "Selecteaza fisierele .txt de adnotari",
        type=["txt"],
        accept_multiple_files=True,
        key="stat_upload"
    )

    clase_stat = st.text_input(
        "Clasele (separate prin virgula):",
        value="grau, porumb, rapita, vegetatie_lipsa",
        key="clase_stat"
    )
    clase_stat_lista = [c.strip() for c in clase_stat.split(",")]

    if fisiere_txt:
        toate_adnotarile = []
        for fisier in fisiere_txt:
            continut = fisier.read().decode("utf-8").strip()
            for linie in continut.split("\n"):
                parti = linie.strip().split()
                if len(parti) == 5:
                    try:
                        cls_id = int(parti[0])
                        x_c, y_c, w_n, h_n = [float(p) for p in parti[1:]]
                        toate_adnotarile.append({
                            "fisier":   fisier.name,
                            "clasa_id": cls_id,
                            "clasa":    clase_stat_lista[cls_id] if cls_id < len(clase_stat_lista) else str(cls_id),
                            "x_c": x_c, "y_c": y_c,
                            "w": w_n, "h": h_n,
                            "aria": round(w_n * h_n * 100, 4),
                        })
                    except (ValueError, IndexError):
                        pass

        if toate_adnotarile:
            df_all = pd.DataFrame(toate_adnotarile)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Fisiere adnotate", len(fisiere_txt))
            c2.metric("Total BBox-uri",   len(df_all))
            c3.metric("Clase unice",      df_all["clasa_id"].nunique())
            c4.metric("BBox/imagine (med)", round(len(df_all)/len(fisiere_txt), 1))

            col_s1, col_s2 = st.columns(2)

            with col_s1:
                dist_cls = df_all["clasa"].value_counts()
                fig_s1, ax_s1 = plt.subplots(figsize=(5, 3))
                culori_bar = ["#c62828","#1565c0","#2e7d32","#e65100"][:len(dist_cls)]
                ax_s1.bar(dist_cls.index, dist_cls.values, color=culori_bar, edgecolor="white")
                ax_s1.set_title("Distributia claselor in dataset", fontsize=9)
                ax_s1.set_ylabel("Nr. BBox-uri")
                ax_s1.spines[["top","right"]].set_visible(False)
                plt.tight_layout()
                buf_s1 = BytesIO(); fig_s1.savefig(buf_s1, dpi=150, bbox_inches="tight")
                buf_s1.seek(0); plt.close()
                st.image(buf_s1, use_container_width=True)

                # Echilibru clase
                max_cls = dist_cls.max(); min_cls = dist_cls.min()
                ratio   = max_cls / max(min_cls, 1)
                if ratio < 3:
                    st.success(f"Dataset echilibrat (ratio max/min = {ratio:.1f}x)")
                elif ratio < 10:
                    st.warning(f"Dataset moderat dezechilibrat ({ratio:.1f}x) — considera augmentare")
                else:
                    st.error(f"Dataset foarte dezechilibrat ({ratio:.1f}x) — necesita reechilibrare")

            with col_s2:
                fig_s2, ax_s2 = plt.subplots(figsize=(5, 3))
                ax_s2.scatter(df_all["w"], df_all["h"], alpha=0.5, s=20,
                              c=[["#c62828","#1565c0","#2e7d32","#e65100"][i % 4]
                                 for i in df_all["clasa_id"]])
                ax_s2.set_xlabel("Latime BBox (normalizat)")
                ax_s2.set_ylabel("Inaltime BBox (normalizat)")
                ax_s2.set_title("Dimensiuni BBox-uri", fontsize=9)
                ax_s2.spines[["top","right"]].set_visible(False)
                plt.tight_layout()
                buf_s2 = BytesIO(); fig_s2.savefig(buf_s2, dpi=150, bbox_inches="tight")
                buf_s2.seek(0); plt.close()
                st.image(buf_s2, use_container_width=True)

            st.dataframe(
                df_all.groupby("clasa").agg(
                    Nr_BBox=("clasa","count"),
                    W_medie=("w", lambda x: round(x.mean(), 4)),
                    H_medie=("h", lambda x: round(x.mean(), 4)),
                    Aria_medie=("aria", lambda x: round(x.mean(), 4)),
                ).reset_index(),
                use_container_width=True, hide_index=True
            )
        else:
            st.warning("Nicio adnotare valida gasita in fisierele incarcate.")
    else:
        st.info("Incarca fisierele .txt de adnotari pentru a vedea statisticile.")

st.markdown("---")

with st.expander("Conceptul Zilei 6 — LabelImg si verificarea adnotarilor"):
    st.markdown("""
**Fluxul complet de adnotare pentru YOLOv8:**
""")
    st.code("""
# 1. Instalare
pip install labelImg

# 2. Pornire
labelImg

# 3. In interfata:
#    - Format: YOLO (nu PascalVOC!)
#    - Open Dir → folderul cu imagini drone
#    - Change Save Dir → labels/train/
#    - W → deseneaza BBox → scrie clasa → Enter
#    - Ctrl+S → salveaza → D → urmatoarea imagine

# 4. Verificare programatica a adnotarilor
def verifica_adnotare(fisier_txt, img_w, img_h):
    with open(fisier_txt) as f:
        for linie in f:
            parti = linie.strip().split()
            assert len(parti) == 5, f"Format invalid: {linie}"
            cls_id = int(parti[0])
            valori = [float(p) for p in parti[1:]]
            assert all(0 <= v <= 1 for v in valori), f"Valori in afara [0,1]: {linie}"
    print("Adnotare valida!")
    """, language="python")
    st.info("**Regula de aur:** adnoteaza minim 50 imagini per clasa pentru rezultate bune. "
            "Cu 200+ imagini per clasa obtii un model de productie.")
