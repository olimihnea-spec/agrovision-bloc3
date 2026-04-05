"""
BLOC 3 — Deep Learning YOLOv8, Ziua 19
Autentificare + Roluri: inspector / admin / viewer
Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu | UCB Targu Jiu | APIA CJ Gorj

CONCEPT CHEIE:
  Autentificarea cu roluri = mecanism prin care sistemul stie CINE acceseaza
  si CE are voie sa faca. Fara autentificare, orice inspector ar putea sterge
  date sau modifica configuratia sistemului.

  3 roluri in AGROVISION:
    - viewer   → citeste rapoarte, vede harta (APIA Central, Prefectura)
    - inspector → incarca imagini, ruleaza detectii, exporta date (Inspector APIA)
    - admin    → toate drepturile + gestioneaza utilizatorii + setari sistem

  Tehnic Streamlit:
    - st.session_state["utilizator"] = {username, rol, prenume}
    - Toate paginile verifica session_state la incarcare
    - Logout = stergere cheie din session_state + st.rerun()
    - Parolele sunt hashuite cu hashlib.sha256 (nu in clear text)

  De ce roluri in aplicatii APIA:
    - Reg. UE 2021/2116 art. 68: separarea functiilor de control
    - Inspector nu poate modifica datele altui inspector
    - Auditabilitate: stim cine a facut ce si cand
"""

import streamlit as st
import hashlib
import datetime
import json
import os

# ─── CONFIGURARE PAGINA ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Autentificare AGROVISION",
    page_icon="🔐",
    layout="wide"
)

# ─── BAZA DE DATE UTILIZATORI (simulata in memorie) ──────────────────────────
# In productie: PostgreSQL / SQLite / Azure AD
# Parola hashata cu SHA-256 pentru securitate

def hash_parola(parola: str) -> str:
    """Hashueaza parola cu SHA-256."""
    return hashlib.sha256(parola.encode("utf-8")).hexdigest()

UTILIZATORI = {
    "admin": {
        "hash": hash_parola("admin2026"),
        "rol": "admin",
        "prenume": "Administrator",
        "email": "admin@agrovision.ro",
        "institutie": "UCB Targu Jiu",
        "activ": True,
        "creat": "2026-01-01"
    },
    "inspector1": {
        "hash": hash_parola("insp2026"),
        "rol": "inspector",
        "prenume": "Ion Popescu",
        "email": "ion.popescu@apia.org.ro",
        "institutie": "APIA CJ Gorj",
        "activ": True,
        "creat": "2026-02-15"
    },
    "inspector2": {
        "hash": hash_parola("insp9999"),
        "rol": "inspector",
        "prenume": "Maria Ionescu",
        "email": "maria.ionescu@apia.org.ro",
        "institutie": "APIA CJ Gorj",
        "activ": True,
        "creat": "2026-03-01"
    },
    "viewer1": {
        "hash": hash_parola("view2026"),
        "rol": "viewer",
        "prenume": "Prefectura Gorj",
        "email": "secretariat@prefecturagorj.ro",
        "institutie": "Prefectura Gorj",
        "activ": True,
        "creat": "2026-03-10"
    },
    "viewer2": {
        "hash": hash_parola("apia_central"),
        "rol": "viewer",
        "prenume": "APIA Central",
        "email": "central@apia.org.ro",
        "institutie": "APIA Central Bucuresti",
        "activ": True,
        "creat": "2026-03-20"
    }
}

# ─── PERMISIUNI PE ROL ───────────────────────────────────────────────────────
PERMISIUNI = {
    "viewer": {
        "poate_vedea_dashboard": True,
        "poate_vedea_harta": True,
        "poate_vedea_rapoarte": True,
        "poate_incarca_imagini": False,
        "poate_rula_detectie": False,
        "poate_exporta_date": False,
        "poate_gestiona_utilizatori": False,
        "poate_modifica_setari": False,
        "poate_sterge_date": False,
        "descriere": "Acces doar citire — rapoarte si harta"
    },
    "inspector": {
        "poate_vedea_dashboard": True,
        "poate_vedea_harta": True,
        "poate_vedea_rapoarte": True,
        "poate_incarca_imagini": True,
        "poate_rula_detectie": True,
        "poate_exporta_date": True,
        "poate_gestiona_utilizatori": False,
        "poate_modifica_setari": False,
        "poate_sterge_date": False,
        "descriere": "Acces complet detectie — fara administrare"
    },
    "admin": {
        "poate_vedea_dashboard": True,
        "poate_vedea_harta": True,
        "poate_vedea_rapoarte": True,
        "poate_incarca_imagini": True,
        "poate_rula_detectie": True,
        "poate_exporta_date": True,
        "poate_gestiona_utilizatori": True,
        "poate_modifica_setari": True,
        "poate_sterge_date": True,
        "descriere": "Acces complet — toate drepturile"
    }
}

# ─── JURNAL ACTIUNI (session log) ────────────────────────────────────────────
if "jurnal_actiuni" not in st.session_state:
    st.session_state["jurnal_actiuni"] = []

def logeaza_actiune(actiune: str, detalii: str = ""):
    """Adauga o intrare in jurnalul de actiuni al sesiunii."""
    utilizator = st.session_state.get("utilizator", {})
    intrare = {
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "utilizator": utilizator.get("username", "anonim"),
        "rol": utilizator.get("rol", "-"),
        "actiune": actiune,
        "detalii": detalii
    }
    st.session_state["jurnal_actiuni"].append(intrare)

# ─── FUNCTII AUTENTIFICARE ───────────────────────────────────────────────────
def autentifica(username: str, parola: str) -> bool:
    """Verifica credentialele si seteaza sesiunea."""
    username = username.strip().lower()
    if username not in UTILIZATORI:
        return False
    user_data = UTILIZATORI[username]
    if not user_data["activ"]:
        return False
    if user_data["hash"] != hash_parola(parola):
        return False
    # Succes — salveaza in session_state
    st.session_state["utilizator"] = {
        "username": username,
        "rol": user_data["rol"],
        "prenume": user_data["prenume"],
        "email": user_data["email"],
        "institutie": user_data["institutie"],
        "login_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    logeaza_actiune("LOGIN", f"Autentificare reusita din pagina 19")
    return True

def deconecteaza():
    """Sterge sesiunea si reporneste pagina."""
    username = st.session_state.get("utilizator", {}).get("username", "?")
    logeaza_actiune("LOGOUT", f"Deconectare voluntara")
    if "utilizator" in st.session_state:
        del st.session_state["utilizator"]
    st.rerun()

def are_permisiune(permisiune: str) -> bool:
    """Verifica daca utilizatorul curent are o anumita permisiune."""
    utilizator = st.session_state.get("utilizator")
    if not utilizator:
        return False
    rol = utilizator.get("rol", "viewer")
    return PERMISIUNI.get(rol, {}).get(permisiune, False)

def verifica_autentificare() -> bool:
    """Returneaza True daca utilizatorul este logat."""
    return "utilizator" in st.session_state

# ─── CULORI PE ROL ───────────────────────────────────────────────────────────
CULORI_ROL = {
    "admin":     {"bg": "#dc3545", "text": "white",  "icon": "ADMIN"},
    "inspector": {"bg": "#0d6efd", "text": "white",  "icon": "INSP"},
    "viewer":    {"bg": "#6c757d", "text": "white",  "icon": "VIEW"}
}

# ─── CSS PERSONALIZAT ─────────────────────────────────────────────────────────
st.markdown("""
<style>
.login-box {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 16px;
    padding: 40px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.4);
    max-width: 460px;
    margin: 0 auto;
}
.login-title {
    color: #e0e0e0;
    font-size: 28px;
    font-weight: 700;
    text-align: center;
    margin-bottom: 8px;
    letter-spacing: 2px;
}
.login-subtitle {
    color: #90a4ae;
    font-size: 14px;
    text-align: center;
    margin-bottom: 32px;
}
.badge-rol {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
}
.card-permisiune {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 4px 0;
    border-left: 4px solid #dee2e6;
}
.card-permisiune.activa {
    background: #d4edda;
    border-left-color: #28a745;
}
.card-permisiune.inactiva {
    background: #f8d7da;
    border-left-color: #dc3545;
}
.user-card {
    background: white;
    border-radius: 12px;
    padding: 16px;
    margin: 8px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border-left: 5px solid #dee2e6;
}
.jurnal-row {
    font-family: 'Courier New', monospace;
    font-size: 12px;
    padding: 4px 8px;
    background: #f8f9fa;
    border-radius: 4px;
    margin: 2px 0;
}
.demo-credentials {
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 8px;
    padding: 12px 16px;
    margin-top: 16px;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTIUNEA A — FORMULAR LOGIN (daca nu e autentificat)
# ═══════════════════════════════════════════════════════════════════════════════

if not verifica_autentificare():

    st.markdown("""
    <div style='text-align:center; padding: 20px 0 10px 0;'>
        <div style='font-size:64px;'>🌾</div>
        <h1 style='color:#1a1a2e; font-size:32px; font-weight:800; letter-spacing:3px;'>
            AGROVISION
        </h1>
        <p style='color:#546e7a; font-size:16px;'>
            Sistem AI de Monitorizare Agricola | APIA CJ Gorj
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:
        with st.form("form_login", clear_on_submit=False):
            st.markdown("""
            <div style='text-align:center; margin-bottom:24px;'>
                <div style='font-size:36px;'>🔐</div>
                <p style='color:#37474f; font-weight:600; font-size:18px; margin:4px 0;'>
                    Autentificare
                </p>
                <p style='color:#90a4ae; font-size:13px;'>
                    Introduceți credentialele de acces
                </p>
            </div>
            """, unsafe_allow_html=True)

            username = st.text_input(
                "Utilizator",
                placeholder="ex: inspector1",
                help="Numele de utilizator primit de la administrator"
            )
            parola = st.text_input(
                "Parola",
                type="password",
                placeholder="••••••••",
                help="Parola contului dvs."
            )

            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                btn_login = st.form_submit_button(
                    "Autentificare",
                    use_container_width=True,
                    type="primary"
                )
            with col_btn2:
                btn_demo = st.form_submit_button(
                    "Demo Rapid",
                    use_container_width=True
                )

            if btn_login:
                if not username or not parola:
                    st.error("Completati utilizatorul si parola.")
                elif autentifica(username, parola):
                    st.success(f"Bun venit, {st.session_state['utilizator']['prenume']}!")
                    st.rerun()
                else:
                    st.error("Credentiale incorecte sau cont inactiv.")

            if btn_demo:
                autentifica("inspector1", "insp2026")
                st.rerun()

    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# SECTIUNEA B — INTERFATA POST-LOGIN
# ═══════════════════════════════════════════════════════════════════════════════

utilizator = st.session_state["utilizator"]
rol = utilizator["rol"]
culoare = CULORI_ROL[rol]
permisiuni = PERMISIUNI[rol]

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='background:{culoare["bg"]}; color:{culoare["text"]};
                border-radius:10px; padding:14px; margin-bottom:16px; text-align:center;'>
        <div style='font-size:36px;'>
            {"👤" if rol == "viewer" else "🔍" if rol == "inspector" else "⚙️"}
        </div>
        <div style='font-size:16px; font-weight:700; margin:4px 0;'>
            {utilizator["prenume"]}
        </div>
        <div style='font-size:11px; opacity:0.85;'>
            {utilizator["institutie"]}
        </div>
        <div style='display:inline-block; background:rgba(255,255,255,0.25);
                    border-radius:12px; padding:2px 12px; font-size:11px;
                    font-weight:700; margin-top:6px; letter-spacing:1px;'>
            {rol.upper()}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"**Login:** {utilizator['login_time']}")
    st.markdown(f"**User:** `{utilizator['username']}`")

    st.divider()
    st.markdown("**Navigare:**")

    # Meniu bazat pe rol
    meniu_optiuni = ["Profilul Meu", "Permisiunile Mele"]
    if permisiuni["poate_vedea_dashboard"]:
        meniu_optiuni.insert(0, "Dashboard")
    if permisiuni["poate_rula_detectie"]:
        meniu_optiuni.append("Simulare Detectie")
    if permisiuni["poate_gestiona_utilizatori"]:
        meniu_optiuni.append("Gestionare Utilizatori")
    if permisiuni["poate_modifica_setari"]:
        meniu_optiuni.append("Setari Sistem")
    meniu_optiuni.append("Jurnal Actiuni")

    sectiune_activa = st.radio(
        "Sectiune",
        meniu_optiuni,
        label_visibility="collapsed"
    )

    st.divider()
    if st.button("Deconectare", use_container_width=True, type="secondary"):
        deconecteaza()

# ── TITLU PRINCIPAL ──────────────────────────────────────────────────────────
st.markdown(f"""
<div style='display:flex; align-items:center; gap:16px; margin-bottom:24px;'>
    <div style='font-size:40px;'>🌾</div>
    <div>
        <h1 style='margin:0; font-size:28px; color:#1a1a2e;'>
            AGROVISION — Panou Utilizator
        </h1>
        <p style='margin:0; color:#546e7a; font-size:14px;'>
            {utilizator["prenume"]} &nbsp;•&nbsp; {utilizator["institutie"]}
            &nbsp;•&nbsp; Rol: <strong>{rol.upper()}</strong>
        </p>
    </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTIUNEA 1 — DASHBOARD (accesibil tuturor)
# ═══════════════════════════════════════════════════════════════════════════════

if sectiune_activa == "Dashboard":
    logeaza_actiune("ACCES_PAGINA", "Dashboard principal")
    st.subheader("Dashboard Principal")

    # KPI-uri accesibile conform rol
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Parcele monitorizate", "10", "LPIS Gorj")
    c2.metric("Conforme", "7", "70%")
    c3.metric("Neconforme", "3", "-30%")
    c4.metric("Suprafata totala", "48.6 ha", "sesiune curenta")

    st.info(f"""
    **Rol {rol.upper()}** — {permisiuni['descriere']}
    Puteti naviga la sectiunile disponibile din meniul lateral stang.
    """)

    if not permisiuni["poate_incarca_imagini"]:
        st.warning(
            "Nu aveti permisiunea de a incarca imagini sau rula detectii. "
            "Contactati administratorul pentru acces extins."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTIUNEA 2 — PROFILUL MEU
# ═══════════════════════════════════════════════════════════════════════════════

elif sectiune_activa == "Profilul Meu":
    logeaza_actiune("ACCES_PAGINA", "Profil utilizator")
    st.subheader("Profilul Meu")

    col1, col2 = st.columns([1, 2])

    with col1:
        avatar_culoare = culoare["bg"]
        initiala = utilizator["prenume"][0].upper()
        st.markdown(f"""
        <div style='background:{avatar_culoare}; width:100px; height:100px;
                    border-radius:50%; display:flex; align-items:center;
                    justify-content:center; font-size:42px; color:white;
                    font-weight:700; margin:0 auto 16px auto; text-align:center;'>
            {initiala}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"**Utilizator:** `{utilizator['username']}`")
        st.markdown(f"**Prenume / Institutie:** {utilizator['prenume']} — {utilizator['institutie']}")
        st.markdown(f"**Email:** {utilizator['email']}")
        st.markdown(f"""
        **Rol:** <span style='background:{culoare["bg"]}; color:{culoare["text"]};
        padding:3px 12px; border-radius:12px; font-size:12px; font-weight:700;'>
        {rol.upper()}</span>
        """, unsafe_allow_html=True)
        st.markdown(f"**Autentificat la:** {utilizator['login_time']}")

    st.divider()
    st.subheader("Schimbare Parola (simulare)")
    with st.form("form_schimba_parola"):
        parola_veche  = st.text_input("Parola actuala", type="password")
        parola_noua1  = st.text_input("Parola noua", type="password")
        parola_noua2  = st.text_input("Confirma parola noua", type="password")
        if st.form_submit_button("Actualizeaza Parola", type="primary"):
            if not parola_veche or not parola_noua1:
                st.error("Completati toate campurile.")
            elif parola_noua1 != parola_noua2:
                st.error("Parolele noi nu coincid.")
            elif len(parola_noua1) < 8:
                st.error("Parola trebuie sa aiba minim 8 caractere.")
            else:
                u = UTILIZATORI.get(utilizator["username"])
                if u and u["hash"] == hash_parola(parola_veche):
                    # In productie: UPDATE in baza de date
                    logeaza_actiune("SCHIMBARE_PAROLA", "Simulare reusita")
                    st.success("Parola actualizata cu succes! (simulare)")
                else:
                    st.error("Parola actuala este incorecta.")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTIUNEA 3 — PERMISIUNILE MELE
# ═══════════════════════════════════════════════════════════════════════════════

elif sectiune_activa == "Permisiunile Mele":
    logeaza_actiune("ACCES_PAGINA", "Vizualizare permisiuni")
    st.subheader(f"Permisiunile Rolului: {rol.upper()}")

    ETICHETE = {
        "poate_vedea_dashboard":        "Vizualizare Dashboard",
        "poate_vedea_harta":            "Vizualizare Harta GIS",
        "poate_vedea_rapoarte":         "Vizualizare Rapoarte",
        "poate_incarca_imagini":        "Incarcare Imagini Drone",
        "poate_rula_detectie":          "Rulare Detectie YOLOv8",
        "poate_exporta_date":           "Export GIS (GeoJSON/SHP/GPX)",
        "poate_gestiona_utilizatori":   "Gestionare Utilizatori",
        "poate_modifica_setari":        "Modificare Setari Sistem",
        "poate_sterge_date":            "Stergere Date"
    }

    ICONITE = {
        "poate_vedea_dashboard":        "📊",
        "poate_vedea_harta":            "🗺️",
        "poate_vedea_rapoarte":         "📄",
        "poate_incarca_imagini":        "📤",
        "poate_rula_detectie":          "🤖",
        "poate_exporta_date":           "💾",
        "poate_gestiona_utilizatori":   "👥",
        "poate_modifica_setari":        "⚙️",
        "poate_sterge_date":            "🗑️"
    }

    col1, col2 = st.columns(2)
    items = list(ETICHETE.items())
    jumatate = len(items) // 2

    for idx, (cheie, eticheta) in enumerate(items):
        col = col1 if idx < jumatate + 1 else col2
        are = permisiuni.get(cheie, False)
        icon_stare = "✅" if are else "❌"
        stil = "activa" if are else "inactiva"
        with col:
            st.markdown(f"""
            <div class="card-permisiune {stil}">
                {ICONITE[cheie]} &nbsp; <strong>{eticheta}</strong>
                &nbsp;&nbsp; {icon_stare}
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.markdown("**Comparatie roluri:**")
    import pandas as pd
    df_comp = pd.DataFrame({
        "Permisiune": list(ETICHETE.values()),
        "viewer":    ["✅" if PERMISIUNI["viewer"][k]    else "❌" for k in ETICHETE],
        "inspector": ["✅" if PERMISIUNI["inspector"][k] else "❌" for k in ETICHETE],
        "admin":     ["✅" if PERMISIUNI["admin"][k]     else "❌" for k in ETICHETE],
    })
    st.dataframe(df_comp, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTIUNEA 4 — SIMULARE DETECTIE (inspector + admin)
# ═══════════════════════════════════════════════════════════════════════════════

elif sectiune_activa == "Simulare Detectie":
    if not permisiuni["poate_rula_detectie"]:
        st.error("Nu aveti permisiunea sa rulati detectii. Rol necesar: inspector sau admin.")
        st.stop()

    logeaza_actiune("ACCES_PAGINA", "Simulare detectie YOLOv8")
    st.subheader("Simulare Detectie YOLOv8 (cu control acces)")

    st.info(f"""
    Aceasta sectiune demonstreaza ca doar utilizatorii cu rol **inspector**
    sau **admin** pot rula detectii. Rolul dvs. curent: **{rol.upper()}** — Acces permis.
    """)

    from PIL import Image, ImageDraw
    import numpy as np
    import io

    uploaded = st.file_uploader(
        "Incarcati o imagine drone pentru detectie",
        type=["jpg", "jpeg", "png"],
        help="Permis doar pentru inspector si admin"
    )

    if uploaded:
        logeaza_actiune("INCARCARE_IMAGINE", uploaded.name)
        img = Image.open(uploaded).convert("RGB")
        img_arr = np.array(img)

        # Simulare detectie (acelasi algoritm ca in zilele anterioare)
        np.random.seed(42)
        h, w = img_arr.shape[:2]
        n_boxes = np.random.randint(3, 8)
        etichete = ["vegetatie", "sol_gol", "apa"]
        culori_cls = {"vegetatie": (34, 139, 34), "sol_gol": (210, 180, 140), "apa": (30, 144, 255)}

        rezultate = []
        img_draw = img.copy()
        draw = ImageDraw.Draw(img_draw)

        for _ in range(n_boxes):
            x1 = np.random.randint(0, w - 80)
            y1 = np.random.randint(0, h - 80)
            x2 = min(x1 + np.random.randint(60, 150), w)
            y2 = min(y1 + np.random.randint(60, 150), h)
            cls = np.random.choice(etichete)
            conf = round(np.random.uniform(0.65, 0.98), 2)
            draw.rectangle([x1, y1, x2, y2], outline=culori_cls[cls], width=3)
            draw.text((x1 + 4, y1 + 4), f"{cls} {conf:.2f}", fill=culori_cls[cls])
            rezultate.append({"Clasa": cls, "Confidenta": conf, "x1": x1, "y1": y1, "x2": x2, "y2": y2})

        col_img1, col_img2 = st.columns(2)
        with col_img1:
            st.image(img, caption="Original", use_container_width=True)
        with col_img2:
            st.image(img_draw, caption="Detectie YOLOv8", use_container_width=True)

        import pandas as pd
        df_rez = pd.DataFrame(rezultate)
        st.dataframe(df_rez[["Clasa", "Confidenta"]], use_container_width=True)
        logeaza_actiune("DETECTIE_RULATA", f"{len(rezultate)} obiecte detectate in {uploaded.name}")

        if permisiuni["poate_exporta_date"]:
            csv_bytes = df_rez.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Export CSV Rezultate",
                data=csv_bytes,
                file_name=f"detectie_{utilizator['username']}_{datetime.date.today()}.csv",
                mime="text/csv"
            )
            logeaza_actiune("EXPORT_CSV", f"Export rezultate detectie")
    else:
        st.markdown("*Incarcati o imagine pentru a incepe detectia.*")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTIUNEA 5 — GESTIONARE UTILIZATORI (doar admin)
# ═══════════════════════════════════════════════════════════════════════════════

elif sectiune_activa == "Gestionare Utilizatori":
    if not permisiuni["poate_gestiona_utilizatori"]:
        st.error("Aceasta sectiune este rezervata exclusiv administratorilor.")
        st.stop()

    logeaza_actiune("ACCES_PAGINA", "Gestionare utilizatori")
    st.subheader("Gestionare Utilizatori (Admin)")

    import pandas as pd

    # Tabel utilizatori
    date_utilizatori = []
    for uname, udata in UTILIZATORI.items():
        date_utilizatori.append({
            "Username": uname,
            "Prenume": udata["prenume"],
            "Rol": udata["rol"],
            "Institutie": udata["institutie"],
            "Email": udata["email"],
            "Activ": "✅" if udata["activ"] else "❌",
            "Creat": udata["creat"]
        })
    df_users = pd.DataFrame(date_utilizatori)

    col_culori = {
        "admin": "background-color: #ffe0e0",
        "inspector": "background-color: #e0eaff",
        "viewer": "background-color: #f0f0f0"
    }

    st.dataframe(df_users, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Adaugare Utilizator Nou (simulare)")

    with st.form("form_adauga_user"):
        c1, c2 = st.columns(2)
        with c1:
            nou_username  = st.text_input("Username")
            nou_parola    = st.text_input("Parola initiala", type="password")
            nou_prenume   = st.text_input("Prenume / Institutie")
        with c2:
            nou_rol       = st.selectbox("Rol", ["viewer", "inspector", "admin"])
            nou_institutie= st.text_input("Institutie")
            nou_email     = st.text_input("Email")

        if st.form_submit_button("Adauga Utilizator", type="primary"):
            if not nou_username or not nou_parola:
                st.error("Username si parola sunt obligatorii.")
            elif nou_username in UTILIZATORI:
                st.error(f"Username '{nou_username}' exista deja.")
            elif len(nou_parola) < 8:
                st.error("Parola trebuie sa aiba minim 8 caractere.")
            else:
                # In productie: INSERT in baza de date
                logeaza_actiune("ADAUGARE_UTILIZATOR", f"User nou: {nou_username}, rol: {nou_rol}")
                st.success(f"Utilizatorul '{nou_username}' a fost adaugat cu rol '{nou_rol}'. (simulare)")

    st.divider()
    st.subheader("Statistici Utilizatori")
    c1, c2, c3 = st.columns(3)
    roluri_count = {"admin": 0, "inspector": 0, "viewer": 0}
    for u in UTILIZATORI.values():
        roluri_count[u["rol"]] += 1
    c1.metric("Admin", roluri_count["admin"])
    c2.metric("Inspector", roluri_count["inspector"])
    c3.metric("Viewer", roluri_count["viewer"])


# ═══════════════════════════════════════════════════════════════════════════════
# SECTIUNEA 6 — SETARI SISTEM (doar admin)
# ═══════════════════════════════════════════════════════════════════════════════

elif sectiune_activa == "Setari Sistem":
    if not permisiuni["poate_modifica_setari"]:
        st.error("Aceasta sectiune este rezervata exclusiv administratorilor.")
        st.stop()

    logeaza_actiune("ACCES_PAGINA", "Setari sistem")
    st.subheader("Setari Sistem AGROVISION (Admin)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Model YOLOv8**")
        st.selectbox("Model activ", [
            "best_v1_mAP083_20260403.pt",
            "yolov8n.pt (implicit)"
        ])
        st.slider("Prag confidenta detectie", 0.1, 1.0, 0.5, 0.05)
        st.number_input("Prag vegetatie (%) — conformitate PAC", 0, 100, 50)

    with col2:
        st.markdown("**Export GIS**")
        st.selectbox("Proiectie implicita", [
            "EPSG:31700 (Stereo70 Romania)",
            "EPSG:4326 (WGS84)",
            "EPSG:3857 (Web Mercator)"
        ])
        st.text_input("Prefix cod LPIS", value="GJ_")
        st.selectbox("Format export implicit", ["GeoJSON", "Shapefile", "GPX"])

    st.divider()
    st.markdown("**Notificari si alerte**")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.toggle("Email la detectie neconformitate", value=True)
    with c2:
        st.toggle("Raport zilnic automat", value=False)
    with c3:
        st.toggle("Mod debug (logging extins)", value=False)

    if st.button("Salveaza Setarile", type="primary"):
        logeaza_actiune("SALVARE_SETARI", "Setari sistem actualizate")
        st.success("Setarile au fost salvate. (simulare — in productie: fisier config.json)")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTIUNEA 7 — JURNAL ACTIUNI
# ═══════════════════════════════════════════════════════════════════════════════

elif sectiune_activa == "Jurnal Actiuni":
    logeaza_actiune("ACCES_PAGINA", "Vizualizare jurnal")
    st.subheader("Jurnal Actiuni Sesiune Curenta")

    jurnal = st.session_state.get("jurnal_actiuni", [])

    if not jurnal:
        st.info("Nicio actiune inregistrata inca in aceasta sesiune.")
    else:
        st.markdown(f"**{len(jurnal)} actiuni inregistrate in sesiunea curenta:**")
        for item in reversed(jurnal):
            st.markdown(f"""
            <div class="jurnal-row">
                <span style='color:#546e7a;'>{item['timestamp']}</span>
                &nbsp;|&nbsp;
                <span style='color:#0d6efd; font-weight:700;'>{item['utilizator']}</span>
                &nbsp;[{item['rol']}]&nbsp;
                <span style='color:#dc3545;'>{item['actiune']}</span>
                &nbsp;— {item['detalii']}
            </div>
            """, unsafe_allow_html=True)

        import pandas as pd
        df_jurnal = pd.DataFrame(jurnal)
        csv_jurnal = df_jurnal.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Export Jurnal CSV",
            data=csv_jurnal,
            file_name=f"jurnal_{utilizator['username']}_{datetime.date.today()}.csv",
            mime="text/csv"
        )

    st.divider()
    st.markdown("""
    **De ce este important jurnalul de actiuni?**

    - **Auditabilitate** (Reg. UE 2021/2116 art. 68): orice decizie trebuie sa poata fi reconstituita
    - **Responsabilitate**: stim exact cine a rulat ce detectie si cand
    - **Securitate**: detectam accesuri neautorizate sau actiuni suspecte
    - **GDPR**: log-urile de acces sunt parte din evidenta prelucrarilor

    In productie, jurnalul se salveaza intr-o baza de date cu timestamp UTC,
    IP-ul utilizatorului si hash-ul actiunii pentru integritate.
    """)


# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.divider()
st.markdown(f"""
<div style='text-align:center; color:#90a4ae; font-size:12px; padding:8px 0;'>
    AGROVISION &nbsp;|&nbsp; Ziua 19 — Autentificare + Roluri &nbsp;|&nbsp;
    Bloc 3 YOLOv8 &nbsp;|&nbsp; UCB Targu Jiu &nbsp;|&nbsp; APIA CJ Gorj
    <br>Sesiune activa: <strong>{utilizator['username']}</strong>
    [{rol.upper()}] — {utilizator['login_time']}
</div>
""", unsafe_allow_html=True)
