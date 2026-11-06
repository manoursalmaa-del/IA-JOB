from urllib.parse import quote
import urllib.parse
from data import CSV_PATH, DATA, DOMAINES
import pandas as pd
import streamlit as st
from style import goto
from gmail import envoyer_candidature


# Fonction d'affichage de la carte Google Maps (issue du code orphelin au début)
def afficher_carte(entreprise: dict) -> None:
  nom_entreprise = entreprise.get("nom", "")
  adresse = entreprise.get("adresse", "")
  ville = entreprise.get("ville", "Marrakech")

  search_query = f"{nom_entreprise} {adresse} {ville}"
  query_encoded = urllib.parse.quote(search_query)

  # Carte Google Maps interactive
  maps_iframe = f"https://maps.google.com/maps?q={query_encoded}&t=&z=15&ie=UTF8&iwloc=&output=embed"
  st.components.v1.iframe(maps_iframe, height=280, scrolling=False)

  # Bouton d'ouverture directe dans Google Maps
  google_maps_direct_link = (
      f"https://www.google.com/maps/search/?api=1&query={query_encoded}"
  )
  st.markdown(
      f"[👉 Ouvrir directement dans Google Maps]({google_maps_direct_link})"
  )


def page_domaines() -> None:
  st.subheader("🎯 Choisissez un domaine")
  st.caption(
      "Sélectionnez un domaine pour découvrir les entreprises"
      " correspondantes."
  )

  items = list(DOMAINES.items())
  for i in range(0, len(items), 3):
    cols = st.columns(3)
    for j in range(3):
      if i + j >= len(items):
        break
      domaine, icon = items[i + j]
      count = len(DATA[DATA["domaine"] == domaine])
      with cols[j]:
        st.markdown(
            f'<div class="domain-card">'
            f'<div class="domain-icon">{icon}</div>'
            f'<div class="domain-name">{domaine}</div>'
            f'<div class="domain-count">{count} entreprise(s)</div>'
            "</div>",
            unsafe_allow_html=True,
        )
        if st.button(
            "Voir →",
            key=f"d_{i+j}",
            use_container_width=True,
            type="primary",
        ):
          st.session_state.domaine = domaine
          goto("Entreprises")
          st.rerun()


def page_entreprises() -> None:
  domaine = st.session_state.get("domaine")
  if not domaine:
    st.info("Choisissez d'abord un domaine.")
    st.button("Aller aux domaines", on_click=goto, args=("Domaines",))
    return

  icon = DOMAINES.get(domaine, "📁")
  st.subheader(f"{icon} {domaine}")
  df_dom = DATA[DATA["domaine"] == domaine].copy()

  f1, f2, f3 = st.columns([2, 1, 1])
  recherche = f1.text_input(
      "🔍 Rechercher par ID, Nom ou Service", placeholder="ex: 12, web..."
  )
  only_email = f2.checkbox("Avec email uniquement")
  min_note = f3.slider("Note min.", 0.0, 5.0, 0.0, 0.5)

  view = df_dom[df_dom["note_num"] >= min_note]
  if only_email:
    view = view[view["email"] != ""]
  if recherche:
    m = view.apply(
        lambda r: recherche.lower() in " ".join(r.astype(str)).lower(), axis=1
    )
    view = view[m]

  st.markdown(f"**{len(view)} résultat(s)** sur {len(df_dom)} entreprise(s)")

  for idx, r in view.iterrows():
    email_tag = "✅ Email" if r["email"] else "❌ Email"
    site_tag = "🌐 Site" if r["site_web"] else ""
    note_txt = f"⭐ {r['note_num']:.1f}" if r["note_num"] > 0 else "—"

    st.markdown(
        f'<div class="card">'
        f'<b style="font-size:1.1rem">ID #{r["id"]} - {r["nom"]}</b><br>'
        f'📍 {r["adresse"] or "Adresse non renseignée"}<br>'
        f'📞 {r["telephone"] or "—"} &nbsp;|&nbsp; {email_tag} &nbsp;'
        f" {site_tag}<br>"
        f'<span class="badge b-blue">{r["type_acteur"] or "—"}</span>'
        f'<span class="badge b-green">{r["secteur"] or "—"}</span>'
        f'<span class="badge b-purple">{note_txt}</span>'
        "</div>",
        unsafe_allow_html=True,
    )

    if st.button(
        "📄 Voir la fiche complète", key=f"v_{idx}", use_container_width=True
    ):
      st.session_state.entreprise_idx = idx
      goto("Détail")
      st.rerun()


def page_detail() -> None:
  idx = st.session_state.get("entreprise_idx")
  if idx is None or idx not in DATA.index:
    st.info("Sélectionnez d'abord une entreprise.")
    st.button("Aller aux entreprises", on_click=goto, args=("Entreprises",))
    return

  r = DATA.loc[idx]
  st.subheader(f"🏢 ID #{r['id']} - {r['nom']}")

  if st.button("⬅️ Retour à la liste"):
    goto("Entreprises")
    st.rerun()

  col1, col2 = st.columns([1.3, 1])

  with col1:
    st.markdown("#### Coordonnées de l'entreprise")
    infos = [
        ("🏷️ ID", r.get("id", "")),
        ("🏷️ Type", r.get("type_acteur", "")),
        ("🎯 Secteur", r.get("secteur", "")),
        ("🔧 Sous-secteur", r.get("sous_secteur", "")),
        ("🤖 Services IA", r.get("services_ia", "")),
        ("📍 Adresse", r.get("adresse", "")),
        ("📞 Téléphone", r.get("telephone", "")),
        ("🌐 Site web", r.get("site_web", "")),
        ("📧 Email", r.get("email", "")),
    ]
    for label, val in infos:
      if val and str(val).strip() and str(val) != "nan":
        if label == "🌐 Site web" and str(val).startswith("http"):
          st.markdown(f"**{label} :** [{val}]({val})")
        else:
          st.markdown(f"**{label} :** {val}")

    # Affichage optionnel de la carte Google Maps
    st.markdown("#### 📍 Localisation")
    afficher_carte(r.to_dict())

  with col2:
    st.markdown("#### 📧 Postuler")
    email = str(r.get("email", "")).strip()

    if email and email != "nan":
      st.success(f"📬 Email destinataire : **{email}**")
      st.caption(
          "Cliquez sur le bouton ci-dessous pour remplir le formulaire de"
          " candidature et joindre votre CV."
      )

      if st.button(
          "📝 Remplir le formulaire & Envoyer mon CV",
          type="primary",
          use_container_width=True,
      ):
        goto("Candidature")
        st.rerun()
    else:
      st.warning("❌ Aucun email disponible pour cette entreprise.")
      st.info("💡 Utilisez le téléphone ou le site web pour les contacter.")


# ============================================================
# FORMULAIRE DE CANDIDATURE
# ============================================================
def page_candidature() -> None:
  idx = st.session_state.get("entreprise_idx")
  if idx is None or idx not in DATA.index:
    st.info("Veuillez d'abord sélectionner une entreprise pour postuler.")
    st.button(
        "Voir la liste des entreprises", on_click=goto, args=("Entreprises",)
    )
    return

  r = DATA.loc[idx]
  email_ent = str(r.get("email", "")).strip()
  if not email_ent or email_ent.lower() == "nan":
    st.error("Aucune adresse e-mail de recrutement n'est disponible pour cette entreprise.")
    return

  st.subheader("📝 Formulaire de Candidature Spontanée")
  st.markdown("---")

  col_ent, col_form = st.columns([1, 1.5], gap="large")

  with col_ent:
    with st.container(border=True):
      st.markdown("### 🏢 Entreprise ciblée")
      st.markdown(f"**Nom :** {r['nom']}")
      st.markdown(f"**Domaine :** {r['domaine']}")
      st.markdown(f"**Secteur :** {r.get('secteur', 'N/A')}")
      st.markdown(f"**Email destinataire :** `{email_ent}`")
      st.markdown(f"**Téléphone :** {r.get('telephone', 'Non renseigné')}")
      st.markdown(f"**Adresse :** {r.get('adresse', 'Non renseignée')}")

    if st.button("⬅️ Retour à la fiche entreprise"):
      goto("Détail")
      st.rerun()

  with col_form:
    st.markdown("### 👤 Vos Coordonnées")
    with st.form(key="candidature_form", clear_on_submit=False):
      col_nom, col_prenom = st.columns(2)
      nom_cand = col_nom.text_input("Nom *", placeholder="ex: El Amrani")
      prenom_cand = col_prenom.text_input("Prénom *", placeholder="ex: Youssef")

      col_email, col_tel = st.columns(2)
      email_cand = col_email.text_input("Votre Email *", placeholder="ex: youssef@gmail.com")
      tel_cand = col_tel.text_input("Votre Téléphone *", placeholder="ex: 06 12 34 56 78")

      titre_cand = st.text_input(
          "Intitulé du poste / Profil *",
          placeholder="ex: Développeur Fullstack / Data Analyst",
      )
      message_cand = st.text_area(
          "Message de motivation",
          value=f"Bonjour,\n\nJe vous adresse ma candidature spontanée pour un poste au sein de {r['nom']}.\n\nCordialement,\n{prenom_cand} {nom_cand}",
          height=130,
      )
      st.markdown("#### 📄 Joindre votre CV (format PDF)")
      uploaded_cv = st.file_uploader("Choisissez votre fichier CV", type=["pdf"])

      submit_button = st.form_submit_button(
          label="📤 Envoyer ma candidature avec mon CV",
          type="primary",
          use_container_width=True,
      )

    if not submit_button:
      return

    champs_manquants = []
    if not nom_cand.strip():
      champs_manquants.append("votre nom")
    if not prenom_cand.strip():
      champs_manquants.append("votre prénom")
    if not email_cand.strip():
      champs_manquants.append("votre adresse e-mail")
    if not tel_cand.strip():
      champs_manquants.append("votre téléphone")
    if not titre_cand.strip():
      champs_manquants.append("l'intitulé du poste / profil")
    if uploaded_cv is None:
      champs_manquants.append("votre CV PDF")

    if champs_manquants:
      st.error("Veuillez renseigner : " + ", ".join(champs_manquants) + ".")
      return

    cv_bytes = uploaded_cv.getvalue()
    if not uploaded_cv.name.lower().endswith(".pdf") or not cv_bytes.startswith(b"%PDF-"):
      st.error("Le fichier choisi n'est pas un PDF valide. Veuillez joindre votre CV au format PDF.")
      return

    if "candidatures_list" not in st.session_state:
      st.session_state.candidatures_list = []

    entreprise_clean = str(r.get("nom", "")).strip().casefold()
    poste_clean = titre_cand.strip().casefold()
    doublon = any(
        str(c.get("entreprise", "")).strip().casefold() == entreprise_clean
        and str(c.get("poste", "")).strip().casefold() == poste_clean
        for c in st.session_state.candidatures_list
    )
    if doublon:
      st.error("Une candidature pour ce poste chez cette entreprise existe déjà dans le suivi.")
      return

    try:
      envoyer_candidature(
          destinataire_entreprise=email_ent,
          email_candidat=email_cand.strip(),
          entreprise=str(r.get("nom", "Entreprise")),
          poste=titre_cand.strip(),
          lettre=(
              f"{message_cand.strip()}\n\n"
              f"Coordonnées du candidat : {prenom_cand.strip()} {nom_cand.strip()}\n"
              f"Téléphone : {tel_cand.strip()}"
          ),
          cv=uploaded_cv,
      )
    except Exception as erreur:
      st.error(f"L'envoi du courriel a échoué : {erreur}. Vérifiez la configuration SMTP Gmail.")
      return

    st.session_state.candidatures_list.append({
        "entreprise": str(r.get("nom", "Entreprise")),
        "poste": titre_cand.strip(),
        "statut": "✅ Candidature envoyée",
        "date": pd.Timestamp.today().strftime("%Y-%m-%d"),
        "notes": f"CV envoyé à {email_ent} — candidat : {email_cand.strip()}",
    })
    st.success(f"Candidature envoyée à {r.get('nom', 'l’entreprise')} avec le CV en pièce jointe.")

def page_analyse() -> None:
  try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
  except ImportError:
    px = go = None

  couleurs = ["#2563EB", "#7C3AED", "#06B6D4", "#10B981", "#F59E0B", "#EC4899", "#EF4444"]
  df = DATA.copy() if isinstance(DATA, pd.DataFrame) else pd.DataFrame(DATA)
  if df.empty:
    st.info("Aucune entreprise réelle n’est disponible pour l’analyse.")
    return

  # Les graphiques utilisent des colonnes présentes dans le dataset réel.
  for colonne in ("nom", "domaine", "secteur", "sous_secteur", "type_acteur", "email", "site_web", "services_ia", "note"):
    if colonne not in df.columns:
      df[colonne] = ""
    df[colonne] = df[colonne].fillna("").astype(str).str.strip()
  if "note_num" in df.columns:
    df["_note"] = pd.to_numeric(df["note_num"], errors="coerce")
  else:
    df["_note"] = pd.to_numeric(df["note"].str.replace(",", ".", regex=False), errors="coerce")
  df["_email_ok"] = df["email"].str.casefold().ne("") & df["email"].str.casefold().ne("nan")
  df["_site_ok"] = df["site_web"].str.casefold().ne("") & df["site_web"].str.casefold().ne("nan")
  for colonne in ("domaine", "secteur", "sous_secteur", "type_acteur"):
    df[colonne] = df[colonne].replace("", "Non renseigné")
  if "id" not in df.columns:
    df["id"] = df.index + 1

  st.markdown("""
  <style>
  .analyse-hero{padding:26px 30px;border-radius:22px;color:#fff;background:linear-gradient(120deg,#172554,#2563EB 58%,#7C3AED);box-shadow:0 14px 32px rgba(37,99,235,.18);margin:4px 0 22px}
  .analyse-hero h1{color:#fff;margin:2px 0 7px;font-size:clamp(1.55rem,3vw,2.15rem)}
  .analyse-hero p{color:#eaf0ff;margin:0}
  .analyse-eyebrow{font-size:.75rem;font-weight:800;letter-spacing:.12em;opacity:.78}
  </style>
  <div class="analyse-hero"><div class="analyse-eyebrow">IA JOB · BUSINESS INTELLIGENCE</div>
  <h1>📊 Analyse de l’écosystème IA &amp; IT</h1>
  <p>Explorez les données et découvrez les tendances des entreprises technologiques à Marrakech.</p></div>
  """, unsafe_allow_html=True)

  # Filtres dynamiques basés sur les valeurs présentes.
  def options(colonne):
    return sorted(v for v in df[colonne].unique().tolist() if v)

  domaines = options("domaine")
  secteurs = options("secteur")
  types = options("type_acteur")
  for cle, defaut in (("analyse_domaine", "Tous"), ("analyse_secteur", "Tous"), ("analyse_type", "Tous"),
                      ("analyse_note_min", 0.0), ("analyse_email", "Tous"), ("analyse_site", "Tous")):
    st.session_state.setdefault(cle, defaut)

  def reinitialiser_analyse():
    st.session_state["analyse_domaine"] = "Tous"
    st.session_state["analyse_secteur"] = "Tous"
    st.session_state["analyse_type"] = "Tous"
    st.session_state["analyse_note_min"] = 0.0
    st.session_state["analyse_email"] = "Tous"
    st.session_state["analyse_site"] = "Tous"
    st.session_state["analyse_table_recherche"] = ""

  st.subheader("🎛️ Filtres")
  f1, f2, f3, f4, f5, f6 = st.columns([1.2, 1.2, 1.2, 1.1, 1, 1])
  domaine_sel = f1.selectbox("Domaine", ["Tous"] + domaines, key="analyse_domaine")
  secteur_sel = f2.selectbox("Secteur", ["Tous"] + secteurs, key="analyse_secteur")
  type_sel = f3.selectbox("Type d’acteur", ["Tous"] + types, key="analyse_type")
  has_ratings = df["_note"].notna().any()
  note_min = f4.slider("Note minimale", 0.0, 5.0, step=0.5, key="analyse_note_min", disabled=not has_ratings)
  email_sel = f5.selectbox("Email", ["Tous", "Avec email", "Sans email"], key="analyse_email")
  site_sel = f6.selectbox("Site web", ["Tous", "Avec site", "Sans site"], key="analyse_site")
  st.button("↺ Réinitialiser les filtres", on_click=reinitialiser_analyse, key="analyse_reset")

  mask = pd.Series(True, index=df.index)
  if domaine_sel != "Tous": mask &= df["domaine"].eq(domaine_sel)
  if secteur_sel != "Tous": mask &= df["secteur"].eq(secteur_sel)
  if type_sel != "Tous": mask &= df["type_acteur"].eq(type_sel)
  if note_min > 0: mask &= df["_note"].fillna(0).ge(note_min)
  if email_sel == "Avec email": mask &= df["_email_ok"]
  elif email_sel == "Sans email": mask &= ~df["_email_ok"]
  if site_sel == "Avec site": mask &= df["_site_ok"]
  elif site_sel == "Sans site": mask &= ~df["_site_ok"]
  vue = df.loc[mask].copy()

  note_disponibles = vue.loc[vue["_note"].between(0.01, 5), "_note"]
  note_moyenne = f"{note_disponibles.mean():.1f}/5" if not note_disponibles.empty else "—"
  kpis = [
    ("🏢 Entreprises", len(vue)),
    ("🧭 Domaines", vue["domaine"].nunique() if not vue.empty else 0),
    ("✉️ Avec email", int(vue["_email_ok"].sum())),
    ("🌐 Avec site", int(vue["_site_ok"].sum())),
    ("⭐ Note moyenne", note_moyenne),
  ]
  st.caption(f"Analyse de {len(vue)} entreprise(s) après filtres · {len(df)} dans le dataset")
  for col, (label, value) in zip(st.columns(5), kpis):
    with col:
      st.metric(label, value)

  if vue.empty:
    st.info("Aucune entreprise ne correspond aux filtres sélectionnés.")
    return

  st.markdown("### 💡 Insights & découvertes")
  insight_cols = st.columns(4)
  domaine_top = vue["domaine"].value_counts()
  secteur_top = vue["secteur"].value_counts()
  insights = [
    ("Domaine principal", domaine_top.index[0] if not domaine_top.empty else "—"),
    ("Secteur principal", secteur_top.index[0] if not secteur_top.empty else "—"),
    ("Couverture email", f"{vue['_email_ok'].mean() * 100:.1f}%"),
    ("Couverture site web", f"{vue['_site_ok'].mean() * 100:.1f}%"),
  ]
  for col, (label, value) in zip(insight_cols, insights):
    with col:
      st.container(border=True).metric(label, value)
  domaine_note = vue[vue["_note"].between(0.01, 5)].groupby("domaine")["_note"].mean().sort_values(ascending=False)
  if not domaine_note.empty:
    st.caption(f"Meilleure note moyenne observée : {domaine_note.index[0]} ({domaine_note.iloc[0]:.1f}/5), sur les entreprises notées.")

  if px is None or go is None:
    st.warning("Plotly n’est pas installé. Ajoutez `plotly` aux dépendances de Streamlit Cloud.")
  else:
    st.markdown("### 🧩 Répartition des entreprises")
    c1, c2 = st.columns(2)
    domaine_counts = vue["domaine"].value_counts().rename_axis("Domaine").reset_index(name="Entreprises")
    with c1:
      fig = px.pie(domaine_counts, names="Domaine", values="Entreprises", hole=.38,
                   title="Répartition des entreprises par domaine", color_discrete_sequence=couleurs)
      fig.update_traces(textposition="inside", textinfo="percent", hovertemplate="%{label}<br>%{value} entreprise(s)<extra></extra>")
      fig.update_layout(height=360, margin=dict(l=8,r=8,t=55,b=8), paper_bgcolor="rgba(0,0,0,0)")
      st.plotly_chart(fig, use_container_width=True, key="analyse_pie_domaines")
    with c2:
      fig = make_subplots(rows=1, cols=2, specs=[[{"type": "domain"}, {"type": "domain"}]],
                          subplot_titles=("Email", "Site web"))
      fig.add_trace(go.Pie(labels=["Présent", "Absent"], values=[int(vue["_email_ok"].sum()), int((~vue["_email_ok"]).sum())], hole=.5, name="Email"), row=1, col=1)
      fig.add_trace(go.Pie(labels=["Présent", "Absent"], values=[int(vue["_site_ok"].sum()), int((~vue["_site_ok"]).sum())], hole=.5, name="Site web"), row=1, col=2)
      fig.update_traces(marker_colors=["#10B981", "#CBD5E1"], hovertemplate="%{label}<br>%{value} entreprise(s)<extra></extra>")
      fig.update_layout(height=360, title="Disponibilité des coordonnées", margin=dict(l=8,r=8,t=65,b=8), paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
      st.plotly_chart(fig, use_container_width=True, key="analyse_donut_coordonnees")

    c1, c2 = st.columns(2)
    sector_counts = vue["secteur"].value_counts().head(15).sort_values().rename_axis("Secteur").reset_index(name="Entreprises")
    with c1:
      fig = px.bar(sector_counts, x="Entreprises", y="Secteur", orientation="h", text="Entreprises",
                   title="Entreprises par secteur", color="Entreprises", color_continuous_scale=["#93C5FD", "#2563EB", "#7C3AED"])
      fig.update_layout(height=max(330, 28 * len(sector_counts) + 100), margin=dict(l=8,r=25,t=55,b=8), coloraxis_showscale=False)
      fig.update_traces(textposition="outside")
      st.plotly_chart(fig, use_container_width=True, key="analyse_secteurs")
    with c2:
      domain_top = domaine_counts.sort_values("Entreprises", ascending=False).head(10).sort_values("Entreprises")
      fig = px.bar(domain_top, x="Entreprises", y="Domaine", orientation="h", text="Entreprises",
                   title="Top 10 des domaines", color="Entreprises", color_continuous_scale=["#BFDBFE", "#7C3AED"])
      fig.update_layout(height=max(330, 28 * len(domain_top) + 100), margin=dict(l=8,r=25,t=55,b=8), coloraxis_showscale=False)
      fig.update_traces(textposition="outside")
      st.plotly_chart(fig, use_container_width=True, key="analyse_top_domaines")

    rated = vue[vue["_note"].between(0.01, 5)].copy()
    if not rated.empty:
      st.markdown("### ⭐ Analyse des notes")
      c1, c2 = st.columns(2)
      with c1:
        fig = px.histogram(rated, x="_note", nbins=10, title="Distribution des notes des entreprises",
                           labels={"_note": "Note (sur 5)", "count": "Entreprises"}, color_discrete_sequence=["#06B6D4"])
        fig.update_layout(height=330, margin=dict(l=8,r=8,t=55,b=8), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, key="analyse_hist_notes")
      with c2:
        rated["_rang"] = range(1, len(rated) + 1)
        fig = px.scatter(rated, x="_rang", y="_note", color="domaine", hover_name="nom",
                         hover_data={"secteur": True, "nombre_avis": True} if "nombre_avis" in rated.columns else {"secteur": True},
                         title="Notes par entreprise et domaine", labels={"_rang": "Rang dans les données", "_note": "Note (sur 5)"}, color_discrete_sequence=couleurs)
        fig.update_layout(height=330, margin=dict(l=8,r=8,t=55,b=8), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, key="analyse_scatter_notes")
      domaines_notes = rated.groupby("domaine").filter(lambda groupe: len(groupe) >= 2)
      if not domaines_notes.empty and domaines_notes["domaine"].nunique() >= 2:
        c1, c2 = st.columns(2)
        with c1:
          fig = px.box(domaines_notes, x="domaine", y="_note", color="domaine", title="Distribution des notes par domaine", color_discrete_sequence=couleurs)
          fig.update_layout(height=360, margin=dict(l=8,r=8,t=55,b=8), showlegend=False, xaxis_title=None, yaxis_title="Note (sur 5)")
          st.plotly_chart(fig, use_container_width=True, key="analyse_box_notes")
        with c2:
          fig = px.violin(domaines_notes, x="domaine", y="_note", color="domaine", box=True, points="outliers", title="Densité des notes par domaine", color_discrete_sequence=couleurs)
          fig.update_layout(height=360, margin=dict(l=8,r=8,t=55,b=8), showlegend=False, xaxis_title=None, yaxis_title="Note (sur 5)")
          st.plotly_chart(fig, use_container_width=True, key="analyse_violin_notes")
    else:
      st.info("Aucune note numérique n’est disponible dans cette sélection : les graphiques de notes sont masqués.")

    st.markdown("### 🗺️ Analyse comparative")
    hierarchy = vue.copy()
    hierarchy["domaine"] = hierarchy["domaine"].replace("", "Non renseigné")
    hierarchy["secteur"] = hierarchy["secteur"].replace("", "Non renseigné")
    hierarchy["sous_secteur"] = hierarchy["sous_secteur"].replace("", "Non renseigné")
    c1, c2 = st.columns(2)
    with c1:
      fig = px.treemap(hierarchy, path=["domaine", "secteur", "sous_secteur"], title="Domaines et sous-domaines · Treemap", color="domaine", color_discrete_sequence=couleurs)
      fig.update_layout(height=420, margin=dict(l=5,r=5,t=55,b=5), paper_bgcolor="rgba(0,0,0,0)")
      st.plotly_chart(fig, use_container_width=True, key="analyse_treemap")
    with c2:
      fig = px.sunburst(hierarchy, path=["domaine", "secteur", "sous_secteur"], title="Hiérarchie domaine → secteur → sous-secteur", color="domaine", color_discrete_sequence=couleurs)
      fig.update_layout(height=420, margin=dict(l=5,r=5,t=55,b=5), paper_bgcolor="rgba(0,0,0,0)")
      st.plotly_chart(fig, use_container_width=True, key="analyse_sunburst")

    heat = pd.crosstab(vue["domaine"], vue["secteur"])
    if not heat.empty:
      fig = px.imshow(heat, text_auto=True, aspect="auto", color_continuous_scale="Blues", title="Heatmap · domaines et secteurs")
      fig.update_layout(height=max(300, 45 * len(heat) + 100), margin=dict(l=8,r=8,t=55,b=8), xaxis_title="Secteur", yaxis_title="Domaine")
      st.plotly_chart(fig, use_container_width=True, key="analyse_heatmap")

    # Radar sur des indicateurs réels exprimés en pourcentage commun.
    domaines_radar = vue.groupby("domaine").agg(
      part=("nom", "size"),
      email_pct=("_email_ok", "mean"),
      site_pct=("_site_ok", "mean"),
      note_moy=("_note", lambda s: s[s.between(0.01, 5)].mean() if s.between(0.01, 5).any() else float("nan")),
    ).sort_values("part", ascending=False).head(6)
    if len(domaines_radar) >= 2:
      indicateurs = ["Part des entreprises", "Couverture email", "Couverture site", "Note moyenne / 5"]
      fig = go.Figure()
      for domaine, ligne in domaines_radar.iterrows():
        valeurs = [100 * ligne["part"] / len(vue), 100 * ligne["email_pct"], 100 * ligne["site_pct"], 20 * ligne["note_moy"] if pd.notna(ligne["note_moy"]) else 0]
        fig.add_trace(go.Scatterpolar(r=valeurs, theta=indicateurs, fill="toself", name=str(domaine)))
      fig.update_layout(title="Comparaison des domaines · indicateurs normalisés", polar=dict(radialaxis=dict(visible=True, range=[0, 100], ticksuffix="%")), height=440, margin=dict(l=25,r=25,t=65,b=25), colorway=couleurs)
      st.plotly_chart(fig, use_container_width=True, key="analyse_radar")

  st.markdown("### 📋 Données filtrées")
  recherche = st.text_input("Rechercher une entreprise", key="analyse_table_recherche").strip()
  table = vue.copy()
  if recherche:
    table = table[table["nom"].str.contains(recherche, case=False, regex=False, na=False)]
  colonnes_table = [c for c in ("id", "nom", "domaine", "secteur", "type_acteur", "note", "email", "site_web") if c in table.columns]
  st.dataframe(table[colonnes_table], use_container_width=True, hide_index=True)
  st.download_button(
    "⬇️ Exporter les résultats en CSV",
    data=table[colonnes_table].to_csv(index=False).encode("utf-8-sig"),
    file_name="analyse_entreprises_ia_job.csv",
    mime="text/csv",
    key="analyse_export_csv",
  )


def page_sources() -> None:
  st.subheader("📡 Sources de données")
  st.success(f"✅ CSV chargé : **{len(DATA)} entreprises**")
  st.dataframe(
      DATA[["id", "nom", "domaine", "secteur", "telephone", "email"]].head(20),
      use_container_width=True,
      hide_index=True,
  )
