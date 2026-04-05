"""
BLOC 3 — Deep Learning YOLOv8, Ziua 22
Baza de date SQLite — istoricul complet al detectiilor
Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu | UCB Targu Jiu | APIA CJ Gorj

CONCEPT CHEIE:
  Pana la Ziua 21, fiecare detectie exista doar cat timp aplicatia e deschisa.
  La inchidere → date pierdute. Inspector APIA are nevoie de ISTORIC:
    - Ce parcele a controlat luna trecuta?
    - Care parcele au fost neconforme in ultimele 3 luni?
    - Cate controale a efectuat in 2026?

  SQLite = baza de date relationala salvata intr-un singur fisier .db pe disk.
  Nu necesita server, nu necesita instalare separata — vine cu Python.

  Structura baza de date AGROVISION:
    Tabela SESIUNI: o sesiune = un control (o zi de teren cu drona)
    Tabela DETECTII: o detectie = o parcela analizata intr-o sesiune

  De ce SQLite si nu Excel/JSON:
    - Interogari rapide cu SQL (WHERE, GROUP BY, ORDER BY)
    - Nu se corupe la scrieri multiple simultane
    - pd.read_sql() = DataFrame direct din baza de date
    - Standard industrial pentru aplicatii locale
    - Compatibil cu PostgreSQL cand vrei sa scalezi la server

  Baza legala APIA:
    - Reg. UE 2021/2116 art. 68: pastrarea evidentelor de control minim 3 ani
    - Auditabilitate OLAF: orice detectie trebuie sa poata fi reconstituita
"""

import streamlit as st
import sqlite3
import pandas as pd
import datetime
import random
import io
import os

# ─── CONFIGURARE PAGINA ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Baza Date SQLite — AGROVISION",
    page_icon="🗄️",
    layout="wide"
)

# ─── CALEA BAZEI DE DATE ──────────────────────────────────────────────────────
# Salvata langa aplicatie — nu in pages/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "agrovision_detectii.db")

# ─── PARCELE LPIS GORJ ────────────────────────────────────────────────────────
PARCELE_LPIS = [
    {"cod": "GJ_78258-1675", "fermier": "Popescu Ion",      "suprafata": 4.32, "uat": "Targu Jiu"},
    {"cod": "GJ_78301-0892", "fermier": "Ionescu Maria",    "suprafata": 6.78, "uat": "Rovinari"},
    {"cod": "GJ_78445-2341", "fermier": "Dumitrescu Gh.",   "suprafata": 3.15, "uat": "Motru"},
    {"cod": "GJ_78512-0077", "fermier": "Stanescu Petre",   "suprafata": 8.90, "uat": "Bumbesti-Jiu"},
    {"cod": "GJ_78634-1129", "fermier": "Olteanu Vasile",   "suprafata": 2.44, "uat": "Novaci"},
    {"cod": "GJ_78720-3388", "fermier": "Marinescu Ana",    "suprafata": 5.67, "uat": "Targu Jiu"},
    {"cod": "GJ_79001-0445", "fermier": "Petrescu Dan",     "suprafata": 7.23, "uat": "Turceni"},
    {"cod": "GJ_79234-1876", "fermier": "Constantin Gh.",   "suprafata": 1.98, "uat": "Aninoasa"},
    {"cod": "GJ_79567-2290", "fermier": "Florescu Elena",   "suprafata": 9.45, "uat": "Rovinari"},
    {"cod": "GJ_80980-2611", "fermier": "Draghici Marin",   "suprafata": 6.64, "uat": "Targu Jiu"},
]

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.sql-box {
    background: #1e1e1e;
    color: #9cdcfe;
    border-radius: 8px;
    padding: 14px 18px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    margin: 8px 0;
    border-left: 4px solid #0052A5;
}
.sql-keyword { color: #569cd6; font-weight: bold; }
.sql-string  { color: #ce9178; }
.tabel-sql {
    background: #f0f4ff;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 6px 0;
    font-family: monospace;
    font-size: 13px;
    border-left: 4px solid #0052A5;
}
.stat-card {
    background: white;
    border-radius: 10px;
    padding: 14px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    border-top: 4px solid #0052A5;
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCTII BAZA DE DATE
# ═══════════════════════════════════════════════════════════════════════════════

def get_conn() -> sqlite3.Connection:
    """Returneaza conexiunea la baza de date."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # acces la coloane dupa nume
    return conn

def initializeaza_bd():
    """Creaza tabelele daca nu exista (CREATE TABLE IF NOT EXISTS)."""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sesiuni (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                data        TEXT NOT NULL,
                inspector   TEXT NOT NULL,
                institutie  TEXT,
                nr_parcele  INTEGER DEFAULT 0,
                nr_conforme INTEGER DEFAULT 0,
                nr_neconf   INTEGER DEFAULT 0,
                suprafata   REAL DEFAULT 0,
                observatii  TEXT,
                creat_la    TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS detectii (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                sesiune_id  INTEGER REFERENCES sesiuni(id),
                cod_lpis    TEXT NOT NULL,
                fermier     TEXT,
                uat         TEXT,
                suprafata   REAL,
                vegetatie   REAL,
                sol_gol     REAL,
                apa         REAL,
                confidenta  REAL,
                status      TEXT,
                data        TEXT,
                inspector   TEXT,
                creat_la    TEXT DEFAULT (datetime('now','localtime'))
            );
        """)

def salveaza_sesiune(data: str, inspector: str, institutie: str,
                     detectii: list, observatii: str = "") -> int:
    """Salveaza o sesiune completa si returneaza ID-ul ei."""
    conforme  = sum(1 for d in detectii if d["status"] == "CONFORM")
    neconf    = len(detectii) - conforme
    suprafata = sum(d["suprafata"] for d in detectii)

    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO sesiuni
               (data, inspector, institutie, nr_parcele, nr_conforme, nr_neconf, suprafata, observatii)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (data, inspector, institutie, len(detectii), conforme, neconf, suprafata, observatii)
        )
        sesiune_id = cur.lastrowid

        for d in detectii:
            conn.execute(
                """INSERT INTO detectii
                   (sesiune_id, cod_lpis, fermier, uat, suprafata,
                    vegetatie, sol_gol, apa, confidenta, status, data, inspector)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (sesiune_id, d["cod_lpis"], d["fermier"], d["uat"],
                 d["suprafata"], d["vegetatie"], d["sol_gol"], d["apa"],
                 d["confidenta"], d["status"], data, inspector)
            )
    return sesiune_id

def sterge_sesiune(sesiune_id: int):
    """Sterge o sesiune si toate detectiile asociate."""
    with get_conn() as conn:
        conn.execute("DELETE FROM detectii WHERE sesiune_id = ?", (sesiune_id,))
        conn.execute("DELETE FROM sesiuni WHERE id = ?", (sesiune_id,))

def get_sesiuni() -> pd.DataFrame:
    """Returneaza toate sesiunile ca DataFrame."""
    with get_conn() as conn:
        return pd.read_sql(
            "SELECT * FROM sesiuni ORDER BY creat_la DESC", conn
        )

def get_detectii(sesiune_id: int = None, status: str = None,
                 data_start: str = None, data_end: str = None) -> pd.DataFrame:
    """Returneaza detectii cu filtre optionale."""
    query  = "SELECT * FROM detectii WHERE 1=1"
    params = []
    if sesiune_id:
        query += " AND sesiune_id = ?"; params.append(sesiune_id)
    if status:
        query += " AND status = ?";     params.append(status)
    if data_start:
        query += " AND data >= ?";      params.append(data_start)
    if data_end:
        query += " AND data <= ?";      params.append(data_end)
    query += " ORDER BY creat_la DESC"
    with get_conn() as conn:
        return pd.read_sql(query, conn, params=params)

def get_statistici() -> dict:
    """Calculeaza statistici globale din baza de date."""
    with get_conn() as conn:
        total_sesiuni   = conn.execute("SELECT COUNT(*) FROM sesiuni").fetchone()[0]
        total_detectii  = conn.execute("SELECT COUNT(*) FROM detectii").fetchone()[0]
        total_neconf    = conn.execute("SELECT COUNT(*) FROM detectii WHERE status='NECONFORM'").fetchone()[0]
        total_conf      = conn.execute("SELECT COUNT(*) FROM detectii WHERE status='CONFORM'").fetchone()[0]
        suprafata_row   = conn.execute("SELECT SUM(suprafata) FROM detectii").fetchone()[0]
        suprafata_total = round(suprafata_row or 0, 2)
    return {
        "sesiuni":    total_sesiuni,
        "detectii":   total_detectii,
        "conforme":   total_conf,
        "neconforme": total_neconf,
        "suprafata":  suprafata_total,
    }

def genereaza_detectii_demo(seed: int, inspector: str) -> list:
    """Genereaza date detectie simulate pentru o sesiune."""
    rng = random.Random(seed)
    rezultate = []
    for p in PARCELE_LPIS:
        veg  = round(rng.uniform(25, 85), 1)
        sol  = round(rng.uniform(5, 35), 1)
        apa  = round(max(0, 100 - veg - sol), 1)
        conf = round(rng.uniform(0.72, 0.97), 2)
        rezultate.append({
            "cod_lpis":   p["cod"],
            "fermier":    p["fermier"],
            "uat":        p["uat"],
            "suprafata":  p["suprafata"],
            "vegetatie":  veg,
            "sol_gol":    sol,
            "apa":        apa,
            "confidenta": conf,
            "status":     "CONFORM" if veg >= 50 else "NECONFORM",
        })
    return rezultate

# ─── INITIALIZARE ─────────────────────────────────────────────────────────────
initializeaza_bd()

# ─── TITLU ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='display:flex; align-items:center; gap:16px; margin-bottom:8px;'>
    <div style='font-size:48px;'>🗄️</div>
    <div>
        <h1 style='margin:0; font-size:28px; color:#0052A5;'>
            Baza de Date SQLite — Istoric Detectii
        </h1>
        <p style='margin:0; color:#546e7a;'>
            Fiecare control se salveaza automat | Cautare | Filtrare | Export
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

st.caption(f"Baza de date: `{DB_PATH}`")

# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Adauga Sesiune",
    "Istoric Sesiuni",
    "Toate Detectiile",
    "Statistici",
    "SQL Direct"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ADAUGA SESIUNE NOUA
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Inregistreaza o sesiune noua de control")

    with st.expander("Ce este o sesiune?", expanded=False):
        st.markdown("""
        O **sesiune** = o zi de control pe teren cu drona.
        Inspectorul zboara deasupra parcelelor, face fotografii,
        ruleaza detectia YOLOv8 si salveaza rezultatele in baza de date.

        Fiecare sesiune contine:
        - Datele inspectorului si data controlului
        - Lista parcelelor analizate cu procentele de vegetatie
        - Status conformitate PAC per parcela
        """)

    col1, col2 = st.columns(2)
    with col1:
        inspector_in  = st.text_input("Inspector",
            value="Prof. Asoc. Dr. Oliviu Mihnea Gamulescu")
        institutie_in = st.text_input("Institutie",
            value="APIA CJ Gorj | UCB Targu Jiu")
        data_in       = st.date_input("Data controlului",
            value=datetime.date.today())
    with col2:
        seed_in       = st.number_input("Seed detectie (reproductibilitate)",
            min_value=1, max_value=9999, value=42)
        obs_in        = st.text_area("Observatii", height=80,
            placeholder="Ex: Conditii meteo bune, vant 15 km/h...")

    # Previzualizare detectii
    detectii_demo = genereaza_detectii_demo(int(seed_in), inspector_in)
    df_prev = pd.DataFrame(detectii_demo)

    st.markdown("**Previzualizare detectii ce vor fi salvate:**")

    def color_status(val):
        if val == "NECONFORM":
            return "background-color:#f8d7da; color:#721c24; font-weight:bold"
        return "background-color:#d4edda; color:#155724; font-weight:bold"

    st.dataframe(
        df_prev[["cod_lpis","fermier","uat","suprafata",
                 "vegetatie","sol_gol","apa","confidenta","status"]]
        .rename(columns={"cod_lpis":"Cod LPIS","fermier":"Fermier",
                          "uat":"UAT","suprafata":"Ha","vegetatie":"Veg%",
                          "sol_gol":"Sol%","apa":"Apa%",
                          "confidenta":"Conf","status":"Status"})
        .style.map(color_status, subset=["Status"]),
        use_container_width=True, hide_index=True
    )

    conf_prev  = sum(1 for d in detectii_demo if d["status"] == "CONFORM")
    neconf_prev = len(detectii_demo) - conf_prev
    c1, c2, c3 = st.columns(3)
    c1.metric("Parcele", len(detectii_demo))
    c2.metric("Conforme", conf_prev)
    c3.metric("Neconforme", neconf_prev)

    if st.button("Salveaza Sesiunea in Baza de Date", type="primary",
                 use_container_width=True):
        sesiune_id = salveaza_sesiune(
            data=str(data_in),
            inspector=inspector_in,
            institutie=institutie_in,
            detectii=detectii_demo,
            observatii=obs_in
        )
        st.success(f"Sesiunea a fost salvata cu ID={sesiune_id}. "
                   f"{len(detectii_demo)} detectii inregistrate.")
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ISTORIC SESIUNI
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Istoric sesiuni de control")

    df_sesiuni = get_sesiuni()

    if df_sesiuni.empty:
        st.info("Nu exista sesiuni salvate. Adauga prima sesiune in tab-ul 'Adauga Sesiune'.")
    else:
        # Statistici rapide
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total sesiuni",   len(df_sesiuni))
        c2.metric("Total parcele",   int(df_sesiuni["nr_parcele"].sum()))
        c3.metric("Total neconforme",int(df_sesiuni["nr_neconf"].sum()))
        c4.metric("Suprafata (ha)",  f"{df_sesiuni['suprafata'].sum():.1f}")

        st.dataframe(
            df_sesiuni[["id","data","inspector","nr_parcele",
                        "nr_conforme","nr_neconf","suprafata","observatii","creat_la"]]
            .rename(columns={
                "id":"ID","data":"Data","inspector":"Inspector",
                "nr_parcele":"Parcele","nr_conforme":"Conforme",
                "nr_neconf":"Neconforme","suprafata":"Ha",
                "observatii":"Observatii","creat_la":"Salvat la"
            }),
            use_container_width=True, hide_index=True
        )

        # Detalii sesiune selectata
        st.divider()
        st.markdown("**Vizualizeaza detaliile unei sesiuni:**")
        id_selectat = st.selectbox(
            "Alege sesiunea dupa ID",
            options=df_sesiuni["id"].tolist(),
            format_func=lambda x: f"ID {x} — {df_sesiuni[df_sesiuni['id']==x]['data'].values[0]} "
                                   f"({df_sesiuni[df_sesiuni['id']==x]['inspector'].values[0]})"
        )
        if id_selectat:
            df_det_ses = get_detectii(sesiune_id=id_selectat)
            if not df_det_ses.empty:
                st.dataframe(
                    df_det_ses[["cod_lpis","fermier","uat","suprafata",
                                "vegetatie","sol_gol","apa","confidenta","status"]]
                    .rename(columns={"cod_lpis":"Cod LPIS","fermier":"Fermier",
                                     "uat":"UAT","suprafata":"Ha","vegetatie":"Veg%",
                                     "sol_gol":"Sol%","apa":"Apa%",
                                     "confidenta":"Conf","status":"Status"})
                    .style.map(color_status, subset=["Status"]),
                    use_container_width=True, hide_index=True
                )

            col_del1, col_del2 = st.columns([3, 1])
            with col_del2:
                if st.button("Sterge aceasta sesiune", type="secondary"):
                    sterge_sesiune(id_selectat)
                    st.warning(f"Sesiunea ID={id_selectat} a fost stearsa.")
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — TOATE DETECTIILE (cu filtre)
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Toate detectiile — cautare si filtrare")

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filtru_status = st.selectbox("Filtreaza dupa status",
            ["Toate", "CONFORM", "NECONFORM"])
    with col_f2:
        data_start = st.date_input("De la data",
            value=datetime.date.today() - datetime.timedelta(days=30))
    with col_f3:
        data_end = st.date_input("Pana la data",
            value=datetime.date.today())

    status_f = None if filtru_status == "Toate" else filtru_status
    df_toate = get_detectii(
        status=status_f,
        data_start=str(data_start),
        data_end=str(data_end)
    )

    if df_toate.empty:
        st.info("Nu exista detectii pentru filtrele selectate.")
    else:
        st.markdown(f"**{len(df_toate)} detectii gasite:**")
        st.dataframe(
            df_toate[["sesiune_id","data","cod_lpis","fermier","uat",
                       "vegetatie","sol_gol","apa","status","inspector"]]
            .rename(columns={
                "sesiune_id":"Sesiune","data":"Data",
                "cod_lpis":"Cod LPIS","fermier":"Fermier","uat":"UAT",
                "vegetatie":"Veg%","sol_gol":"Sol%","apa":"Apa%",
                "status":"Status","inspector":"Inspector"
            })
            .style.map(color_status, subset=["Status"]),
            use_container_width=True, hide_index=True
        )

        # Export Excel
        buf_xl = io.BytesIO()
        with pd.ExcelWriter(buf_xl, engine="openpyxl") as writer:
            df_toate.to_excel(writer, sheet_name="Detectii", index=False)
        buf_xl.seek(0)
        st.download_button(
            "Export Excel — Detectii Filtrate",
            data=buf_xl,
            file_name=f"Detectii_APIA_{data_start}_{data_end}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — STATISTICI
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Statistici globale baza de date")

    stats = get_statistici()

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, (label, val) in zip(
        [c1, c2, c3, c4, c5],
        [("Sesiuni", stats["sesiuni"]),
         ("Detectii totale", stats["detectii"]),
         ("Conforme", stats["conforme"]),
         ("Neconforme", stats["neconforme"]),
         ("Suprafata (ha)", stats["suprafata"])]
    ):
        with col:
            st.markdown(f"""
            <div class="stat-card">
                <div style='font-size:26px; font-weight:800; color:#0052A5;'>{val}</div>
                <div style='font-size:12px; color:#666;'>{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Grafice din baza de date
    df_toate_stats = get_detectii()
    if not df_toate_stats.empty:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown("**Distributie status conformitate**")
            counts = df_toate_stats["status"].value_counts()
            fig, ax = plt.subplots(figsize=(5, 4))
            culori = ["#28a745" if s == "CONFORM" else "#dc3545"
                      for s in counts.index]
            ax.bar(counts.index, counts.values, color=culori, edgecolor="white")
            ax.set_ylabel("Numar detectii")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            for i, v in enumerate(counts.values):
                ax.text(i, v + 0.1, str(v), ha="center", fontweight="bold")
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        with col_g2:
            st.markdown("**Vegetatie medie per UAT**")
            df_uat = (df_toate_stats.groupby("uat")["vegetatie"]
                      .mean().sort_values(ascending=True))
            fig2, ax2 = plt.subplots(figsize=(5, 4))
            culori2 = ["#28a745" if v >= 50 else "#dc3545"
                       for v in df_uat.values]
            ax2.barh(df_uat.index, df_uat.values, color=culori2, edgecolor="white")
            ax2.axvline(50, color="orange", linestyle="--",
                        linewidth=1.5, label="Prag PAC 50%")
            ax2.set_xlabel("Vegetatie medie (%)")
            ax2.legend(fontsize=8)
            ax2.spines["top"].set_visible(False)
            ax2.spines["right"].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig2)
            plt.close(fig2)

        # Top parcele neconforme
        st.divider()
        st.markdown("**Top parcele cu cele mai multe neconformitati:**")
        df_nec = (df_toate_stats[df_toate_stats["status"] == "NECONFORM"]
                  .groupby(["cod_lpis", "fermier"])
                  .size()
                  .reset_index(name="nr_neconformitati")
                  .sort_values("nr_neconformitati", ascending=False)
                  .head(10))
        if not df_nec.empty:
            st.dataframe(df_nec, use_container_width=True, hide_index=True)
        else:
            st.info("Nu exista neconformitati inregistrate.")
    else:
        st.info("Adauga cel putin o sesiune pentru a vedea statisticile.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — SQL DIRECT (Educational)
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Interogari SQL directe — Educational")

    st.info("""
    Aceasta sectiune demonstreaza puterea SQL aplicat pe datele AGROVISION.
    Scrie orice interogare SELECT si vezi rezultatul instant.
    (Doar SELECT este permis — nu se pot modifica datele)
    """)

    exemple_sql = {
        "Toate sesiunile": "SELECT * FROM sesiuni ORDER BY data DESC",
        "Parcele neconforme din ultima luna":
            f"SELECT cod_lpis, fermier, uat, vegetatie, data FROM detectii "
            f"WHERE status='NECONFORM' AND data >= date('now','-30 days') "
            f"ORDER BY vegetatie ASC",
        "Vegetatie medie per UAT":
            "SELECT uat, ROUND(AVG(vegetatie),1) as veg_medie, "
            "COUNT(*) as nr_detectii FROM detectii GROUP BY uat ORDER BY veg_medie ASC",
        "Inspector cu cele mai multe controale":
            "SELECT inspector, COUNT(*) as nr_sesiuni, "
            "SUM(nr_parcele) as total_parcele FROM sesiuni GROUP BY inspector",
        "Rata conformitate per sesiune":
            "SELECT id, data, inspector, nr_parcele, nr_conforme, nr_neconf, "
            "ROUND(nr_conforme*100.0/nr_parcele,1) as rata_conf_pct "
            "FROM sesiuni ORDER BY data DESC",
    }

    sql_ales = st.selectbox("Alege un exemplu sau scrie propria interogare:",
                             list(exemple_sql.keys()))
    sql_input = st.text_area("Interogare SQL:",
                              value=exemple_sql[sql_ales], height=80)

    if st.button("Ruleaza SQL", type="primary"):
        if not sql_input.strip().upper().startswith("SELECT"):
            st.error("Doar interogari SELECT sunt permise in aceasta sectiune.")
        else:
            try:
                with get_conn() as conn:
                    df_sql = pd.read_sql(sql_input, conn)
                st.success(f"{len(df_sql)} randuri returnate.")
                st.dataframe(df_sql, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Eroare SQL: {e}")

    st.divider()
    st.markdown("**Structura bazei de date AGROVISION:**")

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("""
        <div class="tabel-sql">
        <strong>Tabela: sesiuni</strong><br><br>
        id         INTEGER (cheie primara)<br>
        data       TEXT (YYYY-MM-DD)<br>
        inspector  TEXT<br>
        institutie TEXT<br>
        nr_parcele INTEGER<br>
        nr_conforme INTEGER<br>
        nr_neconf  INTEGER<br>
        suprafata  REAL (hectare)<br>
        observatii TEXT<br>
        creat_la   TEXT (timestamp)
        </div>
        """, unsafe_allow_html=True)
    with col_t2:
        st.markdown("""
        <div class="tabel-sql">
        <strong>Tabela: detectii</strong><br><br>
        id         INTEGER (cheie primara)<br>
        sesiune_id INTEGER (cheie straina)<br>
        cod_lpis   TEXT<br>
        fermier    TEXT<br>
        uat        TEXT<br>
        suprafata  REAL<br>
        vegetatie  REAL (%)<br>
        sol_gol    REAL (%)<br>
        apa        REAL (%)<br>
        confidenta REAL (0-1)<br>
        status     TEXT (CONFORM/NECONFORM)<br>
        data       TEXT<br>
        inspector  TEXT
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    **Concepte SQL folosite in aceasta pagina:**

    | Comanda SQL | Folosita pentru |
    |-------------|-----------------|
    | `CREATE TABLE IF NOT EXISTS` | Creaza tabela doar daca nu exista |
    | `INSERT INTO ... VALUES` | Salveaza o detectie noua |
    | `SELECT * FROM ... WHERE` | Filtrare detectii dupa status/data |
    | `GROUP BY ... ORDER BY` | Statistici per UAT sau inspector |
    | `SUM() / AVG() / COUNT()` | Calcule agregate |
    | `pd.read_sql(query, conn)` | DataFrame direct din baza de date |
    | `conn.row_factory = sqlite3.Row` | Acces coloane dupa nume |
    """)

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center; color:#90a4ae; font-size:12px; padding:8px 0;'>
    AGROVISION &nbsp;|&nbsp; Ziua 22 — Baza de Date SQLite &nbsp;|&nbsp;
    sqlite3 | pd.read_sql() | CREATE TABLE | INSERT | SELECT
    &nbsp;|&nbsp; UCB Targu Jiu &nbsp;|&nbsp; APIA CJ Gorj
</div>
""", unsafe_allow_html=True)
