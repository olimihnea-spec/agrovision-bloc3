"""
BLOC 3 — Deep Learning YOLOv8, Ziua 25
Integrare Hugging Face Hub — modelul best.pt pe cloud gratuit
Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu | UCB Targu Jiu | APIA CJ Gorj

CONCEPT CHEIE:
  Problema rezolvata azi:
    - best.pt (6MB, proprietate intelectuala) NU poate fi pe GitHub
    - Streamlit Cloud NU are acces la fisierele locale
    - Cum ajunge modelul pe Streamlit Cloud fara GitHub?

  Solutia: Hugging Face Hub
    - Platforma gratuita dedicata modelelor AI (Meta, Google, Microsoft pun modele aici)
    - Repository privat = modelul nu e public (ca GitHub privat)
    - huggingface_hub.hf_hub_download() = descarca modelul automat la primul acces
    - Se cacheaza local → download o singura data, reutilizat ulterior
    - Streamlit Cloud descarca modelul din Hugging Face la deploy

  Fluxul complet dupa Ziua 25:
    Calculator local:
      best.pt ─── upload ──→ Hugging Face Hub (privat)
                                      │
    Streamlit Cloud:                  ↓
      la pornire ←── hf_hub_download() ──── model descarcat
      model incarcat → detectii functionale pe cloud

  De ce Hugging Face si nu Google Drive / Dropbox:
    - URL stabil (nu expira niciodata)
    - Versioning (poti urca best_v2, best_v3...)
    - Metadate model (mAP, clase, data antrenament)
    - Standard in comunitatea AI — revieweri IEEE il recunosc
    - Gratuit pentru modele publice SI private (cu limite)
"""

import streamlit as st
import os
import datetime

# ─── CONFIGURARE PAGINA ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Hugging Face Hub — AGROVISION",
    page_icon="🤗",
    layout="wide"
)

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_LOCAL = os.path.join(BASE_DIR, "MODEL_ANTRENAT_BEST_PT",
                           "best_v1_mAP083_20260403.pt")
MODEL_DESCARCAT = os.path.join(BASE_DIR, "modele",
                               "best_v1_mAP083_20260403.pt")

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.pas-hf {
    background: white;
    border-radius: 10px;
    padding: 18px 22px;
    margin: 10px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    border-left: 5px solid #FF9D00;
}
.cod-hf {
    background: #1e1e1e;
    color: #d4d4d4;
    border-radius: 8px;
    padding: 14px 18px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    margin: 8px 0;
}
.model-card {
    background: linear-gradient(135deg, #fff8f0, #fff3e0);
    border: 2px solid #FF9D00;
    border-radius: 12px;
    padding: 20px 24px;
    margin: 8px 0;
}
.status-gasit {
    background: #d4edda;
    border-radius: 8px;
    padding: 10px 16px;
    color: #155724;
    font-weight: 600;
    border-left: 4px solid #28a745;
}
.status-lipsa {
    background: #fff3cd;
    border-radius: 8px;
    padding: 10px 16px;
    color: #856404;
    font-weight: 600;
    border-left: 4px solid #ffc107;
}
</style>
""", unsafe_allow_html=True)

# ─── TITLU ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='display:flex; align-items:center; gap:16px; margin-bottom:8px;'>
    <div style='font-size:48px;'>🤗</div>
    <div>
        <h1 style='margin:0; font-size:28px; color:#FF9D00;'>
            Hugging Face Hub
        </h1>
        <p style='margin:0; color:#546e7a;'>
            Modelul best.pt pe cloud | Download automat | Gratuit | Privat
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── STATUS MODEL LOCAL ───────────────────────────────────────────────────────
model_exista = os.path.exists(MODEL_LOCAL) or os.path.exists(MODEL_DESCARCAT)
cale_model_gasit = MODEL_LOCAL if os.path.exists(MODEL_LOCAL) else (
    MODEL_DESCARCAT if os.path.exists(MODEL_DESCARCAT) else None
)
if cale_model_gasit:
    size_mb = os.path.getsize(cale_model_gasit) / (1024 * 1024)
    sursa = "MODEL_ANTRENAT_BEST_PT/" if os.path.exists(MODEL_LOCAL) else "modele/"
    st.markdown(f"""
    <div class="status-gasit">
        Model gasit: <code>best_v1_mAP083_20260403.pt</code>
        ({size_mb:.1f} MB) — {sursa}
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="status-lipsa">
        ⚠ Modelul best.pt nu a fost gasit local.
        Cauta-l in: MODEL_ANTRENAT_BEST_PT/ sau modele/
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Ghid Upload Model",
    "Model Card",
    "Download in Aplicatie",
    "Integrare Streamlit Cloud",
    "Cod Complet"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — GHID UPLOAD MODEL
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Incarca best.pt pe Hugging Face — 5 pasi")

    pasi = [
        {
            "nr": "1",
            "titlu": "Creaza cont Hugging Face",
            "text": "Mergi la huggingface.co → Sign Up → username: oliviu-gamulescu (sau olimihnea-spec)",
            "nota": "Contul este gratuit. Nu necesita card bancar.",
            "cod": ""
        },
        {
            "nr": "2",
            "titlu": "Creaza un repository nou pentru model",
            "text": "huggingface.co/new → Nume: agrovision-yolov8 → Private → Create",
            "nota": "Private = modelul nu e vizibil public. Gratuit pentru orice numar de repo-uri private.",
            "cod": ""
        },
        {
            "nr": "3",
            "titlu": "Genereaza Access Token",
            "text": "Settings → Access Tokens → New token → Nume: AGROVISION → Role: write → Generate",
            "nota": "Salveaza token-ul in secrets.toml (nu in cod). Format: hf_XXXXXXXXXXXXXXXX",
            "cod": ""
        },
        {
            "nr": "4",
            "titlu": "Upload modelul din Python",
            "text": "Ruleaza scriptul de mai jos o singura data de pe calculatorul tau:",
            "nota": "Upload-ul dureaza ~30 secunde pentru 6MB pe conexiune normala.",
            "cod": """from huggingface_hub import HfApi

api = HfApi()

# Autentificare cu token-ul tau
api.upload_file(
    path_or_fileobj="MODEL_ANTRENAT_BEST_PT/best_v1_mAP083_20260403.pt",
    path_in_repo="best_v1_mAP083_20260403.pt",
    repo_id="oliviu-gamulescu/agrovision-yolov8",
    repo_type="model",
    token="hf_TOKEN_TAU_AICI"
)
print("Model urcat cu succes pe Hugging Face!")"""
        },
        {
            "nr": "5",
            "titlu": "Adauga token-ul in secrets.toml",
            "text": "Adauga in .streamlit/secrets.toml si in Streamlit Cloud Secrets:",
            "nota": "Streamlit Cloud foloseste token-ul pentru a descarca modelul privat.",
            "cod": """[huggingface]
token   = "hf_TOKEN_TAU_AICI"
repo_id = "oliviu-gamulescu/agrovision-yolov8"
model   = "best_v1_mAP083_20260403.pt\""""
        },
    ]

    for pas in pasi:
        st.markdown(f"""
        <div class="pas-hf">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                <span style="background:#FF9D00; color:white; border-radius:50%;
                             width:28px; height:28px; display:inline-flex;
                             align-items:center; justify-content:center;
                             font-weight:700; flex-shrink:0;">
                    {pas['nr']}
                </span>
                <strong style="font-size:15px;">{pas['titlu']}</strong>
            </div>
            <p style="margin:4px 0 4px 38px; color:#546e7a; font-size:14px;">
                {pas['text']}
            </p>
            <p style="margin:4px 0 0 38px; background:#fff8e1; padding:6px 10px;
                      border-radius:6px; font-size:13px; color:#856404;">
                {pas['nota']}
            </p>
        </div>
        """, unsafe_allow_html=True)
        if pas["cod"]:
            st.code(pas["cod"], language="python")

    # Buton Upload real (daca modelul exista local si token configurat)
    st.divider()
    st.markdown("#### Upload direct din aceasta pagina")

    hf_token_ok = False
    hf_repo = "oliviu-gamulescu/agrovision-yolov8"
    try:
        hf_token = st.secrets["huggingface"]["token"]
        hf_repo  = st.secrets["huggingface"].get("repo_id", hf_repo)
        hf_token_ok = True
    except Exception:
        pass

    if hf_token_ok and model_exista:
        st.success("Token Hugging Face detectat in secrets.toml. Poti urca modelul direct.")
        if st.button("Urca best.pt pe Hugging Face", type="primary"):
            from huggingface_hub import HfApi
            api = HfApi()
            with st.spinner("Se incarca modelul... (~30 sec)"):
                try:
                    api.upload_file(
                        path_or_fileobj=MODEL_LOCAL,
                        path_in_repo="best_v1_mAP083_20260403.pt",
                        repo_id=hf_repo,
                        repo_type="model",
                        token=hf_token
                    )
                    st.success(f"Model urcat cu succes pe {hf_repo}!")
                except Exception as e:
                    st.error(f"Eroare upload: {e}")
    elif not hf_token_ok:
        st.info("Adauga token-ul Hugging Face in .streamlit/secrets.toml pentru a activa upload-ul direct.")
    elif not model_exista:
        st.warning("Modelul best.pt nu a fost gasit local.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MODEL CARD
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Model Card — documentatia modelului")

    st.info("""
    **Model Card** = documentul care descrie modelul AI: ce face, cum a fost antrenat,
    pe ce date, ce performante are. Standard obligatoriu pe Hugging Face.
    Reviewerii IEEE se uita la Model Card cand evalueza articolul.
    """)

    model_card = """---
language: ro
license: agpl-3.0
tags:
  - object-detection
  - yolov8
  - agriculture
  - drone
  - apia
  - lpis
  - romania
datasets:
  - custom (imagini drone LPIS Gorj, Romania)
metrics:
  - mAP50: 0.829
  - precision: 0.641
  - recall: 0.667
---

# AGROVISION YOLOv8n — Detectie Culturi Agricole din Imagini Drone

## Descriere

Model YOLOv8n antrenat pentru detectia si clasificarea vegetatiei agricole
din imagini drone, in contextul controalelor APIA (Agentia de Plati si
Interventie pentru Agricultura) din Romania.

**Autor:** Prof. Asoc. Dr. Oliviu Mihnea Gamulescu
**Institutie:** Universitatea "Constantin Brancusi" din Targu-Jiu,
Facultatea de Inginerie, Departamentul de Energie, Mediu si Agroturism
**Email:** oliviu.gamulescu@apia.org.ro
**Data antrenament:** 3 aprilie 2026

## Clase detectate

| ID | Clasa | Descriere |
|----|-------|-----------|
| 0 | vegetatie | Culturi agricole, pasuni, vegetatie verde |
| 1 | sol_gol | Teren necultivat, aratura, sol expus |
| 2 | apa | Surse de apa, irigare, umiditate |

## Performante

| Metrica | Valoare |
|---------|---------|
| mAP50 | **0.829** (82.9%) |
| mAP50-95 | 0.412 |
| Precision | 0.641 |
| Recall | 0.667 |
| F1 Score | 0.653 |

## Date antrenament

- **Imagini originale:** 7 fotografii drone, zona LPIS Gorj, Romania
- **Augmentare:** factor 7x (flip, rotatie, brightness, contrast, zgomot)
- **Total imagini:** 49 (train: 34 / val: 10 / test: 5)
- **Rezolutie:** 640x640 px (tiled din imagini 4608x3456 px)
- **Echipament:** Intel Core i7-7500U, 16GB RAM, CPU only
- **Durata antrenament:** ~45 minute, 50 epoch-uri

## Utilizare

```python
from ultralytics import YOLO
from huggingface_hub import hf_hub_download

# Descarca modelul
model_path = hf_hub_download(
    repo_id="oliviu-gamulescu/agrovision-yolov8",
    filename="best_v1_mAP083_20260403.pt"
)

# Incarca si ruleaza
model = YOLO(model_path)
results = model.predict("imagine_drone.jpg", conf=0.5)
```

## Contexte de utilizare

Destinat controlului conformitatii parcelelor agricole conform
Regulamentului UE 2021/2116 (PAC 2023-2027). Pragul de conformitate
vegetatie >= 50% din suprafata parcelei.

## Limitari

- Antrenat pe imagini din zona Gorj, Romania — performanta poate varia
  pentru alte zone geografice sau conditii de lumina diferite
- Dataset mic (7 imagini originale) — rezultatele sunt orientative
- Nu inlocuieste inspectia fizica pe teren

## Citare

```
@inproceedings{gamulescu2026agrovision,
  title={UAV-Assisted IoT Network for Precision Agriculture:
         Real-Time Crop Detection Using YOLOv8 for LPIS
         Compliance Monitoring in Romania},
  author={Gamulescu, Oliviu Mihnea},
  booktitle={IEEE FINE 2026},
  year={2026}
}
```
"""
    st.code(model_card, language="markdown")

    buf = model_card.encode("utf-8")
    st.download_button(
        "Descarca README.md (Model Card)",
        data=buf,
        file_name="README.md",
        mime="text/markdown"
    )
    st.caption("Incarca acest fisier README.md in repository-ul Hugging Face odata cu modelul.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — DOWNLOAD IN APLICATIE
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Download automat al modelului in aplicatie")

    st.markdown("""
    Aceasta functie inlocuieste incarcarea manuala a modelului.
    In loc de `YOLO("MODEL_ANTRENAT_BEST_PT/best.pt")`,
    aplicatia descarca singura modelul din Hugging Face la primul acces.
    """)

    st.markdown("#### Functia de incarcare inteligenta — copiaz-o in aplicatie:")

    cod_loader = '''import os
import streamlit as st
from ultralytics import YOLO
from huggingface_hub import hf_hub_download

@st.cache_resource
def incarca_model():
    """
    Incarca modelul YOLOv8:
    1. Incearca modelul local (rulare pe calculator)
    2. Daca nu exista, descarca din Hugging Face (Streamlit Cloud)
    """
    # Calea locala
    cale_locala = os.path.join(
        os.path.dirname(__file__),
        "MODEL_ANTRENAT_BEST_PT",
        "best_v1_mAP083_20260403.pt"
    )

    if os.path.exists(cale_locala):
        # Calculator local — folosim fisierul direct
        return YOLO(cale_locala), "local"

    # Streamlit Cloud — descarcam din Hugging Face
    try:
        token   = st.secrets["huggingface"]["token"]
        repo_id = st.secrets["huggingface"]["repo_id"]
        fisier  = st.secrets["huggingface"]["model"]

        cale_hf = hf_hub_download(
            repo_id=repo_id,
            filename=fisier,
            token=token       # necesar pentru repo privat
        )
        return YOLO(cale_hf), "huggingface"

    except Exception as e:
        st.warning(f"Modelul antrenat nu e disponibil: {e}")
        st.info("Se foloseste modelul implicit YOLOv8n (neantrenat pe culturi).")
        return YOLO("yolov8n.pt"), "default"


# Utilizare in orice pagina:
model, sursa = incarca_model()
st.caption(f"Model incarcat din: {sursa}")
'''
    st.code(cod_loader, language="python")

    st.markdown("#### Logica de fallback — 3 niveluri:")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style='background:#d4edda; border-radius:10px; padding:14px; text-align:center;'>
            <div style='font-size:24px;'>💻</div>
            <strong>Nivel 1</strong><br>
            <small>Calculator local</small><br>
            <small>best.pt exista pe disk</small><br>
            <small style='color:#28a745;'>Cel mai rapid</small>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style='background:#fff3cd; border-radius:10px; padding:14px; text-align:center;'>
            <div style='font-size:24px;'>🤗</div>
            <strong>Nivel 2</strong><br>
            <small>Hugging Face Hub</small><br>
            <small>Download automat</small><br>
            <small style='color:#856404;'>~30 sec prima oara</small>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style='background:#f8d7da; border-radius:10px; padding:14px; text-align:center;'>
            <div style='font-size:24px;'>⬇️</div>
            <strong>Nivel 3</strong><br>
            <small>YOLOv8n implicit</small><br>
            <small>COCO, neantrenat</small><br>
            <small style='color:#dc3545;'>Fallback sigur</small>
        </div>
        """, unsafe_allow_html=True)

    st.info("""
    **De ce @st.cache_resource?**
    Modelul se descarca/incarca O SINGURA DATA per sesiune Streamlit.
    Fara cache, la fiecare actiune a utilizatorului s-ar descarca din nou
    modelul de 6MB — aplicatia ar fi foarte lenta.
    """)

    st.divider()
    st.markdown("#### Testeaza descarcarea acum")

    hf_ok = False
    try:
        hf_cfg = st.secrets.get("huggingface", {})
        hf_token   = hf_cfg.get("token", "")
        hf_repo    = hf_cfg.get("repo_id", "")
        hf_model   = hf_cfg.get("model", "")
        hf_ok = bool(hf_token and hf_repo and hf_model)
    except Exception:
        hf_ok = False

    if not hf_ok:
        st.warning("secrets.toml nu contine sectiunea [huggingface]. Adauga token, repo_id si model.")
    else:
        st.success(f"secrets.toml OK — repo: `{hf_repo}` | model: `{hf_model}`")
        dest_dir = os.path.join(BASE_DIR, "modele")
        dest_path = os.path.join(dest_dir, hf_model)

        if os.path.exists(dest_path):
            marime = os.path.getsize(dest_path) / 1024 / 1024
            st.success(f"Modelul este deja descarcat local: `modele/{hf_model}` ({marime:.1f} MB)")
        else:
            if st.button("Descarca modelul din Hugging Face", type="primary",
                         use_container_width=True):
                try:
                    from huggingface_hub import hf_hub_download
                    os.makedirs(dest_dir, exist_ok=True)
                    with st.spinner("Se descarca modelul din Hugging Face... (30-60 sec)"):
                        cale_hf = hf_hub_download(
                            repo_id=hf_repo,
                            filename=hf_model,
                            token=hf_token,
                            local_dir=dest_dir
                        )
                    marime = os.path.getsize(cale_hf) / 1024 / 1024
                    st.success(f"Modelul descarcat cu succes! ({marime:.1f} MB)")
                    st.info(f"Salvat in: `{cale_hf}`")
                    st.balloons()
                except Exception as e:
                    st.error(f"Eroare la descarcare: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — INTEGRARE STREAMLIT CLOUD
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Deployment complet pe Streamlit Cloud cu model Hugging Face")

    st.success("""
    Dupa Ziua 25, AGROVISION merge complet pe Streamlit Cloud:
    - Codul pe GitHub (privat, fara model)
    - Modelul pe Hugging Face (privat, accesibil cu token)
    - Secrets in Streamlit Cloud Settings
    - Aplicatia descarca modelul automat la deploy
    """)

    st.markdown("#### Diagrama completa:")
    st.code("""
  CALCULATOR LOCAL                 CLOUD (gratuit)
  ─────────────────                ───────────────────────────────────────

  best.pt ────────────────────────→ Hugging Face Hub
  (model antrenat)    upload        oliviu-gamulescu/agrovision-yolov8
                      1x                    │
                                            │ hf_hub_download()
  cod Python ─────────────────────→ GitHub  │  (automat la pornire)
  (fara best.pt)      git push      privat  │
                                       │    │
                                       └────┼──→ Streamlit Cloud
                                            │    (deploy automat)
                                            │
                                   Token HF │ (in Secrets)
                                            ↓
                                   http://agrovision.streamlit.app
                                   (accesibil 24/7, de oriunde)
""", language="text")

    st.markdown("#### Checklist final deployment:")
    checklist = [
        ("Cont GitHub creat (olimihnea-spec)", True),
        ("Repo GitHub privat (agrovision-bloc3)", True),
        ("requirements.txt cu toate pachetele", True),
        (".gitignore — best.pt si secrets excluse", True),
        ("Cont Hugging Face creat", False),
        ("Repo HF privat (agrovision-yolov8) creat", False),
        ("best.pt urcat pe Hugging Face", False),
        ("HF token adaugat in secrets.toml", False),
        ("Streamlit Cloud conectat la GitHub", False),
        ("Secrets adaugate in Streamlit Cloud Settings", False),
        ("Test deployment — modelul se descarca automat", False),
    ]
    for item, ok in checklist:
        icon = "✅" if ok else "⬜"
        st.markdown(f"{icon} {item}")

    st.markdown("#### Adauga huggingface_hub in requirements.txt:")
    st.code("huggingface_hub==1.9.0", language="text")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — COD COMPLET
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Cod complet — upload si download model")

    with st.expander("Script upload_model_hf.py — ruleaza o singura data"):
        st.code("""\"\"\"
Script: upload_model_hf.py
Scop: Urca best.pt pe Hugging Face Hub (ruleaza o singura data)
Rulare: python upload_model_hf.py
\"\"\"
from huggingface_hub import HfApi
import os

# Configurare
HF_TOKEN   = "hf_TOKEN_TAU_AICI"     # din HF Settings > Access Tokens
REPO_ID    = "oliviu-gamulescu/agrovision-yolov8"
MODEL_PATH = "MODEL_ANTRENAT_BEST_PT/best_v1_mAP083_20260403.pt"
README_PATH = "README.md"

api = HfApi()

# Creeaza repo daca nu exista
api.create_repo(
    repo_id=REPO_ID,
    repo_type="model",
    private=True,          # repo PRIVAT
    exist_ok=True,         # nu arunca eroare daca exista deja
    token=HF_TOKEN
)
print(f"Repo: https://huggingface.co/{REPO_ID}")

# Urca modelul
print("Se incarca modelul...")
api.upload_file(
    path_or_fileobj=MODEL_PATH,
    path_in_repo=os.path.basename(MODEL_PATH),
    repo_id=REPO_ID,
    repo_type="model",
    token=HF_TOKEN
)
print(f"Model urcat: {os.path.basename(MODEL_PATH)}")

# Urca Model Card (README.md)
if os.path.exists(README_PATH):
    api.upload_file(
        path_or_fileobj=README_PATH,
        path_in_repo="README.md",
        repo_id=REPO_ID,
        repo_type="model",
        token=HF_TOKEN
    )
    print("Model Card (README.md) urcat.")

print("\\nGata! Modelul este disponibil pe Hugging Face.")
print(f"URL: https://huggingface.co/{REPO_ID}")
""", language="python")

    with st.expander("Functia incarca_model() — copiaz-o in Acasa.py sau utils.py"):
        st.code("""import os, streamlit as st
from ultralytics import YOLO
from huggingface_hub import hf_hub_download

@st.cache_resource
def incarca_model():
    cale_locala = os.path.join(
        os.path.dirname(__file__),
        "MODEL_ANTRENAT_BEST_PT",
        "best_v1_mAP083_20260403.pt"
    )
    if os.path.exists(cale_locala):
        return YOLO(cale_locala), "local"
    try:
        hf_cfg  = st.secrets["huggingface"]
        cale_hf = hf_hub_download(
            repo_id  = hf_cfg["repo_id"],
            filename = hf_cfg["model"],
            token    = hf_cfg["token"]
        )
        return YOLO(cale_hf), "huggingface"
    except Exception:
        return YOLO("yolov8n.pt"), "default"
""", language="python")

    st.markdown("""
    **Comparatie: inainte si dupa Ziua 25**

    | | Inainte (Zilele 1-24) | Dupa (Ziua 25+) |
    |-|-----------------------|-----------------|
    | Model | Doar local (best.pt) | Local + Hugging Face |
    | Streamlit Cloud | Model lipseste | Model descarcat automat |
    | GitHub | best.pt exclus | best.pt exclus (ramine asa) |
    | Acces | Doar calculator personal | Oricine cu linkul |
    """)

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center; color:#90a4ae; font-size:12px; padding:8px 0;'>
    AGROVISION &nbsp;|&nbsp; Ziua 25 — Hugging Face Hub &nbsp;|&nbsp;
    hf_hub_download | upload_file | Model Card | cache_resource
    &nbsp;|&nbsp; UCB Targu Jiu &nbsp;|&nbsp; APIA CJ Gorj
</div>
""", unsafe_allow_html=True)
