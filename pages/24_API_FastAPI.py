"""
BLOC 3 — Deep Learning YOLOv8, Ziua 24
API REST cu FastAPI — AGROVISION ca serviciu web
Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu | UCB Targu Jiu | APIA CJ Gorj

CONCEPT CHEIE:
  Pana acum, AGROVISION e o aplicatie Streamlit = interfata vizuala pentru oameni.
  Din Ziua 24: AGROVISION devine si un API = interfata pentru alte programe.

  API REST = Application Programming Interface
    - QGIS poate cere date de la AGROVISION automat
    - Excel/VBA poate rula o detectie si primi rezultatul ca JSON
    - Un alt script Python poate folosi modelul fara sa deschida browserul
    - APIA Central poate interoga toate parcelele judetului Gorj

  FastAPI vs Flask (Ziua 56 din cursul vechi):
    - FastAPI genereaza automat documentatie Swagger UI
    - Validare date cu Pydantic (clase Python simple)
    - Async nativ — mai rapid la cereri multiple
    - Standard modern: OpenAPI 3.0

  Cum functioneaza:
    Streamlit ruleaza pe portul 8501
    FastAPI ruleaza pe portul 8000
    Le pornesti in doua terminale separate.

  Metode HTTP:
    GET  = citeste date (lista parcele, statistici)
    POST = trimite date si primesti rezultat (detectie)
    PUT  = modifica date existente
    DELETE = sterge date
"""

import streamlit as st
import requests
import json
import subprocess
import sys
import os
import time

# ─── CONFIGURARE PAGINA ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="API FastAPI — AGROVISION",
    page_icon="⚡",
    layout="wide"
)

API_URL = "http://localhost:8000"

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.endpoint-box {
    border-radius: 8px;
    padding: 12px 16px;
    margin: 6px 0;
    font-family: monospace;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.method-get    { background:#d1ecf1; border-left:4px solid #0c5460; color:#0c5460; }
.method-post   { background:#d4edda; border-left:4px solid #155724; color:#155724; }
.badge-get  { background:#17a2b8; color:white; padding:2px 10px; border-radius:4px;
               font-weight:700; font-size:11px; }
.badge-post { background:#28a745; color:white; padding:2px 8px; border-radius:4px;
               font-weight:700; font-size:11px; }
.json-box {
    background: #1e1e1e;
    color: #9cdcfe;
    border-radius: 8px;
    padding: 14px 18px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    overflow-x: auto;
}
.status-online  { background:#d4edda; color:#155724; border-radius:6px;
                  padding:8px 16px; font-weight:700; }
.status-offline { background:#f8d7da; color:#721c24; border-radius:6px;
                  padding:8px 16px; font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ─── TITLU ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='display:flex; align-items:center; gap:16px; margin-bottom:8px;'>
    <div style='font-size:48px;'>⚡</div>
    <div>
        <h1 style='margin:0; font-size:28px; color:#0052A5;'>
            API REST cu FastAPI
        </h1>
        <p style='margin:0; color:#546e7a;'>
            AGROVISION ca serviciu web | GET/POST | JSON | Swagger UI
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── VERIFICARE STATUS API ────────────────────────────────────────────────────
def verifica_api() -> bool:
    try:
        r = requests.get(f"{API_URL}/", timeout=2)
        return r.status_code == 200
    except Exception:
        return False

api_activ = verifica_api()

col_s1, col_s2 = st.columns([2, 1])
with col_s1:
    if api_activ:
        st.markdown('<div class="status-online">✅ API ONLINE — http://localhost:8000</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-offline">❌ API OFFLINE — porneste serverul (vezi Tab 1)</div>',
                    unsafe_allow_html=True)
with col_s2:
    if st.button("Verifica status API", use_container_width=True):
        st.rerun()

st.divider()

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Pornire Server",
    "Endpoint-uri",
    "Testeaza API",
    "Cod Explicat",
    "Clienti API"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PORNIRE SERVER
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Cum pornesti serverul FastAPI")

    st.info("""
    **Streamlit si FastAPI ruleaza in acelasi timp, pe porturi diferite:**
    - Streamlit: `http://localhost:8501` (interfata vizuala)
    - FastAPI:   `http://localhost:8000` (API pentru programe)
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Terminal 1 — Streamlit (deja pornit)")
        st.code(
            'cd "G:\\CLAUDE CODE INSTRUIRE VOL II 90 ZILE STREAMLIT ISI YOLO'
            '\\Bloc3_YOLOv8\\yolo_app"\n'
            'python -m streamlit run Acasa.py',
            language="bash"
        )

        st.markdown("#### Terminal 2 — FastAPI (deschide unul nou)")
        st.code(
            'cd "G:\\CLAUDE CODE INSTRUIRE VOL II 90 ZILE STREAMLIT ISI YOLO'
            '\\Bloc3_YOLOv8\\yolo_app"\n'
            '"G:\\CLAUDE CODE INSTRUIRE\\.venv\\Scripts\\python.exe" '
            '-m uvicorn api:app --reload --port 8000',
            language="bash"
        )

    with col2:
        st.markdown("#### Sau foloseste fisierul .bat creat automat:")
        bat_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "porneste_api.bat"
        )
        bat_exista = os.path.exists(bat_path)
        if bat_exista:
            st.success(f"porneste_api.bat exista: `{bat_path}`")
        else:
            st.warning("porneste_api.bat nu exista inca — il cream mai jos")

        if st.button("Creeaza porneste_api.bat", use_container_width=True):
            continut_bat = (
                '@echo off\n'
                'title AGROVISION API Server\n'
                'cd /d "G:\\CLAUDE CODE INSTRUIRE VOL II 90 ZILE STREAMLIT ISI YOLO'
                '\\Bloc3_YOLOv8\\yolo_app"\n'
                '"G:\\CLAUDE CODE INSTRUIRE\\.venv\\Scripts\\python.exe" '
                '-m uvicorn api:app --reload --port 8000\n'
                'pause\n'
            )
            with open(bat_path, "w") as f:
                f.write(continut_bat)
            st.success("porneste_api.bat creat!")
            # Copiem pe stick
            stick_path = bat_path.replace(
                "G:\\CLAUDE CODE INSTRUIRE VOL II 90 ZILE STREAMLIT ISI YOLO",
                "I:\\CLAUDE CODE INSTRUIRE VOL II 90 ZILE STREAMLIT ISI YOLO"
            )
            try:
                import shutil
                shutil.copy(bat_path, stick_path)
            except Exception:
                pass

    st.divider()
    st.markdown("#### Dupa pornire — acceseaza:")
    st.markdown("""
    | URL | Ce vezi |
    |-----|---------|
    | `http://localhost:8000` | Raspuns JSON: status API |
    | `http://localhost:8000/docs` | **Swagger UI** — testezi toate endpoint-urile vizual |
    | `http://localhost:8000/redoc` | Documentatie alternativa ReDoc |
    | `http://localhost:8000/parcele` | Lista toate parcelele LPIS |
    | `http://localhost:8000/statistici` | KPI-uri din baza de date |
    """)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ENDPOINT-URI
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Endpoint-urile AGROVISION API")

    endpoints = [
        ("GET",  "/",                   "Status API — verifica daca serverul e activ"),
        ("GET",  "/parcele",            "Lista toate parcelele LPIS Gorj"),
        ("GET",  "/parcele/{cod_lpis}", "Detalii parcela dupa cod LPIS"),
        ("POST", "/detectie",           "Ruleaza detectie YOLOv8 pe o parcela"),
        ("GET",  "/detectie/batch",     "Detectie pe toate parcelele simultan"),
        ("GET",  "/sesiuni",            "Ultimele sesiuni din baza de date"),
        ("GET",  "/statistici",         "KPI-uri globale din baza de date"),
    ]

    for metoda, cale, desc in endpoints:
        badge = f'<span class="badge-get">GET</span>' if metoda == "GET" \
                else f'<span class="badge-post">POST</span>'
        cls = "method-get" if metoda == "GET" else "method-post"
        st.markdown(f"""
        <div class="endpoint-box {cls}">
            {badge}
            <strong style="min-width:260px;">{cale}</strong>
            <span style="color:#555; font-family:sans-serif;">{desc}</span>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("#### Exemplu raspuns JSON — `/parcele/GJ_78258-1675`")
    st.code("""{
    "cod": "GJ_78258-1675",
    "fermier": "Popescu Ion",
    "suprafata": 4.32,
    "cultura": "grau",
    "uat": "Targu Jiu",
    "lat": 45.0421,
    "lon": 23.2718
}""", language="json")

    st.markdown("#### Exemplu raspuns JSON — `POST /detectie`")
    st.code("""{
    "cod_lpis": "GJ_78258-1675",
    "fermier": "Popescu Ion",
    "suprafata": 4.32,
    "vegetatie": 38.4,
    "sol_gol": 42.1,
    "apa": 19.5,
    "confidenta": 0.891,
    "status": "NECONFORM",
    "prag_pac": 50.0,
    "data": "2026-04-05",
    "inspector": "Gamulescu O.M.",
    "mesaj": "ATENTIE: vegetatie 38.4% sub pragul PAC de 50%. Deficit: 11.6%."
}""", language="json")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — TESTEAZA API (live daca serverul e pornit)
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Testeaza API-ul live")

    if not api_activ:
        st.warning("API-ul nu este pornit. Deschide Terminal 2 si ruleaza uvicorn (vezi Tab 1).")

    st.markdown("#### GET /")
    if st.button("Testeaza GET /  (status)", use_container_width=False):
        try:
            r = requests.get(f"{API_URL}/", timeout=3)
            st.success(f"Status: {r.status_code}")
            st.json(r.json())
        except Exception as e:
            st.error(f"API offline: {e}")

    st.divider()
    st.markdown("#### GET /parcele")
    if st.button("Testeaza GET /parcele", use_container_width=False):
        try:
            r = requests.get(f"{API_URL}/parcele", timeout=3)
            st.success(f"Status: {r.status_code}")
            st.json(r.json())
        except Exception as e:
            st.error(f"API offline: {e}")

    st.divider()
    st.markdown("#### GET /parcele/{cod_lpis}")
    cod_test = st.selectbox("Alege parcela:", [
        "GJ_78258-1675", "GJ_78301-0892", "GJ_78445-2341",
        "GJ_78512-0077", "GJ_78634-1129"
    ])
    if st.button(f"Testeaza GET /parcele/{cod_test}"):
        try:
            r = requests.get(f"{API_URL}/parcele/{cod_test}", timeout=3)
            st.success(f"Status: {r.status_code}")
            st.json(r.json())
        except Exception as e:
            st.error(f"API offline: {e}")

    st.divider()
    st.markdown("#### POST /detectie")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        cod_det = st.selectbox("Parcela pentru detectie:", [
            "GJ_78258-1675", "GJ_78301-0892", "GJ_78512-0077",
            "GJ_79001-0445", "GJ_80980-2611"
        ], key="det_cod")
        insp_det = st.text_input("Inspector:", value="Gamulescu O.M.", key="det_insp")
        seed_det = st.number_input("Seed:", value=42, key="det_seed")
    with col_d2:
        st.markdown("**Body cerere (JSON):**")
        st.code(json.dumps({
            "cod_lpis":  cod_det,
            "inspector": insp_det,
            "seed":      seed_det
        }, indent=2), language="json")

    if st.button("Testeaza POST /detectie", type="primary"):
        try:
            r = requests.post(
                f"{API_URL}/detectie",
                json={"cod_lpis": cod_det, "inspector": insp_det, "seed": int(seed_det)},
                timeout=3
            )
            st.success(f"Status: {r.status_code}")
            rez = r.json()
            st.json(rez)
            if rez.get("status") == "NECONFORM":
                st.error(f"NECONFORM: {rez['mesaj']}")
            else:
                st.success(f"CONFORM: {rez['mesaj']}")
        except Exception as e:
            st.error(f"API offline: {e}")

    st.divider()
    st.markdown("#### GET /detectie/batch — toate parcelele")
    if st.button("Testeaza GET /detectie/batch"):
        try:
            r = requests.get(f"{API_URL}/detectie/batch?seed=42", timeout=5)
            st.success(f"Status: {r.status_code}")
            data = r.json()
            st.metric("Total", data["total"])
            col1, col2, col3 = st.columns(3)
            col1.metric("Conforme", data["conforme"])
            col2.metric("Neconforme", data["neconforme"])
            col3.metric("Rata conformitate", f"{data['rata_conformitate']}%")
            import pandas as pd
            st.dataframe(pd.DataFrame(data["rezultate"]), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"API offline: {e}")

    st.divider()
    st.markdown("#### GET /statistici")
    if st.button("Testeaza GET /statistici"):
        try:
            r = requests.get(f"{API_URL}/statistici", timeout=3)
            st.success(f"Status: {r.status_code}")
            st.json(r.json())
        except Exception as e:
            st.error(f"API offline: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — COD EXPLICAT
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Cum functioneaza codul FastAPI")

    with st.expander("1. Initializarea aplicatiei FastAPI", expanded=True):
        st.code("""from fastapi import FastAPI

app = FastAPI(
    title="AGROVISION API",
    description="API REST pentru detectie culturi | APIA CJ Gorj",
    version="1.0.0"
)""", language="python")
        st.markdown("""
        `FastAPI()` creeaza aplicatia. Parametrii `title`, `description`, `version`
        apar automat in documentatia Swagger UI la `/docs`.
        """)

    with st.expander("2. Endpoint GET simplu"):
        st.code("""@app.get("/parcele")
def get_toate_parcelele():
    return {"total": 10, "parcele": PARCELE_LPIS}""", language="python")
        st.markdown("""
        `@app.get("/parcele")` = decoratorul care leaga URL-ul `/parcele`
        de functia Python. La GET pe acel URL, FastAPI apeleaza functia
        si returneaza automat dictionarul ca JSON.
        """)

    with st.expander("3. Parametru in URL"):
        st.code("""@app.get("/parcele/{cod_lpis}")
def get_parcela(cod_lpis: str):
    parcela = PARCELE_INDEX.get(cod_lpis)
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela nu exista")
    return parcela""", language="python")
        st.markdown("""
        `{cod_lpis}` in URL = parametru dinamic. FastAPI il preia automat
        si il valideaza ca `str`. `HTTPException(404)` = raspuns standard
        cand resursa nu exista (ca pagina 404 in browser).
        """)

    with st.expander("4. Endpoint POST cu validare Pydantic"):
        st.code("""from pydantic import BaseModel

class CerereDetectie(BaseModel):
    cod_lpis:  str
    inspector: str = "AGROVISION"  # valoare implicita
    seed:      int = 42

@app.post("/detectie")
def ruleaza_detectie(cerere: CerereDetectie):
    # cerere.cod_lpis, cerere.inspector, cerere.seed
    # sunt validate automat de Pydantic
    ...
    return rezultat""", language="python")
        st.markdown("""
        **Pydantic** = validare automata date intrare. Daca clientul trimite
        `cod_lpis` ca numar (nu string), FastAPI returneaza automat eroare 422
        cu explicatia. Nu mai scriem `if` pentru validari manuale.
        """)

    with st.expander("5. Cum apelezi API-ul din Python (client)"):
        st.code("""import requests

# GET — lista parcele
r = requests.get("http://localhost:8000/parcele")
parcele = r.json()["parcele"]

# POST — detectie
r = requests.post("http://localhost:8000/detectie", json={
    "cod_lpis": "GJ_78258-1675",
    "inspector": "Gamulescu O.M.",
    "seed": 42
})
rezultat = r.json()
print(rezultat["status"])   # CONFORM sau NECONFORM
print(rezultat["vegetatie"]) # ex: 62.4
""", language="python")

    with st.expander("6. Cum apelezi API-ul din Excel/VBA"):
        st.code("""' VBA macro in Excel
Sub DetectieAGROVISION()
    Dim http As Object
    Set http = CreateObject("MSXML2.XMLHTTP")
    http.Open "POST", "http://localhost:8000/detectie", False
    http.setRequestHeader "Content-Type", "application/json"
    http.Send "{""cod_lpis"": ""GJ_78258-1675"", ""seed"": 42}"
    MsgBox http.responseText
End Sub""", language="vb")
        st.markdown("""
        Orice program care poate face cereri HTTP poate folosi API-ul:
        Excel/VBA, QGIS (Python console), Google Sheets (Apps Script), Postman, curl...
        """)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — CLIENTI API (exemple de integrare)
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Clienti API — cum integreaza alte sisteme AGROVISION")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### QGIS — Python Console")
        st.code("""import requests

# In QGIS Python Console (Plugins > Console)
r = requests.get("http://localhost:8000/parcele")
parcele = r.json()["parcele"]

# Creeaza layer puncte in QGIS
from qgis.core import (QgsVectorLayer,
    QgsFeature, QgsPointXY, QgsGeometry)

layer = QgsVectorLayer("Point?crs=EPSG:4326",
    "Parcele AGROVISION", "memory")
pr = layer.dataProvider()

for p in parcele:
    f = QgsFeature()
    f.setGeometry(QgsGeometry.fromPointXY(
        QgsPointXY(p["lon"], p["lat"])))
    pr.addFeature(f)

QgsProject.instance().addMapLayer(layer)
print(f"Adaugate {len(parcele)} parcele in QGIS!")
""", language="python")

        st.markdown("#### curl — linie de comanda")
        st.code("""# Status API
curl http://localhost:8000/

# Lista parcele
curl http://localhost:8000/parcele

# Detectie
curl -X POST http://localhost:8000/detectie \\
  -H "Content-Type: application/json" \\
  -d '{"cod_lpis": "GJ_78258-1675", "seed": 42}'

# Batch toate parcelele
curl http://localhost:8000/detectie/batch?seed=42
""", language="bash")

    with col2:
        st.markdown("#### Script Python autonom")
        st.code("""import requests
import pandas as pd
from datetime import date

# Detectie toate parcelele
r = requests.get(
    "http://localhost:8000/detectie/batch",
    params={"seed": 42, "inspector": "Inspector APIA"}
)
data = r.json()

# Salveaza in Excel
df = pd.DataFrame(data["rezultate"])
df.to_excel(
    f"Raport_AGROVISION_{date.today()}.xlsx",
    index=False
)
print(f"Conforme: {data['conforme']}/{data['total']}")
print(f"Raport salvat!")
""", language="python")

        st.markdown("#### Scenarii reale APIA")
        st.markdown("""
        | Scenariu | Client | Endpoint |
        |----------|--------|----------|
        | APIA Central interogheaza toate parcelele Gorj | Script Python automat | `GET /parcele` |
        | Inspector incarca imagine → detectie imediata | QGIS Plugin | `POST /detectie` |
        | Raport zilnic automat | Sarcina Windows Task Scheduler | `GET /detectie/batch` |
        | Statistici pentru teza doctorat | Jupyter Notebook | `GET /statistici` |
        | Alerta SMS/email neconformitate | Script serverless | `POST /detectie` |
        """)

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center; color:#90a4ae; font-size:12px; padding:8px 0;'>
    AGROVISION &nbsp;|&nbsp; Ziua 24 — API REST FastAPI &nbsp;|&nbsp;
    FastAPI 0.135 | uvicorn | Pydantic | GET/POST | JSON | Swagger UI
    &nbsp;|&nbsp; UCB Targu Jiu &nbsp;|&nbsp; APIA CJ Gorj
</div>
""", unsafe_allow_html=True)
