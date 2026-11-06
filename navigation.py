
import streamlit as st


def render_navigation():
  # 1. Liste unifiée des noms de pages (identique aux clés de votre router)
  pages = [
      "Profil",
      "Accueil",
      "Domaines",
      "Entreprises",
      "Stages IT",
      "Matching IA",
      "Générateur CV",  # Nom propre pour l'affichage
      "Candidature",
      "Suivi",
      "Analyse",
      "Sources",

  ]

  # 2. Initialisation de la page par défaut
  if "page" not in st.session_state:
    st.session_state.page = "Accueil"

  # 3. Alignement & Mise en page de la barre de navigation
  col_brand, col_nav = st.columns([2.5, 7.5])

  with col_brand:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 8px; padding-top: 2px;">
            <div style="
                background: #2563EB;
                width: 36px;
                height: 36px;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                color: white;
                flex-shrink: 0;
            ">⚡</div>
            <div style="font-family: 'Plus Jakarta Sans', sans-serif;">
                <div style="font-size: 18px; font-weight: 800; color: #0F172A; line-height: 1; white-space: nowrap;">
                    IA JOB
                </div>
                <div style="font-size: 9px; font-weight: 700; color: #2563EB; text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap;">
                    Career Platform
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  with col_nav:
    cols = st.columns(len(pages))
    for i, page_name in enumerate(pages):
      # Vérification si la page courante est active
      is_active = st.session_state.page == page_name
      btn_type = "primary" if is_active else "secondary"

      # Affichage dynamique avec key unique pour éviter l'erreur React/insertBefore
      if cols[i].button(
          page_name,
          key=f"nav_btn_{i}_{page_name.replace(' ', '_')}",
          type=btn_type,
          use_container_width=True,
      ):
        st.session_state.page = page_name
        st.rerun()

  st.divider()
