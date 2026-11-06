import os
import pandas as pd
import streamlit as st
import pandas as pd
import os

# Chemins des données
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "entreprises.csv")

# Chargement / Définition des données principales
DOMAINES = ["Intelligence Artificielle", "Développement Web", "Cybersécurité", "Data Science", "Cloud & DevOps"]

# Définition de la variable DATA attendue par accueil.py et entreprises.py
DATA = {
    "domaines": DOMAINES,
    # Ajoutez ici d'autres données globales si nécessaire
}

CSV_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "entreprises_marrakech_emails.csv"
)

DOMAINES = {
    "Intelligence Artificielle": "🤖",
    "Développement Web & Mobile": "💻",
    "Marketing Digital": "📢",
    "Informatique & Technologies": "🖥️",
    "Conseil & Consulting": "💼",
    "Formation & Éducation": "🎓",
    "Startups & Coworking": "🚀",
    "Agences Digitales": "🎨",
}

def classer(row: pd.Series) -> str:
    t = " ".join([str(row.get(c, "")) for c in
                  ["secteur", "sous_secteur", "services_ia", "type_acteur",
                   "nom", "categorie_google", "query"]]).lower()

    def has(*kws):
        return any(k in t for k in kws)

    if has("intelligence artificielle", " ai", "ia ", "machine learning",
           "deep learning", "nlp", "chatbot", "agents ia", "computer vision"):
        return "Intelligence Artificielle"
    if has("web", "mobile", "site internet", "développement", "logiciel",
           "software", "app mobile"):
        return "Développement Web & Mobile"
    if has("marketing", "communication", "seo", "branding", "publicité",
           "référencement", "digital"):
        return "Marketing Digital"
    if has("conseil", "consulting", "consultant", "audit", "comptable",
           "fiduciaire", "expert"):
        return "Conseil & Consulting"
    if has("formation", "école", "académie", "institut", "université",
           "faculté", "enseignement"):
        return "Formation & Éducation"
    if has("startup", "coworking", "incubateur", "business center"):
        return "Startups & Coworking"
    if has("agence"):
        return "Agences Digitales"
    return "Informatique & Technologies"

@st.cache_data
def load_data() -> pd.DataFrame:
    if not os.path.exists(CSV_PATH):
        st.error(f"❌ Fichier introuvable : {CSV_PATH}")
        return pd.DataFrame()

    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    
    if "id" not in df.columns:
        df["id"] = df.index + 1
    else:
        df["id"] = pd.to_numeric(df["id"], errors="coerce").fillna(df.index + 1).astype(int)

    for col in ["nom", "type_acteur", "secteur", "sous_secteur", "services_ia",
                "adresse", "quartier", "telephone", "site_web", "email",
                "categorie_google", "note", "query", "linkedin", "instagram",
                "facebook", "google_maps"]:
        if col in df.columns:
            df[col] = (df[col].astype(str)
                       .replace("nan", "").replace("Non renseigné", "")
                       .replace("À vérifier", "").str.strip())
        else:
            df[col] = ""

    df["latitude"] = pd.to_numeric(df.get("latitude"), errors="coerce")
    df["longitude"] = pd.to_numeric(df.get("longitude"), errors="coerce")
    df["note_num"] = pd.to_numeric(df.get("note"), errors="coerce").fillna(0.0)
    df["nombre_avis"] = pd.to_numeric(df.get("nombre_avis", 0), errors="coerce").fillna(0).astype(int)
    
    df["domaine"] = df.apply(classer, axis=1)
    return df

DATA = load_data()