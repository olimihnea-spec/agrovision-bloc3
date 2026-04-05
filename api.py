"""
AGROVISION — API REST cu FastAPI
Ziua 24 | Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu

Pornire server API:
    python -m uvicorn api:app --reload --port 8000

Documentatie interactiva (Swagger UI):
    http://localhost:8000/docs

Utilizare:
    GET  /              → status API
    GET  /parcele       → lista toate parcelele LPIS
    GET  /parcele/{cod} → detalii parcela specifica
    POST /detectie      → ruleaza detectie pe o parcela
    GET  /sesiuni       → istoricul din baza de date SQLite
    GET  /statistici    → KPI-uri globale
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import random
import datetime
import os

# ─── INITIALIZARE APP ─────────────────────────────────────────────────────────
app = FastAPI(
    title="AGROVISION API",
    description="API REST pentru detectie culturi agricole YOLOv8 | APIA CJ Gorj",
    version="1.0.0",
    contact={
        "name": "Prof. Asoc. Dr. Oliviu Mihnea Gamulescu",
        "email": "oliviu.gamulescu@apia.org.ro"
    }
)

# CORS — permite cereri din Streamlit (localhost:8501) si din browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── BAZA DE DATE ─────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "agrovision_detectii.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ─── DATE LPIS ────────────────────────────────────────────────────────────────
PARCELE_LPIS = [
    {"cod": "GJ_78258-1675", "fermier": "Popescu Ion",      "suprafata": 4.32,
     "cultura": "grau",    "uat": "Targu Jiu",    "lat": 45.0421, "lon": 23.2718},
    {"cod": "GJ_78301-0892", "fermier": "Ionescu Maria",    "suprafata": 6.78,
     "cultura": "porumb",  "uat": "Rovinari",     "lat": 44.9183, "lon": 23.1645},
    {"cod": "GJ_78445-2341", "fermier": "Dumitrescu Gh.",   "suprafata": 3.15,
     "cultura": "rapita",  "uat": "Motru",        "lat": 44.8067, "lon": 22.9876},
    {"cod": "GJ_78512-0077", "fermier": "Stanescu Petre",   "suprafata": 8.90,
     "cultura": "grau",    "uat": "Bumbesti-Jiu", "lat": 45.1823, "lon": 23.3912},
    {"cod": "GJ_78634-1129", "fermier": "Olteanu Vasile",   "suprafata": 2.44,
     "cultura": "porumb",  "uat": "Novaci",       "lat": 45.3012, "lon": 23.6734},
    {"cod": "GJ_78720-3388", "fermier": "Marinescu Ana",    "suprafata": 5.67,
     "cultura": "floarea", "uat": "Targu Jiu",    "lat": 45.0198, "lon": 23.2456},
    {"cod": "GJ_79001-0445", "fermier": "Petrescu Dan",     "suprafata": 7.23,
     "cultura": "grau",    "uat": "Turceni",      "lat": 44.8734, "lon": 23.4012},
    {"cod": "GJ_79234-1876", "fermier": "Constantin Gh.",   "suprafata": 1.98,
     "cultura": "pasune",  "uat": "Aninoasa",     "lat": 45.0867, "lon": 23.5219},
    {"cod": "GJ_79567-2290", "fermier": "Florescu Elena",   "suprafata": 9.45,
     "cultura": "porumb",  "uat": "Rovinari",     "lat": 44.9045, "lon": 23.1823},
    {"cod": "GJ_80980-2611", "fermier": "Draghici Marin",   "suprafata": 6.64,
     "cultura": "grau",    "uat": "Targu Jiu",    "lat": 45.0534, "lon": 23.2901},
]

PARCELE_INDEX = {p["cod"]: p for p in PARCELE_LPIS}

# ─── MODELE PYDANTIC (validare date intrare/iesire) ───────────────────────────
class CerereDetectie(BaseModel):
    cod_lpis:  str
    inspector: str = "AGROVISION"
    seed:      int = 42

class RezultatDetectie(BaseModel):
    cod_lpis:    str
    fermier:     str
    suprafata:   float
    vegetatie:   float
    sol_gol:     float
    apa:         float
    confidenta:  float
    status:      str
    prag_pac:    float = 50.0
    data:        str
    inspector:   str
    mesaj:       str


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT-URI API
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/", tags=["Status"])
def root():
    """Verifica daca API-ul este activ."""
    return {
        "status":    "online",
        "serviciu":  "AGROVISION API",
        "versiune":  "1.0.0",
        "model":     "YOLOv8n | mAP50=0.829",
        "timestamp": datetime.datetime.now().isoformat(),
        "docs":      "http://localhost:8000/docs"
    }


@app.get("/parcele", tags=["Parcele LPIS"])
def get_toate_parcelele():
    """Returneaza lista completa a parcelelor LPIS Gorj."""
    return {
        "total":   len(PARCELE_LPIS),
        "judet":   "Gorj",
        "parcele": PARCELE_LPIS
    }


@app.get("/parcele/{cod_lpis}", tags=["Parcele LPIS"])
def get_parcela(cod_lpis: str):
    """Returneaza detaliile unei parcele dupa codul LPIS."""
    parcela = PARCELE_INDEX.get(cod_lpis)
    if not parcela:
        raise HTTPException(
            status_code=404,
            detail=f"Parcela '{cod_lpis}' nu a fost gasita in LPIS Gorj."
        )
    return parcela


@app.post("/detectie", response_model=RezultatDetectie, tags=["Detectie YOLOv8"])
def ruleaza_detectie(cerere: CerereDetectie):
    """
    Ruleaza detectie YOLOv8 pe o parcela specificata.
    Returneaza procentele de vegetatie, sol gol, apa si statusul PAC.
    """
    parcela = PARCELE_INDEX.get(cerere.cod_lpis)
    if not parcela:
        raise HTTPException(
            status_code=404,
            detail=f"Parcela '{cerere.cod_lpis}' nu exista."
        )

    # Simulare detectie YOLOv8 (seed reproductibil)
    rng = random.Random(cerere.seed)
    veg  = round(rng.uniform(25, 85), 2)
    sol  = round(rng.uniform(5, 35), 2)
    apa  = round(max(0, 100 - veg - sol), 2)
    conf = round(rng.uniform(0.72, 0.97), 3)
    status = "CONFORM" if veg >= 50.0 else "NECONFORM"
    mesaj = (
        f"Parcela conforma PAC (vegetatie {veg}% >= 50%)."
        if status == "CONFORM"
        else f"ATENTIE: vegetatie {veg}% sub pragul PAC de 50%. Deficit: {50-veg:.2f}%."
    )

    return RezultatDetectie(
        cod_lpis=cerere.cod_lpis,
        fermier=parcela["fermier"],
        suprafata=parcela["suprafata"],
        vegetatie=veg,
        sol_gol=sol,
        apa=apa,
        confidenta=conf,
        status=status,
        data=str(datetime.date.today()),
        inspector=cerere.inspector,
        mesaj=mesaj
    )


@app.get("/detectie/batch", tags=["Detectie YOLOv8"])
def detectie_toate_parcelele(seed: int = 42, inspector: str = "AGROVISION"):
    """Ruleaza detectie pe toate cele 10 parcele simultan."""
    rezultate = []
    rng = random.Random(seed)
    for p in PARCELE_LPIS:
        veg  = round(rng.uniform(25, 85), 2)
        sol  = round(rng.uniform(5, 35), 2)
        apa  = round(max(0, 100 - veg - sol), 2)
        conf = round(rng.uniform(0.72, 0.97), 3)
        rezultate.append({
            "cod_lpis":   p["cod"],
            "fermier":    p["fermier"],
            "suprafata":  p["suprafata"],
            "vegetatie":  veg,
            "sol_gol":    sol,
            "apa":        apa,
            "confidenta": conf,
            "status":     "CONFORM" if veg >= 50 else "NECONFORM",
            "data":       str(datetime.date.today()),
            "inspector":  inspector
        })
    conforme   = sum(1 for r in rezultate if r["status"] == "CONFORM")
    neconforme = len(rezultate) - conforme
    return {
        "total":      len(rezultate),
        "conforme":   conforme,
        "neconforme": neconforme,
        "rata_conformitate": round(conforme / len(rezultate) * 100, 1),
        "rezultate":  rezultate
    }


@app.get("/sesiuni", tags=["Baza de Date"])
def get_sesiuni(limit: int = 10):
    """Returneaza ultimele sesiuni de control din baza de date."""
    if not os.path.exists(DB_PATH):
        return {"sesiuni": [], "nota": "Baza de date nu exista inca."}
    try:
        conn = get_db()
        rows = conn.execute(
            f"SELECT * FROM sesiuni ORDER BY creat_la DESC LIMIT {limit}"
        ).fetchall()
        conn.close()
        return {"total": len(rows), "sesiuni": [dict(r) for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/statistici", tags=["Baza de Date"])
def get_statistici():
    """Returneaza statistici globale din baza de date."""
    if not os.path.exists(DB_PATH):
        return {"nota": "Baza de date nu exista inca."}
    try:
        conn = get_db()
        total_sesiuni  = conn.execute("SELECT COUNT(*) FROM sesiuni").fetchone()[0]
        total_detectii = conn.execute("SELECT COUNT(*) FROM detectii").fetchone()[0]
        neconforme     = conn.execute(
            "SELECT COUNT(*) FROM detectii WHERE status='NECONFORM'").fetchone()[0]
        suprafata      = conn.execute(
            "SELECT SUM(suprafata) FROM detectii").fetchone()[0] or 0
        veg_medie      = conn.execute(
            "SELECT AVG(vegetatie) FROM detectii").fetchone()[0] or 0
        conn.close()
        return {
            "sesiuni":          total_sesiuni,
            "detectii":         total_detectii,
            "neconforme":       neconforme,
            "conforme":         total_detectii - neconforme,
            "suprafata_ha":     round(suprafata, 2),
            "vegetatie_medie":  round(veg_medie, 2),
            "model":            "YOLOv8n | mAP50=0.829",
            "timestamp":        datetime.datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
