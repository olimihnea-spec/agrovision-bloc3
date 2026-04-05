"""
BLOC 3 — Deep Learning YOLOv8, Ziua 26
Analiza NDVI si Indici Spectrali Avansati — integrare YOLOv8 + spectral
Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu | UCB Targu Jiu | APIA CJ Gorj

CONCEPT CHEIE:
  YOLOv8 detecteaza UNDE sunt clasele (vegetatie/sol/apa) prin bounding box.
  Indicii spectrali masoara CUM ESTE vegetatia — sanatate, vigoare, stres.

  Combinatia ideala pentru APIA:
    YOLOv8  → "64% din parcela este vegetatie" (conformitate PAC)
    NDVI    → "vegetatia are vigoare 0.72" (calitatea culturii)
    NDWI    → "umiditatea solului este scazuta" (risc seceta)

  Indici calculati din RGB (camera normala, nu multispectral):
    ExG  = 2*G - R - B          → vegetatie verde (simplu, rapid)
    VARI = (G-R)/(G+R-B)        → rezistent la conditii atmosferice
    GLI  = (2G-R-B)/(2G+R+B)   → sensibil la clorofila
    NGRDI= (G-R)/(G+R)          → diferenta normalizata verde-rosu
    ExGR = ExG - 1.4*R - G      → discrimineaza sol de vegetatie

  NDVI real necesita camera multispectral (NIR + RED).
  Simulam NDVI din RGB folosind formula aproximativa pentru demo academic.

  Utilitate teza doctorat:
    Acesti indici au aparut in teza "Contribuții privind recunoașterea
    automata a culturilor cu ajutorul unei Drone" — Universitatea Petrosani 2024
"""

import streamlit as st
import numpy as np
from PIL import Image
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd

# ─── CONFIGURARE PAGINA ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Analiza NDVI Spectral — AGROVISION",
    page_icon="🌿",
    layout="wide"
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.indice-card {
    background: white;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 6px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    border-left: 5px solid #2d8c4e;
}
.formula-box {
    background: #f0fff4;
    border: 1px solid #2d8c4e;
    border-radius: 8px;
    padding: 10px 16px;
    font-family: monospace;
    font-size: 14px;
    margin: 6px 0;
}
.metric-verde  { color: #155724; font-weight: 700; }
.metric-galben { color: #856404; font-weight: 700; }
.metric-rosu   { color: #721c24; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ─── FUNCTII CALCUL INDICI ────────────────────────────────────────────────────

def calculeaza_indici(img_arr: np.ndarray) -> dict:
    """Calculeaza toti indicii spectrali din imaginea RGB."""
    img_f = img_arr.astype(np.float32) / 255.0
    R = img_f[:, :, 0]
    G = img_f[:, :, 1]
    B = img_f[:, :, 2]
    eps = 1e-8  # evita impartirea la zero

    ExG   = 2*G - R - B
    VARI  = (G - R) / (G + R - B + eps)
    GLI   = (2*G - R - B) / (2*G + R + B + eps)
    NGRDI = (G - R) / (G + R + eps)
    ExGR  = ExG - 1.4*R - G
    # NDVI simulat din RGB (aproximare pentru demo)
    NDVI_sim = (G - R) / (G + R + eps)

    # Clipam la range rezonabil
    VARI  = np.clip(VARI,  -1, 1)
    GLI   = np.clip(GLI,   -1, 1)
    NGRDI = np.clip(NGRDI, -1, 1)
    NDVI_sim = np.clip(NDVI_sim, -1, 1)

    return {
        "ExG":      ExG,
        "VARI":     VARI,
        "GLI":      GLI,
        "NGRDI":    NGRDI,
        "ExGR":     ExGR,
        "NDVI_sim": NDVI_sim,
    }

def statistici_indice(arr: np.ndarray) -> dict:
    """Calculeaza statistici pentru un indice spectral."""
    return {
        "medie":  float(np.mean(arr)),
        "mediana":float(np.median(arr)),
        "std":    float(np.std(arr)),
        "min":    float(np.min(arr)),
        "max":    float(np.max(arr)),
        "p25":    float(np.percentile(arr, 25)),
        "p75":    float(np.percentile(arr, 75)),
    }

def clasificare_sanatate(ndvi_medie: float) -> tuple:
    """Clasifica sanatatea vegetatiei dupa NDVI simulat."""
    if ndvi_medie > 0.3:
        return "Vegetatie sanatoasa", "#28a745", "Cultura viguroasa, fara semne de stres"
    elif ndvi_medie > 0.1:
        return "Vegetatie moderata", "#ffc107", "Vegetatie prezenta dar cu vigoare redusa"
    elif ndvi_medie > 0:
        return "Vegetatie slaba", "#fd7e14", "Posibil stres hidric sau nutritional"
    else:
        return "Sol gol / Nevegetatie", "#dc3545", "Suprafata fara vegetatie activa"

def harta_colorata(arr: np.ndarray, cmap_name: str = "RdYlGn",
                   titlu: str = "", vmin: float = -1, vmax: float = 1) -> bytes:
    """Genereaza harta colorata pentru un indice spectral."""
    fig, ax = plt.subplots(figsize=(6, 4))
    im = ax.imshow(arr, cmap=cmap_name, vmin=vmin, vmax=vmax)
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title(titlu, fontsize=11, fontweight="bold")
    ax.axis("off")
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()

def histograma_indice(arr: np.ndarray, titlu: str, culoare: str) -> bytes:
    """Genereaza histograma distributiei valorilor indicelui."""
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.hist(arr.flatten(), bins=50, color=culoare, alpha=0.75, edgecolor="white")
    ax.axvline(np.mean(arr), color="red", linestyle="--",
               linewidth=1.5, label=f"Medie: {np.mean(arr):.3f}")
    ax.set_title(titlu, fontsize=10, fontweight="bold")
    ax.set_xlabel("Valoare indice")
    ax.set_ylabel("Frecventa pixeli")
    ax.legend(fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFATA STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style='display:flex; align-items:center; gap:16px; margin-bottom:8px;'>
    <div style='font-size:48px;'>🌿</div>
    <div>
        <h1 style='margin:0; font-size:28px; color:#2d8c4e;'>
            Analiza NDVI si Indici Spectrali
        </h1>
        <p style='margin:0; color:#546e7a;'>
            ExG | VARI | GLI | NGRDI | NDVI simulat | Harti colorate | Statistici ISI
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Analiza Imagine",
    "Toti Indicii",
    "Comparatie Indici",
    "Teorie si Formule"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ANALIZA IMAGINE
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Analiza spectral a imaginii drone")

    col_up, col_cfg = st.columns([2, 1])

    with col_up:
        uploaded = st.file_uploader(
            "Incarca imagine drone (JPG/PNG)",
            type=["jpg", "jpeg", "png"],
            help="Orice imagine color. Rezultate mai bune cu imagini drone reale."
        )

    with col_cfg:
        indice_ales = st.selectbox("Indice de afisat:", [
            "NDVI_sim", "ExG", "VARI", "GLI", "NGRDI", "ExGR"
        ])
        prag_vegetatie = st.slider(
            "Prag detectie vegetatie:", -0.5, 0.5, 0.1, 0.05,
            help="Pixelii cu indice > prag = vegetatie"
        )

    if uploaded:
        img = Image.open(uploaded).convert("RGB")

        # Redimensionam daca e prea mare (performanta)
        MAX_DIM = 800
        w, h = img.size
        if max(w, h) > MAX_DIM:
            scale = MAX_DIM / max(w, h)
            img = img.resize((int(w*scale), int(h*scale)), Image.LANCZOS)

        img_arr = np.array(img)
        indici  = calculeaza_indici(img_arr)
        arr_ales = indici[indice_ales]

        # ── Imagini ────────────────────────────────────────────────────────
        col1, col2, col3 = st.columns(3)

        with col1:
            st.image(img, caption="Imagine originala", use_container_width=True)

        with col2:
            harta = harta_colorata(
                arr_ales, "RdYlGn",
                f"Harta {indice_ales}", -0.5, 0.8
            )
            st.image(harta, caption=f"Harta {indice_ales}", use_container_width=True)

        with col3:
            # Masca vegetatie
            masca = (arr_ales > prag_vegetatie).astype(np.uint8) * 255
            img_masca = Image.fromarray(masca, mode="L")
            # Aplica verde pe vegetatie
            overlay = img_arr.copy()
            overlay[masca > 0] = [34, 139, 34]
            alpha = 0.5
            blend = (img_arr * (1 - alpha) + overlay * alpha).astype(np.uint8)
            st.image(blend,
                     caption=f"Vegetatie detectata (prag>{prag_vegetatie})",
                     use_container_width=True)

        # ── KPI-uri ────────────────────────────────────────────────────────
        st.divider()
        stats = statistici_indice(arr_ales)
        pct_vegetatie = float(np.mean(arr_ales > prag_vegetatie) * 100)
        stare, culoare_stare, descriere_stare = clasificare_sanatate(
            statistici_indice(indici["NDVI_sim"])["medie"]
        )

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric(f"{indice_ales} Medie",    f"{stats['medie']:.3f}")
        c2.metric(f"{indice_ales} Mediana",  f"{stats['mediana']:.3f}")
        c3.metric("Std Dev",                 f"{stats['std']:.3f}")
        c4.metric("Vegetatie (%)",           f"{pct_vegetatie:.1f}%")
        c5.metric("Status PAC",
                  "CONFORM" if pct_vegetatie >= 50 else "NECONFORM")

        st.markdown(f"""
        <div style='background:{culoare_stare}22; border-left:4px solid {culoare_stare};
                    border-radius:8px; padding:12px 16px; margin:8px 0;'>
            <strong style='color:{culoare_stare};'>{stare}</strong>
            — {descriere_stare}
        </div>
        """, unsafe_allow_html=True)

        # ── Histograma ─────────────────────────────────────────────────────
        hist = histograma_indice(arr_ales, f"Distributie {indice_ales}", "#2d8c4e")
        st.image(hist, use_container_width=False, width=500)

        # ── Download harta ─────────────────────────────────────────────────
        st.download_button(
            f"Descarca Harta {indice_ales} (PNG)",
            data=harta,
            file_name=f"harta_{indice_ales}_{uploaded.name}",
            mime="image/png"
        )

    else:
        st.info("Incarca o imagine drone pentru a incepe analiza spectrala.")
        st.markdown("""
        **Imagini potrivite pentru test:**
        - Orice fotografie cu vegetatie verde (camp, gradina, parc)
        - Imagini drone din dosarul tau APIA
        - Imaginea GJ_78258-1675 (parcela Gorj din cursul anterior)
        """)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TOTI INDICII (daca e imaginea incarcata)
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Comparatie vizuala toti indicii spectrali")

    if uploaded:
        img2    = Image.open(uploaded).convert("RGB")
        w2, h2  = img2.size
        if max(w2, h2) > 800:
            sc = 800 / max(w2, h2)
            img2 = img2.resize((int(w2*sc), int(h2*sc)), Image.LANCZOS)
        arr2    = np.array(img2)
        indici2 = calculeaza_indici(arr2)

        cfg_indici = {
            "ExG":      ("#2d8c4e", "RdYlGn", -0.5,  1.0),
            "VARI":     ("#1565c0", "RdYlGn", -1.0,  1.0),
            "GLI":      ("#6a1b9a", "RdYlGn", -0.5,  0.5),
            "NGRDI":    ("#e65100", "RdYlGn", -0.5,  0.5),
            "ExGR":     ("#4e342e", "RdYlGn", -1.0,  1.0),
            "NDVI_sim": ("#1b5e20", "RdYlGn", -1.0,  1.0),
        }

        cols = st.columns(3)
        for idx, (nume, (culoare, cmap, vmin, vmax)) in enumerate(cfg_indici.items()):
            arr_i = indici2[nume]
            stats_i = statistici_indice(arr_i)
            harta_i = harta_colorata(arr_i, cmap, nome := f"{nume}",
                                     vmin, vmax)
            with cols[idx % 3]:
                st.image(harta_i, caption=f"{nome} (medie: {stats_i['medie']:.3f})",
                         use_container_width=True)

        st.divider()
        st.markdown("**Tabel comparativ statistici:**")
        rows = []
        for nume in cfg_indici:
            s = statistici_indice(indici2[nume])
            rows.append({
                "Indice": nume,
                "Medie":  round(s["medie"], 4),
                "Mediana":round(s["mediana"], 4),
                "Std":    round(s["std"], 4),
                "Min":    round(s["min"], 4),
                "Max":    round(s["max"], 4),
                "Veg>0 (%)": round(float(np.mean(indici2[nume] > 0) * 100), 1)
            })
        df_stats = pd.DataFrame(rows)
        st.dataframe(df_stats, use_container_width=True, hide_index=True)

        # Export Excel cu statistici
        buf_xl = io.BytesIO()
        with pd.ExcelWriter(buf_xl, engine="openpyxl") as writer:
            df_stats.to_excel(writer, sheet_name="Indici_Spectrali", index=False)
        buf_xl.seek(0)
        st.download_button(
            "Export Excel Statistici Indici",
            data=buf_xl,
            file_name="statistici_indici_spectrali.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Incarca mai intai o imagine in Tab-ul 'Analiza Imagine'.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — COMPARATIE INDICI (grafic radar/bar)
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Grafic comparativ indici — util pentru articol ISI")

    if uploaded:
        img3    = Image.open(uploaded).convert("RGB")
        w3, h3  = img3.size
        if max(w3, h3) > 800:
            sc3 = 800 / max(w3, h3)
            img3 = img3.resize((int(w3*sc3), int(h3*sc3)), Image.LANCZOS)
        arr3    = np.array(img3)
        indici3 = calculeaza_indici(arr3)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Mediile indicilor spectrali:**")
            medii = {k: float(np.mean(v)) for k, v in indici3.items()}
            fig, ax = plt.subplots(figsize=(6, 4))
            culori_bar = ["#2d8c4e" if v > 0 else "#dc3545"
                          for v in medii.values()]
            bars = ax.bar(list(medii.keys()), list(medii.values()),
                          color=culori_bar, edgecolor="white", width=0.6)
            ax.axhline(0, color="black", linewidth=0.8, linestyle="-")
            ax.set_ylabel("Valoare medie indice")
            ax.set_title("Medii indici spectrali — imagine incarcata",
                         fontsize=10, fontweight="bold")
            for bar, val in zip(bars, medii.values()):
                ax.text(bar.get_x() + bar.get_width()/2,
                        val + (0.01 if val >= 0 else -0.03),
                        f"{val:.3f}", ha="center", fontsize=8, fontweight="bold")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            plt.tight_layout()
            buf_bar = io.BytesIO()
            plt.savefig(buf_bar, format="png", dpi=150, bbox_inches="tight")
            plt.close(fig)
            buf_bar.seek(0)
            st.image(buf_bar.read(), use_container_width=True)

        with col2:
            st.markdown("**Corelatie Pearson intre indici:**")
            # Aplatizam fiecare indice si calculam corelatie
            flat = {k: v.flatten() for k, v in indici3.items()}
            df_flat = pd.DataFrame(flat)
            # Esantionam 5000 pixeli pentru viteza
            if len(df_flat) > 5000:
                df_flat = df_flat.sample(5000, random_state=42)
            corr = df_flat.corr()
            fig2, ax2 = plt.subplots(figsize=(6, 5))
            im2 = ax2.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1)
            plt.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
            ax2.set_xticks(range(len(corr)))
            ax2.set_yticks(range(len(corr)))
            ax2.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=8)
            ax2.set_yticklabels(corr.columns, fontsize=8)
            for i in range(len(corr)):
                for j in range(len(corr)):
                    ax2.text(j, i, f"{corr.values[i,j]:.2f}",
                             ha="center", va="center", fontsize=7,
                             color="white" if abs(corr.values[i,j]) > 0.6 else "black")
            ax2.set_title("Corelatie Pearson indici spectrali",
                          fontsize=10, fontweight="bold")
            plt.tight_layout()
            buf_corr = io.BytesIO()
            plt.savefig(buf_corr, format="png", dpi=150, bbox_inches="tight")
            plt.close(fig2)
            buf_corr.seek(0)
            st.image(buf_corr.read(), use_container_width=True)

        st.info("""
        **Utilizare in articol ISI:**
        Aceste grafice (medii indici + matrice corelatie) constituie
        Figura 2 si Figura 3 dintr-un articol de Remote Sensing.
        Exporta-le la 300 DPI din butonul de mai jos.
        """)

        # Export 300 DPI
        if st.button("Genereaza figuri 300 DPI pentru articol ISI"):
            figuri = {}
            for idx_name, arr_idx in indici3.items():
                fig_hi, ax_hi = plt.subplots(figsize=(6, 4))
                im_hi = ax_hi.imshow(arr_idx, cmap="RdYlGn", vmin=-0.5, vmax=0.8)
                plt.colorbar(im_hi, ax=ax_hi, fraction=0.046, pad=0.04)
                ax_hi.set_title(f"Indice {idx_name} — {uploaded.name}",
                                fontsize=12, fontweight="bold")
                ax_hi.axis("off")
                plt.tight_layout()
                buf_hi = io.BytesIO()
                plt.savefig(buf_hi, format="png", dpi=300, bbox_inches="tight")
                plt.close(fig_hi)
                buf_hi.seek(0)
                figuri[idx_name] = buf_hi.read()

            import zipfile
            buf_zip = io.BytesIO()
            with zipfile.ZipFile(buf_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                for name, data in figuri.items():
                    zf.writestr(f"Fig_{name}_300dpi.png", data)
            buf_zip.seek(0)
            st.download_button(
                "Descarca toate figurile 300 DPI (ZIP)",
                data=buf_zip,
                file_name="figuri_indici_spectral_300dpi.zip",
                mime="application/zip"
            )
    else:
        st.info("Incarca o imagine in Tab-ul 'Analiza Imagine'.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — TEORIE SI FORMULE
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Teorie indici spectrali — referinta academica")

    indici_info = [
        {
            "nume": "ExG — Excess Green Index",
            "formula": "ExG = 2×G − R − B",
            "range": "[-2, 2] tipic [-0.5, 1.0]",
            "culoare": "#2d8c4e",
            "descriere": "Cel mai simplu indice de vegetatie din RGB. Amplifica canalul verde fata de rosu si albastru. Valori pozitive = vegetatie, negative = sol sau cer.",
            "utilizare": "Detectie rapida vegetatie, clasificare binara CONFORM/NECONFORM",
            "referinta": "Meyer & Neto (2008), Biosystems Engineering"
        },
        {
            "nume": "VARI — Visible Atmospherically Resistant Index",
            "formula": "VARI = (G − R) / (G + R − B)",
            "range": "[-1, 1]",
            "culoare": "#1565c0",
            "descriere": "Rezistent la efectele atmosferice (ceata, umiditate). Mai robust decat ExG in conditii de teren variate. Recomandat pentru imagini drone la altitudine.",
            "utilizare": "Analiza vegetatie in conditii atmosferice variabile, drone la 50-120m",
            "referinta": "Gitelson et al. (2002), Journal of Plant Physiology"
        },
        {
            "nume": "GLI — Green Leaf Index",
            "formula": "GLI = (2G − R − B) / (2G + R + B)",
            "range": "[-1, 1] tipic [-0.2, 0.3]",
            "culoare": "#6a1b9a",
            "descriere": "Sensibil la continutul de clorofila. Normalizat in [−1,1]. Corelat cu densitatea frunzisului si sanatatea culturii.",
            "utilizare": "Estimare vigoare cultura, detectie stres nutritional",
            "referinta": "Louhaichi et al. (2001), Geocarto International"
        },
        {
            "nume": "NGRDI — Normalized Green-Red Difference Index",
            "formula": "NGRDI = (G − R) / (G + R)",
            "range": "[-1, 1]",
            "culoare": "#e65100",
            "descriere": "Similar cu NDVI dar calculat din verde si rosu vizibil. Corelat cu LAI (Leaf Area Index). Util cand nu exista banda NIR.",
            "utilizare": "Estimare LAI, densitate vegetatie, pasuni",
            "referinta": "Tucker (1979), Remote Sensing of Environment"
        },
        {
            "nume": "NDVI simulat (din RGB)",
            "formula": "NDVI_sim = (G − R) / (G + R)  [aproximare]",
            "range": "[-1, 1]",
            "culoare": "#1b5e20",
            "descriere": "NDVI real = (NIR − RED) / (NIR + RED) si necesita camera multispectral. Aceasta versiune foloseste GREEN in loc de NIR — rezultat aproximativ, util pentru demo si comparatii relative.",
            "utilizare": "Demo academic, comparatie relativa intre parcele",
            "referinta": "Rouse et al. (1973), NASA — NDVI original"
        },
    ]

    for info in indici_info:
        st.markdown(f"""
        <div class="indice-card" style="border-left-color:{info['culoare']};">
            <strong style="font-size:15px; color:{info['culoare']};">{info['nume']}</strong>
        </div>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"""
            <div class="formula-box">
                <strong>Formula:</strong> {info['formula']}<br>
                <strong>Range:</strong> {info['range']}
            </div>
            """, unsafe_allow_html=True)
            st.caption(f"Referinta: {info['referinta']}")
        with col2:
            st.markdown(f"**Descriere:** {info['descriere']}")
            st.markdown(f"**Utilizare APIA:** {info['utilizare']}")

    st.divider()
    st.markdown("""
    **De ce acesti indici sunt importanti pentru teza ta de doctorat:**

    Teza *"Contribuții privind recunoașterea automată a culturilor cu ajutorul
    unei Drone"* (Universitatea din Petroșani, 2024) foloseste acesti indici
    pentru a demonstra ca imaginile drone pot inlocui partial inspectia fizica
    a parcelelor APIA. Combinatia YOLOv8 (detectie) + indici spectrali (calitate)
    ofera un sistem complet de evaluare a conformitatii PAC.

    **Legatura cu articolul IEEE FINE 2026 (paper_28):**
    Sectiunea Methodology include calculul VARI si ExG ca etapa de
    pre-procesare inainte de inferenta YOLOv8, justificand alegerea
    algoritmului pe baza literaturii de specialitate.
    """)

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center; color:#90a4ae; font-size:12px; padding:8px 0;'>
    AGROVISION &nbsp;|&nbsp; Ziua 26 — Analiza NDVI si Indici Spectrali &nbsp;|&nbsp;
    ExG | VARI | GLI | NGRDI | NDVI_sim | numpy | matplotlib
    &nbsp;|&nbsp; UCB Targu Jiu &nbsp;|&nbsp; APIA CJ Gorj
</div>
""", unsafe_allow_html=True)
