from datetime import date, timedelta
from hashlib import sha1
from urllib.parse import urlparse
import pandas as pd
import streamlit as st
from fetch_jobs import (
    load_or_create_jobs,
    nettoyer_description,
)


def page_stages() -> None:
  try:
    import plotly.express as px
  except ImportError:
    px = None

  palette = ["#2563EB", "#7C3AED", "#06B6D4", "#10B981", "#F59E0B", "#EC4899"]

  # Charge l’API Remotive automatiquement; le collecteur applique son cache de 6 h.
  st.session_state["offres_donnees_session"] = load_or_create_jobs()
  df_jobs = st.session_state["offres_donnees_session"]
  if not isinstance(df_jobs, pd.DataFrame):
    df_jobs = pd.DataFrame(df_jobs)

  total = len(df_jobs)
  source_count = (
      df_jobs["source"]
      .fillna("")
      .astype(str)
      .str.strip()
      .replace("", pd.NA)
      .nunique()
      if total and "source" in df_jobs.columns
      else 0
  )

  st.markdown("""
  <style>
  .offers-hero{position:relative;overflow:hidden;display:flex;align-items:center;justify-content:space-between;gap:24px;padding:28px 32px;border-radius:22px;color:#fff;background:linear-gradient(120deg,#172554 0%,#1d4ed8 48%,#7c3aed 78%,#06b6d4 120%);box-shadow:0 16px 38px rgba(37,99,235,.22);margin:4px 0 24px;border:1px solid rgba(255,255,255,.22)}
  .offers-hero:after{content:"";position:absolute;width:220px;height:220px;border-radius:50%;right:12%;top:-145px;background:rgba(255,255,255,.13);box-shadow:0 0 0 34px rgba(255,255,255,.05)}
  .offers-hero-copy,.offers-hero-count{position:relative;z-index:1}
  .offers-hero-label{display:inline-block;padding:6px 11px;border-radius:999px;background:rgba(255,255,255,.16);font-size:.72rem;font-weight:800;letter-spacing:.11em}
  .offers-hero h1{color:#fff;margin:13px 0 7px;font-size:clamp(1.5rem,3vw,2.15rem);line-height:1.15}
  .offers-hero p{color:#eaf1ff;margin:0;max-width:720px}
  .offers-hero-note{margin-top:12px;color:#fff;font-size:.88rem;font-weight:700}
  .offers-hero-count{flex:0 0 140px;text-align:center;padding:15px 18px;border-radius:18px;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.27);backdrop-filter:blur(8px)}
  .offers-hero-count strong{display:block;font-size:2rem;line-height:1.05;color:#fff}
  .offers-hero-count span{display:block;margin-top:5px;font-size:.82rem;color:#eef2ff}
  @media(max-width:640px){.offers-hero{align-items:flex-start;flex-direction:column;padding:22px}.offers-hero-count{flex-basis:auto;width:100%;box-sizing:border-box;text-align:left}.offers-hero-count strong{display:inline;margin-right:8px}}
  </style>
  <section class="offers-hero">
    <div class="offers-hero-copy">
      <span class="offers-hero-label">IA JOB · CARRIÈRES &amp; OPPORTUNITÉS</span>
      <h1>💼 Trouvez votre prochaine opportunité</h1>
      <p>Explorez les offres d’emploi, stages et opportunités IT &amp; IA disponibles sur les plateformes sélectionnées.</p>
      <div class="offers-hero-note">✨ Votre prochaine opportunité commence ici !</div>
    </div>
    <div class="offers-hero-count"><strong>""" + str(total) + """</strong><span>Offres disponibles</span></div>
  </section>
  """, unsafe_allow_html=True)

  df_jobs = st.session_state["offres_donnees_session"]
  if df_jobs.empty:
    st.info("Aucune offre enregistrée pour le moment.")
    return

  df = df_jobs.copy()
  colonnes = (
      "titre",
      "entreprise",
      "domaine",
      "type_offre",
      "ville",
      "description",
      "url",
      "source",
      "date_publication",
  )
  for col in colonnes:
    if col not in df.columns:
      df[col] = ""
    df[col] = df[col].fillna("").astype(str).str.strip()

  df["description"] = df["description"].map(nettoyer_description)

  def _date_value(value):
    if not value:
      return None
    try:
      parsed = pd.to_datetime(value, errors="coerce", utc=True)
      return None if pd.isna(parsed) else parsed.date()
    except (TypeError, ValueError):
      return None

  df["_date"] = df["date_publication"].map(_date_value)
  df["_stage"] = (
      df["type_offre"]
      .str.casefold()
      .str.contains(r"stage|pfe|intern|stagiaire", na=False)
  )

  kpis = [
      ("Total des offres", total, "💼", "blue"),
      ("Offres d’emploi", int((~df["_stage"]).sum()), "🧑‍💻", "violet"),
      ("Offres de stage", int(df["_stage"].sum()), "🎓", "turquoise"),
      ("Sites sources", source_count, "🔗", "green"),
  ]
  st.markdown("""
  <style>
  .offers-stat-card{box-sizing:border-box;width:100%;min-height:112px;padding:17px 19px;border-radius:16px;box-shadow:0 8px 20px rgba(23,37,84,.10);display:flex;flex-direction:column;justify-content:center;transition:transform .18s ease,box-shadow .18s ease}
  .offers-stat-card:hover{transform:translateY(-2px);box-shadow:0 12px 24px rgba(23,37,84,.15)}
  .offers-stat-label{font-size:.88rem;font-weight:650;color:#334155;line-height:1.35}
  .offers-stat-value{font-size:2rem;font-weight:800;line-height:1.15;margin-top:8px;color:#172554}
  </style>
  """, unsafe_allow_html=True)
  kpi_palette = {
      "blue": ("#dbeafe", "#bfdbfe", "#2563eb"),
      "violet": ("#ede9fe", "#ddd6fe", "#7c3aed"),
      "turquoise": ("#cffafe", "#a5f3fc", "#0891b2"),
      "green": ("#d1fae5", "#a7f3d0", "#059669"),
  }
  for col, (titre, valeur, icone, couleur) in zip(st.columns(4), kpis):
    fond, bordure, accent = kpi_palette[couleur]
    with col:
      st.markdown(
          f'<div class="offers-stat-card" style="background:linear-gradient(140deg,{fond} 0%,#ffffff 100%);border:1px solid {bordure};border-top:4px solid {accent};">'
          f'<div class="offers-stat-label">{icone} {titre}</div>'
          f'<div class="offers-stat-value">{valeur}</div></div>',
          unsafe_allow_html=True,
      )

  def _clear_search():
    st.session_state["offres_recherche_saisie"] = ""
    st.session_state["offres_recherche_active"] = ""

  def _reset_filters():
    defaults = {
        "offres_sources": ["Tous les sites"],
        "offres_type": "Tous",
        "offres_domaine": "Tous",
        "offres_ville": "Toutes",
        "offres_date": "Toutes les dates",
        "offres_experience": "Tous",
        "offres_mode": "Tous",
        "offres_tri": "Plus récentes",
        "offres_recherche_saisie": "",
        "offres_recherche_active": "",
    }
    for key, value in defaults.items():
      st.session_state[key] = value

  st.subheader("🔎 Recherche d’offres")
  st.caption("Poste, entreprise, compétences, domaine ou ville.")
  with st.form("offres_recherche_form"):
    c1, c2 = st.columns([5, 1])
    with c1:
      st.text_input(
          "Recherche",
          placeholder="Ex. Python, Data Analyst, Marrakech, LinkedIn…",
          key="offres_recherche_saisie",
      )
    with c2:
      submitted = st.form_submit_button(
          "🔍 Rechercher", type="primary", use_container_width=True
      )
  if submitted:
    st.session_state["offres_recherche_active"] = (
        st.session_state.get("offres_recherche_saisie", "").strip()
    )
  st.button(
      "Effacer la recherche",
      key="offres_clear_search",
      on_click=_clear_search,
  )

  st.subheader("🎛️ Affiner ma recherche (Filtre par site : LinkedIn, Indeed...)")
  st.caption(
      "Filtrez instantanément vos offres par plateforme d'origine et par"
      " critères."
  )

  def _options(column):
    return (
        sorted(
            x
            for x in df[column].dropna().astype(str).str.strip().unique()
            if x
        )
        if column in df.columns
        else []
    )

  domaines, villes, types = (_options(c) for c in ("domaine", "ville", "type_offre"))
  sources = ["Remotive", "LinkedIn", "Indeed", "ReKrute"]
  defaults = {
      "offres_sources": ["Tous les sites"],
      "offres_type": "Tous",
      "offres_domaine": "Tous",
      "offres_ville": "Toutes",
      "offres_date": "Toutes les dates",
      "offres_tri": "Plus récentes",
  }
  for key, value in defaults.items():
    st.session_state.setdefault(key, value)

  row1 = st.columns(3)
  with row1[0]:
    source_sel = st.multiselect(
        "Site source (LinkedIn, Indeed...)",
        ["Tous les sites"] + sources,
        key="offres_sources",
        help="Sélectionnez une ou plusieurs sources pour filtrer.",
    )
  with row1[1]:
    type_sel = st.selectbox("Type d’offre", ["Tous"] + types, key="offres_type")
  with row1[2]:
    domaine_sel = st.selectbox(
        "Domaine", ["Tous"] + domaines, key="offres_domaine"
    )

  row2 = st.columns(4)
  with row2[0]:
    ville_sel = st.selectbox(
        "Localisation", ["Toutes"] + villes, key="offres_ville"
    )
  with row2[1]:
    date_sel = st.selectbox(
        "Date de publication",
        ["Toutes les dates", "Aujourd’hui", "Cette semaine", "Ce mois"],
        key="offres_date",
        disabled=df["_date"].notna().sum() == 0,
    )

  exp_col = next(
      (
          c
          for c in ("niveau_experience", "experience", "niveau")
          if c in df.columns
      ),
      None,
  )
  mode_col = next(
      (
          c
          for c in ("mode_travail", "mode_de_travail", "teletravail")
          if c in df.columns
      ),
      None,
  )
  exp_sel = mode_sel = "Tous"
  if exp_col and _options(exp_col):
    st.session_state.setdefault("offres_experience", "Tous")
    with row2[2]:
      exp_sel = st.selectbox(
          "Niveau d’expérience", ["Tous"] + _options(exp_col), key="offres_experience"
      )
  if mode_col and _options(mode_col):
    st.session_state.setdefault("offres_mode", "Tous")
    with row2[3]:
      mode_sel = st.selectbox(
          "Mode de travail", ["Tous"] + _options(mode_col), key="offres_mode"
      )
  st.button(
      "Réinitialiser les filtres",
      key="offres_reset_filters",
      on_click=_reset_filters,
  )

  mask = pd.Series(True, index=df.index)
  sources_choisies = [source for source in source_sel if source != "Tous les sites"]
  if sources_choisies:
    if "sources" in df.columns:
      mask &= df["sources"].map(
          lambda values: any(
              source
              in (values if isinstance(values, list) else [str(values)])
              for source in sources_choisies
          )
      )
    else:
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
    start_date = (
        today
        if date_sel == "Aujourd’hui"
        else today - timedelta(days=today.weekday())
        if date_sel == "Cette semaine"
        else today.replace(day=1)
    )
    mask &= df["_date"].map(lambda d: d is not None and start_date <= d <= today)

  query = st.session_state.get("offres_recherche_active", "").strip()
  search_cols = [
      c
      for c in (
          "titre",
          "entreprise",
          "competences",
          "skills",
          "domaine",
          "ville",
          "description",
      )
      if c in df.columns
  ]
  if query:
    matches = pd.Series(False, index=df.index)
    for col in search_cols:
      matches |= df[col].astype(str).str.contains(
          query, case=False, regex=False, na=False
      )
    mask &= matches

  results = df.loc[mask].copy()
  st.markdown(f"### ✨ {len(results)} offre(s) correspondent à votre recherche")
  sort_mode = st.selectbox(
      "Trier les résultats",
      ["Plus récentes", "Pertinence", "Entreprise A → Z"],
      key="offres_tri",
  )
  if sort_mode == "Entreprise A → Z":
    results = results.sort_values(
        "entreprise", key=lambda s: s.str.casefold(), na_position="last"
    )
  elif sort_mode == "Pertinence" and query:
    results["_score"] = 0
    for col in search_cols:
      values = results[col].astype(str).str.casefold()
      results["_score"] += (
          values.eq(query.casefold()).astype(int) * 3
          + values.str.contains(query.casefold(), regex=False).astype(int)
      )
    results = results.sort_values(
        ["_score", "_date"], ascending=[False, False], na_position="last"
    )
  else:
    results = results.sort_values("_date", ascending=False, na_position="last")

  st.subheader("⭐ Opportunités à découvrir")
  st.caption("Offres récentes issues de vos sources (LinkedIn, Indeed...).")
  recent = (
      results[results["_date"].notna()]
      .sort_values("_date", ascending=False)
      .head(3)
  )
  if not recent.empty:
    for _, job in recent.iterrows():
      st.write(
          f"🔹 **{job['titre']}** · {job['entreprise']} · 📍 {job['ville']} ·"
          f" 🔗 *{job['source']}*"
      )

  st.subheader("📋 Offres disponibles")
  st.caption("Ouvrez chaque annonce depuis sa source originale.")
  view_mode = st.radio(
      "Présentation", ["Grille", "Liste"], horizontal=True, key="offres_vue"
  )

  st.markdown("""
  <style>
  [class*="st-key-offer_card_remotive_"] [data-testid="stVerticalBlockBorderWrapper"]{background:linear-gradient(145deg,#fff1f2 0%,#ffffff 78%)!important;border:1px solid #fecdd3!important;border-top:4px solid #e11d48!important;border-radius:18px!important;box-shadow:0 8px 22px rgba(225,29,72,.09)!important;transition:transform .18s ease,box-shadow .18s ease}
  [class*="st-key-offer_card_linkedin_"] [data-testid="stVerticalBlockBorderWrapper"]{background:linear-gradient(145deg,#eff6ff 0%,#ffffff 78%)!important;border:1px solid #bfdbfe!important;border-top:4px solid #2563eb!important;border-radius:18px!important;box-shadow:0 8px 22px rgba(37,99,235,.09)!important;transition:transform .18s ease,box-shadow .18s ease}
  [class*="st-key-offer_card_indeed_"] [data-testid="stVerticalBlockBorderWrapper"]{background:linear-gradient(145deg,#ecfeff 0%,#ffffff 78%)!important;border:1px solid #a5f3fc!important;border-top:4px solid #0891b2!important;border-radius:18px!important;box-shadow:0 8px 22px rgba(8,145,178,.09)!important;transition:transform .18s ease,box-shadow .18s ease}
  [class*="st-key-offer_card_rekrute_"] [data-testid="stVerticalBlockBorderWrapper"]{background:linear-gradient(145deg,#f5f3ff 0%,#ffffff 78%)!important;border:1px solid #ddd6fe!important;border-top:4px solid #7c3aed!important;border-radius:18px!important;box-shadow:0 8px 22px rgba(124,58,237,.09)!important;transition:transform .18s ease,box-shadow .18s ease}
  [class*="st-key-offer_card_other_"] [data-testid="stVerticalBlockBorderWrapper"]{background:linear-gradient(145deg,#f8fafc 0%,#ffffff 78%)!important;border:1px solid #cbd5e1!important;border-top:4px solid #64748b!important;border-radius:18px!important;box-shadow:0 8px 22px rgba(15,23,42,.07)!important}
  [class*="st-key-offer_card_"] [data-testid="stVerticalBlockBorderWrapper"]:hover{transform:translateY(-3px);box-shadow:0 14px 28px rgba(15,23,42,.13)!important}
  @media(prefers-reduced-motion:reduce){[class*="st-key-offer_card_"] [data-testid="stVerticalBlockBorderWrapper"]{transition:none}}
  </style>
  """, unsafe_allow_html=True)

  def _card(job):
    title = str(job.get("titre") or "Intitulé non renseigné")
    company = str(job.get("entreprise") or "Entreprise non renseignée")
    city = str(job.get("ville") or "Localisation non renseignée")
    domain = str(job.get("domaine") or "Domaine non renseigné")
    offer_type = str(job.get("type_offre") or "Type non renseigné")
    source = str(job.get("source") or "Source non renseignée")
    sources_job = job.get("sources", [])
    if not isinstance(sources_job, list) or not sources_job:
      sources_job = [source]
    source_urls = job.get("source_urls", {})
    if not isinstance(source_urls, dict):
      source_urls = {}
    description = (
        nettoyer_description(job.get("description"))
        or "Description non disponible dans la source."
    )
    description = description[:520] + (
        "…" if len(description) > 520 else ""
    )
    published = job.get("_date")
    date_text = (
        published.strftime("%d/%m/%Y") if published else "Date non renseignée"
    )
    url = str(job.get("url") or "").strip()
    try:
      parsed = urlparse(url)
      valid_url = (
          url
          if parsed.scheme in ("http", "https")
          and parsed.netloc
          and parsed.path not in ("", "/")
          else None
      )
    except ValueError:
      valid_url = None

    skills_col = None
    for candidate_col in ("competences", "skills"):
      skill_value = job.get(candidate_col)
      if (
          candidate_col in job.index
          and pd.notna(skill_value)
          and str(skill_value).strip()
      ):
        skills_col = candidate_col
        break

    key_seed = "|".join((str(job.get("id") or ""), title, company, url))
    card_key = sha1(key_seed.encode("utf-8")).hexdigest()[:14]
    source_class = {
        "remotive": "remotive", "linkedin": "linkedin",
        "indeed": "indeed", "rekrute": "rekrute",
    }.get(source.casefold(), "other")
    badges = [
        f"💼 {offer_type}",
        f"🎯 {domain}",
        f"🔗 {', '.join(sources_job)}",
        f"📅 {date_text}",
    ]

    with st.container(border=True, key=f"offer_card_{source_class}_{card_key}"):
      st.subheader(f"🏢 {title}")
      st.write(f"**{company}** · 📍 {city}")
      st.caption(" · ".join(badges))
      st.write(description)
      if skills_col:
        st.write(f"**Compétences :** {job.get(skills_col)}")

      valid_source_urls = []
      for platform in sources_job:
        candidate_url = str(
            source_urls.get(platform)
            or (url if platform == source else "")
        ).strip()
        parsed_candidate = urlparse(candidate_url)
        if (
            parsed_candidate.scheme in ("http", "https")
            and parsed_candidate.netloc
        ):
          valid_source_urls.append((platform, candidate_url))
      if not valid_source_urls and valid_url:
        valid_source_urls = [(source, valid_url)]

      if valid_source_urls:
        link_columns = st.columns(min(2, len(valid_source_urls)))
        for index, (platform, source_url) in enumerate(valid_source_urls):
          with link_columns[index % len(link_columns)]:
            st.link_button(
                f"🌐 Postuler · {platform}",
                source_url,
                key=f"postuler_{card_key}_{index}",
                type="primary",
                use_container_width=True,
            )
      else:
        st.info("Lien original indisponible.")

  if results.empty:
    st.info(
        "Aucune offre ne correspond aux filtres. Modifiez les critères ou"
        " réinitialisez-les."
    )
  elif view_mode == "Grille":
    for start_index in range(0, len(results), 2):
      columns = st.columns(2)
      for column, (_, job) in zip(
          columns, results.iloc[start_index : start_index + 2].iterrows()
      ):
        with column:
          _card(job)
  else:
    for _, job in results.iterrows():
      _card(job)

  # Section d'analyse graphique
  with st.expander("📊 Analyse des offres", expanded=False):
    if px is None:
      st.warning(
          "Les graphiques nécessitent Plotly. Installez-le avec : py -m pip"
          " install plotly"
      )
    elif not results.empty:
      c1, c2 = st.columns(2)
      with c1:
        st.markdown("#### Répartition par site source (LinkedIn, Indeed...)")
        counts = (
            results["source"]
            .replace("", "Source non renseignée")
            .value_counts()
            .rename_axis("Source")
            .reset_index(name="Offres")
        )
        fig = px.pie(
            counts,
            names="Source",
            values="Offres",
            hole=0.55,
            color_discrete_sequence=palette,
        )
        fig.update_traces(
            textposition="inside",
            textinfo="percent",
            hovertemplate="%{label}<br>%{value} offre(s)<extra></extra>",
        )
        fig.update_layout(
            height=320,
            margin=dict(l=8, r=8, t=15, b=8),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(
            fig, use_container_width=True, config={"displayModeBar": False}
        )
      with c2:
        st.markdown("#### Offres par domaine")
        counts = (
            results["domaine"]
            .replace("", "Domaine non renseigné")
            .value_counts()
            .rename_axis("Domaine")
            .reset_index(name="Offres")
        )
        fig = px.bar(
            counts,
            x="Domaine",
            y="Offres",
            color="Domaine",
            text="Offres",
            color_discrete_sequence=palette,
        )
        fig.update_layout(
            height=320,
            margin=dict(l=8, r=8, t=15, b=8),
            xaxis_title=None,
            yaxis_title="Offres",
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(
            fig, use_container_width=True, config={"displayModeBar": False}
        )


if __name__ == "__main__":
  page_stages()
