"""
BLOC 3 — Deep Learning YOLOv8, Ziua 20
Rapoarte PDF Oficiale APIA — generare automata cu fpdf2
Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu | UCB Targu Jiu | APIA CJ Gorj

CONCEPT CHEIE:
  Un raport PDF oficial = documentul final pe care inspectorul APIA il semneaza
  si il depune la dosar. Pana acum exportam date brute (Excel, GeoJSON).
  Acum generam un document structurat, gata de tiparit sau transmis electronic.

  De ce fpdf2 si nu python-docx:
    - PDF = format fix, nu se poate modifica accidental
    - Compatibil cu orice sistem (nu necesita Microsoft Office)
    - Ideal pentru arhivare APIA (LPIS, DRN, dosare control)
    - fpdf2 = biblioteca Python pura, fara dependente externe grele

  Structura raportului oficial:
    1. Antet institutional (APIA, inspector, data, nr. raport)
    2. Rezumat executiv (KPI: conforme/neconforme/suprafata)
    3. Tabel parcele cu rezultatele detectiei
    4. Grafic distributie clase (salvat ca PNG, inclus in PDF)
    5. Concluzii si recomandari (conform Reg. UE 2021/2116)
    6. Sectiune semnatura inspector

  Utilitate reala APIA:
    - Inspector genereaza raportul dupa control teren cu drona
    - Il trimite la APIA Central impreuna cu imaginile georeferentiate
    - Dovada pentru OLAF/Curtea de Conturi ca s-a efectuat controlul
"""

import streamlit as st
import datetime
import io
import random
import os
import tempfile

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from fpdf import FPDF
import pandas as pd

# ─── CONFIGURARE PAGINA ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Rapoarte PDF APIA",
    page_icon="📄",
    layout="wide"
)

# ─── DATE LPIS GORJ (aceleasi 10 parcele din zilele anterioare) ───────────────
PARCELE_LPIS = [
    {"cod": "GJ_78258-1675", "fermier": "Popescu Ion",      "suprafata": 4.32, "cultura": "grau",    "judet": "Gorj", "uat": "Targu Jiu",   "lat": 45.0421, "lon": 23.2718},
    {"cod": "GJ_78301-0892", "fermier": "Ionescu Maria",    "suprafata": 6.78, "cultura": "porumb",  "judet": "Gorj", "uat": "Rovinari",    "lat": 44.9183, "lon": 23.1645},
    {"cod": "GJ_78445-2341", "fermier": "Dumitrescu Gh.",   "suprafata": 3.15, "cultura": "rapita",  "judet": "Gorj", "uat": "Motru",       "lat": 44.8067, "lon": 22.9876},
    {"cod": "GJ_78512-0077", "fermier": "Stanescu Petre",   "suprafata": 8.90, "cultura": "grau",    "judet": "Gorj", "uat": "Bumbesti-Jiu","lat": 45.1823, "lon": 23.3912},
    {"cod": "GJ_78634-1129", "fermier": "Olteanu Vasile",   "suprafata": 2.44, "cultura": "porumb",  "judet": "Gorj", "uat": "Novaci",      "lat": 45.3012, "lon": 23.6734},
    {"cod": "GJ_78720-3388", "fermier": "Marinescu Ana",    "suprafata": 5.67, "cultura": "floarea", "judet": "Gorj", "uat": "Targu Jiu",   "lat": 45.0198, "lon": 23.2456},
    {"cod": "GJ_79001-0445", "fermier": "Petrescu Dan",     "suprafata": 7.23, "cultura": "grau",    "judet": "Gorj", "uat": "Turceni",     "lat": 44.8734, "lon": 23.4012},
    {"cod": "GJ_79234-1876", "fermier": "Constantin Gh.",   "suprafata": 1.98, "cultura": "pasune",  "judet": "Gorj", "uat": "Aninoasa",    "lat": 45.0867, "lon": 23.5219},
    {"cod": "GJ_79567-2290", "fermier": "Florescu Elena",   "suprafata": 9.45, "cultura": "porumb",  "judet": "Gorj", "uat": "Rovinari",    "lat": 44.9045, "lon": 23.1823},
    {"cod": "GJ_80980-2611", "fermier": "Draghici Marin",   "suprafata": 6.64, "cultura": "grau",    "judet": "Gorj", "uat": "Targu Jiu",   "lat": 45.0534, "lon": 23.2901},
]

def genereaza_date_detectie(seed: int = 42) -> list:
    """Genereaza rezultate detectie simulate pentru cele 10 parcele."""
    rng = random.Random(seed)
    rezultate = []
    for p in PARCELE_LPIS:
        veg  = round(rng.uniform(25, 85), 1)
        sol  = round(rng.uniform(5, 40), 1)
        apa  = round(max(0, 100 - veg - sol), 1)
        conf = round(rng.uniform(0.72, 0.97), 2)
        conform = "CONFORM" if veg >= 50 else "NECONFORM"
        rezultate.append({
            **p,
            "vegetatie_pct": veg,
            "sol_gol_pct": sol,
            "apa_pct": apa,
            "confidenta": conf,
            "status": conform,
            "alerta": veg < 50
        })
    return rezultate

# ─── CLASA PDF PERSONALIZATA ──────────────────────────────────────────────────
class RaportAPIA(FPDF):
    """PDF cu antet si subsol institutional APIA."""

    # Caractere Unicode care nu sunt suportate de Helvetica (Latin-1 only)
    # Suprascriem normalize_text pentru a le inlocui automat in TOT textul PDF
    _UNICODE_MAP = {
        "\u2014": "-",   # em dash —
        "\u2013": "-",   # en dash –
        "\u201c": '"',   # " ghilimele stanga
        "\u201d": '"',   # " ghilimele dreapta
        "\u2018": "'",   # ' apostrof stanga
        "\u2019": "'",   # ' apostrof dreapta
        "\u2026": "...", # … puncte de suspensie
        "\u00b0": " gr", # ° grade
        "\u00d7": "x",   # × inmultire
    }

    def normalize_text(self, text: str) -> str:
        """Inlocuieste caracterele nesupportate de Helvetica inainte de randare."""
        for char, repl in self._UNICODE_MAP.items():
            text = text.replace(char, repl)
        return super().normalize_text(text)

    def __init__(self, inspector: str, nr_raport: str, data_control: str):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.inspector   = inspector
        self.nr_raport   = nr_raport
        self.data_control = data_control
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(20, 25, 20)

    def header(self):
        # Linie sus
        self.set_draw_color(0, 82, 165)
        self.set_line_width(1.0)
        self.line(20, 12, 190, 12)

        # Titlu stanga
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(0, 82, 165)
        self.set_xy(20, 14)
        self.cell(90, 5, "AGENTIA DE PLATI SI INTERVENTIE PENTRU AGRICULTURA", ln=0)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(80, 80, 80)
        self.set_xy(20, 19)
        self.cell(90, 4, "Centrul Judetean Gorj | Serviciul Control pe Teren", ln=0)

        # Nr. raport dreapta
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(0, 82, 165)
        self.set_xy(130, 14)
        self.cell(60, 5, f"Raport nr. {self.nr_raport}", align="R", ln=0)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(80, 80, 80)
        self.set_xy(130, 19)
        self.cell(60, 4, f"Data: {self.data_control}", align="R", ln=0)

        # Linie separare
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.3)
        self.line(20, 24, 190, 24)
        self.set_xy(20, 27)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.3)
        self.line(20, self.get_y(), 190, self.get_y())
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(90, 8,
            "AGROVISION v1.0 | YOLOv8 | UCB Targu Jiu | APIA CJ Gorj",
            align="L")
        self.cell(80, 8,
            f"Inspector: {self.inspector} | Pagina {self.page_no()}/{{nb}}",
            align="R")

    def titlu_sectiune(self, text: str):
        self.ln(4)
        self.set_fill_color(0, 82, 165)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 7, f"  {text}", fill=True, ln=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def subtitlu(self, text: str):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(50, 50, 50)
        self.cell(0, 6, text, ln=True)
        self.set_text_color(0, 0, 0)

    def paragraf(self, text: str):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(60, 60, 60)
        self.set_x(self.l_margin)  # siguranta: reset la marginea stanga
        self.multi_cell(self.epw, 5, text)
        self.ln(1)

    def kpi_box(self, eticheta: str, valoare: str, culoare_r: int, culoare_g: int, culoare_b: int):
        """Caseta KPI colorata."""
        x = self.get_x()
        y = self.get_y()
        self.set_fill_color(culoare_r, culoare_g, culoare_b)
        self.set_draw_color(culoare_r, culoare_g, culoare_b)
        self.rect(x, y, 38, 18, "F")
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(255, 255, 255)
        self.set_xy(x, y + 2)
        self.cell(38, 8, valoare, align="C", ln=False)
        self.set_font("Helvetica", "", 7)
        self.set_xy(x, y + 10)
        self.cell(38, 5, eticheta, align="C", ln=False)
        self.set_text_color(0, 0, 0)
        self.set_xy(x + 40, y)


def genereaza_grafic_distributie(date: list) -> bytes:
    """Genereaza grafic distributie clase si returneaza ca bytes PNG."""
    medii = {
        "Vegetatie": np.mean([d["vegetatie_pct"] for d in date]),
        "Sol gol":   np.mean([d["sol_gol_pct"]   for d in date]),
        "Apa":       np.mean([d["apa_pct"]        for d in date]),
    }
    culori = ["#2d8c4e", "#c8a96e", "#4a90d9"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    fig.patch.set_facecolor("white")

    # Pie chart
    wedges, texts, autotexts = ax1.pie(
        list(medii.values()),
        labels=list(medii.keys()),
        colors=culori,
        autopct="%1.1f%%",
        startangle=90,
        pctdistance=0.75
    )
    for at in autotexts:
        at.set_fontsize(9)
        at.set_color("white")
        at.set_fontweight("bold")
    ax1.set_title("Distributie medie clase (%)", fontsize=11, fontweight="bold", pad=10)

    # Bar chart conform/neconform
    conforme    = sum(1 for d in date if d["status"] == "CONFORM")
    neconforme  = len(date) - conforme
    ax2.bar(["Conforme", "Neconforme"], [conforme, neconforme],
            color=["#28a745", "#dc3545"], width=0.5, edgecolor="white")
    ax2.set_title("Status conformitate PAC", fontsize=11, fontweight="bold", pad=10)
    ax2.set_ylabel("Numar parcele")
    for i, v in enumerate([conforme, neconforme]):
        ax2.text(i, v + 0.1, str(v), ha="center", fontweight="bold", fontsize=12)
    ax2.set_ylim(0, max(conforme, neconforme) + 2)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def construieste_pdf(
    date: list,
    inspector: str,
    institutie: str,
    nr_raport: str,
    data_control: str,
    observatii: str,
    include_grafic: bool
) -> bytes:
    """Construieste raportul PDF complet si returneaza bytes."""

    pdf = RaportAPIA(inspector, nr_raport, data_control)
    pdf.alias_nb_pages()
    pdf.add_page()

    # ── TITLU RAPORT ──────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 82, 165)
    pdf.cell(0, 10,
        "RAPORT DE CONTROL TEREN CU DRONA — DETECTIE YOLOv8",
        align="C", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6,
        "Monitorizare vegetatie | Analiza conformitate PAC 2023-2027",
        align="C", ln=True)
    pdf.ln(3)

    # ── SECTIUNEA 1: DATE GENERALE ────────────────────────────────────────────
    pdf.titlu_sectiune("1. DATE GENERALE")

    date_generale = [
        ("Inspector:", inspector),
        ("Institutie:", institutie),
        ("Judet:", "Gorj"),
        ("Data controlului:", data_control),
        ("Nr. raport:", nr_raport),
        ("Model AI folosit:", "YOLOv8n — best_v1_mAP083_20260403.pt"),
        ("mAP50 model:", "0.829 (82.9%)"),
        ("Clase detectate:", "vegetatie / sol_gol / apa"),
        ("Baza legala:", "Reg. UE 2021/2116 | Reg. UE 2022/1173"),
    ]
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)
    for eticheta, valoare in date_generale:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(55, 5, eticheta, ln=False)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, valoare, ln=True)
    pdf.ln(2)

    # ── SECTIUNEA 2: REZUMAT EXECUTIV (KPI) ───────────────────────────────────
    pdf.titlu_sectiune("2. REZUMAT EXECUTIV")

    total     = len(date)
    conforme  = sum(1 for d in date if d["status"] == "CONFORM")
    nec       = total - conforme
    suprafata = sum(d["suprafata"] for d in date)
    alerte    = sum(1 for d in date if d["alerta"])
    med_veg   = np.mean([d["vegetatie_pct"] for d in date])

    pdf.set_xy(20, pdf.get_y())
    pdf.kpi_box("Total parcele",     str(total),          0, 82, 165)
    pdf.set_x(pdf.get_x() + 2)
    pdf.kpi_box("Conforme",          str(conforme),       40, 167, 69)
    pdf.set_x(pdf.get_x() + 2)
    pdf.kpi_box("Neconforme",        str(nec),            220, 53, 69)
    pdf.set_x(pdf.get_x() + 2)
    pdf.kpi_box("Alerte active",     str(alerte),         255, 140, 0)
    pdf.set_x(pdf.get_x() + 2)
    pdf.kpi_box(f"Supraf. (ha)",     f"{suprafata:.1f}",  80, 80, 80)
    # Dupa 5 kpi_box, cursorul X depaseste 210mm (latimea A4)
    # Resetam explicit la marginea stanga inainte de orice text
    pdf.set_xy(20, pdf.get_y() + 22)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(pdf.epw, 5,
        f"Vegetatie medie sesiune: {med_veg:.1f}% | "
        f"Prag conformitate PAC: 50% | "
        f"Rata conformitate: {conforme/total*100:.1f}% ({conforme}/{total} parcele)"
    )
    pdf.ln(2)

    # ── SECTIUNEA 3: GRAFICE ──────────────────────────────────────────────────
    if include_grafic:
        pdf.titlu_sectiune("3. GRAFICE ANALIZA")
        grafic_bytes = genereaza_grafic_distributie(date)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(grafic_bytes)
            tmp_path = tmp.name
        try:
            pdf.image(tmp_path, x=25, w=160)
        finally:
            os.unlink(tmp_path)
        pdf.ln(4)
    else:
        pdf.titlu_sectiune("3. GRAFICE ANALIZA")
        pdf.paragraf("Graficele nu au fost incluse in acest raport.")

    # ── SECTIUNEA 4: TABEL PARCELE ────────────────────────────────────────────
    pdf.titlu_sectiune("4. TABEL PARCELE CONTROLATE")

    # Header tabel
    COL = [38, 28, 16, 20, 20, 16, 16, 26]
    HEADERS = ["Cod LPIS", "Fermier", "Sup.(ha)", "Veg.(%)", "Sol(%)", "Apa(%)", "Conf.", "Status"]
    pdf.set_fill_color(0, 82, 165)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_line_width(0.2)
    for w, h in zip(COL, HEADERS):
        pdf.cell(w, 6, h, border=1, align="C", fill=True, ln=False)
    pdf.ln()

    # Randuri tabel
    pdf.set_font("Helvetica", "", 7)
    for i, d in enumerate(date):
        fill_color = (255, 255, 255) if i % 2 == 0 else (245, 245, 245)
        pdf.set_fill_color(*fill_color)

        if d["status"] == "NECONFORM":
            pdf.set_text_color(180, 0, 0)
        else:
            pdf.set_text_color(0, 100, 0)

        status_txt = "CONFORM" if d["status"] == "CONFORM" else "NECONFORM"

        pdf.set_text_color(40, 40, 40)
        vals = [
            d["cod"],
            d["fermier"][:16],
            f"{d['suprafata']:.2f}",
            f"{d['vegetatie_pct']:.1f}",
            f"{d['sol_gol_pct']:.1f}",
            f"{d['apa_pct']:.1f}",
            f"{d['confidenta']:.2f}",
        ]
        for w, v in zip(COL[:-1], vals):
            pdf.cell(w, 5, v, border=1, align="C", fill=True, ln=False)

        # Status colorat
        if d["status"] == "CONFORM":
            pdf.set_fill_color(212, 237, 218)
            pdf.set_text_color(21, 128, 61)
        else:
            pdf.set_fill_color(248, 215, 218)
            pdf.set_text_color(180, 0, 0)
        pdf.cell(COL[-1], 5, status_txt, border=1, align="C", fill=True, ln=True)
        pdf.set_text_color(40, 40, 40)
        pdf.set_fill_color(255, 255, 255)

    pdf.ln(4)

    # ── SECTIUNEA 5: CONCLUZII SI RECOMANDARI ─────────────────────────────────
    pdf.titlu_sectiune("5. CONCLUZII SI RECOMANDARI")

    concluzii = (
        f"In urma controlului cu aeronava fara pilot (drona) efectuat in data de "
        f"{data_control}, au fost analizate {total} parcele agricole din judetul Gorj, "
        f"cu o suprafata totala de {suprafata:.2f} ha.\n\n"
        f"Din totalul parcelelor analizate, {conforme} ({conforme/total*100:.1f}%) "
        f"respecta conditia minima de vegetatie (>= 50%) impusa de Regulamentul UE "
        f"2021/2116, art. 14, privind ecoconditionalitatile PAC 2023-2027.\n\n"
        f"Un numar de {nec} parcele ({nec/total*100:.1f}%) au inregistrat un procent "
        f"de vegetatie sub pragul de 50%, ceea ce constituie o potentiala neconformitate "
        f"si necesita verificare suplimentara la fata locului."
    )
    pdf.paragraf(concluzii)

    if nec > 0:
        pdf.subtitlu("Recomandari:")
        rec_items = [
            f"1. Verificare fizica a celor {nec} parcele neconforme in termen de 10 zile lucratoare.",
            "2. Notificarea fermierilor in cauza conform procedurilor APIA in vigoare.",
            "3. Actualizarea sistemului IACS cu rezultatele controlului.",
            "4. Arhivarea imaginilor drone si a prezentului raport in dosarul de control.",
        ]
        for rec in rec_items:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(pdf.epw, 5, rec)
        pdf.ln(1)

    if observatii.strip():
        pdf.subtitlu("Observatii inspector:")
        pdf.paragraf(observatii)

    # ── SECTIUNEA 6: SEMNATURA ────────────────────────────────────────────────
    pdf.titlu_sectiune("6. SEMNATURA SI VALIDARE")
    pdf.ln(6)

    # Doua coloane semnatura
    y_sem = pdf.get_y()
    pdf.set_font("Helvetica", "", 9)

    # Stanga: inspector
    pdf.set_xy(20, y_sem)
    pdf.cell(80, 5, "Inspector control teren:", ln=False)
    pdf.set_xy(110, y_sem)
    pdf.cell(80, 5, "Sef serviciu control:", ln=True)

    pdf.set_xy(20, y_sem + 6)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(80, 5, inspector, ln=False)
    pdf.set_xy(110, y_sem + 6)
    pdf.cell(80, 5, "_______________________", ln=True)

    pdf.set_xy(20, y_sem + 12)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(80, 5, institutie, ln=False)
    pdf.set_xy(110, y_sem + 12)
    pdf.cell(80, 5, "APIA CJ Gorj", ln=True)

    pdf.set_xy(20, y_sem + 24)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5,
        "Semnatura electronica / stampila: ___________________________",
        ln=True)
    pdf.ln(4)
    pdf.set_text_color(0, 0, 0)

    # ── NOTA DE SUBSOL ────────────────────────────────────────────────────────
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.3)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(pdf.epw, 4,
        "Prezentul raport a fost generat automat de sistemul AGROVISION "
        "folosind modelul de inteligenta artificiala YOLOv8n (mAP50=0.829). "
        "Rezultatele constituie suport decizional si nu inlocuiesc verificarea "
        "fizica pe teren conform procedurilor APIA. "
        "Baza legala: Reg. UE 2021/2116, Reg. UE 2022/1173, Reg. UE 2022/2472."
    )

    # Returnam bytes PDF
    return bytes(pdf.output())


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFATA STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════════

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.preview-box {
    background: #f8f9fa;
    border: 2px dashed #dee2e6;
    border-radius: 10px;
    padding: 20px;
    margin: 10px 0;
}
.kpi-pdf {
    background: white;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border-top: 4px solid #0052A5;
}
</style>
""", unsafe_allow_html=True)

# ─── TITLU ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='display:flex; align-items:center; gap:16px; margin-bottom:8px;'>
    <div style='font-size:48px;'>📄</div>
    <div>
        <h1 style='margin:0; font-size:28px; color:#0052A5;'>
            Rapoarte PDF Oficiale APIA
        </h1>
        <p style='margin:0; color:#546e7a;'>
            Generare automata raport control teren cu drona | YOLOv8 | fpdf2
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander("Concept cheie — de ce PDF in loc de Excel?", expanded=False):
    st.markdown("""
    **PDF vs Excel pentru rapoarte oficiale:**

    | Criteriu | Excel | PDF |
    |----------|-------|-----|
    | Modificabil dupa generare | Da (risc!) | Nu (sigur) |
    | Necesar Microsoft Office | Da | Nu |
    | Compatibil APIA/OLAF | Partial | Complet |
    | Semnatura electronica | Greu | Standard |
    | Arhivare juridica | Nu | Da |

    **In APIA:** rapoartele de control se depun in format PDF semnat.
    Excel-ul ramane pentru analiza interna; PDF-ul merge la dosar.

    **fpdf2** = biblioteca Python care genereaza PDF din cod, fara programe externe.
    Lucreaza cu coordonate mm pe pagina A4, exact ca o imprimanta.
    """)

st.divider()

# ─── CONFIGURARE RAPORT ───────────────────────────────────────────────────────
st.subheader("Configurare Raport")

col1, col2 = st.columns(2)

with col1:
    inspector_input = st.text_input(
        "Numele inspectorului",
        value="Prof. Asoc. Dr. Oliviu Mihnea Gamulescu",
        help="Va aparea in antet si la semnatura"
    )
    institutie_input = st.text_input(
        "Institutia",
        value="APIA CJ Gorj | UCB Targu Jiu"
    )
    nr_raport_input = st.text_input(
        "Numarul raportului",
        value=f"CTRL-GJ-{datetime.date.today().strftime('%Y%m%d')}-001"
    )

with col2:
    data_control_input = st.date_input(
        "Data controlului",
        value=datetime.date.today()
    )
    seed_input = st.number_input(
        "Seed date detectie (reproductibilitate)",
        min_value=1, max_value=9999, value=42,
        help="Acelasi seed = aceleasi date simulate. Schimba pentru date diferite."
    )
    include_grafic = st.checkbox("Include grafice in PDF", value=True)

observatii_input = st.text_area(
    "Observatii inspector (optional)",
    placeholder="Ex: Parcelele GJ_78258-1675 si GJ_78301-0892 prezinta semne de seceta...",
    height=80
)

st.divider()

# ─── PREVIZUALIZARE DATE ──────────────────────────────────────────────────────
st.subheader("Previzualizare Date Detectie")

date_detectie = genereaza_date_detectie(seed=int(seed_input))
df_preview = pd.DataFrame(date_detectie)[[
    "cod", "fermier", "suprafata", "vegetatie_pct",
    "sol_gol_pct", "apa_pct", "confidenta", "status"
]]
df_preview.columns = [
    "Cod LPIS", "Fermier", "Suprafata (ha)", "Vegetatie (%)",
    "Sol gol (%)", "Apa (%)", "Confidenta", "Status"
]

def coloreaza_status(val):
    if val == "NECONFORM":
        return "background-color: #f8d7da; color: #721c24; font-weight: bold"
    elif val == "CONFORM":
        return "background-color: #d4edda; color: #155724; font-weight: bold"
    return ""

st.dataframe(
    df_preview.style.applymap(coloreaza_status, subset=["Status"]),
    use_container_width=True,
    hide_index=True
)

# KPI-uri sumar
total     = len(date_detectie)
conforme  = sum(1 for d in date_detectie if d["status"] == "CONFORM")
nec       = total - conforme
supraf    = sum(d["suprafata"] for d in date_detectie)
med_veg   = np.mean([d["vegetatie_pct"] for d in date_detectie])

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total parcele", total)
c2.metric("Conforme", conforme, f"{conforme/total*100:.0f}%")
c3.metric("Neconforme", nec, f"-{nec/total*100:.0f}%", delta_color="inverse")
c4.metric("Suprafata (ha)", f"{supraf:.1f}")
c5.metric("Veg. medie (%)", f"{med_veg:.1f}")

st.divider()

# ─── PREVIZUALIZARE GRAFICE ───────────────────────────────────────────────────
if include_grafic:
    with st.expander("Previzualizare grafice (vor fi incluse in PDF)", expanded=True):
        grafic_bytes = genereaza_grafic_distributie(date_detectie)
        st.image(grafic_bytes, use_container_width=True)

# ─── GENERARE PDF ────────────────────────────────────────────────────────────
st.subheader("Generare Raport PDF")

col_gen1, col_gen2 = st.columns([2, 1])
with col_gen1:
    st.info("""
    Raportul va contine:
    - Antet institutional APIA CJ Gorj
    - Rezumat executiv cu 5 KPI-uri colorate
    - Grafice distributie clase + conformitate (optional)
    - Tabel complet cele 10 parcele LPIS Gorj
    - Concluzii si recomandari automate
    - Sectiune semnatura inspector
    - Nota legala (Reg. UE 2021/2116)
    """)
with col_gen2:
    st.markdown(f"""
    <div style='background:#f0f4ff; border-radius:10px; padding:16px; text-align:center;'>
        <div style='font-size:36px;'>📋</div>
        <div style='font-size:14px; font-weight:700; color:#0052A5;'>
            Raport gata de generat
        </div>
        <div style='font-size:12px; color:#546e7a; margin-top:4px;'>
            {total} parcele | {supraf:.1f} ha | {conforme}/{total} conforme
        </div>
    </div>
    """, unsafe_allow_html=True)

if st.button("Genereaza Raport PDF", type="primary", use_container_width=True):
    with st.spinner("Se genereaza raportul PDF..."):
        try:
            pdf_bytes = construieste_pdf(
                date=date_detectie,
                inspector=inspector_input,
                institutie=institutie_input,
                nr_raport=nr_raport_input,
                data_control=str(data_control_input),
                observatii=observatii_input,
                include_grafic=include_grafic
            )
            st.success(f"Raport generat cu succes! ({len(pdf_bytes) // 1024} KB)")

            nume_fisier = f"Raport_APIA_{nr_raport_input}_{data_control_input}.pdf"
            st.download_button(
                label="Descarca Raport PDF",
                data=pdf_bytes,
                file_name=nume_fisier,
                mime="application/pdf",
                use_container_width=True
            )

            # Informatii tehnice
            with st.expander("Detalii tehnice raport generat"):
                st.markdown(f"""
                - **Fisier:** `{nume_fisier}`
                - **Dimensiune:** {len(pdf_bytes):,} bytes ({len(pdf_bytes)//1024} KB)
                - **Parcele:** {total}
                - **Grafice incluse:** {'Da' if include_grafic else 'Nu'}
                - **Biblioteca:** fpdf2
                - **Encoding:** UTF-8 (caractere latine)
                - **Format:** A4 Portrait, margini 20mm
                """)
        except Exception as e:
            st.error(f"Eroare la generarea PDF: {e}")
            st.exception(e)

# ─── SECTIUNEA EDUCATIONALA ───────────────────────────────────────────────────
st.divider()
st.subheader("Cum functioneaza fpdf2?")

with st.expander("Structura codului PDF explicata"):
    st.code("""
# 1. Creeaza un obiect PDF
from fpdf import FPDF
pdf = FPDF(orientation="P", unit="mm", format="A4")
pdf.add_page()

# 2. Seteaza fontul
pdf.set_font("Helvetica", "B", 12)   # font, stil (B/I/BI), marime

# 3. Scrie text
pdf.cell(width, height, "Text",
    border=1,    # 0=fara, 1=toate, L/R/T/B=partial
    align="C",   # L/C/R
    fill=True,   # umple cu culoarea de fundal
    ln=True      # salt la rand nou dupa
)

# 4. Text multiline (wrap automat)
pdf.multi_cell(0, 5, "Text lung care se rupe automat pe mai multe randuri...")

# 5. Pozitionare exacta (coordonate mm de la colt stanga-sus)
pdf.set_xy(x=20, y=50)   # muta cursorul la pozitia exacta

# 6. Culori
pdf.set_fill_color(0, 82, 165)    # RGB fundal
pdf.set_text_color(255, 255, 255) # RGB text
pdf.set_draw_color(200, 200, 200) # RGB bordura

# 7. Imagine (PNG/JPG)
pdf.image("grafic.png", x=25, w=160)  # x, latime (inaltimea = proportionala)

# 8. Exporta
pdf_bytes = bytes(pdf.output())   # in memorie (pentru Streamlit download)
pdf.output("fisier.pdf")          # salvare pe disc
""", language="python")

    st.markdown("""
    **Concepte importante:**
    - Pagina A4 = 210mm x 297mm. Origine (0,0) = colt stanga-sus.
    - `cell()` = dreptunghi cu text, cursorul avanseaza automat la dreapta.
    - `multi_cell()` = text cu wrap, cursorul coboara la rand nou dupa fiecare rand.
    - `header()` si `footer()` = metode suprascrise, apelate automat pe fiecare pagina.
    - `alias_nb_pages()` + `{nb}` in footer = numar total pagini (calculat la final).
    """)

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center; color:#90a4ae; font-size:12px; padding:8px 0;'>
    AGROVISION &nbsp;|&nbsp; Ziua 20 — Rapoarte PDF Oficiale &nbsp;|&nbsp;
    fpdf2 &nbsp;|&nbsp; Bloc 3 YOLOv8 &nbsp;|&nbsp; UCB Targu Jiu &nbsp;|&nbsp; APIA CJ Gorj
</div>
""", unsafe_allow_html=True)
