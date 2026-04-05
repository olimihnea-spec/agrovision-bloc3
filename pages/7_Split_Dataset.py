"""
BLOC 3 — Deep Learning YOLOv8, Ziua 7
Split automat dataset — impartire train/val/test cu shuffle
Autor: Prof. Asoc. Dr. Oliviu Mihnea Gamulescu | UCB Targu Jiu | APIA CJ Gorj

CONCEPT CHEIE:
  random.shuffle(lista)              — amesteca aleator lista de fisiere
  shutil.copy(src, dst)              — copiaza fisier dintr-un loc in altul
  os.path.splitext(fisier)           — separa numele de extensie: "img001", ".jpg"
  Structura output: images/train/ + images/val/ + images/test/
                    labels/train/ + labels/val/ + labels/test/
  zipfile — intregul dataset split gata de antrenat, intr-un ZIP
"""

import streamlit as st
import numpy as np
import pandas as pd
import os
import random
import zipfile
import json
from io import BytesIO
from datetime import date
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ─── Configurare pagina ───────────────────────────────────────────────────────
st.set_page_config(page_title="Split Dataset — Ziua 7", layout="wide")

st.markdown("""
<style>
.titlu { color:#2e7d32; font-size:1.05rem; font-weight:700;
         border-bottom:2px solid #2e7d32; padding-bottom:4px; margin-bottom:12px; }
.card  { background:#e8f5e9; border-left:4px solid #2e7d32;
         border-radius:6px; padding:12px 16px; margin-bottom:8px; }
.card-albastru { background:#e3f2fd; border-left:4px solid #1565c0;
                 border-radius:6px; padding:12px 16px; margin-bottom:8px; }
.card-rosu  { background:#ffebee; border-left:4px solid #c62828;
              border-radius:6px; padding:12px 16px; margin-bottom:8px; }
.fisier-ok  { background:#e8f5e9; border-radius:4px; padding:3px 8px;
              font-family:monospace; font-size:0.8rem; color:#1b5e20;
              display:inline-block; margin:2px; }
.fisier-err { background:#ffebee; border-radius:4px; padding:3px 8px;
              font-family:monospace; font-size:0.8rem; color:#c62828;
              display:inline-block; margin:2px; }
</style>
""", unsafe_allow_html=True)

st.title("Ziua 7 — Split Automat Dataset")
st.markdown("**Impartire train/val/test cu shuffle — gata de antrenat YOLOv8**")
st.markdown("---")

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab_upload, tab_manual, tab_verificare = st.tabs([
    "Split din fisiere incarcate", "Split manual (cai locale)", "Verificare dataset"
])

# ══════════════════════════════════════════════════════
# TAB 1 — UPLOAD + SPLIT
# ══════════════════════════════════════════════════════
with tab_upload:
    st.markdown('<p class="titlu">Upload imagini + adnotari → Split automat → ZIP</p>',
                unsafe_allow_html=True)

    st.markdown("""
    <div class="card-albastru">
        <strong>Cum functioneaza:</strong><br>
        1. Incarci imaginile (.jpg) SI adnotarile (.txt) cu acelasi nume<br>
        2. Aplicatia le asociaza automat (img001.jpg ↔ img001.txt)<br>
        3. Le imparte in train/val/test cu shuffle<br>
        4. Genereaza ZIP cu structura corecta + data.yaml gata de antrenat
    </div>
    """, unsafe_allow_html=True)

    col_up1, col_up2 = st.columns(2)
    with col_up1:
        fisiere_img = st.file_uploader(
            "Imagini (.jpg, .png)",
            type=["jpg","jpeg","png"],
            accept_multiple_files=True,
            key="img_split"
        )
    with col_up2:
        fisiere_txt = st.file_uploader(
            "Adnotari YOLO (.txt)",
            type=["txt"],
            accept_multiple_files=True,
            key="txt_split"
        )

    # Setari split
    st.markdown("**Setari split:**")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        pct_train = st.slider("Train (%)", 50, 90, 70, 5)
    with col_s2:
        pct_val   = st.slider("Val (%)",   5,  40, 20, 5)
    with col_s3:
        pct_test  = 100 - pct_train - pct_val
        st.metric("Test (%)", pct_test)
    with col_s4:
        seed_split = st.number_input("Seed shuffle", value=42, min_value=0)

    clase_input = st.text_input(
        "Clasele (in ordine, separate prin virgula):",
        value="grau, porumb, rapita, vegetatie_lipsa"
    )
    clase_lista = [c.strip() for c in clase_input.split(",")]

    if pct_test < 0:
        st.error("Train% + Val% depaseste 100%. Ajusteaza valorile.")
    elif fisiere_img and fisiere_txt:
        # Asociere imagine ↔ adnotare
        dict_img = {os.path.splitext(f.name)[0]: f for f in fisiere_img}
        dict_txt = {os.path.splitext(f.name)[0]: f for f in fisiere_txt}

        perechi_ok  = [(k, dict_img[k], dict_txt[k])
                       for k in dict_img if k in dict_txt]
        doar_img    = [k for k in dict_img if k not in dict_txt]
        doar_txt    = [k for k in dict_txt if k not in dict_img]

        col_r1, col_r2, col_r3 = st.columns(3)
        col_r1.metric("Perechi complete", len(perechi_ok), delta="OK")
        col_r2.metric("Imagini fara .txt", len(doar_img),
                      delta=None if not doar_img else f"-{len(doar_img)}")
        col_r3.metric("TXT fara imagine",  len(doar_txt),
                      delta=None if not doar_txt else f"-{len(doar_txt)}")

        if doar_img:
            st.warning(f"Imagini fara adnotare: {', '.join(doar_img[:5])}"
                       + ("..." if len(doar_img) > 5 else ""))
        if doar_txt:
            st.warning(f"TXT fara imagine: {', '.join(doar_txt[:5])}"
                       + ("..." if len(doar_txt) > 5 else ""))

        if perechi_ok and st.button("Genereaza Dataset Split ZIP", type="primary"):
            with st.spinner("Se proceseaza..."):
                # Shuffle
                random.seed(seed_split)
                perechi = list(perechi_ok)
                random.shuffle(perechi)

                n = len(perechi)
                n_train = max(1, int(n * pct_train / 100))
                n_val   = max(1, int(n * pct_val   / 100))
                n_test  = n - n_train - n_val

                splits = {
                    "train": perechi[:n_train],
                    "val":   perechi[n_train:n_train+n_val],
                    "test":  perechi[n_train+n_val:],
                }

                # data.yaml
                yaml_content = (
                    f"path: ./dataset_split\n"
                    f"train: images/train\n"
                    f"val:   images/val\n"
                    f"test:  images/test\n\n"
                    f"nc: {len(clase_lista)}\n"
                    f"names:\n"
                )
                for i, cls in enumerate(clase_lista):
                    yaml_content += f"  {i}: {cls}\n"

                # split_info.json
                info = {
                    "data_generare": date.today().strftime("%Y-%m-%d"),
                    "seed": seed_split,
                    "total": n,
                    "train": n_train,
                    "val":   n_val,
                    "test":  n_test,
                    "clase": clase_lista,
                }

                # ZIP
                buf_zip = BytesIO()
                with zipfile.ZipFile(buf_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                    zf.writestr("dataset_split/data.yaml", yaml_content)
                    zf.writestr("dataset_split/split_info.json",
                                json.dumps(info, ensure_ascii=False, indent=2))

                    for split_name, perechi_split in splits.items():
                        for nume, f_img, f_txt in perechi_split:
                            ext = os.path.splitext(f_img.name)[1]
                            zf.writestr(
                                f"dataset_split/images/{split_name}/{nume}{ext}",
                                f_img.read()
                            )
                            f_img.seek(0)
                            zf.writestr(
                                f"dataset_split/labels/{split_name}/{nume}.txt",
                                f_txt.read().decode("utf-8")
                            )
                            f_txt.seek(0)

                buf_zip.seek(0)

            # Rezumat
            st.success("Dataset split generat!")
            col_rez1, col_rez2, col_rez3, col_rez4 = st.columns(4)
            col_rez1.metric("Total", n)
            col_rez2.metric("Train", n_train, delta=f"{pct_train}%")
            col_rez3.metric("Val",   n_val,   delta=f"{pct_val}%")
            col_rez4.metric("Test",  n_test,  delta=f"{pct_test}%")

            # Grafic split
            fig, ax = plt.subplots(figsize=(5, 2.5))
            ax.barh(["Train","Val","Test"], [n_train, n_val, n_test],
                    color=["#1565c0","#2e7d32","#e65100"])
            for i, v in enumerate([n_train, n_val, n_test]):
                ax.text(v + 0.1, i, str(v), va="center", fontsize=9)
            ax.set_xlabel("Nr. imagini")
            ax.set_title("Distributie split dataset")
            ax.spines[["top","right"]].set_visible(False)
            plt.tight_layout()
            buf_fig = BytesIO(); fig.savefig(buf_fig, dpi=120, bbox_inches="tight")
            buf_fig.seek(0); plt.close()
            st.image(buf_fig)

            st.download_button(
                "Descarca Dataset Split ZIP",
                data=buf_zip,
                file_name=f"dataset_split_{date.today().strftime('%Y%m%d')}.zip",
                mime="application/zip"
            )

            # Comanda antrenare
            st.markdown("**Comanda antrenare YOLOv8 (copiaza in terminal):**")
            st.code(
                f"yolo train model=yolov8n.pt data=dataset_split/data.yaml "
                f"epochs=50 imgsz=640 batch=16",
                language="bash"
            )

# ══════════════════════════════════════════════════════
# TAB 2 — SPLIT MANUAL (cai locale)
# ══════════════════════════════════════════════════════
with tab_manual:
    st.markdown('<p class="titlu">Split din folder local — genereaza script Python</p>',
                unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        Daca imaginile sunt deja pe calculatorul tau, genereaza un script Python
        care face split-ul direct pe disk — fara sa le incarci in browser.
        <br>Util pentru seturi mari (sute de imagini).
    </div>
    """, unsafe_allow_html=True)

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        folder_sursa = st.text_input(
            "Folder sursa (imagini + .txt in acelasi loc):",
            value=r"G:\DRONE_DATASET\adnotat"
        )
        folder_dest = st.text_input(
            "Folder destinatie (dataset split):",
            value=r"G:\DRONE_DATASET\dataset_split"
        )
    with col_m2:
        pct_tr = st.slider("Train (%)", 50, 90, 70, 5, key="m_train")
        pct_vl = st.slider("Val (%)",   5,  40, 20, 5, key="m_val")
        pct_ts = 100 - pct_tr - pct_vl
        st.metric("Test (%)", pct_ts)
        seed_m = st.number_input("Seed", value=42, key="m_seed")

    clase_m = st.text_input("Clase:", value="grau, porumb, rapita, vegetatie_lipsa",
                             key="clase_m")
    clase_m_lista = [c.strip() for c in clase_m.split(",")]

    script = f'''"""
Split automat dataset YOLO
Generat de: AGROVISION — Bloc 3, Ziua 7
Data: {date.today().strftime("%d.%m.%Y")}
"""

import os, random, shutil, json

FOLDER_SURSA = r"{folder_sursa}"
FOLDER_DEST  = r"{folder_dest}"
PCT_TRAIN    = {pct_tr}
PCT_VAL      = {pct_vl}
SEED         = {seed_m}
CLASE        = {clase_m_lista}

# Gaseste toate perechile imagine + adnotare
extensii_img = {{".jpg", ".jpeg", ".png"}}
fisiere_img  = {{os.path.splitext(f)[0]: f
                for f in os.listdir(FOLDER_SURSA)
                if os.path.splitext(f)[1].lower() in extensii_img}}
fisiere_txt  = {{os.path.splitext(f)[0]: f
                for f in os.listdir(FOLDER_SURSA)
                if f.endswith(".txt")}}

perechi = [k for k in fisiere_img if k in fisiere_txt]
print(f"Gasit {{len(perechi)}} perechi complete.")

# Shuffle
random.seed(SEED)
random.shuffle(perechi)

n       = len(perechi)
n_train = max(1, int(n * PCT_TRAIN / 100))
n_val   = max(1, int(n * PCT_VAL   / 100))
splits  = {{
    "train": perechi[:n_train],
    "val":   perechi[n_train:n_train+n_val],
    "test":  perechi[n_train+n_val:],
}}

# Creeaza structura foldere
for split in ["train","val","test"]:
    os.makedirs(os.path.join(FOLDER_DEST, "images", split), exist_ok=True)
    os.makedirs(os.path.join(FOLDER_DEST, "labels", split), exist_ok=True)

# Copiaza fisierele
for split_name, lista in splits.items():
    for nume in lista:
        f_img = fisiere_img[nume]
        f_txt = fisiere_txt[nume]
        shutil.copy(
            os.path.join(FOLDER_SURSA, f_img),
            os.path.join(FOLDER_DEST, "images", split_name, f_img)
        )
        shutil.copy(
            os.path.join(FOLDER_SURSA, f_txt),
            os.path.join(FOLDER_DEST, "labels", split_name, f_txt)
        )
    print(f"  {{split_name}}: {{len(lista)}} imagini")

# data.yaml
yaml = f"path: {{FOLDER_DEST}}\\\\n"
yaml += "train: images/train\\nval:   images/val\\ntest:  images/test\\n\\n"
yaml += f"nc: {{len(CLASE)}}\\nnames:\\n"
for i, cls in enumerate(CLASE):
    yaml += f"  {{i}}: {{cls}}\\n"

with open(os.path.join(FOLDER_DEST, "data.yaml"), "w") as f:
    f.write(yaml)

print(f"\\nDataset split gata in: {{FOLDER_DEST}}")
print(f"Train: {{len(splits['train'])}} | Val: {{len(splits['val'])}} | Test: {{len(splits['test'])}}")
print("\\nComanda antrenare:")
print(f"  yolo train model=yolov8n.pt data={{FOLDER_DEST}}/data.yaml epochs=50 imgsz=640")
'''

    st.code(script, language="python")

    buf_script = BytesIO(script.encode("utf-8"))
    st.download_button(
        "Descarca script split_dataset.py",
        data=buf_script,
        file_name="split_dataset.py",
        mime="text/plain"
    )

    st.markdown("""
    <div class="card-albastru">
        <strong>Cum rulezi scriptul:</strong><br>
        1. Descarca scriptul<br>
        2. Pune-l in acelasi folder cu imaginile<br>
        3. In terminal: <code>python split_dataset.py</code>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# TAB 3 — VERIFICARE DATASET
# ══════════════════════════════════════════════════════
with tab_verificare:
    st.markdown('<p class="titlu">Verificare dataset — upload data.yaml + structura</p>',
                unsafe_allow_html=True)

    st.markdown("""
    <div class="card-albastru">
        Verifica daca un dataset este corect structurat inainte de antrenare.
        Incarca fisierul <code>data.yaml</code> si aplicatia raporteaza ce lipseste.
    </div>
    """, unsafe_allow_html=True)

    yaml_file = st.file_uploader("Incarca data.yaml", type=["yaml","yml"])

    if yaml_file:
        try:
            import yaml as pyyaml
            continut = yaml_file.read().decode("utf-8")
            data = pyyaml.safe_load(continut)

            st.code(continut, language="yaml")

            # Verificari
            erori = []; ok = []

            for camp in ["path","train","val","nc","names"]:
                if camp in data:
                    ok.append(f"Campul '{camp}' prezent")
                else:
                    erori.append(f"Campul '{camp}' lipsa!")

            if "nc" in data and "names" in data:
                nc   = data["nc"]
                names = data["names"]
                n_names = len(names) if isinstance(names, (list, dict)) else 0
                if nc == n_names:
                    ok.append(f"nc={nc} coincide cu nr. de clase ({n_names})")
                else:
                    erori.append(f"nc={nc} dar {n_names} clase in 'names'!")

            for msg in ok:
                st.success(msg)
            for msg in erori:
                st.error(msg)

            if not erori:
                st.balloons()
                st.success("data.yaml valid — gata de antrenat!")

        except ImportError:
            st.warning("Instaleaza pyyaml: pip install pyyaml")
            st.code(yaml_file.read().decode("utf-8"))
        except Exception as e:
            st.error(f"Eroare la parsarea YAML: {e}")
    else:
        # Afisare template data.yaml
        st.markdown("**Template data.yaml:**")
        st.code("""
path: ./dataset_culturi_gorj
train: images/train
val:   images/val
test:  images/test

nc: 4
names:
  0: grau
  1: porumb
  2: rapita
  3: vegetatie_lipsa
        """, language="yaml")

st.markdown("---")

# ─── Concept Ziua 7 ───────────────────────────────────────────────────────────
with st.expander("Conceptul Zilei 7 — Split dataset cu shuffle"):
    st.markdown("""
**De ce shuffle inainte de split?**
Fara shuffle, daca ai adnotat imaginile in ordine (toate parcelele de grau primele,
apoi porumb etc.), train-ul va contine doar grau si val doar porumb — model prost.
Cu shuffle, fiecare split are o distributie reprezentativa.
""")
    st.code("""
import random, shutil, os

fisiere = ["img001", "img002", ..., "img100"]

# OBLIGATORIU: shuffle cu seed fix (reproductibil)
random.seed(42)
random.shuffle(fisiere)

n_train = int(len(fisiere) * 0.70)   # 70 imagini
n_val   = int(len(fisiere) * 0.20)   # 20 imagini
# test   = restul             0.10   # 10 imagini

train = fisiere[:n_train]
val   = fisiere[n_train:n_train+n_val]
test  = fisiere[n_train+n_val:]

# Copiaza fisierele in structura corecta
for nume in train:
    shutil.copy(f"sursa/{nume}.jpg", f"dataset/images/train/{nume}.jpg")
    shutil.copy(f"sursa/{nume}.txt", f"dataset/labels/train/{nume}.txt")
    """, language="python")
    st.info("**shutil.copy(src, dst)** — copiaza fisierul (nu muta). "
            "Pastreaza originalele intacte pentru siguranta.")
