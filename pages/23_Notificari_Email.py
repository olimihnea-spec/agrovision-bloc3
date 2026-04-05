"""
BLOC 3 — Deep Learning YOLOv8, Ziua 23
Notificari Email Automate — alerte neconformitati APIA
Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu | UCB Targu Jiu | APIA CJ Gorj

CONCEPT CHEIE:
  Pana acum: inspectorul vede neconformitatile pe ecran si le exporta manual.
  Din Ziua 23: sistemul trimite automat email catre inspector si/sau fermier
  imediat ce o neconformitate este detectata.

  De ce email automat in APIA:
    - Reg. UE 2021/2116 art. 14: fermierul trebuie notificat in scris
    - Reducere timp administrativ: 0 minute in loc de 30 min per scrisoare
    - Trasabilitate: data/ora trimiterii salvata in baza de date
    - Dovada pentru OLAF/Curtea de Conturi

  Biblioteci Python folosite:
    - smtplib (built-in) = protocolul SMTP pentru trimitere email
    - email.mime = construirea mesajului (text + HTML + atasamente)
    - Credentialele se pastreaza in .streamlit/secrets.toml (niciodata in cod)

  IMPORTANT: Gmail necesita "App Password" (nu parola contului normal).
    Setari Google → Securitate → Verificare in 2 pasi (activat) →
    Parole pentru aplicatii → AGROVISION → copiaza cele 16 caractere

  Simulare vs. Trimitere reala:
    - Aplicatia are MOD SIMULARE (implicit) — nu trimite nimic
    - Dupa ce configurezi Gmail App Password in secrets.toml → trimitere reala
"""

import streamlit as st
import smtplib
import ssl
import datetime
import sqlite3
import os
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ─── CONFIGURARE PAGINA ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Notificari Email — AGROVISION",
    page_icon="📧",
    layout="wide"
)

# ─── BAZA DE DATE (din Ziua 22) ───────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "agrovision_detectii.db")

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.email-preview {
    background: white;
    border: 1px solid #dee2e6;
    border-radius: 10px;
    padding: 24px;
    font-family: Arial, sans-serif;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.email-header-bar {
    background: #0052A5;
    color: white;
    padding: 12px 20px;
    border-radius: 8px 8px 0 0;
    font-size: 18px;
    font-weight: 700;
    margin: -24px -24px 20px -24px;
}
.email-field {
    color: #546e7a;
    font-size: 12px;
    margin: 4px 0;
}
.alert-neconf {
    background: #f8d7da;
    border-left: 4px solid #dc3545;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 13px;
}
.alert-conf {
    background: #d4edda;
    border-left: 4px solid #28a745;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 13px;
}
.config-box {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 16px 20px;
    border: 1px solid #dee2e6;
    margin: 8px 0;
}
.jurnal-row {
    font-family: monospace;
    font-size: 12px;
    padding: 6px 10px;
    background: #f8f9fa;
    border-radius: 4px;
    margin: 3px 0;
    border-left: 3px solid #dee2e6;
}
</style>
""", unsafe_allow_html=True)

# ─── DATE DEMO PARCELE ───────────────────────────────────────────────────────
PARCELE_DEMO = [
    {"cod": "GJ_78258-1675", "fermier": "Popescu Ion",      "veg": 38.4, "status": "NECONFORM", "email": "popescu.ion@email.ro"},
    {"cod": "GJ_78301-0892", "fermier": "Ionescu Maria",    "veg": 62.1, "status": "CONFORM",   "email": "ionescu.maria@email.ro"},
    {"cod": "GJ_78445-2341", "fermier": "Dumitrescu Gh.",   "veg": 44.7, "status": "NECONFORM", "email": "dumitrescu.gh@email.ro"},
    {"cod": "GJ_78512-0077", "fermier": "Stanescu Petre",   "veg": 71.3, "status": "CONFORM",   "email": "stanescu.petre@email.ro"},
    {"cod": "GJ_78634-1129", "fermier": "Olteanu Vasile",   "veg": 29.8, "status": "NECONFORM", "email": "olteanu.vasile@email.ro"},
    {"cod": "GJ_78720-3388", "fermier": "Marinescu Ana",    "veg": 55.6, "status": "CONFORM",   "email": "marinescu.ana@email.ro"},
    {"cod": "GJ_79001-0445", "fermier": "Petrescu Dan",     "veg": 68.9, "status": "CONFORM",   "email": "petrescu.dan@email.ro"},
    {"cod": "GJ_79234-1876", "fermier": "Constantin Gh.",   "veg": 41.2, "status": "NECONFORM", "email": "constantin.gh@email.ro"},
    {"cod": "GJ_79567-2290", "fermier": "Florescu Elena",   "veg": 77.4, "status": "CONFORM",   "email": "florescu.elena@email.ro"},
    {"cod": "GJ_80980-2611", "fermier": "Draghici Marin",   "veg": 35.1, "status": "NECONFORM", "email": "draghici.marin@email.ro"},
]

# ─── JURNAL EMAIL (in session_state) ─────────────────────────────────────────
if "jurnal_email" not in st.session_state:
    st.session_state["jurnal_email"] = []

def adauga_jurnal(destinatar: str, subiect: str, tip: str, succes: bool, nota: str = ""):
    st.session_state["jurnal_email"].append({
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "destinatar": destinatar,
        "subiect": subiect[:40] + "..." if len(subiect) > 40 else subiect,
        "tip": tip,
        "status": "TRIMIS" if succes else "SIMULAT",
        "nota": nota
    })

# ─── FUNCTII EMAIL ────────────────────────────────────────────────────────────

def construieste_email_neconformitate(
    fermier: str, cod_lpis: str, veg_pct: float,
    inspector: str, data_control: str
) -> str:
    """Returneaza corpul HTML al emailului de notificare neconformitate."""
    return f"""
    <html><body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;">

    <div style="background:#0052A5; color:white; padding:16px 24px; border-radius:8px 8px 0 0;">
        <h2 style="margin:0; font-size:20px;">AGROVISION — Notificare Neconformitate</h2>
        <p style="margin:4px 0 0 0; font-size:13px; opacity:0.85;">
            APIA CJ Gorj | Serviciul Control pe Teren
        </p>
    </div>

    <div style="border:1px solid #dee2e6; border-top:none; padding:24px;
                border-radius:0 0 8px 8px;">

        <p>Stimate/Stimata <strong>{fermier}</strong>,</p>

        <p>In urma controlului pe teren cu aeronava fara pilot (drona) efectuat
        in data de <strong>{data_control}</strong>, parcela dumneavoastra a fost
        identificata cu un procent de vegetatie sub pragul minim admis.</p>

        <div style="background:#f8d7da; border-left:4px solid #dc3545;
                    border-radius:6px; padding:16px; margin:16px 0;">
            <strong style="color:#721c24;">NECONFORM — Actiune necesara</strong><br><br>
            <table style="font-size:14px; width:100%;">
                <tr><td style="color:#666; width:180px;">Cod parcela LPIS:</td>
                    <td><strong>{cod_lpis}</strong></td></tr>
                <tr><td style="color:#666;">Vegetatie detectata:</td>
                    <td><strong style="color:#dc3545;">{veg_pct:.1f}%</strong></td></tr>
                <tr><td style="color:#666;">Prag minim PAC:</td>
                    <td><strong>50%</strong></td></tr>
                <tr><td style="color:#666;">Deficit:</td>
                    <td><strong style="color:#dc3545;">{50 - veg_pct:.1f}%</strong></td></tr>
            </table>
        </div>

        <p><strong>Actiuni necesare in termen de 10 zile lucratoare:</strong></p>
        <ol style="font-size:14px; line-height:1.8;">
            <li>Prezentati-va la sediul APIA CJ Gorj cu documentele parcelei</li>
            <li>Depuneti o declaratie pe propria raspundere privind starea parcelei</li>
            <li>Puteti solicita o noua inspectie daca considerati ca rezultatul
                nu reflecta realitatea</li>
        </ol>

        <div style="background:#fff3cd; border-radius:6px; padding:12px 16px;
                    font-size:13px; margin-top:16px;">
            <strong>Baza legala:</strong> Regulamentul UE 2021/2116, art. 14 —
            Ecoconditionalitati PAC 2023-2027. Neconformitatea poate conduce la
            reducerea platilor directe.
        </div>

        <hr style="border:none; border-top:1px solid #dee2e6; margin:20px 0;">
        <p style="font-size:13px; color:#666;">
            Inspector: <strong>{inspector}</strong><br>
            Data notificarii: <strong>{data_control}</strong><br>
            Sistem: AGROVISION v1.0 | YOLOv8 | UCB Targu Jiu
        </p>

        <p style="font-size:12px; color:#999;">
            Acest email a fost generat automat de sistemul AGROVISION.
            Pentru informatii suplimentare contactati APIA CJ Gorj:
            Str. I.C. Pompilian nr. 51, Targu Jiu, jud. Gorj.
        </p>
    </div>
    </body></html>
    """

def construieste_email_raport(
    inspector: str, nr_total: int, nr_neconf: int,
    data_control: str, lista_neconf: list
) -> str:
    """Email de raport catre inspector cu toate neconformitatile sesiunii."""
    randuri = ""
    for p in lista_neconf:
        randuri += f"""
        <tr>
            <td style="padding:8px; border-bottom:1px solid #dee2e6;">{p['cod']}</td>
            <td style="padding:8px; border-bottom:1px solid #dee2e6;">{p['fermier']}</td>
            <td style="padding:8px; border-bottom:1px solid #dee2e6; color:#dc3545;
                       font-weight:bold;">{p['veg']:.1f}%</td>
        </tr>"""

    return f"""
    <html><body style="font-family: Arial, sans-serif; color: #333; max-width:640px; margin:0 auto;">

    <div style="background:#0052A5; color:white; padding:16px 24px; border-radius:8px 8px 0 0;">
        <h2 style="margin:0; font-size:20px;">AGROVISION — Raport Sesiune Control</h2>
        <p style="margin:4px 0 0 0; font-size:13px; opacity:0.85;">{data_control}</p>
    </div>

    <div style="border:1px solid #dee2e6; border-top:none; padding:24px;
                border-radius:0 0 8px 8px;">

        <p>Buna ziua, <strong>{inspector}</strong>,</p>
        <p>Rezumatul sesiunii de control din data de <strong>{data_control}</strong>:</p>

        <div style="display:flex; gap:12px; margin:16px 0;">
            <div style="background:#e8f4fd; border-radius:8px; padding:14px 20px;
                        text-align:center; flex:1;">
                <div style="font-size:28px; font-weight:800; color:#0052A5;">{nr_total}</div>
                <div style="font-size:12px; color:#666;">Total parcele</div>
            </div>
            <div style="background:#d4edda; border-radius:8px; padding:14px 20px;
                        text-align:center; flex:1;">
                <div style="font-size:28px; font-weight:800; color:#28a745;">
                    {nr_total - nr_neconf}</div>
                <div style="font-size:12px; color:#666;">Conforme</div>
            </div>
            <div style="background:#f8d7da; border-radius:8px; padding:14px 20px;
                        text-align:center; flex:1;">
                <div style="font-size:28px; font-weight:800; color:#dc3545;">{nr_neconf}</div>
                <div style="font-size:12px; color:#666;">Neconforme</div>
            </div>
        </div>

        {'<h3 style="color:#dc3545;">Parcele neconforme detectate:</h3><table style="width:100%; border-collapse:collapse;"><tr style="background:#f8f9fa;"><th style="padding:8px; text-align:left;">Cod LPIS</th><th style="padding:8px; text-align:left;">Fermier</th><th style="padding:8px; text-align:left;">Vegetatie</th></tr>' + randuri + '</table>' if lista_neconf else '<p style="color:#28a745;"><strong>Toate parcelele sunt conforme!</strong></p>'}

        <hr style="border:none; border-top:1px solid #dee2e6; margin:20px 0;">
        <p style="font-size:12px; color:#999;">
            Generat automat de AGROVISION v1.0 | YOLOv8 | UCB Targu Jiu | APIA CJ Gorj
        </p>
    </div>
    </body></html>
    """

def trimite_email_real(
    smtp_server: str, port: int,
    expeditor: str, parola_app: str,
    destinatar: str, subiect: str, corp_html: str
) -> tuple[bool, str]:
    """Trimite email real via SMTP SSL. Returneaza (succes, mesaj)."""
    try:
        msg = MIMEMultipart("alternative")
        msg["From"]    = expeditor
        msg["To"]      = destinatar
        msg["Subject"] = subiect
        msg.attach(MIMEText(corp_html, "html", "utf-8"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(expeditor, parola_app)
            server.sendmail(expeditor, destinatar, msg.as_string())
        return True, "Email trimis cu succes."
    except smtplib.SMTPAuthenticationError:
        return False, "Eroare autentificare: verifica emailul si App Password."
    except smtplib.SMTPException as e:
        return False, f"Eroare SMTP: {e}"
    except Exception as e:
        return False, f"Eroare: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFATA STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style='display:flex; align-items:center; gap:16px; margin-bottom:8px;'>
    <div style='font-size:48px;'>📧</div>
    <div>
        <h1 style='margin:0; font-size:28px; color:#0052A5;'>
            Notificari Email Automate
        </h1>
        <p style='margin:0; color:#546e7a;'>
            Alerte neconformitati PAC | smtplib | Template HTML | APIA CJ Gorj
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# Banner mod simulare
mod_real = False
try:
    _email_cfg = st.secrets.get("email", {})
    if _email_cfg.get("expeditor") and _email_cfg.get("parola_app"):
        mod_real = True
except Exception:
    pass

if mod_real:
    st.success("MOD REAL — credentiale email configurate in secrets.toml. Emailurile se trimit efectiv.")
else:
    st.warning("""
    **MOD SIMULARE** — emailurile NU se trimit, doar se previzualizeaza.
    Pentru trimitere reala: adauga credentialele Gmail in `.streamlit/secrets.toml`
    (vezi Tab 4 — Configurare).
    """)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Alerta Neconformitate",
    "Raport Inspector",
    "Trimitere in Masa",
    "Configurare Gmail",
    "Jurnal Trimiteri"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ALERTA NECONFORMITATE (1 fermier)
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Trimite alerta catre un fermier")

    neconforme = [p for p in PARCELE_DEMO if p["status"] == "NECONFORM"]

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("**Selecteaza parcela neconforma:**")
        optiuni = {f"{p['cod']} — {p['fermier']} ({p['veg']:.1f}%)": p
                   for p in neconforme}
        ales = st.selectbox("Parcela:", list(optiuni.keys()))
        parcela = optiuni[ales]

        inspector_t1 = st.text_input("Inspector (expeditor)",
            value="Prof. Asoc. Dr. Oliviu Mihnea Gamulescu",
            key="insp_t1")
        email_dest = st.text_input("Email destinatar (fermier)",
            value=parcela["email"])
        data_ctrl = st.date_input("Data controlului",
            value=datetime.date.today(), key="data_t1")

        st.markdown("**Sumar parcela selectate:**")
        st.markdown(f"""
        <div class="alert-neconf">
            <strong>{parcela['cod']}</strong> — {parcela['fermier']}<br>
            Vegetatie: <strong style='color:#dc3545;'>{parcela['veg']:.1f}%</strong>
            (prag PAC: 50%) | Deficit: {50 - parcela['veg']:.1f}%
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("**Previzualizare email:**")
        corp = construieste_email_neconformitate(
            fermier=parcela["fermier"],
            cod_lpis=parcela["cod"],
            veg_pct=parcela["veg"],
            inspector=inspector_t1,
            data_control=str(data_ctrl)
        )
        with st.container():
            st.markdown(f"""
            <div class="email-preview">
                <div class="email-header-bar">AGROVISION — Notificare Neconformitate</div>
                <div class="email-field"><strong>Catre:</strong> {email_dest}</div>
                <div class="email-field"><strong>Subiect:</strong>
                    Notificare neconformitate — {parcela['cod']}</div>
                <div class="email-field"><strong>Data:</strong> {data_ctrl}</div>
                <hr style="border:1px solid #eee; margin:10px 0;">
                <p style="font-size:13px;">
                    Stimate {parcela['fermier']},<br><br>
                    Parcela <strong>{parcela['cod']}</strong> a fost identificata
                    cu <strong style="color:#dc3545;">{parcela['veg']:.1f}% vegetatie</strong>
                    — sub pragul PAC de 50%.<br><br>
                    Deficit: <strong style="color:#dc3545;">{50 - parcela['veg']:.1f}%</strong>
                    | Actiune necesara in 10 zile.
                </p>
            </div>
            """, unsafe_allow_html=True)

    if st.button("Trimite / Simuleaza Email Neconformitate",
                 type="primary", use_container_width=True):
        subiect = f"Notificare neconformitate PAC — {parcela['cod']} — APIA CJ Gorj"
        if mod_real:
            cfg = st.secrets["email"]
            ok, msg = trimite_email_real(
                cfg.get("smtp_server", "smtp.gmail.com"),
                int(cfg.get("port", 465)),
                cfg["expeditor"], cfg["parola_app"],
                email_dest, subiect, corp
            )
            if ok:
                st.success(f"Email trimis catre {email_dest}!")
            else:
                st.error(msg)
        else:
            ok = True
            msg = "Simulare"
            st.info(f"SIMULARE: Email catre {email_dest} — subiect: {subiect}")

        adauga_jurnal(email_dest, subiect, "Neconformitate", ok, msg)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — RAPORT INSPECTOR
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Trimite raport de sesiune catre inspector")

    col1, col2 = st.columns([1, 1])

    with col1:
        inspector_t2 = st.text_input("Inspector",
            value="Prof. Asoc. Dr. Oliviu Mihnea Gamulescu", key="insp_t2")
        email_insp   = st.text_input("Email inspector",
            value="oliviu.gamulescu@apia.org.ro")
        data_ctrl_t2 = st.date_input("Data controlului",
            value=datetime.date.today(), key="data_t2")

        neconf_rap = [p for p in PARCELE_DEMO if p["status"] == "NECONFORM"]
        st.markdown(f"**Sesiune curenta:** {len(PARCELE_DEMO)} parcele, "
                    f"{len(neconf_rap)} neconforme")
        for p in PARCELE_DEMO:
            stil = "alert-neconf" if p["status"] == "NECONFORM" else "alert-conf"
            icon = "❌" if p["status"] == "NECONFORM" else "✅"
            st.markdown(f"""
            <div class="{stil}">
                {icon} {p['cod']} — {p['fermier']}
                ({p['veg']:.1f}%)
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("**Previzualizare raport:**")
        corp_rap = construieste_email_raport(
            inspector=inspector_t2,
            nr_total=len(PARCELE_DEMO),
            nr_neconf=len(neconf_rap),
            data_control=str(data_ctrl_t2),
            lista_neconf=[{"cod": p["cod"], "fermier": p["fermier"],
                           "veg": p["veg"]} for p in neconf_rap]
        )
        st.markdown(f"""
        <div class="email-preview">
            <div class="email-header-bar">AGROVISION — Raport Sesiune Control</div>
            <div class="email-field"><strong>Catre:</strong> {email_insp}</div>
            <div class="email-field"><strong>Subiect:</strong>
                Raport control {data_ctrl_t2} — {len(PARCELE_DEMO)} parcele</div>
            <hr style="border:1px solid #eee; margin:10px 0;">
            <div style="display:flex; gap:10px; text-align:center;">
                <div style="background:#e8f4fd; border-radius:6px; padding:10px; flex:1;">
                    <div style="font-size:22px; font-weight:800; color:#0052A5;">
                        {len(PARCELE_DEMO)}</div>
                    <div style="font-size:11px; color:#666;">Total</div>
                </div>
                <div style="background:#d4edda; border-radius:6px; padding:10px; flex:1;">
                    <div style="font-size:22px; font-weight:800; color:#28a745;">
                        {len(PARCELE_DEMO) - len(neconf_rap)}</div>
                    <div style="font-size:11px; color:#666;">Conforme</div>
                </div>
                <div style="background:#f8d7da; border-radius:6px; padding:10px; flex:1;">
                    <div style="font-size:22px; font-weight:800; color:#dc3545;">
                        {len(neconf_rap)}</div>
                    <div style="font-size:11px; color:#666;">Neconforme</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if st.button("Trimite / Simuleaza Raport Inspector",
                 type="primary", use_container_width=True):
        subiect_rap = (f"Raport control AGROVISION — {data_ctrl_t2} — "
                       f"{len(PARCELE_DEMO)} parcele, {len(neconf_rap)} neconforme")
        if mod_real:
            cfg = st.secrets["email"]
            ok, msg = trimite_email_real(
                cfg.get("smtp_server", "smtp.gmail.com"),
                int(cfg.get("port", 465)),
                cfg["expeditor"], cfg["parola_app"],
                email_insp, subiect_rap, corp_rap
            )
            if ok:
                st.success(f"Raport trimis catre {email_insp}!")
            else:
                st.error(msg)
        else:
            ok = True
            st.info(f"SIMULARE: Raport catre {email_insp} — {subiect_rap}")

        adauga_jurnal(email_insp, subiect_rap, "Raport Inspector", ok)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — TRIMITERE IN MASA (toti fermierii neconformi)
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Trimitere in masa — toti fermierii neconformi")

    st.info("""
    Aceasta sectiune trimite automat cate un email fiecarui fermier neconform.
    In loc sa scrii 5 scrisori separat, AGROVISION le genereaza si le trimite
    pe toate in cateva secunde.
    """)

    neconf_masa = [p for p in PARCELE_DEMO if p["status"] == "NECONFORM"]

    inspector_masa = st.text_input("Inspector (expeditor)",
        value="Prof. Asoc. Dr. Oliviu Mihnea Gamulescu", key="insp_masa")
    data_masa = st.date_input("Data controlului",
        value=datetime.date.today(), key="data_masa")

    st.markdown(f"**{len(neconf_masa)} fermieri vor primi notificare:**")
    for p in neconf_masa:
        st.markdown(f"""
        <div class="alert-neconf">
            ❌ <strong>{p['fermier']}</strong> — {p['cod']}
            | Vegetatie: {p['veg']:.1f}% | Email: {p['email']}
        </div>
        """, unsafe_allow_html=True)

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        trimite_btn = st.button(
            f"Trimite / Simuleaza {len(neconf_masa)} Emailuri",
            type="primary", use_container_width=True
        )
    with col_b2:
        email_cc = st.text_input("CC inspector (optional)",
            value="oliviu.gamulescu@apia.org.ro",
            help="Va primi o copie a tuturor notificarilor")

    if trimite_btn:
        progress = st.progress(0, text="Se proceseaza...")
        rezultate = []
        for i, p in enumerate(neconf_masa):
            corp_p = construieste_email_neconformitate(
                fermier=p["fermier"], cod_lpis=p["cod"],
                veg_pct=p["veg"], inspector=inspector_masa,
                data_control=str(data_masa)
            )
            subiect_p = f"Notificare neconformitate PAC — {p['cod']} — APIA CJ Gorj"

            if mod_real:
                cfg = st.secrets["email"]
                ok, msg = trimite_email_real(
                    cfg.get("smtp_server", "smtp.gmail.com"),
                    int(cfg.get("port", 465)),
                    cfg["expeditor"], cfg["parola_app"],
                    p["email"], subiect_p, corp_p
                )
            else:
                ok, msg = True, "Simulare"

            rezultate.append({
                "Fermier": p["fermier"], "Email": p["email"],
                "Status": "TRIMIS" if ok else "EROARE", "Nota": msg
            })
            adauga_jurnal(p["email"], subiect_p, "Masa-Neconformitate", ok, msg)
            progress.progress((i + 1) / len(neconf_masa),
                              text=f"Procesat {i+1}/{len(neconf_masa)}: {p['fermier']}")

        progress.empty()
        df_rez = pd.DataFrame(rezultate)
        st.dataframe(df_rez, use_container_width=True, hide_index=True)
        trimise = sum(1 for r in rezultate if r["Status"] == "TRIMIS")
        if mod_real:
            st.success(f"{trimise}/{len(neconf_masa)} emailuri trimise cu succes!")
        else:
            st.info(f"SIMULARE: {trimise}/{len(neconf_masa)} emailuri procesate.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — CONFIGURARE GMAIL
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Configurare Gmail pentru trimitere reala")

    st.markdown("""
    ### Pasii pentru activare Gmail

    **Pas 1 — Activeaza verificarea in 2 pasi:**
    """)
    st.code("myaccount.google.com → Securitate → Verificare in 2 pasi → Activare", language="text")

    st.markdown("**Pas 2 — Creaza App Password:**")
    st.code("myaccount.google.com → Securitate → Parole aplicatii → AGROVISION → Genereaza", language="text")
    st.caption("Vei primi 16 caractere (ex: `abcd efgh ijkl mnop`) — salveaza-le!")

    st.markdown("**Pas 3 — Adauga in `.streamlit/secrets.toml`:**")
    st.code("""[email]
expeditor  = "emailul_tau@gmail.com"
parola_app = "abcdefghijklmnop"
smtp_server = "smtp.gmail.com"
port = 465""", language="toml")

    st.markdown("**Pas 4 — Pe Streamlit Cloud:** Settings → Secrets → lipesti continutul de mai sus")

    st.warning("""
    **Niciodata** nu pune emailul si parola direct in codul Python!
    Daca uiti si faci `git push`, parola ajunge pe GitHub si contul
    poate fi compromis in minute.
    `secrets.toml` este exclus din Git prin `.gitignore`.
    """)

    st.divider()
    st.markdown("### Furnizori SMTP alternativi (tot gratuit)")
    st.markdown("""
    | Furnizor | SMTP Server | Port | Cont necesar |
    |----------|-------------|------|--------------|
    | Gmail | smtp.gmail.com | 465 | gmail.com + App Password |
    | Outlook | smtp.office365.com | 587 | outlook.com |
    | Yahoo | smtp.mail.yahoo.com | 465 | yahoo.com + App Password |
    | Zoho | smtp.zoho.eu | 465 | zoho.eu (gratuit pana 5 useri) |
    """)

    st.divider()
    st.markdown("### Test conexiune SMTP")
    with st.form("form_test_smtp"):
        test_email_dest = st.text_input("Trimite email test catre:", placeholder="test@gmail.com")
        if st.form_submit_button("Testeaza conexiunea"):
            if not mod_real:
                st.warning("Credentialele nu sunt configurate in secrets.toml. "
                           "Urmeaza pasii de mai sus.")
            elif not test_email_dest:
                st.error("Introdu o adresa email de test.")
            else:
                cfg = st.secrets["email"]
                ok, msg = trimite_email_real(
                    cfg.get("smtp_server", "smtp.gmail.com"),
                    int(cfg.get("port", 465)),
                    cfg["expeditor"], cfg["parola_app"],
                    test_email_dest,
                    "Test AGROVISION — conexiune SMTP OK",
                    "<h3>AGROVISION</h3><p>Conexiunea SMTP functioneaza corect!</p>"
                )
                if ok:
                    st.success(f"Test reusit! Email trimis catre {test_email_dest}")
                else:
                    st.error(f"Test esuat: {msg}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — JURNAL TRIMITERI
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Jurnal trimiteri sesiune curenta")

    jurnal = st.session_state.get("jurnal_email", [])

    if not jurnal:
        st.info("Niciun email procesat inca in aceasta sesiune.")
    else:
        st.markdown(f"**{len(jurnal)} operatiuni inregistrate:**")
        for item in reversed(jurnal):
            culoare = "#d4edda" if item["status"] in ("TRIMIS","SIMULAT") else "#f8d7da"
            border  = "#28a745" if item["status"] in ("TRIMIS","SIMULAT") else "#dc3545"
            st.markdown(f"""
            <div class="jurnal-row" style="border-left-color:{border};
                         background:{culoare};">
                <span style="color:#546e7a;">{item['timestamp']}</span>
                &nbsp;|&nbsp;
                <strong>[{item['status']}]</strong>
                &nbsp;|&nbsp; {item['tip']}
                &nbsp;→&nbsp; {item['destinatar']}
                &nbsp;|&nbsp; <em>{item['subiect']}</em>
            </div>
            """, unsafe_allow_html=True)

        if st.button("Sterge jurnal sesiune", type="secondary"):
            st.session_state["jurnal_email"] = []
            st.rerun()

    st.divider()
    st.markdown("""
    **Concepte smtplib folosite:**

    ```python
    import smtplib, ssl
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    # Construim mesajul
    msg = MIMEMultipart("alternative")
    msg["From"]    = "expeditor@gmail.com"
    msg["To"]      = "destinatar@email.ro"
    msg["Subject"] = "Notificare APIA"
    msg.attach(MIMEText(corp_html, "html", "utf-8"))

    # Trimitem via SSL (port 465)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login("expeditor@gmail.com", "app_password_16_chars")
        server.sendmail("expeditor", "destinatar", msg.as_string())
    ```
    """)

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center; color:#90a4ae; font-size:12px; padding:8px 0;'>
    AGROVISION &nbsp;|&nbsp; Ziua 23 — Notificari Email Automate &nbsp;|&nbsp;
    smtplib | MIMEMultipart | SSL | Template HTML
    &nbsp;|&nbsp; UCB Targu Jiu &nbsp;|&nbsp; APIA CJ Gorj
</div>
""", unsafe_allow_html=True)
