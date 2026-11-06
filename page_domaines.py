import streamlit as st
import pandas as pd
from data import DATA, ALL_DOMAINES
from style import goto

def page_domaines() -> None:
    st.subheader("🌐 Domaines d'activité (IA & Développement)")

    if DATA.empty:
        st.warning("Aucune donnée chargée.")
        return

    # Mots-clés pour filtrer spécifiquement IA et Développement
    keywords_ia_dev = [
        "ia", "intelligence artificielle", "artificial intelligence",
        "développement", "developpement", "dev", "web", "software",
        "logiciel", "informatique", "data", "digital"
    ]

    # Séparation des domaines IA & Développeurs et des autres domaines du dataset
    domaines_ia_dev = [
        d for d in ALL_DOMAINES 
        if any(kw in d.lower() for kw in keywords_ia_dev)
    ]
    domaines_autres = [d for d in ALL_DOMAINES if d not in domaines_ia_dev]

    # Onglets pour classer proprement sans rechargements HTML instables
    tab1, tab2 = st.tabs(["🤖 IA & Développement", "📂 Tous les domaines"])

    with tab1:
        st.markdown("### Entreprises en IA & Développement Software")
        if not domaines_ia_dev:
            st.info("Aucun domaine IA / Développement détecté explicitement dans le dataset.")
        else:
            cols = st.columns(3)
            for idx, dom in enumerate(domaines_ia_dev):
                count = len(DATA[DATA["domaine"] == dom])
                with cols[idx % 3]:
                    with st.container(border=True):
                        st.markdown(f"**{dom}**")
                        st.caption(f"🏢 {count} entreprise(s)")
                        if st.button("Voir les entreprises", key=f"btn_iadev_{idx}", use_container_width=True):
                            st.session_state.domaine = dom
                            goto("Entreprises")
                            st.rerun()

    with tab2:
        st.markdown("### Ensemble des domaines disponibles")
        cols_all = st.columns(3)
        for idx, dom in enumerate(ALL_DOMAINES):
            count = len(DATA[DATA["domaine"] == dom])
            with cols_all[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"**{dom}**")
                    st.caption(f"🏢 {count} entreprise(s)")
                    if st.button("Voir les entreprises", key=f"btn_all_{idx}", use_container_width=True):
                        st.session_state.domaine = dom
                        goto("Entreprises")
                        st.rerun()