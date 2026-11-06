
import streamlit as st
# Configuration de la page
st.set_page_config(
    page_title="IA JOB · Plateforme de Carrière",
    page_icon="⚡",
    layout="wide"
)

# Application des styles et initialisation
from style import apply_custom_styles, init_session_state, goto, score_color
from navigation import render_navigation

apply_custom_styles()
init_session_state()

# Rendu de la barre de navigation personnalisée avec IA JOB
render_navigation()

# Importation des pages de l'application
from accueil import page_accueil
from entreprises import page_domaines, page_entreprises, page_detail, page_candidature, page_analyse, page_sources
from page_suivi import page_suivi_candidatures
from stages import page_stages
from matching_ia import page_matching_ia
from profil import page_profil

try:
    from generator_cv import page_cv_generator
except ImportError:
    page_cv_generator = None

router = {
    "Profil": page_profil,
    "Accueil": page_accueil,
    "Domaines": page_domaines,
    "Entreprises": page_entreprises,
    "Stages IT": page_stages,
    "Matching IA": page_matching_ia,

    "🤖 Générateur CV": (
        page_cv_generator
        if page_cv_generator
        else (lambda: st.error("❌ Module generator_cv.py non chargé"))
    ),
    "Générateur CV": (
        page_cv_generator
        if page_cv_generator
        else (lambda: st.error("❌ Module generator_cv.py non chargé"))
    ),
    "Générateur": (
        page_cv_generator
        if page_cv_generator
        else (lambda: st.error("❌ Module generator_cv.py non chargé"))
    ),
    "générateur": (
        page_cv_generator
        if page_cv_generator
        else (lambda: st.error("❌ Module generator_cv.py non chargé"))
    ),
    "Détail": page_detail,
    "Candidature": page_candidature,
    "Suivi": page_suivi_candidatures,
    "Analyse": page_analyse,
    "Sources": page_sources,
}
# Affichage de la page sélectionnée
current_page = st.session_state.get("page", "Accueil")
if current_page in router:
    router[current_page]()
current_page = st.session_state.get("page", "Accueil")


# Pied de page
st.divider()
st.markdown(
    '<div style="text-align:center; color:#64748B; font-size:0.85rem; font-weight:600; padding:10px 0;">'
    '⚡ <b>IA JOB</b> — Intelligence Career Platform'
    '</div>',
    unsafe_allow_html=True
)
