import streamlit as st
import re
import sys
import os
from candidature_storage import authenticate_user, create_user, init_database

# Gestion des imports selon la structure de votre projet
try:
    from style import goto
except ModuleNotFoundError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from style import goto

# ============================================================
# FONCTIONS DE SÉCURITÉ ET VALIDATION
# ============================================================

def is_valid_email(email: str) -> bool:
    """Vérifie le format de l'adresse email."""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email))

# ============================================================
# PAGE PRINCIPALE : CRÉATION DE PROFIL ET INSCRIPTION
# ============================================================

def page_profil() -> None:
    init_database()

    profile = st.session_state.get("user_profile")
    if profile and profile.get("id"):
        st.title("👤 Mon compte IA JOB")
        st.success(f"Connecté en tant que {profile.get('prenom', '')} {profile.get('nom', '')} · {profile.get('email', '')}")
        if st.button("Se déconnecter", type="secondary", key="profil_logout"):
            st.session_state.pop("user_profile", None)
            st.session_state["candidatures_list"] = []
            st.session_state["page"] = "Profil"
            st.rerun()
        return
    # Invalide les anciens profils conservés uniquement en session, sans identifiant DB.
    if profile:
        st.session_state.pop("user_profile", None)

    with st.expander("🔐 Déjà un compte ? Se connecter", expanded=False):
        with st.form("connexion_compte_ia_job"):
            login_email = st.text_input("Adresse e-mail", key="connexion_email")
            login_password = st.text_input("Mot de passe", type="password", key="connexion_mot_de_passe")
            login_submit = st.form_submit_button("Se connecter", type="primary", use_container_width=True)
        if login_submit:
            authenticated = authenticate_user(login_email, login_password)
            if authenticated:
                st.session_state["user_profile"] = authenticated
                st.session_state["user_registered"] = True
                st.session_state["candidatures_list"] = []
                st.toast(f"Bienvenue {authenticated.get('prenom', '')} !", icon="👋")
                st.rerun()
            else:
                st.error("Adresse e-mail ou mot de passe incorrect.")

    # Styles visuels
    st.markdown("""
    <style>
    .hero-profile {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #EC4899 100%);
        border-radius: 24px;
        padding: 35px 28px;
        color: white;
        box-shadow: 0 15px 30px rgba(79, 70, 229, 0.25);
    }
    .hero-profile h1 {
        color: #FFFFFF !important;
        font-size: 2.2rem;
        margin-bottom: 12px;
    }
    .hero-profile p {
        color: #EEF2FF;
        font-size: 1.05rem;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

    # Titre général
    st.markdown("<h2 style='text-align: center; color: #1E293B;'>🤖 Bienvenue sur AI Marrakech Ecosystem</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B; font-size: 1.1rem; margin-bottom: 30px;'>Rejoignez l'écosystème IA & Tech de Marrakech et boostez votre carrière.</p>", unsafe_allow_html=True)

    # Disposition en 2 colonnes
    col_gauche, col_droite = st.columns([1.1, 1.4], gap="large")

    # ------------------------------------------------------------
    # PARTIE GAUCHE : PRÉSENTATION
    # ------------------------------------------------------------
    with col_gauche:
        st.markdown("""
        <div class="hero-profile">
            <h1>🚀 Explorez le Hub IA de Marrakech</h1>
            <p>Accédez à la plateforme d'intelligence territoriale la plus complète dédiée aux entreprises, startups et professionnels de la Tech à Marrakech.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        
        with st.container(border=True):
            st.markdown("<b>🏢 Entreprises & Startups IA</b>", unsafe_allow_html=True)
            st.caption("Consultez les coordonnées, domaines d'activité et la présence numérique des acteurs du digital.")

        with st.container(border=True):
            st.markdown("<b>💼 Opportunités & Stages IT</b>", unsafe_allow_html=True)
            st.caption("Postulez directement aux offres de stages PFE, emplois et opportunités de recrutement locales.")

        with st.container(border=True):
            st.markdown("<b>📊 Analyse de l'Écosystème</b>", unsafe_allow_html=True)
            st.caption("Visualisez les tendances du marché, les compétences recherchées et la dynamique technologique.")

    # ------------------------------------------------------------
    # PARTIE DROITE : FORMULAIRE D'INSCRIPTION
    # ------------------------------------------------------------
    with col_droite:
        st.markdown("### 📝 Créer mon profil")
        
        with st.form(key="registration_form", clear_on_submit=False):
            
            # 1. Informations Personnelles
            st.markdown("##### 👤 Informations Personnelles")
            c_prenom, c_nom = st.columns(2)
            prenom = c_prenom.text_input("Prénom *", placeholder="ex. Youssef")
            nom = c_nom.text_input("Nom *", placeholder="ex. El Amrani")
            
            email = st.text_input("Adresse e-mail *", placeholder="ex. youssef.amrani@gmail.com")
            
            c_pass1, c_pass2 = st.columns(2)
            password = c_pass1.text_input("Mot de passe *", type="password", placeholder="8 caractères minimum")
            confirm_password = c_pass2.text_input("Confirmer le mot de passe *", type="password", placeholder="Confirmer")

            st.divider()

            # 2. Profil Professionnel
            st.markdown("##### 🎯 Profil & Domaines d'Intérêt")
            c_profil, c_ville = st.columns(2)
            
            profils_options = [
                "Étudiant", "Stagiaire", "Jeune diplômé", "Développeur", 
                "Data Analyst", "Data Scientist", "Ingénieur en IA", 
                "Entrepreneur / Startup", "Recruteur / RH", "Autre"
            ]
            profil_pro = c_profil.selectbox("Profil professionnel *", profils_options)
            ville = c_ville.text_input("Ville *", value="Marrakech")

            domaines_options = [
                "Intelligence Artificielle", "Data Science", "Machine Learning", 
                "Deep Learning", "Développement Web & Mobile", 
                "Cybersécurité", "Automatisation / RPA"
            ]
            domaine_interet = st.multiselect("Centres d'intérêt principaux", domaines_options, default=["Intelligence Artificielle"])

            st.divider()

            # 3. CV
            st.markdown("##### 📄 Télécharger votre CV (Optionnel)")
            uploaded_cv = st.file_uploader("Format : PDF, DOC ou DOCX", type=["pdf", "doc", "docx"])

            # 4. Conditions
            coche_cgv = st.checkbox("J'accepte les conditions d'utilisation et la politique de confidentialité *")

            # Bouton de soumission
            submit_button = st.form_submit_button(
                label="✨ Créer mon profil et accéder à l'accueil", 
                type="primary", 
                use_container_width=True
            )

        # ------------------------------------------------------------
        # VALIDATION ET REDIRECTION DIRECTE
        # ------------------------------------------------------------
        if submit_button:
            if not prenom or not nom or not email or not password or not confirm_password or not ville:
                st.error("⚠️ Veuillez remplir tous les champs obligatoires (*).")
            
            elif not is_valid_email(email):
                st.error("⚠️ L'adresse email saisie est invalide.")
            
            elif len(password) < 8:
                st.error("⚠️ Le mot de passe doit contenir au moins 8 caractères.")
            
            elif password != confirm_password:
                st.error("⚠️ Les mots de passe ne correspondent pas.")
            
            elif not coche_cgv:
                st.warning("⚠️ Veuillez accepter les conditions d'utilisation.")
            
            else:
                # Création de compte persistante dans la base SQLite existante.
                profile_data = {
                    "prenom": prenom,
                    "nom": nom,
                    "email": email,
                    "profil_pro": profil_pro,
                    "ville": ville,
                    "domaines_interet": domaine_interet,
                    "cv_filename": uploaded_cv.name if uploaded_cv else None,
                }
                try:
                    user_id = create_user(profile_data, password)
                except ValueError as erreur:
                    st.error(str(erreur))
                else:
                    user_profile = {
                        **profile_data,
                        "id": user_id,
                        "is_logged_in": True,
                    }
                    st.session_state["user_profile"] = user_profile
                    st.session_state["user_registered"] = True
                    st.session_state["candidatures_list"] = []
                    st.toast(f"Félicitations {prenom} ! Votre compte a été créé.", icon="🎉")
                    goto("Accueil")
                    st.rerun()
