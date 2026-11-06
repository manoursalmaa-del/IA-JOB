import streamlit as st
import pandas as pd
from fetch_jobs import load_or_create_jobs



def page_stages() -> None:
    from datetime import date, timedelta
    from hashlib import sha1
    from urllib.parse import urlparse

    try:
        import plotly.express as px
    except ImportError:
        px = None

    palette = ["#2563EB", "#7C3AED", "#06B6D4", "#10B981", "#F59E0B", "#EC4899"]

    if "offres_donnees_session" not in st.session_state:
        st.session_state["offres_donnees_session"] = load_or_create_jobs()
    df_jobs = st.session_state["offres_donnees_session"]
    if not isinstance(df_jobs, pd.DataFrame):
        df_jobs = pd.DataFrame(df_jobs)
    total = len(df_jobs)
    source_count = df_jobs["source"].fillna("").astype(str).str.strip().replace("", pd.NA).nunique() if total and "source" in df_jobs.columns else 0
    with st.container(border=True):
        head, total_col = st.columns([4, 1])
        with head:
            st.caption("IA JOB · CARRIÈRES & OPPORTUNITÉS")
            st.title("💼 Trouvez votre prochaine opportunité")
            st.write("Explorez les meilleures offres d'emploi, stages et opportunités IT & IA.")
            st.markdown("**Votre prochaine opportunité commence ici !**")
        with total_col:
            st.metric("Offres disponibles", total)
    if df_jobs.empty:
        st.info("Aucune offre n’est disponible depuis les sources actuelles. Réessayez plus tard.")
        return

    df = df_jobs.copy()
    colonnes = ("titre", "entreprise", "domaine", "type_offre", "ville", "description", "url", "source", "date_publication")
    for col in colonnes:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str).str.strip()

    def _date_value(value):
        if not value:
            return None
        try:
            parsed = pd.to_datetime(value, errors="coerce", utc=True)
            return None if pd.isna(parsed) else parsed.date()
        except (TypeError, ValueError):
            return None

    df["_date"] = df["date_publication"].map(_date_value)
    df["_stage"] = df["type_offre"].str.casefold().str.contains(r"stage|pfe|intern|stagiaire", na=False)
    kpis = [
        ("Total des offres", total, "💼", "blue"),
        ("Offres d’emploi", int((~df["_stage"]).sum()), "🧑‍💻", "violet"),
        ("Offres de stage", int(df["_stage"].sum()), "🎓", "turquoise"),
        ("Sites sources", source_count, "🔗", "green"),
    ]
    for col, (titre, valeur, icone, couleur) in zip(st.columns(4), kpis):
        with col:
            with st.container(border=True):
                st.metric(f"{icone} {titre}", valeur)

    def _clear_search():
        st.session_state["offres_recherche_saisie"] = ""
        st.session_state["offres_recherche_active"] = ""

    def _reset_filters():
        defaults = {
            "offres_sources": ["Tous les sites"], "offres_type": "Tous",
            "offres_domaine": "Tous", "offres_ville": "Toutes",
            "offres_date": "Toutes les dates", "offres_experience": "Tous",
            "offres_mode": "Tous", "offres_tri": "Plus récentes",
            "offres_recherche_saisie": "", "offres_recherche_active": "",
        }
        for key, value in defaults.items():
            st.session_state[key] = value

    st.subheader("🔎 Recherche d’offres")
    st.caption("Poste, entreprise, compétences, domaine ou ville.")
    with st.form("offres_recherche_form"):
        c1, c2 = st.columns([5, 1])
        with c1:
            st.text_input("Recherche", placeholder="Ex. Python, Data Analyst, Marrakech…", key="offres_recherche_saisie")
        with c2:
            submitted = st.form_submit_button("🔍 Rechercher", type="primary", use_container_width=True)
    if submitted:
        st.session_state["offres_recherche_active"] = st.session_state.get("offres_recherche_saisie", "").strip()
    st.button("Effacer la recherche", key="offres_clear_search", on_click=_clear_search)

    st.subheader("🎛️ Affiner ma recherche")
    st.caption("Les options proviennent des offres réellement chargées.")
    def _options(column):
        return sorted(x for x in df[column].dropna().astype(str).str.strip().unique() if x) if column in df.columns else []

    sources, domaines, villes, types = (_options(c) for c in ("source", "domaine", "ville", "type_offre"))
    defaults = {
        "offres_sources": ["Tous les sites"], "offres_type": "Tous",
        "offres_domaine": "Tous", "offres_ville": "Toutes",
        "offres_date": "Toutes les dates", "offres_tri": "Plus récentes",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    row1 = st.columns(3)
    with row1[0]:
        source_sel = st.multiselect("Site source", ["Tous les sites"] + sources, key="offres_sources", help="Choisissez un ou plusieurs sites réellement présents.")
    with row1[1]:
        type_sel = st.selectbox("Type d’offre", ["Tous"] + types, key="offres_type")
    with row1[2]:
        domaine_sel = st.selectbox("Domaine", ["Tous"] + domaines, key="offres_domaine")
    row2 = st.columns(4)
    with row2[0]:
        ville_sel = st.selectbox("Localisation", ["Toutes"] + villes, key="offres_ville")
    with row2[1]:
        date_sel = st.selectbox("Date de publication", ["Toutes les dates", "Aujourd’hui", "Cette semaine", "Ce mois"], key="offres_date", disabled=df["_date"].notna().sum() == 0)

    exp_col = next((c for c in ("niveau_experience", "experience", "niveau") if c in df.columns), None)
    mode_col = next((c for c in ("mode_travail", "mode_de_travail", "teletravail") if c in df.columns), None)
    exp_sel = mode_sel = "Tous"
    if exp_col and _options(exp_col):
        st.session_state.setdefault("offres_experience", "Tous")
        with row2[2]:
            exp_sel = st.selectbox("Niveau d’expérience", ["Tous"] + _options(exp_col), key="offres_experience")
    if mode_col and _options(mode_col):
        st.session_state.setdefault("offres_mode", "Tous")
        with row2[3]:
            mode_sel = st.selectbox("Mode de travail", ["Tous"] + _options(mode_col), key="offres_mode")
    st.button("Réinitialiser les filtres", key="offres_reset_filters", on_click=_reset_filters)

    mask = pd.Series(True, index=df.index)
    sources_choisies = [source for source in source_sel if source != "Tous les sites"]
    if sources_choisies:
        mask &= df["source"].isin(sources_choisies)
    if type_sel != "Tous":
        mask &= df["type_offre"].eq(type_sel)
    if domaine_sel != "Tous":
        mask &= df["domaine"].eq(domaine_sel)
    if ville_sel != "Toutes":
        mask &= df["ville"].eq(ville_sel)
    if exp_col and exp_sel != "Tous":
        mask &= df[exp_col].astype(str).eq(exp_sel)
    if mode_col and mode_sel != "Tous":
        mask &= df[mode_col].astype(str).eq(mode_sel)
    if date_sel != "Toutes les dates":
        today = date.today()
        start_date = today if date_sel == "Aujourd’hui" else today - timedelta(days=today.weekday()) if date_sel == "Cette semaine" else today.replace(day=1)
        mask &= df["_date"].map(lambda d: d is not None and start_date <= d <= today)

    query = st.session_state.get("offres_recherche_active", "").strip()
    search_cols = [c for c in ("titre", "entreprise", "competences", "skills", "domaine", "ville", "description") if c in df.columns]
    if query:
        matches = pd.Series(False, index=df.index)
        for col in search_cols:
            matches |= df[col].astype(str).str.contains(query, case=False, regex=False, na=False)
        mask &= matches

    results = df.loc[mask].copy()
    st.markdown(f"### ✨ {len(results)} offre(s) correspondent à votre recherche")
    sort_mode = st.selectbox("Trier les résultats", ["Plus récentes", "Pertinence", "Entreprise A → Z"], key="offres_tri")
    if sort_mode == "Entreprise A → Z":
        results = results.sort_values("entreprise", key=lambda s: s.str.casefold(), na_position="last")
    elif sort_mode == "Pertinence" and query:
        results["_score"] = 0
        for col in search_cols:
            values = results[col].astype(str).str.casefold()
            results["_score"] += values.eq(query.casefold()).astype(int) * 3 + values.str.contains(query.casefold(), regex=False).astype(int)
        results = results.sort_values(["_score", "_date"], ascending=[False, False], na_position="last")
    else:
        results = results.sort_values("_date", ascending=False, na_position="last")

    st.subheader("⭐ Opportunités à découvrir")
    st.caption("Offres récentes dans les résultats filtrés.")
    recent = results[results["_date"].notna()].sort_values("_date", ascending=False).head(3)
    if not recent.empty:
        st.caption("Sélection automatique des offres récentes disponibles, sans recommandations fictives.")
        for _, job in recent.iterrows():
            st.write(f"{job['titre']} · {job['entreprise']} · {job['ville']} · {job['source']}")

    st.subheader("📋 Offres disponibles")
    st.caption("Ouvrez chaque annonce depuis sa source originale.")
    view_mode = st.radio("Présentation", ["Grille", "Liste"], horizontal=True, key="offres_vue")

    def _card(job):
        title = str(job.get("titre") or "Intitulé non renseigné")
        company = str(job.get("entreprise") or "Entreprise non renseignée")
        city = str(job.get("ville") or "Localisation non renseignée")
        domain = str(job.get("domaine") or "Domaine non renseigné")
        offer_type = str(job.get("type_offre") or "Type non renseigné")
        source = str(job.get("source") or "Source non renseignée")
        description = str(job.get("description") or "Description non disponible.")
        description = description[:520] + ("…" if len(description) > 520 else "")
        published = job.get("_date")
        date_text = published.strftime("%d/%m/%Y") if published else "Date non renseignée"
        url = str(job.get("url") or "").strip()
        try:
            parsed = urlparse(url)
            valid_url = url if parsed.scheme in ("http", "https") and parsed.netloc and parsed.path not in ("", "/") else None
        except ValueError:
            valid_url = None
        skills_col = None
        for candidate_col in ("competences", "skills"):
            skill_value = job.get(candidate_col)
            if candidate_col in job.index and pd.notna(skill_value) and str(skill_value).strip():
                skills_col = candidate_col
                break
        key_seed = "|".join((str(job.get("id") or ""), title, company, url))
        card_key = sha1(key_seed.encode("utf-8")).hexdigest()[:14]
        badges = [f"💼 {offer_type}", f"🎯 {domain}", f"🔗 {source}", f"📅 {date_text}"]
        for candidate_col, label in (
            ("contrat", "Contrat"),
            ("type_contrat", "Contrat"),
            ("contract_type", "Contrat"),
            (exp_col, "Expérience"),
            (mode_col, "Mode"),
        ):
            value = job.get(candidate_col) if candidate_col else None
            if candidate_col in job.index and pd.notna(value) and str(value).strip():
                badges.append(f"{label} : {value}")
        with st.container(border=True):
            st.subheader(f"🏢 {title}")
            st.write(f"**{company}** · 📍 {city}")
            st.caption(" · ".join(badges))
            st.write(description)
            if skills_col:
                st.write(f"**Compétences :** {job.get(skills_col)}")
            if valid_url:
                left, right = st.columns(2)
                with left:
                    st.link_button("🌐 Voir l’offre", valid_url, key=f"voir_offre_{card_key}", use_container_width=True)
                with right:
                    st.link_button("📝 Postuler", valid_url, key=f"postuler_offre_{card_key}", type="primary", use_container_width=True)
            else:
                st.info("Lien original indisponible ; aucun lien n’a été inventé.")

    if results.empty:
        st.info("Aucune offre ne correspond aux filtres. Modifiez les critères ou réinitialisez-les.")
    elif view_mode == "Grille":
        for start_index in range(0, len(results), 2):
            columns = st.columns(2)
            for column, (_, job) in zip(columns, results.iloc[start_index:start_index + 2].iterrows()):
                with column:
                    _card(job)
    else:
        for _, job in results.iterrows():
            _card(job)

    with st.expander("📊 Analyse des offres", expanded=False):
        if px is None:
            st.warning("Les graphiques nécessitent Plotly. Installez-le avec : py -m pip install plotly")
        elif not results.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### Répartition par site source")
                counts = results["source"].replace("", "Source non renseignée").value_counts().rename_axis("Source").reset_index(name="Offres")
                fig = px.pie(counts, names="Source", values="Offres", hole=.55, color_discrete_sequence=palette)
                fig.update_traces(textposition="inside", textinfo="percent", hovertemplate="%{label}<br>%{value} offre(s)<extra></extra>")
                fig.update_layout(height=320, margin=dict(l=8, r=8, t=15, b=8), paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            with c2:
                st.markdown("#### Offres par domaine")
                counts = results["domaine"].replace("", "Domaine non renseigné").value_counts().rename_axis("Domaine").reset_index(name="Offres")
                fig = px.bar(counts, x="Domaine", y="Offres", color="Domaine", text="Offres", color_discrete_sequence=palette)
                fig.update_layout(height=320, margin=dict(l=8, r=8, t=15, b=8), xaxis_title=None, yaxis_title="Offres", showlegend=False, paper_bgcolor="rgba(0,0,0,0)")
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            a, b = st.columns(2)
            dated = results[results["_date"].notna()]
            if not dated.empty:
                with a:
                    st.markdown("#### Publications par date")
                    fig = px.histogram(dated, x="_date", color_discrete_sequence=[palette[2]])
                    fig.update_layout(height=300, margin=dict(l=8, r=8, t=15, b=8), xaxis_title=None, yaxis_title="Offres", paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            with b:
                st.markdown("#### Répartition stages / autres offres")
                split = pd.DataFrame({"Catégorie": ["Stages", "Autres offres"], "Offres": [int(results["_stage"].sum()), int((~results["_stage"]).sum())]})
                fig = px.pie(split, names="Catégorie", values="Offres", hole=.58, color_discrete_sequence=[palette[1], palette[0]])
                fig.update_traces(textposition="inside", textinfo="percent", hovertemplate="%{label}<br>%{value} offre(s)<extra></extra>")
                fig.update_layout(height=300, margin=dict(l=8, r=8, t=15, b=8), paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            st.markdown("#### Entreprises qui publient le plus")
            top = results["entreprise"].replace("", "Entreprise non renseignée").value_counts().head(10).rename_axis("Entreprise").reset_index(name="Offres").sort_values("Offres", ascending=True)
            fig = px.bar(top, x="Offres", y="Entreprise", orientation="h", text="Offres", color="Offres", color_continuous_scale=["#BFDBFE", palette[0], palette[1]])
            fig.update_layout(height=max(280, 32 * len(top) + 80), margin=dict(l=8, r=18, t=15, b=8), coloraxis_showscale=False, xaxis_title="Offres", yaxis_title=None, paper_bgcolor="rgba(0,0,0,0)")
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})




