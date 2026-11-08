from datetime import datetime
import streamlit as st

if "last_refresh_time" not in st.session_state:
    st.session_state.last_refresh_time = datetime.now()

last_refresh_time_val = st.session_state.last_refresh_time

def last_refresh(source_name="Remotive"):
    """Renvoie les informations de la dernière synchronisation."""
    return {
        "finished_at": st.session_state.last_refresh_time.strftime("%Y-%m-%d %H:%M:%S"),
        "message": "Actualisation réussie"
    }

def normaliser_plateforme(nom_plateforme):
    """Normalise le nom de la plateforme source."""
    if not nom_plateforme:
        return "Autre"
    p = str(nom_plateforme).strip().lower()
    if "link" in p:
        return "LinkedIn"
    elif "ind" in p:
        return "Indeed"
    elif "rekr" in p:
        return "ReKrute"
    elif "remot" in p:
        return "Remotive"
    return str(nom_plateforme).strip().capitalize()

def load_offers():
    """Charge ou initialise la base de données globale d'offres dans la session."""
    if "offres_database" not in st.session_state:
        st.session_state.offres_database = [
            {
                "id": 1,
                "titre": "Stage Développeur Python / IA",
                "entreprise": "TechMarrakech",
                "ville": "Marrakech",
                "source": "LinkedIn",
                "domaine": "Intelligence Artificielle",
                "type_offre": "Stage",
                "description": "Stage de développement Python et IA basé à Marrakech. Participation à la conception de modèles et automatisation.",
                "url_offre": "https://www.linkedin.com/jobs/",
                "date_publication": "2026-11-05",
                "sources": ["LinkedIn"],
                "source_urls": {"LinkedIn": "https://www.linkedin.com/jobs/"}
            },
            {
                "id": 2,
                "titre": "Stage Data Analyst Junior",
                "entreprise": "Maroc Digital Lab",
                "ville": "Marrakech",
                "source": "Indeed",
                "domaine": "Data & Analytics",
                "type_offre": "Stage",
                "description": "Stage analyse de données et Business Intelligence. Manipulation de DataFrames Pandas et création de tableaux de bord.",
                "url_offre": "https://ma.indeed.com/",
                "date_publication": "2026-11-04",
                "sources": ["Indeed"],
                "source_urls": {"Indeed": "https://ma.indeed.com/"}
            },
            {
                "id": 3,
                "titre": "Stage Assistant Business Intelligence",
                "entreprise": "Atlas Cloud Solutions",
                "ville": "Marrakech",
                "source": "Remotive",
                "domaine": "Data",
                "type_offre": "Stage",
                "description": "Stage reporting et tableaux de bord BI pour des projets internationaux en télétravail.",
                "url_offre": "https://remotive.com/",
                "date_publication": "2026-11-02",
                "sources": ["Remotive"],
                "source_urls": {"Remotive": "https://remotive.com/"}
            }
        ]
    return st.session_state.offres_database

def save_offers(offers):
    """Sauvegarde la liste des offres dans la session."""
    st.session_state.offres_database = offers

def refresh_allowed(source_name="Remotive"):
    """Vérifie si l'actualisation est permise."""
    return True, "Actualisation autorisée"

def start_refresh(source_name="Remotive"):
    """Marque le début d'une actualisation."""
    st.session_state.last_refresh_time = datetime.now()

def finish_refresh(*args, **kwargs):
    """Gère la fin d'une actualisation de manière flexible (évite les erreurs de paramètres)."""
    st.session_state.last_refresh_time = datetime.now()