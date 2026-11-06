import streamlit as st
from data import DATA, DOMAINES, CSV_PATH
from style import goto, score_color

def page_accueil() -> None:
    left, right = st.columns([1.15, .85], gap="large")
    with left:
        st.markdown('<div class="hero"><h1>Les meilleures entreprises IA & informatique de Marrakech.</h1>'
                    '<p>Explorez les agences, entreprises et startups du digital, découvrez leurs coordonnées et envoyez-leur votre CV en un clic.</p></div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([2, 1.5, 1])
        c1.text_input("Recherche", key="q_home", placeholder="ex. intelligence artificielle")
        c2.selectbox("Domaine", ["Tous"] + list(DOMAINES.keys()), key="dom_home")
        c3.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
        c3.button("Explorer", type="primary", use_container_width=True, on_click=goto, args=("Domaines",))
    with right:
        coords = DATA.dropna(subset=["latitude", "longitude"]).head(20)
        if not coords.empty:
            st.map(coords.rename(columns={"latitude": "lat", "longitude": "lon"})[["lat", "lon"]], height=260)

    total = len(DATA)
    with_email = len(DATA[DATA["email"] != ""])
    with_site = len(DATA[DATA["site_web"] != ""])
    domains_n = DATA["domaine"].nunique()

    k = st.columns(4)
    kpis = [
        ("k1", "Entreprises référencées", f"{total}", "base Google Places"),
        ("k2", "Emails disponibles", f"{with_email}", "prêts à contacter"),
        ("k3", "Sites web", f"{with_site}", "à explorer"),
        ("k4", "Domaines couverts", f"{domains_n}", "IA, web, marketing..."),
    ]
    for col, (cls, label, val, sub) in zip(k, kpis):
        col.markdown(f'<div class="kpi {cls}"><small>{label}</small><b>{val}</b><span>{sub}</span></div>', unsafe_allow_html=True)

    # ✅ NOUVEAU CODE CORRIGÉ :
    st.subheader("Top entreprises (note Google)")
    top = (DATA[DATA["note_num"] > 0]
           .sort_values("note_num", ascending=False)
           .head(5))

    for _, r in top.iterrows():
        sc = int(r["note_num"] * 20)  # note sur 100
        
        # Conteneur natif Streamlit sans bug React / removeChild
        with st.container(border=True):
            col_score, col_info = st.columns([0.15, 0.85])
            
            with col_score:
                st.markdown(
                    f'<span class="score" style="background:{score_color(r.note_num)}">{sc}</span>',
                    unsafe_allow_html=True
                )
            
            with col_info:
                st.markdown(
                    f"**ID #{r['id']} - {r['nom']}** &nbsp;·&nbsp; `{r['domaine']}` &nbsp;·&nbsp; "
                    f"*⭐ {r['note_num']:.1f} ({r['nombre_avis']} avis)*"
                )