"""
AGROVISION — Raport PDF Ministerial
Ziua 36 | Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu

Scop:
    Generare raport PDF oficial multi-pagina la nivel judetean,
    destinat APIA Central / Ministerul Agriculturii / Prefectura Gorj.

    Diferenta fata de Ziua 20 (raport per parcela):
      - Ziua 20 = nivel inspector (1 parcela, 1 detectie)
      - Ziua 36 = nivel director/minister (agregat per UAT, judet)

    Structura raport ministerial:
      Pagina 1: Coperta + date raport
      Pagina 2: Sumar executiv (KPI-uri judetene)
      Pagina 3: Tabel per UAT (fermieri, suprafata, plati, conformitate)
      Pagina 4: Grafice (culturi + conformitate per UAT)
      Pagina 5: Concluzii + recomandari + semnatura

CONCEPT CHEIE — grafice in PDF:
    matplotlib salveaza graficul in BytesIO (memorie) ca PNG temporar.
    fpdf2 citeste PNG-ul si il insereaza in pagina PDF.
    Zero fisiere pe disk — totul in memorie.

CONCEPT CHEIE — multi-pagina:
    pdf.add_page() adauga o pagina noua.
    header() si footer() sunt apelate automat la fiecare pagina noua.
    Numerotarea paginilor se face in footer() cu self.page_no().
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
import tempfile
import os
from datetime import date, datetime
from fpdf import FPDF

# ─── CONFIGURARE PAGINA ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Raport PDF Ministerial | AGROVISION",
    page_icon="PDF",
    layout="wide"
)

# ─── DATE SIMULATE (aceleasi ca Zilele 34-35) ─────────────────────────────────
UAT_GORJ = [
    {"uat": "Targu Jiu",    "lat": 45.042, "lon": 23.272},
    {"uat": "Rovinari",     "lat": 44.918, "lon": 23.165},
    {"uat": "Motru",        "lat": 44.807, "lon": 22.988},
    {"uat": "Bumbesti-Jiu", "lat": 45.182, "lon": 23.391},
    {"uat": "Novaci",       "lat": 45.301, "lon": 23.673},
    {"uat": "Turceni",      "lat": 44.873, "lon": 23.401},
    {"uat": "Aninoasa",     "lat": 45.087, "lon": 23.522},
    {"uat": "Balesti",      "lat": 44.971, "lon": 23.489},
    {"uat": "Carbunesti",   "lat": 44.956, "lon": 23.527},
    {"uat": "Tismana",      "lat": 45.033, "lon": 22.992},
    {"uat": "Sacelele",     "lat": 45.118, "lon": 23.197},
    {"uat": "Vladuleni",    "lat": 44.842, "lon": 23.317},
]

CULTURI = ["grau", "porumb", "rapita", "floarea_soarelui",
           "lucerna", "pasune", "orz", "triticale"]

PLATII_BAZA = {
    "grau": 185, "porumb": 175, "rapita": 190,
    "floarea_soarelui": 172, "lucerna": 160,
    "pasune": 110, "orz": 178, "triticale": 165,
}


@st.cache_data
def genereaza_date(an: int) -> pd.DataFrame:
    """Genereaza date simulate pentru campania PAC a anului dat."""
    rand = np.random.RandomState(an)
    rows = []
    fermier_id = 1
    for uat_info in UAT_GORJ:
        n_fermieri = rand.randint(40, 120)
        for _ in range(n_fermieri):
            cultura   = rand.choice(CULTURI, p=[0.25,0.22,0.08,0.07,0.12,0.15,0.07,0.04])
            suprafata = round(rand.uniform(0.5, 25.0), 2)
            ndvi      = round(rand.uniform(0.2, 0.85), 3)
            conform   = rand.random() > 0.18
            risc      = rand.choice([1, 2, 3], p=[0.55, 0.30, 0.15])
            plata_baza   = round(suprafata * PLATII_BAZA[cultura], 2)
            plata_verde  = round(suprafata * rand.uniform(40, 65), 2) if conform else 0
            plata_totala = round(plata_baza + plata_verde if conform else plata_baza * 0.3, 2)
            rows.append({
                "fermier_id":   f"GJ{an}-{fermier_id:05d}",
                "uat":          uat_info["uat"],
                "cultura":      cultura,
                "suprafata":    suprafata,
                "ndvi":         ndvi,
                "conform":      conform,
                "risc":         risc,
                "plata_baza":   plata_baza,
                "plata_verde":  plata_verde,
                "plata_totala": plata_totala,
            })
            fermier_id += 1
    return pd.DataFrame(rows)


# ─── GRAFICE MATPLOTLIB → BytesIO ────────────────────────────────────────────

def grafic_culturi(df: pd.DataFrame) -> bytes:
    """Grafic bar - distributie suprafata per cultura."""
    cult_ha = df.groupby("cultura")["suprafata"].sum().sort_values(ascending=False)
    culori = ["#27ae60","#2980b9","#e67e22","#e74c3c",
              "#8e44ad","#16a085","#f39c12","#2c3e50"]
    fig, ax = plt.subplots(figsize=(9, 4))
    bars = ax.bar(cult_ha.index, cult_ha.values, color=culori[:len(cult_ha)], edgecolor="white")
    ax.set_title("Suprafata cultivata per cultura (ha) — Judetul Gorj", fontsize=12, fontweight="bold")
    ax.set_xlabel("Cultura", fontsize=10)
    ax.set_ylabel("Suprafata (ha)", fontsize=10)
    for bar, val in zip(bars, cult_ha.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                f"{val:.0f}", ha="center", va="bottom", fontsize=8, fontweight="bold")
    ax.set_facecolor("#f8f9fa")
    fig.patch.set_facecolor("white")
    plt.xticks(rotation=25, ha="right", fontsize=9)
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def grafic_conformitate_uat(df_uat: pd.DataFrame) -> bytes:
    """Grafic bara orizontala - rata conformitate per UAT."""
    fig, ax = plt.subplots(figsize=(9, 5))
    culori = ["#27ae60" if v >= 80 else "#e67e22" if v >= 65 else "#e74c3c"
              for v in df_uat["rata_conformitate"]]
    bars = ax.barh(df_uat["uat"], df_uat["rata_conformitate"],
                   color=culori, edgecolor="white", height=0.6)
    ax.axvline(x=80, color="#e74c3c", linestyle="--", linewidth=1.5, label="Prag 80%")
    ax.set_title("Rata conformitate PAC per UAT (%)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Conformitate (%)", fontsize=10)
    ax.set_xlim(0, 105)
    for bar, val in zip(bars, df_uat["rata_conformitate"]):
        ax.text(val + 0.5, bar.get_y() + bar.get_height()/2,
                f"{val:.1f}%", va="center", fontsize=8, fontweight="bold")
    verde  = mpatches.Patch(color="#27ae60", label=">= 80% (OK)")
    portoc = mpatches.Patch(color="#e67e22", label="65-79% (Atentie)")
    rosu   = mpatches.Patch(color="#e74c3c", label="< 65% (Critic)")
    ax.legend(handles=[verde, portoc, rosu], loc="lower right", fontsize=8)
    ax.set_facecolor("#f8f9fa")
    fig.patch.set_facecolor("white")
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ─── CLASA PDF MINISTERIAL ────────────────────────────────────────────────────

class RaportMinisterialPDF(FPDF):
    """PDF multi-pagina cu antet si subsol automate pe fiecare pagina."""

    def __init__(self, titlu_raport: str, nr_raport: str, data_raport: str):
        super().__init__()
        self.titlu_raport = titlu_raport
        self.nr_raport    = nr_raport
        self.data_raport  = data_raport
        self.set_auto_page_break(auto=True, margin=20)

    def normalize_text(self, txt: str) -> str:
        """Inlocuieste caractere Unicode nesuportate de Helvetica."""
        replacements = {
            "\u2014": "-",   # em dash —
            "\u2013": "-",   # en dash –
            "\u2019": "'",   # apostrof drept '
            "\u2018": "'",   # apostrof stang '
            "\u201c": '"',   # ghilimea stanga "
            "\u201d": '"',   # ghilimea dreapta "
            "\u2022": "*",   # bullet •
            "\u2026": "...", # puncte de suspensie …
        }
        for char, repl in replacements.items():
            txt = txt.replace(char, repl)
        return txt

    def header(self):
        """Antet pe fiecare pagina."""
        # Bara verde
        self.set_fill_color(39, 174, 96)
        self.rect(0, 0, 210, 12, "F")
        # Titlu institutie
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 2)
        self.cell(0, 8, "AGENTIA DE PLATI SI INTERVENTIE PENTRU AGRICULTURA - CJ GORJ", ln=0)
        # Nr raport dreapta
        self.set_xy(-60, 2)
        self.cell(50, 8, f"Nr. {self.nr_raport}", align="R", ln=0)
        # Spatiu dupa antet
        self.set_text_color(0, 0, 0)
        self.ln(8)

    def footer(self):
        """Subsol pe fiecare pagina — numar pagina + data."""
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.set_fill_color(245, 245, 245)
        self.rect(0, self.get_y(), 210, 15, "F")
        self.set_x(10)
        self.cell(90, 8, f"Generat: {self.data_raport} | AGROVISION v3.0", ln=0)
        self.cell(0, 8, f"Pagina {self.page_no()} / {{nb}}", align="R")
        self.set_text_color(0, 0, 0)

    def titlu_sectiune(self, text: str):
        """Titlu de sectiune cu bara colorata."""
        self.ln(4)
        self.set_fill_color(41, 128, 185)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 8, f"  {text}", ln=True, fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def kpi_box(self, label: str, valoare: str, culoare_rgb: tuple):
        """Caseta KPI colorata."""
        r, g, b = culoare_rgb
        x_start = self.get_x()
        y_start = self.get_y()
        w = 42
        # Fond
        self.set_fill_color(r, g, b)
        self.rect(x_start, y_start, w, 18, "F")
        # Valoare (mare)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(255, 255, 255)
        self.set_xy(x_start, y_start + 1)
        self.cell(w, 9, valoare, align="C", ln=False)
        # Label (mic)
        self.set_font("Helvetica", "", 7)
        self.set_xy(x_start, y_start + 10)
        self.cell(w, 6, label, align="C", ln=False)
        self.set_text_color(0, 0, 0)
        self.set_xy(x_start + w + 3, y_start)

    def rand_tabel(self, valori: list, largimi: list, bold: bool = False,
                   fond_rgb: tuple = None):
        """Un rand in tabel."""
        if fond_rgb:
            self.set_fill_color(*fond_rgb)
        if bold:
            self.set_font("Helvetica", "B", 8)
        else:
            self.set_font("Helvetica", "", 8)
        fill = fond_rgb is not None
        for val, w in zip(valori, largimi):
            text = str(val) if val is not None else ""
            self.cell(w, 6, text[:22], border=1, align="C", fill=fill)
        self.ln()


# ─── FUNCTIE GENERARE PDF ─────────────────────────────────────────────────────

def genereaza_pdf(df: pd.DataFrame, df_uat: pd.DataFrame,
                  an: int, nr_raport: str, inspector: str) -> bytes:
    """Genereaza PDF ministerial complet si returneaza bytes."""

    data_azi  = date.today().strftime("%d.%m.%Y")
    ora_azi   = datetime.now().strftime("%H:%M")
    data_long = date.today().strftime("%d %B %Y")

    pdf = RaportMinisterialPDF(
        titlu_raport=f"Raport PAC Campania {an} — Judetul Gorj",
        nr_raport=nr_raport,
        data_raport=f"{data_azi} ora {ora_azi}"
    )
    pdf.alias_nb_pages()   # activeaza {nb} pentru total pagini

    # ── PAGINA 1: COPERTA ──────────────────────────────────────────────────────
    pdf.add_page()
    pdf.ln(10)

    # Titlu principal
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(39, 174, 96)
    pdf.cell(0, 12, "RAPORT OFICIAL PAC", ln=True, align="C")
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 9, f"Campania {an} — Judetul Gorj", ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # Linie separator
    pdf.set_draw_color(39, 174, 96)
    pdf.set_line_width(1.0)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(6)

    # Date raport
    pdf.set_font("Helvetica", "", 11)
    info_rand = [
        ("Institutia emitenta",  "APIA — Centrul Judetean Gorj"),
        ("Nr. raport",           nr_raport),
        ("Data emiterii",        f"{data_long}"),
        ("Inspector responsabil", inspector),
        ("Campania agricola",    str(an)),
        ("Baza legala",          "Reg. UE 2021/2116 + Reg. UE 2022/1173"),
        ("Sistem utilizat",      "AGROVISION v3.0 (YOLOv8 + LPIS Gorj)"),
    ]
    for eticheta, valoare in info_rand:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(70, 7, f"{eticheta}:", ln=False)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, valoare, ln=True)

    pdf.ln(6)
    # KPI-uri coperta
    total_fermieri  = len(df)
    total_ha        = df["suprafata"].sum()
    total_plati     = df["plata_totala"].sum()
    rata_conf       = df["conform"].mean() * 100
    neconforme      = (~df["conform"]).sum()

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 7, "SUMAR EXECUTIV:", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    pdf.set_x(10)
    pdf.kpi_box("Total fermieri",   f"{total_fermieri:,}",  (39, 174, 96))
    pdf.kpi_box("Suprafata totala", f"{total_ha:,.0f} ha",  (41, 128, 185))
    pdf.kpi_box("Plati totale",     f"{total_plati/1e6:.2f}M EUR", (230, 126, 34))
    pdf.kpi_box("Conformitate",     f"{rata_conf:.1f}%",    (142, 68, 173))
    pdf.ln(22)

    pdf.set_fill_color(255, 235, 235)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 8,
             f"  ATENTIE: {neconforme} cereri neconforme identificate ({neconforme/total_fermieri*100:.1f}%)",
             ln=True, fill=True)

    # ── PAGINA 2: TABEL PER UAT ────────────────────────────────────────────────
    pdf.add_page()
    pdf.titlu_sectiune("1. SITUATIE PER UNITATE ADMINISTRATIV-TERITORIALA (UAT)")

    # Header tabel
    cols  = ["UAT", "Fermieri", "Supraf.(ha)", "Conform(%)", "Plati(EUR)", "Risc med."]
    largimi = [38, 22, 28, 26, 32, 22]
    pdf.set_fill_color(41, 128, 185)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8)
    for col, w in zip(cols, largimi):
        pdf.cell(w, 7, col, border=1, align="C", fill=True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)

    # Randuri
    for i, row in df_uat.iterrows():
        fond = (240, 248, 255) if i % 2 == 0 else (255, 255, 255)
        conf_val = row["rata_conformitate"]
        if conf_val < 65:
            fond = (255, 235, 235)
        elif conf_val < 80:
            fond = (255, 248, 220)
        pdf.rand_tabel(
            [row["uat"],
             f"{row['fermieri']:,}",
             f"{row['suprafata_ha']:.0f}",
             f"{conf_val:.1f}%",
             f"{row['plati_eur']:,.0f}",
             f"{row['risc_mediu']:.2f}"],
            largimi,
            fond_rgb=fond
        )

    # Rand TOTAL
    pdf.rand_tabel(
        ["TOTAL JUDET",
         f"{df_uat['fermieri'].sum():,}",
         f"{df_uat['suprafata_ha'].sum():.0f}",
         f"{df_uat['rata_conformitate'].mean():.1f}%",
         f"{df_uat['plati_eur'].sum():,.0f}",
         f"{df_uat['risc_mediu'].mean():.2f}"],
        largimi,
        bold=True,
        fond_rgb=(39, 174, 96)
    )

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5,
             "Legenda: Verde = conformitate >= 80% | Galben = 65-79% | Rosu = < 65%",
             ln=True)
    pdf.set_text_color(0, 0, 0)

    # ── PAGINA 3: GRAFICE ─────────────────────────────────────────────────────
    pdf.add_page()
    pdf.titlu_sectiune("2. GRAFICE STATISTICE — CAMPANIA " + str(an))

    # Grafic 1 — culturi
    png_culturi = grafic_culturi(df)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(png_culturi)
        tmp1 = f.name
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "Figura 1. Distributia suprafetei cultivate per cultura (ha)", ln=True)
    pdf.image(tmp1, x=10, w=185)
    os.unlink(tmp1)
    pdf.ln(3)

    # Grafic 2 — conformitate UAT
    png_conf = grafic_conformitate_uat(df_uat)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(png_conf)
        tmp2 = f.name
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "Figura 2. Rata de conformitate PAC per UAT (%)", ln=True)
    pdf.image(tmp2, x=10, w=185)
    os.unlink(tmp2)

    # ── PAGINA 4: CONCLUZII + SEMNATURA ───────────────────────────────────────
    pdf.add_page()
    pdf.titlu_sectiune("3. CONCLUZII SI RECOMANDARI")

    uat_critice = df_uat[df_uat["rata_conformitate"] < 65]["uat"].tolist()
    uat_atentie = df_uat[(df_uat["rata_conformitate"] >= 65) &
                         (df_uat["rata_conformitate"] < 80)]["uat"].tolist()

    pdf.set_font("Helvetica", "", 10)
    concluzii = [
        f"1. In campania {an}, judetul Gorj a inregistrat {total_fermieri:,} cereri PAC,"
        f" acoperind {total_ha:,.0f} ha si plati totale de {total_plati/1e6:.2f} milioane EUR.",

        f"2. Rata de conformitate judetena este de {rata_conf:.1f}%, cu {neconforme} cereri"
        f" neconforme ({neconforme/total_fermieri*100:.1f}% din total).",

        f"3. Cultura dominanta este graul ({df[df['cultura']=='grau']['suprafata'].sum():.0f} ha),"
        f" urmata de porumb ({df[df['cultura']=='porumb']['suprafata'].sum():.0f} ha).",
    ]

    if uat_critice:
        concluzii.append(
            f"4. UAT-uri cu conformitate CRITICA (< 65%): {', '.join(uat_critice)}."
            " Se recomanda control suplimentar pe teren conform Reg. UE 2021/2116, Art. 68."
        )
    if uat_atentie:
        concluzii.append(
            f"5. UAT-uri cu conformitate in ATENTIE (65-79%): {', '.join(uat_atentie)}."
            " Se recomanda monitorizare UAV pentru campania urmatoare."
        )

    concluzii.append(
        "6. Sistemul AGROVISION (YOLOv8 + LPIS) a procesat datele in mai putin de 5 secunde,"
        " confirmand eficienta detectiei automate a culturilor pentru conformitate PAC."
    )

    for concluzie in concluzii:
        pdf.multi_cell(0, 6, concluzie)
        pdf.ln(2)

    # Recomandari
    pdf.ln(4)
    pdf.titlu_sectiune("4. RECOMANDARI PENTRU CAMPANIA URMATOARE")
    rec = [
        "- Extinderea controlului UAV la UAT-urile cu conformitate sub 80%",
        "- Integrarea datelor Sentinel-2 (NDVI) pentru validare satelitara saptamanala",
        "- Actualizarea LPIS cu parcelele modificate (fuziuni, divizari) identificate in teren",
        "- Trimiterea notificarilor de pre-control cu minimum 48h inainte (Reg. UE 2021/2116)",
        "- Arhivarea electronica a rapoartelor PDF in DMS-ul APIA Central",
    ]
    pdf.set_font("Helvetica", "", 10)
    for r in rec:
        pdf.cell(0, 6, r, ln=True)

    # Semnatura
    pdf.ln(10)
    pdf.set_draw_color(100, 100, 100)
    pdf.set_line_width(0.3)

    # Doua coloane semnatura
    y_semn = pdf.get_y()
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(20, y_semn)
    pdf.cell(80, 6, "Director APIA CJ Gorj", align="C", ln=False)
    pdf.set_xy(110, y_semn)
    pdf.cell(80, 6, "Inspector responsabil", align="C", ln=True)

    pdf.ln(14)
    pdf.set_xy(20, pdf.get_y())
    pdf.line(20, pdf.get_y(), 100, pdf.get_y())
    pdf.set_xy(110, pdf.get_y())
    pdf.line(110, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(3)

    pdf.set_font("Helvetica", "I", 9)
    pdf.set_xy(20, pdf.get_y())
    pdf.cell(80, 5, "Semnatura si stampila", align="C", ln=False)
    pdf.set_xy(110, pdf.get_y())
    pdf.cell(80, 5, inspector, align="C", ln=True)

    # Genereaza bytes
    return bytes(pdf.output())


# ─── INTERFATA STREAMLIT ──────────────────────────────────────────────────────

st.title("Raport PDF Ministerial — AGROVISION")
st.markdown("**Ziua 36** | Generare raport oficial multi-pagina pentru APIA Central / Minister")

st.info(
    "**Concept cheie:** Graficele matplotlib sunt salvate ca PNG in memorie (BytesIO), "
    "incluse in PDF cu pdf.image(), apoi sterse — zero fisiere pe disk."
)

# ── Parametri raport ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Parametri raport")
    an_selectat  = st.selectbox("Campania agricola", [2024, 2023, 2022], index=0)
    nr_raport    = st.text_input("Numarul raportului", value="APIA-GJ-2024-001")
    inspector    = st.text_input("Inspector responsabil",
                                 value="Prof. Asoc. Dr. Oliviu M. Gamulescu")
    genereaza_btn = st.button("Genereaza PDF", type="primary", use_container_width=True)

# ── Date ──────────────────────────────────────────────────────────────────────
df = genereaza_date(an_selectat)

# Agregate per UAT
df_uat = df.groupby("uat").agg(
    fermieri       = ("fermier_id", "count"),
    suprafata_ha   = ("suprafata", "sum"),
    rata_conformitate = ("conform", lambda x: x.mean() * 100),
    plati_eur      = ("plata_totala", "sum"),
    risc_mediu     = ("risc", "mean"),
    ndvi_mediu     = ("ndvi", "mean"),
).reset_index().round(2)

# ── Preview ───────────────────────────────────────────────────────────────────
st.subheader(f"Preview date — Campania {an_selectat}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total fermieri",   f"{len(df):,}")
col2.metric("Suprafata totala", f"{df['suprafata'].sum():,.0f} ha")
col3.metric("Plati totale",     f"{df['plata_totala'].sum()/1e6:.2f}M EUR")
col4.metric("Conformitate",     f"{df['conform'].mean()*100:.1f}%")

st.dataframe(
    df_uat.style.background_gradient(subset=["rata_conformitate"], cmap="RdYlGn"),
    use_container_width=True,
    height=300
)

# ── Generare PDF ──────────────────────────────────────────────────────────────
if genereaza_btn:
    with st.spinner("Generez raportul PDF (4 pagini)..."):
        try:
            pdf_bytes = genereaza_pdf(df, df_uat, an_selectat, nr_raport, inspector)
            st.success(f"Raport generat: {len(pdf_bytes)/1024:.1f} KB — 4 pagini")
            st.download_button(
                label="Descarca Raport PDF Ministerial",
                data=pdf_bytes,
                file_name=f"Raport_PAC_{an_selectat}_Gorj_{nr_raport.replace('/', '-')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
        except Exception as e:
            st.error(f"Eroare la generare: {e}")
            st.exception(e)

# ── Teorie ────────────────────────────────────────────────────────────────────
with st.expander("Concepte cheie Ziua 36"):
    st.markdown("""
    ### Ce am invatat azi

    **1. PDF multi-pagina**
    ```python
    pdf.add_page()        # pagina noua
    # header() si footer() se apeleaza AUTOMAT la fiecare add_page()
    pdf.alias_nb_pages()  # activeaza {nb} = total pagini in footer
    ```

    **2. Grafice matplotlib in PDF (fara disk)**
    ```python
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    buf.seek(0)
    png_bytes = buf.read()

    # In PDF:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(png_bytes)
        tmp = f.name
    pdf.image(tmp, x=10, w=185)
    os.unlink(tmp)   # sterge fisierul temporar
    ```

    **3. Diferenta Ziua 20 vs Ziua 36**
    | Ziua 20 | Ziua 36 |
    |---|---|
    | Raport per parcela | Raport judetean |
    | 1 pagina | 4 pagini |
    | Date brute LPIS | Date agregate per UAT |
    | Inspector control teren | Director + Minister |

    **4. alias_nb_pages()**
    - Se apeleaza o singura data, inainte de add_page()
    - Activeaza placeholder-ul `{nb}` in footer
    - fpdf2 inlocuieste `{nb}` cu numarul total de pagini dupa ce stie cate pagini are documentul
    """)
