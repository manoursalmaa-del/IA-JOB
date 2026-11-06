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
  st.subheader("📊 Analyse de l'écosystème")
  c1, c2 = st.columns(2)
  with c1:
    st.bar_chart(DATA["domaine"].value_counts())
  with c2:
    stats = pd.Series({
        "Avec email": len(DATA[DATA["email"] != ""]),
        "Avec site web": len(DATA[DATA["site_web"] != ""]),
        "Sans email": len(DATA[DATA["email"] == ""]),
    })
    st.bar_chart(stats)


def page_sources() -> None:
  st.subheader("📡 Sources de données")
  st.success(f"✅ CSV chargé : **{len(DATA)} entreprises**")
  st.dataframe(
      DATA[["id", "nom", "domaine", "secteur", "telephone", "email"]].head(20),
      use_container_width=True,
      hide_index=True,
  )
