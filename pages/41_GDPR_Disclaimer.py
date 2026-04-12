import streamlit as st

st.set_page_config(
    page_title="GDPR / Disclaimer — AgroVision",
    page_icon="shield",
    layout="wide"
)

st.title("Protectia Datelor si Disclaimer")
st.caption("Regulamentul (UE) 2016/679 — GDPR | Aplicatie demonstrativa / educationala")

st.info(
    "**Scop demonstrativ si educational** — AgroVision este o aplicatie "
    "prototip dezvoltata in scop de cercetare academica si demonstratie institutionala. "
    "Nu este un sistem operational APIA si nu genereaza decizii administrative reale."
)

st.markdown("---")

# Sectiunea 1 — Operator de date
st.subheader("1. Operatorul de date")
col1, col2 = st.columns(2)
with col1:
    st.markdown("""
**In context academic (UCB):**
- Universitatea \"Constantin Brancusi\" din Targu Jiu
- Facultatea de Inginerie
- Departamentul de Energie, Mediu si Agroturism
- Str. Tineretului, Nr. 4, Targu Jiu, 210185, Gorj
""")
with col2:
    st.markdown("""
**In context institutional (APIA):**
- APIA — Centrul Judetean Gorj
- Serviciul Control pe Teren
- Str. I. C. Popilian, nr. 51, CP 210132
- Targu Jiu, Gorj, Romania
""")

st.markdown("**Contact responsabil date:** oliviu.gamulescu@apia.ro")

st.markdown("---")

# Sectiunea 2 — Date procesate
st.subheader("2. Ce date proceseaza aplicatia")

st.markdown("""
| Categorie | Date procesate | Temei legal | Durata |
|---|---|---|---|
| **Parcele LPIS** | ID parcela, suprafata, coordonate — 10 parcele reprezentative Gorj | Interes legitim cercetare (Art. 6.1.f GDPR) | Sesiune activa |
| **Imagini UAV** | Imagini aeriene procesate de modelul YOLOv8 (vegetatie / sol / apa) | Interes legitim cercetare | Sesiune activa |
| **Conturi utilizatori** | Username, rol, stare sesiune de autentificare | Necesitate contractuala (Art. 6.1.b) | Sesiune activa |
| **Exporturi Excel/PDF** | Rapoarte generate cu date parcele si rezultate detectie | Interes legitim cercetare | La cerere utilizator |
""")

st.warning(
    "Datele de parcele folosite sunt **reprezentative** (selectate din LPIS Gorj "
    "pentru antrenamentul modelului YOLOv8 in april 2026). "
    "Nu sunt asociate cu date personale de identificare ale fermierilor."
)

st.markdown("---")

# Sectiunea 3 — Masuri de protectie
st.subheader("3. Cum protejam datele")

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
**Masuri tehnice:**
- Autentificare cu roluri (admin / inspector / viewer)
- Acces diferentiat pe functionalitati
- Sesiuni independente per utilizator
- Hosting: Streamlit Community Cloud (SUA)
    """)
with col2:
    st.markdown("""
**Limitari importante:**
- Nu se stocheaza date permanent pe server
- Nu se transmit date catre terti
- Modelul YOLOv8 ruleaza local (inferenta pe imaginea incarcata)
- Exporturile raman in sesiunea utilizatorului
    """)

st.markdown("---")

# Sectiunea 4 — Drepturi utilizatori
st.subheader("4. Drepturile tale ca utilizator (Art. 15-22 GDPR)")

st.markdown("""
Ca persoana vizata, ai urmatoarele drepturi:

- **Dreptul de acces** — sa stii ce date se proceseaza despre tine
- **Dreptul la rectificare** — corectarea datelor inexacte
- **Dreptul la stergere** — \"dreptul de a fi uitat\"
- **Dreptul la restrictionarea prelucrarii**
- **Dreptul la portabilitate** — primirea datelor intr-un format structurat
- **Dreptul la opozitie** — impotriva prelucrarii bazate pe interes legitim

**Pentru exercitarea drepturilor:**
- Email: oliviu.gamulescu@apia.ro
- Autoritate de supraveghere: **ANSPDCP** — www.dataprotection.ro
""")

st.markdown("---")

# Sectiunea 5 — Disclaimer
st.subheader("5. Disclaimer")

st.error("""
**IMPORTANT — Citeste inainte de utilizare:**

1. AgroVision este o aplicatie **demonstrativa si educationala**, dezvoltata ca
   parte a unei cercetari doctorale si academice.

2. **Nu este un sistem oficial APIA** si nu are nicio legatura cu sistemele
   informatice operationale ale Agentiei de Plati si Interventie pentru Agricultura.

3. Rezultatele detectiei YOLOv8 (vegetatie / sol gol / apa) sunt generate
   de un model de cercetare cu mAP50 = 82.9% si **nu constituie baza pentru
   decizii administrative, sanctiuni sau plati PAC**.

4. Datele de parcele incluse sunt folosite exclusiv in scop demonstrativ.
   Orice asemanare cu situatii reale de control este coincidenta.

5. Aplicatia este gazduita pe **Streamlit Community Cloud** (Snowflake Inc., SUA).
   Utilizand aplicatia, esti de acord cu termenii Streamlit:
   https://streamlit.io/terms-of-use
""")

st.markdown("---")

# Footer
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.85em;'>
Ultima actualizare: 12 aprilie 2026 &nbsp;|&nbsp;
AgroVision v1.0 &nbsp;|&nbsp;
Contact: oliviu.gamulescu@apia.ro
</div>
""", unsafe_allow_html=True)
