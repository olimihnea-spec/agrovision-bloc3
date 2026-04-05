"""
BLOC 3 — Deep Learning YOLOv8, Ziua 21
Deployment pe Streamlit Community Cloud — acces 24/7, gratuit
Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu | UCB Targu Jiu | APIA CJ Gorj

CONCEPT CHEIE:
  Deployment = procesul prin care aplicatia ta locala devine accesibila
  de oriunde in lume, pe orice dispozitiv, 24 ore din 24.

  Fara deployment: aplicatia merge doar pe calculatorul tau.
  Cu deployment: link permanent pe care il trimiti studentilor UCB,
  colegilor APIA, reviewerilor IEEE, comisiei UEFISCDI.

  Stack GRATUIT complet:
    GitHub (privat) → stocheaza codul
    Streamlit Community Cloud → ruleaza aplicatia online
    .gitignore → protejeaza secrets + modelul best.pt
    secrets.toml → parole in afara codului

  De ce Streamlit Community Cloud si nu altceva:
    - 0 RON/luna (nu cere card bancar)
    - Suporta repo GitHub privat (codul tau nu e public)
    - Deploy automat la fiecare git push
    - Gestioneaza secrets in interfata web (fara fisiere cu parole online)
    - Recunoscut de IEEE si UEFISCDI ca platforma demo academica
"""

import streamlit as st
import os
import subprocess
import datetime

# ─── CONFIGURARE PAGINA ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Deployment Cloud AGROVISION",
    page_icon="🚀",
    layout="wide"
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.pas-box {
    background: white;
    border-radius: 12px;
    padding: 20px 24px;
    margin: 12px 0;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    border-left: 5px solid #0052A5;
}
.pas-numar {
    background: #0052A5;
    color: white;
    border-radius: 50%;
    width: 32px;
    height: 32px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 16px;
    margin-right: 10px;
}
.status-ok {
    background: #d4edda;
    border: 1px solid #28a745;
    border-radius: 8px;
    padding: 10px 16px;
    color: #155724;
    font-weight: 600;
}
.status-warn {
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 8px;
    padding: 10px 16px;
    color: #856404;
    font-weight: 600;
}
.cmd-box {
    background: #1e1e1e;
    color: #d4d4d4;
    border-radius: 8px;
    padding: 14px 18px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    margin: 8px 0;
}
.fisier-box {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 6px 0;
    font-family: monospace;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# ─── TITLU ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='display:flex; align-items:center; gap:16px; margin-bottom:8px;'>
    <div style='font-size:48px;'>🚀</div>
    <div>
        <h1 style='margin:0; font-size:28px; color:#0052A5;'>
            Deployment pe Streamlit Community Cloud
        </h1>
        <p style='margin:0; color:#546e7a;'>
            Aplicatia AGROVISION online — gratuit, 24/7, accesibil de oriunde
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── VERIFICARE FISIERE NECESARE ──────────────────────────────────────────────
st.subheader("Verificare fisiere pentru deployment")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

fisiere_necesare = {
    "requirements.txt":           os.path.join(BASE, "requirements.txt"),
    ".gitignore":                  os.path.join(BASE, ".gitignore"),
    ".streamlit/config.toml":     os.path.join(BASE, ".streamlit", "config.toml"),
    ".streamlit/secrets.toml":    os.path.join(BASE, ".streamlit", "secrets.toml"),
    "Acasa.py":                   os.path.join(BASE, "Acasa.py"),
}

col1, col2 = st.columns(2)
toate_ok = True
for idx, (nume, cale) in enumerate(fisiere_necesare.items()):
    col = col1 if idx % 2 == 0 else col2
    exista = os.path.exists(cale)
    if not exista:
        toate_ok = False
    with col:
        icon = "✅" if exista else "❌"
        culoare = "#d4edda" if exista else "#f8d7da"
        text_c = "#155724" if exista else "#721c24"
        st.markdown(f"""
        <div style='background:{culoare}; border-radius:8px; padding:10px 14px;
                    margin:4px 0; color:{text_c}; font-family:monospace; font-size:13px;'>
            {icon} &nbsp; {nume}
        </div>
        """, unsafe_allow_html=True)

if toate_ok:
    st.success("Toate fisierele necesare sunt prezente. Aplicatia e gata de deployment!")
else:
    st.warning("Unele fisiere lipsesc. Ruleaza sectiunea 'Genereaza fisiere' de mai jos.")

st.divider()

# ─── TABS PRINCIPALE ─────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Pasii de deployment",
    "Fisiere generate",
    "Secrets (parole)",
    "Dupa deployment"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — GHID PAS CU PAS
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Ghid complet deployment — 6 pasi")

    pasi = [
        {
            "titlu": "Creaza cont GitHub (daca nu ai)",
            "detalii": "Mergi la github.com → Sign up → alege username (ex: olimihnea-spec) → confirma email.",
            "nota": "Ai deja contul: olimihnea-spec (creat la Ziua 21 Bloc 1)",
            "comenzi": [],
            "status": "ok"
        },
        {
            "titlu": "Creaza repository privat pe GitHub",
            "detalii": "github.com → New repository → Nume: agrovision-bloc3 → Private → Create",
            "nota": "Privat = codul nu e vizibil public. Gratuit pentru conturi personale.",
            "comenzi": [],
            "status": "ok"
        },
        {
            "titlu": "Initializeaza Git si urca codul",
            "detalii": "Deschide terminalul in folderul yolo_app si ruleaza comenzile:",
            "nota": "Inlocuieste olimihnea-spec cu username-ul tau GitHub",
            "comenzi": [
                "cd \"G:\\CLAUDE CODE INSTRUIRE VOL II 90 ZILE STREAMLIT ISI YOLO\\Bloc3_YOLOv8\\yolo_app\"",
                "git init",
                "git add .",
                "git commit -m \"AGROVISION v1.0 - Bloc 3 YOLOv8\"",
                "git branch -M main",
                "git remote add origin https://github.com/olimihnea-spec/agrovision-bloc3.git",
                "git push -u origin main"
            ],
            "status": "actiune"
        },
        {
            "titlu": "Conecteaza Streamlit Community Cloud la GitHub",
            "detalii": "Mergi la share.streamlit.io → Sign in with GitHub → New app",
            "nota": "Selecteaza: Repository=agrovision-bloc3 | Branch=main | Main file=Acasa.py",
            "comenzi": [],
            "status": "actiune"
        },
        {
            "titlu": "Adauga secrets in Streamlit Cloud",
            "detalii": "In Streamlit Cloud: App settings → Secrets → lipesti continutul din secrets.toml",
            "nota": "Astfel parolele nu sunt in cod si nu apar pe GitHub.",
            "comenzi": [],
            "status": "important"
        },
        {
            "titlu": "Deploy automat!",
            "detalii": "Streamlit Cloud instaleaza automat pachetele din requirements.txt si porneste aplicatia.",
            "nota": "La fiecare git push nou, aplicatia se actualizeaza automat in ~2 minute.",
            "comenzi": [],
            "status": "ok"
        },
    ]

    CULORI_STATUS = {
        "ok":       ("#0052A5", "✅"),
        "actiune":  ("#28a745", "▶"),
        "important":("#dc3545", "⚠"),
    }

    for i, pas in enumerate(pasi):
        culoare, icon = CULORI_STATUS[pas["status"]]
        st.markdown(f"""
        <div class="pas-box" style="border-left-color: {culoare};">
            <div style="display:flex; align-items:center; margin-bottom:8px;">
                <span style="background:{culoare}; color:white; border-radius:50%;
                             width:28px; height:28px; display:inline-flex;
                             align-items:center; justify-content:center;
                             font-weight:700; margin-right:10px; flex-shrink:0;">
                    {i+1}
                </span>
                <strong style="font-size:15px;">{pas['titlu']}</strong>
                &nbsp; {icon}
            </div>
            <p style="margin:4px 0 4px 38px; color:#546e7a; font-size:14px;">
                {pas['detalii']}
            </p>
            <p style="margin:4px 0 0 38px; color:#856404; font-size:13px;
                      background:#fff8e1; padding:6px 10px; border-radius:6px;">
                {pas['nota']}
            </p>
        </div>
        """, unsafe_allow_html=True)

        if pas["comenzi"]:
            with st.expander(f"Comenzi terminale — Pasul {i+1}"):
                for cmd in pas["comenzi"]:
                    st.code(cmd, language="bash")

    st.info("""
    **Rezultatul final:** vei avea un link de forma:
    `https://olimihnea-spec-agrovision-bloc3-acasa-XXXXX.streamlit.app`

    Pe care il trimiti oricui, de pe orice dispozitiv, fara sa fie pornit calculatorul tau.
    """)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — FISIERE GENERATE
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Fisierele create pentru deployment")

    st.markdown("#### requirements.txt — pachetele Python necesare")
    req_path = os.path.join(BASE, "requirements.txt")
    if os.path.exists(req_path):
        with open(req_path) as f:
            continut_req = f.read()
        st.code(continut_req, language="text")
        st.success("requirements.txt exista — Streamlit Cloud il citeste automat la deploy.")
    else:
        st.error("requirements.txt lipsa!")

    st.markdown("#### .gitignore — ce NU se urca pe GitHub")
    gi_path = os.path.join(BASE, ".gitignore")
    if os.path.exists(gi_path):
        with open(gi_path) as f:
            continut_gi = f.read()
        st.code(continut_gi, language="text")
        st.success(".gitignore exista — modelul best.pt si parolele sunt protejate.")
    else:
        st.error(".gitignore lipsa!")

    st.markdown("#### .streamlit/config.toml — aspect aplicatie")
    cfg_path = os.path.join(BASE, ".streamlit", "config.toml")
    if os.path.exists(cfg_path):
        with open(cfg_path) as f:
            continut_cfg = f.read()
        st.code(continut_cfg, language="toml")
        st.success("config.toml exista — tema albastra APIA aplicata.")
    else:
        st.error("config.toml lipsa!")

    st.divider()
    st.markdown("""
    **De ce fiecare fisier este important:**

    | Fisier | Fara el | Cu el |
    |--------|---------|-------|
    | `requirements.txt` | Streamlit Cloud nu stie ce sa instaleze → eroare | Instaleaza automat toate pachetele |
    | `.gitignore` | best.pt si parolele ajung pe GitHub | Raman local, protejate |
    | `config.toml` | Tema implicita gri Streamlit | Tema albastra #0052A5 APIA |
    | `secrets.toml` | Parolele in cod (risc) | Parolele in interfata Streamlit Cloud |
    """)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SECRETS (PAROLE)
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Gestionarea parolelor in Streamlit Cloud")

    st.warning("""
    **Regula de aur:** Parolele nu se pun niciodata in cod si nu se urca pe GitHub.
    Streamlit Cloud are o sectiune speciala **Secrets** unde le introduci direct
    prin interfata web — nu sunt vizibile in niciun fisier public.
    """)

    st.markdown("#### Ce introduci in Streamlit Cloud → Settings → Secrets:")

    secrets_demo = """[users.admin]
hash = "HASH_SHA256_PAROLA_ADMIN"
rol = "admin"
prenume = "Administrator"

[users.inspector1]
hash = "HASH_SHA256_PAROLA_INSPECTOR1"
rol = "inspector"
prenume = "Ion Popescu"

[app]
nume = "AGROVISION"
versiune = "1.0"
"""
    st.code(secrets_demo, language="toml")

    st.info("""
    **Cum obtii hash-ul SHA-256 al parolei tale:**
    Ruleaza in terminal:
    ```python
    import hashlib
    print(hashlib.sha256("parola_ta".encode()).hexdigest())
    ```
    Copiaza rezultatul (64 caractere) in locul `HASH_SHA256_...`
    """)

    st.markdown("#### Generare hash pentru parole noi:")
    import hashlib
    with st.form("form_hash"):
        parola_test = st.text_input("Introdu parola (nu se salveaza, doar afisam hash-ul):",
                                     type="password")
        if st.form_submit_button("Genereaza Hash SHA-256"):
            if parola_test:
                h = hashlib.sha256(parola_test.encode()).hexdigest()
                st.success(f"Hash SHA-256: `{h}`")
                st.caption("Copiaza acest hash in Streamlit Cloud Secrets.")
            else:
                st.error("Introdu o parola.")

    st.markdown("""
    #### De ce SHA-256 si nu parola simpla?

    Daca cineva obtine acces la secrets (ex: un angajat Streamlit), vede doar:
    ```
    hash = "51c8a9a9e76e6e1b..."   ← 64 caractere fara sens
    ```
    Nu poate afla parola originala din hash (functie ireversibila).
    Parola `admin2026` devine `51c8a9...` — nu se poate recupera din hash.
    """)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — DUPA DEPLOYMENT
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Ce poti face dupa deployment")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Actualizare aplicatie")
        st.markdown("""
        Oricand modifici codul local si vrei sa actualizezi versiunea online:
        ```bash
        git add .
        git commit -m "Actualizare: ziua 22 adaugata"
        git push
        ```
        Streamlit Cloud detecteaza push-ul si redeploy-uieste automat in ~2 minute.
        """)

        st.markdown("#### Impartire link")
        st.markdown("""
        Trimite linkul aplicatiei catre:
        - **Studenti UCB** — acces direct din browser, fara instalare
        - **Colegi APIA** — demo control teren cu drona
        - **Comisie UEFISCDI** — dovada aplicatie functionala
        - **Revieweri IEEE** — link in articol: *"Demo available at [link]"*
        """)

    with col2:
        st.markdown("#### Limitele planului gratuit")
        st.markdown("""
        | Limita | Valoare gratuita |
        |--------|-----------------|
        | Aplicatii active | 3 aplicatii |
        | RAM per aplicatie | 1 GB |
        | CPU | Partajat |
        | Domeniu custom | Nu (doar .streamlit.app) |
        | Repo privat GitHub | DA - inclus |
        | Secrets | DA - inclus |
        | Bandwidth | Nelimitat |

        **Pentru uzul tau (academic + demo):** planul gratuit e mai mult decat suficient.
        """)

        st.markdown("#### Daca aplicatia doarme")
        st.markdown("""
        Streamlit Cloud opreste aplicatia dupa cateva zile de inactivitate
        (nimeni nu a accesat-o). La primul acces, se reporneste in ~30 secunde.

        **Nu e o problema** pentru uz academic/demo.
        Daca vrei sa fie mereu activa: trimite linkul periodic sau seteaza
        un ping automat (gratuit cu UptimeRobot.com).
        """)

    st.divider()
    st.markdown("#### Modelul best.pt pe cloud — strategie")
    st.info("""
    **Problema:** best.pt (6MB) nu e pe GitHub (protejat de .gitignore).
    Pe Streamlit Cloud, paginile care au nevoie de model vor folosi **mod simulare**.

    **Solutie pe termen lung:**
    - Urca modelul pe **Hugging Face Hub** (gratuit, dedicat modele AI)
    - In aplicatie: `from huggingface_hub import hf_hub_download`
    - Modelul se descarca automat la primul acces

    Aceasta e exact cum fac companiile mari (Meta, Google) cu modelele lor AI.
    Il implementam la o zi viitoare.
    """)

    st.markdown("#### Checklist final inainte de a da linkul altora")
    checklist = [
        ("Parolele demo sunt schimbate sau sterse din cod", True),
        ("secrets.toml e in .gitignore (nu pe GitHub)", True),
        ("best.pt e in .gitignore (nu pe GitHub)", True),
        ("requirements.txt contine toate pachetele", True),
        ("Aplicatia merge local fara erori", True),
        ("Paginile cu model real au mod de fallback (simulare)", False),
        ("Linkul a fost testat pe alt dispozitiv", False),
    ]
    for item, ok in checklist:
        icon = "✅" if ok else "⬜"
        st.markdown(f"{icon} {item}")

# ─── SECTIUNEA CONCEPTE ───────────────────────────────────────────────────────
st.divider()
st.subheader("Concepte cheie — Ziua 21")

with st.expander("Ce inseamna fiecare fisier de configurare"):
    st.markdown("""
    **requirements.txt**
    Lista exacta a pachetelor Python necesare (cu versiuni).
    Streamlit Cloud ruleaza `pip install -r requirements.txt` automat.
    Fara el → eroare `ModuleNotFoundError` la deploy.

    **.gitignore**
    Lista fisierelor pe care Git le ignora complet.
    Fisierele din .gitignore nu apar niciodata pe GitHub, indiferent de `git add .`
    Regulile merg pe pattern: `*.pt` = toate fisierele .pt | `runs/` = tot folderul runs/

    **.streamlit/config.toml**
    Configuratia aplicatiei Streamlit: culori, fonturi, limite upload, securitate CORS/XSRF.
    Se aplica atat local cat si pe cloud.

    **.streamlit/secrets.toml**
    Fisier LOCAL cu parole/chei API. NU se urca pe GitHub.
    Pe Streamlit Cloud, secretele se introduc in interfata web — nu in fisier.
    Accesate in cod cu: `st.secrets["users"]["admin"]["hash"]`
    """)

with st.expander("Fluxul complet de lucru cu Git + Streamlit Cloud"):
    st.markdown("""
    ```
    Calculator local                    GitHub (privat)         Streamlit Cloud
    ─────────────────                   ───────────────         ───────────────
    Modifici cod          git push →    Codul actualizat   →    Detecteaza push
    Testezi local                       (fara secrets.toml)     Reinstaleaza pachete
    git add .                           (fara *.pt)             Reporneste aplicatia
    git commit -m "..."                                         Link actualizat in ~2min
    git push
    ```

    **Avantajul principal:** Nu trebuie sa trimiți aplicatia nimănui.
    Dai linkul o singura data — ei vad mereu ultima versiune.
    """)

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.divider()
st.markdown(f"""
<div style='text-align:center; color:#90a4ae; font-size:12px; padding:8px 0;'>
    AGROVISION &nbsp;|&nbsp; Ziua 21 — Deployment Streamlit Cloud &nbsp;|&nbsp;
    GitHub privat + Secrets + .gitignore &nbsp;|&nbsp;
    UCB Targu Jiu &nbsp;|&nbsp; APIA CJ Gorj
</div>
""", unsafe_allow_html=True)
