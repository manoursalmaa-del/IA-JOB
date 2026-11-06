import os
from urllib.parse import quote

import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================
st.set_page_config(page_title="AI Marrakech Ecosystem Intelligence",
                   page_icon="🧭", layout="wide")

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "entreprises_marrakech_emails.csv")
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    # Nettoyage
    for col in ["nom", "type_acteur", "secteur", "sous_secteur", "services_ia",
                "adresse", "quartier", "telephone", "site_web", "email",
                "categorie_google", "note", "query", "linkedin", "instagram",
                "facebook", "google_maps"]:
        if col in df.columns:
            df[col] = (df[col].astype(str)
                       .replace("nan", "").replace("Non renseigné", "")
                       .replace("À vérifier", "").str.strip())
    # Note en numérique
    df["note_num"] = pd.to_numeric(df["note"], errors="coerce").fillna(0.0)
    df["nombre_avis"] = pd.to_numeric(df.get("nombre_avis", 0),
                                      errors="coerce").fillna(0).astype(int)
    return df


try:
    DATA = load_data()
except FileNotFoundError:
    st.error(f"❌ Fichier introuvable : {CSV_PATH}\n\n"
             "Placez `entreprises_marrakech_emails.csv` dans le même dossier que ce script.")
    st.stop()