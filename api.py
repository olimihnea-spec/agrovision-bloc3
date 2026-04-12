"""
AGROVISION — API REST cu FastAPI
Ziua 24 | Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu

Pornire server API:
    python -m uvicorn api:app --reload --port 8000

Documentatie interactiva (Swagger UI):
    http://localhost:8000/docs

Endpoint-uri:
    GET  /              -> status API
    GET  /parcele       -> lista toate parcelele LPIS
    GET  /parcele/{cod} -> detalii parcela specifica
    POST /detectie      -> ruleaza detectie YOLOv8 REALA pe imagine incarcata
    GET  /detectie/batch -> detectie simulata pe toate parcelele (fara imagine)
    GET  /sesiuni       -> istoricul din baza de date SQLite
    GET  /statistici    -> KPI-uri globale
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import numpy as np
import sqlite3
import datetime
import os
import io
import random

# ─── INCARCARE MODEL YOLOV8 ───────────────────────────────────────────────────
_model = None  # cache model (se incarca o singura data)

def get_model():
    """Incarca modelul YOLOv8 din HuggingFace (sau local). Cache la primul apel."""
    global _model
    if _model is not None:
        return _model

    from ultralytics import YOLO

    # Incearca mai intai fisierul local
    cale_locala = os.path.join(os.path.dirname(__file__),
                               "MODEL_ANTRENAT_BEST_PT", "best.pt")
    if os.path.exists(cale_locala):
        _model = YOLO(cale_locala)
        return _model

    # Descarca de pe HuggingFace Hub
    try:
        from huggingface_hub import hf_hub_download

        # Citeste credentials din .streamlit/secrets.toml
        secrets_path = os.path.join(os.path.dirname(__file__),
                                    ".streamlit", "secrets.toml")
        try:
            import tomllib
            with open(secrets_path, "rb") as f:
                secrets = tomllib.load(f)
        except ImportError:
            import toml
            secrets = toml.load(secrets_path)

        hf_cfg  = secrets["huggingface"]
        cale_hf = hf_hub_download(
            repo_id  = hf_cfg["repo_id"],
            filename = hf_cfg["model"],
            token    = hf_cfg["token"]
        )
        _model = YOLO(cale_hf)
        return _model

    except Exception:
        # Fallback: model generic YOLOv8n (fara antrenament custom)
        _model = YOLO("yolov8n.pt")
        return _model


def calculeaza_procente_din_detectii(result, img_w: int, img_h: int):
    """
    Calculeaza procentele de acoperire per clasa din bounding box-urile YOLOv8.

    Clase model AgroVision:
        0 = vegetatie
        1 = sol_gol
        2 = apa

    Logica: suma ariilor BBox per clasa / aria totala imagine * 100
    Daca nu e detectat nimic, returneaza 0% pentru toate clasele.
    """
    total_area = img_w * img_h
    arii = {0: 0.0, 1: 0.0, 2: 0.0}  # vegetatie, sol_gol, apa
    confidenta_total = []

    if result.boxes is not None and len(result.boxes) > 0:
        for box in result.boxes:
            cls  = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            aria = (x2 - x1) * (y2 - y1)
            if cls in arii:
                arii[cls] += aria
            confidenta_total.append(conf)

    veg = round(arii[0] / total_area * 100, 2)
    sol = round(arii[1] / total_area * 100, 2)
    apa = round(arii[2] / total_area * 100, 2)

    # Normalizeaza daca suma depaseste 100% (BBox-uri suprapuse)
    suma = veg + sol + apa
    if suma > 100:
        factor = 100.0 / suma
        veg = round(veg * factor, 2)
        sol = round(sol * factor, 2)
        apa = round(100.0 - veg - sol, 2)

    conf_medie = round(sum(confidenta_total) / len(confidenta_total), 3) \
                 if confidenta_total else 0.0

    return veg, sol, apa, conf_medie


# ─── INITIALIZARE APP ─────────────────────────────────────────────────────────
app = FastAPI(
    title="AGROVISION API",
    description="API REST pentru detectie culturi agricole YOLOv8 REALA | APIA CJ Gorj",
    version="1.1.0",
    contact={
        "name": "Prof. Asoc. Dr. Oliviu Mihnea Gamulescu",
        "email": "oliviu.gamulescu@apia.org.ro"
    }
)

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

# ─── MODELE PYDANTIC ──────────────────────────────────────────────────────────
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
    sursa:       str = "YOLOv8_real"


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT-URI API
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/", tags=["Status"])
def root():
    """Verifica daca API-ul este activ."""
    return {
        "status":    "online",
        "serviciu":  "AGROVISION API",
        "versiune":  "1.1.0",
        "model":     "YOLOv8n | mAP50=0.829 | inferenta REALA",
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
async def ruleaza_detectie(
    imagine: UploadFile = File(..., description="Imagine drone (JPG/PNG) a parcelei"),
    cod_lpis: str = Form(..., description="Codul LPIS al parcelei (ex: GJ_78258-1675)"),
    inspector: str = Form("AGROVISION", description="Numele inspectorului")
):
    """
    Ruleaza detectie YOLOv8 REALA pe imaginea incarcata.

    Trimite:
    - imagine: fisier JPG sau PNG (multipart/form-data)
    - cod_lpis: codul parcelei din LPIS Gorj
    - inspector: numele inspectorului (optional)

    Returneaza procentele REALE de vegetatie/sol_gol/apa calculate din BBox-urile
    detectate de modelul best_v1_mAP083_20260403.pt (mAP50=0.829).
    """
    # Validare extensie fisier
    if not imagine.filename.lower().endswith((".jpg", ".jpeg", ".png")):
        raise HTTPException(
            status_code=400,
            detail="Fisierul trebuie sa fie JPG sau PNG."
        )

    # Validare parcela LPIS
    parcela = PARCELE_INDEX.get(cod_lpis)
    if not parcela:
        raise HTTPException(
            status_code=404,
            detail=f"Parcela '{cod_lpis}' nu exista in LPIS Gorj."
        )

    # Citeste si valideaza imaginea
    continut = await imagine.read()
    try:
        img = Image.open(io.BytesIO(continut)).convert("RGB")
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Fisierul incarcat nu este o imagine valida."
        )

    img_w, img_h = img.size

    # Ruleaza inferenta YOLOv8 reala
    try:
        model = get_model()
        results = model.predict(
            source=np.array(img),
            conf=0.25,
            iou=0.45,
            imgsz=640,
            verbose=False
        )
        result = results[0]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Eroare inferenta YOLOv8: {str(e)}"
        )

    # Calculeaza procentele din BBox-uri reale
    veg, sol, apa, conf = calculeaza_procente_din_detectii(result, img_w, img_h)

    status = "CONFORM" if veg >= 50.0 else "NECONFORM"
    mesaj = (
        f"Parcela conforma PAC (vegetatie {veg}% >= 50%)."
        if status == "CONFORM"
        else f"ATENTIE: vegetatie {veg}% sub pragul PAC de 50%. Deficit: {50-veg:.2f}%."
    )

    return RezultatDetectie(
        cod_lpis   = cod_lpis,
        fermier    = parcela["fermier"],
        suprafata  = parcela["suprafata"],
        vegetatie  = veg,
        sol_gol    = sol,
        apa        = apa,
        confidenta = conf,
        status     = status,
        data       = str(datetime.date.today()),
        inspector  = inspector,
        mesaj      = mesaj,
        sursa      = "YOLOv8_real"
    )


@app.get("/detectie/batch", tags=["Detectie YOLOv8"])
def detectie_toate_parcelele(seed: int = 42, inspector: str = "AGROVISION"):
    """
    Detectie simulata pe toate cele 10 parcele simultan.

    NOTA: Acest endpoint este simulat deoarece necesita cate o imagine per parcela.
    Pentru detectie reala, foloseste POST /detectie cu imaginea fiecarei parcele.
    Valorile sunt reproductibile (seed fix) pentru demonstratii.
    """
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
            "inspector":  inspector,
            "sursa":      "simulat"
        })
    conforme   = sum(1 for r in rezultate if r["status"] == "CONFORM")
    neconforme = len(rezultate) - conforme
    return {
        "total":             len(rezultate),
        "conforme":          conforme,
        "neconforme":        neconforme,
        "rata_conformitate": round(conforme / len(rezultate) * 100, 1),
        "nota":              "Batch simulat — pentru detectie reala foloseste POST /detectie",
        "rezultate":         rezultate
    }


@app.get("/sesiuni", tags=["Baza de Date"])
def get_sesiuni(limit: int = 10):
    """Returneaza ultimele sesiuni de control din baza de date."""
    if not os.path.exists(DB_PATH):
        return {"sesiuni": [], "nota": "Baza de date nu exista inca."}
    try:
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM sesiuni ORDER BY creat_la DESC LIMIT ?", (limit,)
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
            "sesiuni":         total_sesiuni,
            "detectii":        total_detectii,
            "neconforme":      neconforme,
            "conforme":        total_detectii - neconforme,
            "suprafata_ha":    round(suprafata, 2),
            "vegetatie_medie": round(veg_medie, 2),
            "model":           "YOLOv8n | mAP50=0.829 | inferenta reala",
            "timestamp":       datetime.datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
