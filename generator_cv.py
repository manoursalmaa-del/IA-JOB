import base64
import html
import re
import unicodedata
from io import BytesIO

import streamlit as st
from fpdf import FPDF


# ============================================================
# TEMPLATES DE CV
# ============================================================
TEMPLATES = {
    "Classique": {
        "description": "Un CV sobre et professionnel avec une colonne latérale.",
        "couleur": "#1E3A8A",
        "sidebar": True,
    },
    "Moderne": {
        "description": "Un CV moderne avec une couleur personnalisable.",
        "couleur": "#0F766E",
        "sidebar": True,
    },
    "ATS-Friendly": {
        "description": "Une mise en page simple à une colonne, adaptée à la lecture par les logiciels ATS.",
        "couleur": "#334155",
        "sidebar": False,
    },
    "IT / Data Science": {
        "description": "Une structure orientée informatique, data, développement et intelligence artificielle.",
        "couleur": "#6D28D9",
        "sidebar": False,
    },
}


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================
def safe_html(value):
    """Évite qu'un texte saisi par l'utilisateur soit interprété comme du HTML."""
    return html.escape(str(value or "")).replace("\n", "<br>")


def pdf_text(value):
    """Compatibilité avec les polices PDF standard et les caractères français."""
    value = str(value or "")
    replacements = {
        "\u2022": "-", "\u2013": "-", "\u2014": "-",
        "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
        "\u00a0": " ", "\u2026": "...",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value.encode("latin-1", "replace").decode("latin-1")


def enrichir_texte_local(competences, experience):
    """Améliore la présentation sans inventer de compétences, résultats ou expériences.

    Cette fonction est une aide rédactionnelle locale et non un appel à une IA externe.
    """
    blocs = []
    mots = [item.strip(" -•\t") for item in re.split(r"[,;\n]", competences or "") if item.strip(" -•\t")]
    if mots:
        blocs.append("Compétences techniques et transversales :\n- " + "\n- ".join(mots))
    if (experience or "").strip():
        blocs.append("Expériences et missions déclarées :\n" + experience.strip())
    return "\n\n".join(blocs)


def extraire_mots_cles(texte):
    """Extrait les mots-clés utiles pour une comparaison indicative avec une offre."""
    stop_words = {
        "avec", "dans", "pour", "sous", "entre", "être", "avoir", "vous", "nous",
        "votre", "vos", "des", "les", "une", "un", "aux", "sur", "par", "que",
        "qui", "est", "sont", "plus", "comme", "ainsi", "the", "and", "with",
        "for", "from", "are", "will", "this", "experience", "expérience",
        "compétences", "competences", "poste", "profil", "recherche", "souhaité",
        "souhaite", "mission", "missions", "candidat", "candidate",
    }
    words = re.findall(r"[A-Za-zÀ-ÿ0-9+#.]{2,}", (texte or "").lower())
    result = set()
    for word in words:
        if word in stop_words:
            continue
        normalise = unicodedata.normalize("NFKD", word).encode("ascii", "ignore").decode("ascii")
        if normalise:
            result.add(normalise)
    return result


def couleur_rgb(hex_color):
    """Convertit #RRGGBB en tuple RGB pour FPDF."""
    value = (hex_color or "#1E3A8A").lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", value):
        value = "1E3A8A"
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def ajouter_section_pdf(pdf, titre, contenu, couleur):
    contenu = (contenu or "").strip()
    if not contenu:
        return
    pdf.set_text_color(*couleur)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, pdf_text(titre.upper()), new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*couleur)
    y = pdf.get_y()
    pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
    pdf.ln(2)
    pdf.set_text_color(45, 55, 65)
    pdf.set_font("Arial", "", 9.5)
    pdf.multi_cell(0, 5, pdf_text(contenu))
    pdf.ln(3)


def generer_pdf(data, template_name):
    """Crée le PDF en reprenant le style général du template choisi."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()
    couleur = couleur_rgb(data.get("couleur", TEMPLATES[template_name]["couleur"]))
    nom_complet = f"{data.get('prenom', '')} {data.get('nom', '')}".strip()

    # Les templates ATS et IT gardent une structure à une colonne.
    if template_name in ("ATS-Friendly", "IT / Data Science"):
        pdf.set_fill_color(*couleur)
        pdf.rect(0, 0, 210, 9, style="F")
        pdf.ln(7)
        pdf.set_text_color(*couleur)
        pdf.set_font("Arial", "B", 19 if template_name != "ATS-Friendly" else 17)
        pdf.cell(0, 11, pdf_text(nom_complet), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 7, pdf_text(data.get("titre", "")), new_x="LMARGIN", new_y="NEXT", align="C")
        contact = " | ".join(v for v in [data.get("email", ""), data.get("telephone", ""), data.get("adresse", "")] if v)
        pdf.set_text_color(70, 70, 70)
        pdf.set_font("Arial", "", 9)
        if contact:
            pdf.multi_cell(0, 5, pdf_text(contact), align="C")
        pdf.ln(5)
    else:
        pdf.set_fill_color(*couleur)
        pdf.rect(0, 0, 210, 36, style="F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 18)
        pdf.set_xy(12, 8)
        pdf.cell(0, 10, pdf_text(nom_complet), new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(12)
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 7, pdf_text(data.get("titre", "")), new_x="LMARGIN", new_y="NEXT")
        pdf.set_y(42)
        pdf.set_text_color(55, 65, 81)
        pdf.set_font("Arial", "", 9)
        contact = " | ".join(v for v in [data.get("email", ""), data.get("telephone", ""), data.get("adresse", "")] if v)
        if contact:
            pdf.multi_cell(0, 5, pdf_text(contact))
        pdf.ln(3)

    ajouter_section_pdf(pdf, "Profil et compétences", data.get("competences_enrichies") or data.get("competences_brutes"), couleur)
    ajouter_section_pdf(pdf, "Formation", data.get("formation"), couleur)
    ajouter_section_pdf(pdf, "Expérience professionnelle", data.get("experience"), couleur)
    ajouter_section_pdf(pdf, "Projets", data.get("projets"), couleur)
    ajouter_section_pdf(pdf, "Langues", data.get("langues"), couleur)
    ajouter_section_pdf(pdf, "Centres d'intérêt", data.get("interets"), couleur)

    # Compatibilité fpdf2 et ancienne version pyfpdf.
    output = pdf.output()
    if isinstance(output, bytearray):
        return bytes(output)
    if isinstance(output, bytes):
        return output
    # Ancien pyfpdf peut retourner une chaîne lorsqu'on utilise dest="S".
    old_output = pdf.output(dest="S")
    return old_output.encode("latin-1") if isinstance(old_output, str) else bytes(old_output)


# ============================================================
# PAGE STREAMLIT
# ============================================================
def page_cv_generator():
    st.markdown(
        """
        <div style="background:linear-gradient(135deg,#1E3A8A,#2563EB);padding:20px;
        border-radius:12px;color:white;margin-bottom:20px;">
          <h2 style="margin:0;">🤖 Omniroot - Générateur de CV Intelligent</h2>
          <p style="margin:7px 0 0;">Choisissez une structure, préparez votre CV,
          comparez-le à une offre et exportez-le en PDF.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    defaults = {
        "nom": "", "prenom": "", "titre": "", "email": "", "telephone": "",
        "adresse": "", "competences_brutes": "", "competences_enrichies": "",
        "formation": "", "experience": "", "projets": "", "langues": "",
        "interets": "", "couleur": "#1E3A8A", "template": "Classique",
        "offre_emploi": "", "photo": None,
    }
    if "cv_data" not in st.session_state:
        st.session_state.cv_data = defaults.copy()
    else:
        for key, value in defaults.items():
            st.session_state.cv_data.setdefault(key, value)

    data = st.session_state.cv_data

    st.markdown("### 1. Choisir une structure de CV")
    template_name = st.selectbox(
        "Template", list(TEMPLATES.keys()),
        index=list(TEMPLATES.keys()).index(data["template"]) if data["template"] in TEMPLATES else 0,
        key="cv_template_choice",
    )
    st.caption(TEMPLATES[template_name]["description"])
    default_color = data.get("couleur") or TEMPLATES[template_name]["couleur"]
    couleur_theme = st.color_picker("Couleur principale du CV", value=default_color, key="cv_color_choice")

    col_form, col_preview = st.columns([1.05, 1], gap="large")

    with col_form:
        st.markdown("### 2. Informations personnelles et contenu")
        with st.form("form_cv_advanced"):
            c1, c2 = st.columns(2)
            prenom = c1.text_input("Prénom", value=data["prenom"], placeholder="Ex. Youssef")
            nom = c2.text_input("Nom", value=data["nom"], placeholder="Ex. El Amrani")
            titre = st.text_input("Poste recherché / titre professionnel", value=data["titre"], placeholder="Ex. Développeur Python / Data Analyst")

            c3, c4 = st.columns(2)
            email = c3.text_input("Email", value=data["email"])
            telephone = c4.text_input("Téléphone", value=data["telephone"], placeholder="+212 6...")
            adresse = st.text_input("Ville / Adresse", value=data["adresse"], placeholder="Casablanca, Maroc")

            competences = st.text_area(
                "Compétences techniques et personnelles", value=data["competences_brutes"],
                placeholder="Python, SQL, Pandas, Streamlit, Machine Learning, communication...", height=90,
            )
            formation = st.text_area("Formations et diplômes", value=data["formation"], height=75, placeholder="Diplôme, établissement, année...")
            experience = st.text_area("Expériences professionnelles / stages", value=data["experience"], height=90, placeholder="Poste, entreprise, dates, missions réellement réalisées...")
            projets = st.text_area("Projets réalisés", value=data["projets"], height=75, placeholder="Projet, technologies, résultat...")

            c5, c6 = st.columns(2)
            langues = c5.text_input("Langues", value=data["langues"], placeholder="Arabe, français, anglais")
            interets = c6.text_input("Centres d'intérêt", value=data["interets"])
            photo = st.file_uploader("Photo de profil (facultative)", type=["jpg", "jpeg", "png"])
            offre = st.text_area(
                "Offre d'emploi cible (facultatif)", value=data["offre_emploi"], height=100,
                placeholder="Collez ici la description de l'offre pour comparer ses mots-clés à votre CV.",
            )
            submit = st.form_submit_button("Enregistrer et préparer le CV", type="primary", use_container_width=True)

        if submit:
            data.update({
                "prenom": prenom.strip(), "nom": nom.strip(), "titre": titre.strip(),
                "email": email.strip(), "telephone": telephone.strip(), "adresse": adresse.strip(),
                "competences_brutes": competences.strip(), "formation": formation.strip(),
                "experience": experience.strip(), "projets": projets.strip(),
                "langues": langues.strip(), "interets": interets.strip(),
                "couleur": couleur_theme, "template": template_name, "offre_emploi": offre.strip(),
            })
            if photo is not None:
                data["photo"] = photo.getvalue()
                data["photo_type"] = photo.type or "image/jpeg"
            # Assistant rédactionnel local : il organise seulement les informations fournies.
            data["competences_enrichies"] = enrichir_texte_local(competences, experience)
            st.session_state.cv_data = data
            st.success("CV mis à jour. Vérifiez les informations avant de télécharger le PDF.")
            st.rerun()

    # Le choix du template et la couleur s'appliquent immédiatement à l'aperçu.
    data = st.session_state.cv_data
    data["template"] = template_name
    data["couleur"] = couleur_theme
    theme = couleur_theme

    with col_preview:
        st.markdown("### 3. Aperçu dynamique")
        photo_html = (
            '<div style="width:82px;height:82px;border-radius:50%;background:#ffffff33;'
            'margin:0 auto 12px;display:flex;align-items:center;justify-content:center;font-size:30px;">👤</div>'
        )
        if data.get("photo"):
            b64_img = base64.b64encode(data["photo"]).decode("ascii")
            mime = data.get("photo_type", "image/jpeg")
            photo_html = (
                '<div style="text-align:center;margin-bottom:12px;">'
                f'<img src="data:{mime};base64,{b64_img}" style="width:82px;height:82px;'
                'border-radius:50%;object-fit:cover;border:3px solid white;"></div>'
            )

        full_name = safe_html(f"{data['prenom'] or 'Prénom'} {data['nom'] or 'Nom'}")
        job_title = safe_html(data["titre"] or "Poste recherché")
        contact_html = "<br>".join(safe_html(x) for x in [data["email"] or "Email", data["telephone"] or "Téléphone", data["adresse"] or "Ville"])
        skills = safe_html(data["competences_enrichies"] or data["competences_brutes"] or "À compléter")
        education = safe_html(data["formation"] or "À compléter")
        experience_html = safe_html(data["experience"] or "À compléter")
        projects = safe_html(data["projets"] or "À compléter")
        languages = safe_html(data["langues"] or "À compléter")
        interests = safe_html(data["interets"] or "À compléter")

        if TEMPLATES[template_name]["sidebar"]:
            preview = f"""
            <div style="display:flex;border:1px solid #CBD5E1;border-radius:12px;overflow:hidden;background:white;color:#1E293B;font-family:Arial,sans-serif;min-height:480px;">
              <div style="width:36%;background:{theme};color:white;padding:15px 12px;box-sizing:border-box;overflow-wrap:anywhere;">
                {photo_html}<h3 style="text-align:center;font-size:16px;color:white;">{full_name}</h3>
                <p style="text-align:center;font-size:12px;color:white;">{job_title}</p><hr style="border-color:#ffffff66;">
                <b style="font-size:12px;">CONTACT</b><p style="font-size:11px;">{contact_html}</p>
                <b style="font-size:12px;">LANGUES</b><p style="font-size:11px;">{languages}</p>
                <b style="font-size:12px;">CENTRES D'INTÉRÊT</b><p style="font-size:11px;">{interests}</p>
              </div>
              <div style="width:64%;padding:17px;box-sizing:border-box;overflow-wrap:anywhere;">
                <h4 style="color:{theme};border-bottom:2px solid {theme};">COMPÉTENCES</h4><p style="font-size:12px;white-space:pre-wrap;">{skills}</p>
                <h4 style="color:{theme};border-bottom:2px solid {theme};">FORMATION</h4><p style="font-size:12px;white-space:pre-wrap;">{education}</p>
                <h4 style="color:{theme};border-bottom:2px solid {theme};">EXPÉRIENCE</h4><p style="font-size:12px;white-space:pre-wrap;">{experience_html}</p>
                <h4 style="color:{theme};border-bottom:2px solid {theme};">PROJETS</h4><p style="font-size:12px;white-space:pre-wrap;">{projects}</p>
              </div>
            </div>"""
        else:
            preview = f"""
            <div style="border:1px solid #CBD5E1;border-top:8px solid {theme};border-radius:10px;background:white;padding:20px;color:#1E293B;font-family:Arial,sans-serif;overflow-wrap:anywhere;">
              <div style="text-align:center;">{photo_html}<h2 style="margin:4px;color:{theme};">{full_name}</h2>
                <p>{job_title}</p><p style="font-size:11px;">{contact_html}</p></div>
              <h4 style="color:{theme};border-bottom:2px solid {theme};">COMPÉTENCES</h4><p style="font-size:12px;white-space:pre-wrap;">{skills}</p>
              <h4 style="color:{theme};border-bottom:2px solid {theme};">FORMATION</h4><p style="font-size:12px;white-space:pre-wrap;">{education}</p>
              <h4 style="color:{theme};border-bottom:2px solid {theme};">EXPÉRIENCE</h4><p style="font-size:12px;white-space:pre-wrap;">{experience_html}</p>
              <h4 style="color:{theme};border-bottom:2px solid {theme};">PROJETS</h4><p style="font-size:12px;white-space:pre-wrap;">{projects}</p>
              <p style="font-size:12px;"><b>Langues :</b> {languages} &nbsp; <b>Intérêts :</b> {interests}</p>
            </div>"""
        st.markdown(preview, unsafe_allow_html=True)

        if data.get("offre_emploi", "").strip():
            texte_cv = " ".join([
                data.get("titre", ""), data.get("competences_brutes", ""),
                data.get("formation", ""), data.get("experience", ""), data.get("projets", ""),
            ])
            requis = extraire_mots_cles(data["offre_emploi"])
            presents = extraire_mots_cles(texte_cv)
            trouves = sorted(requis & presents)
            manquants = sorted(requis - presents)
            st.markdown("### 4. Comparaison avec l'offre d'emploi")
            if requis:
                score = round(len(trouves) / len(requis) * 100)
                st.metric("Correspondance indicative des mots-clés", f"{score}%")
                st.caption("Ce score compare des mots-clés. Ce n'est pas une évaluation complète par une IA.")
                if trouves:
                    st.write("**Mots-clés présents :** " + ", ".join(trouves))
                if manquants:
                    st.write("**Mots-clés non trouvés dans le CV :** " + ", ".join(manquants[:30]))
                    st.info("Ajoutez un élément uniquement s'il correspond réellement à vos compétences ou à votre expérience.")
            else:
                st.info("L'offre ne contient pas assez de mots-clés exploitables pour effectuer la comparaison.")

        if data.get("prenom", "").strip() and data.get("nom", "").strip():
            try:
                pdf_bytes = generer_pdf(data, template_name)
                st.download_button(
                    "📥 Télécharger mon CV en PDF", data=pdf_bytes,
                    file_name=f"CV_{data['prenom']}_{data['nom']}.pdf".replace(" ", "_"),
                    mime="application/pdf", use_container_width=True, type="primary",
                )
            except Exception as exc:
                st.error(f"Erreur pendant la génération du PDF : {exc}")
                st.caption("Installez la bibliothèque recommandée avec : py -m pip install --upgrade fpdf2")
        else:
            st.info("Renseignez le prénom et le nom, puis cliquez sur Enregistrer pour activer le téléchargement PDF.")

    st.caption(
        "Transparence : l'assistant de rédaction et la comparaison fonctionnent localement. "
        "Aucun appel à une véritable API d'IA n'est effectué dans cette version. "
        "Une API pourra être ajoutée séparément pour une reformulation plus avancée."
    )


# Pour lancer cette page seule, décommentez les deux lignes suivantes :
# if __name__ == "__main__":
#     page_cv_generator()
