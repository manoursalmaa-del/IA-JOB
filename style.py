import streamlit as st

# Liste complète de toutes les pages de l'application
PAGES = ["Profil", "Accueil", "Domaines", "Entreprises", "Stages IT", "generator_cv", "Candidature", "Analyse", "Sources"]

def apply_custom_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Bricolage+Grotesque:wght@700;800&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Plus Jakarta Sans', sans-serif; 
    }
    
    h1, h2, h3 { 
        font-family: 'Bricolage Grotesque', sans-serif !important; 
        letter-spacing: -.02em; 
    }
    
    /* Conteneur principal */
    .block-container { 
        max-width: 1240px; 
        padding-top: 2.5rem !important; 
        padding-bottom: 2rem !important;
    }
    
    /* Logo / Marque en haut à gauche */
    .brand { 
        font: 800 1.25rem 'Bricolage Grotesque'; 
        color: #1E293B;
        line-height: 1.15;
    }
    
    /* Style des boutons de la barre de navigation */
    div[data-testid="column"] div.stButton > button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        padding: 8px 14px !important;
        height: auto !important;
        min-height: 40px !important;
        font-size: 0.88rem !important;
        border: 1px solid #E2E8F0 !important;
        background-color: #FFFFFF !important;
        color: #475569 !important;
        transition: all 0.25s ease-in-out !important;
    }
    
    /* Bouton de la page active (Rouge / Corail vif) */
    div[data-testid="column"] div.stButton > button[kind="primary"] {
        background: #FF4B4B !important;
        border: none !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 14px rgba(255, 75, 75, 0.35) !important;
    }
    
    div[data-testid="column"] div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08) !important;
    }
    
    /* Section Hero (Titre Principal) */
    .hero h1 { 
        font-size: 3.2rem; 
        line-height: 1.08; 
        color: #0F172A;
        font-weight: 800;
        margin-bottom: 0.8rem; 
    }
    
    .hero p { 
        color: #64748B; 
        font-size: 1.05rem; 
        line-height: 1.5;
        max-width: 52ch; 
    }
    
    /* Bouton principal "Explorateur" */
    div.stButton > button[kind="primary"] {
        background: #FF4B4B !important;
        border-color: #FF4B4B !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 14px rgba(255, 75, 75, 0.35) !important;
    }
    
    /* ===== CARTES KPIS ULTRA-COLORÉES ET ARRONDIES ===== */
    .kpi { 
        border-radius: 24px; 
        padding: 24px 22px; 
        color: #FFFFFF; 
        min-height: 160px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 10px 20px -5px rgba(0,0,0,0.06);
        transition: transform 0.3s ease;
    }
    
    .kpi:hover {
        transform: translateY(-4px);
    }
    
    .kpi small { 
        font-weight: 700; 
        font-size: 0.95rem;
        opacity: 0.95; 
        display: block;
    }
    
    .kpi b { 
        display: block; 
        font: 800 3.2rem/1 'Bricolage Grotesque'; 
        margin: 8px 0 4px; 
    }
    
    .kpi span { 
        font-size: 0.85rem; 
        opacity: 0.9; 
        font-weight: 600;
    }
    
    .k1 { background: #2B3FD6; } /* Bleu électrique */
    .k2 { background: #E23D6E; } /* Rose / Framboise vif */
    .k3 { background: #17B890; color: #FFFFFF; } /* Vert menthe / Émeraude */
    .k4 { background: #F5B324; color: #1E293B; } /* Jaune / Or vif */
    
    /* Style des Cartes Entreprises & Domaines */
    .card { 
        border: 1px solid #E2E8F0; 
        border-radius: 20px; 
        padding: 18px 22px; 
        margin-bottom: 12px; 
        background: #FFFFFF;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        transition: all 0.25s ease;
    }
    
    .card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
    }
    
    .score { 
        display: inline-block; 
        width: 46px; 
        height: 46px; 
        line-height: 46px; 
        text-align: center;
        border-radius: 50%; 
        color: #FFFFFF; 
        font-weight: 800; 
        margin-right: 14px; 
    }
    
    .domain-card { 
        border-radius: 20px; 
        padding: 22px; 
        text-align: center;
        border: 1px solid #E2E8F0; 
        background: #FFFFFF; 
        margin-bottom: 10px; 
        transition: all 0.3s ease;
    }
    
    .domain-card:hover { 
        transform: translateY(-4px);
        box-shadow: 0 12px 25px rgba(43, 63, 214, 0.12);
        border-color: #93C5FD;
    }
    
    .domain-icon { font-size: 2.5rem; }
    .domain-name { font-weight: 700; margin-top: 8px; color: #1E293B; }
    .domain-count { color: #64748B; font-size: 0.9rem; }
    
    /* Badges colorés */
    .badge { 
        display: inline-block; 
        padding: 4px 12px; 
        border-radius: 50px;
        font-size: 0.78rem; 
        font-weight: 700; 
        margin-right: 6px; 
        margin-top: 4px;
    }
    .b-blue { background: #EFF6FF; color: #2563EB; border: 1px solid #BFDBFE; }
    .b-green { background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; }
    .b-purple { background: #F5F3FF; color: #7C3AED; border: 1px solid #DDD6FE; }
    
    /* Bouton d'action / Email */
    .email-btn { 
        display: inline-block; 
        background: #FF4B4B;
        color: #FFFFFF !important; 
        padding: 12px 26px; 
        border-radius: 50px;
        text-decoration: none; 
        font-weight: 700; 
        font-size: 0.9rem;
        box-shadow: 0 6px 18px rgba(255, 75, 75, 0.35);
        transition: all 0.3s ease;
    }
    
    .email-btn:hover { 
        transform: translateY(-2px); 
        box-shadow: 0 8px 22px rgba(255, 75, 75, 0.5); 
        color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

def init_session_state():
    st.session_state.setdefault("page", "Accueil")
    st.session_state.setdefault("domaine", None)
    st.session_state.setdefault("entreprise_idx", None)
    st.session_state.setdefault("selected_job", None)
    st.session_state.setdefault("user_profile", None)
    st.session_state.setdefault("tracked", {})

def goto(page: str) -> None:
    st.session_state.page = page
    st.rerun()  # <--- CRUCIAL : Force la mise à jour de Streamlit vers la nouvelle page

def score_color(s: float) -> str:
    return ("#17B890" if s >= 4.5 else "#2B3FD6" if s >= 4.0
            else "#7A4DE8" if s >= 3.5 else "#E23D6E")