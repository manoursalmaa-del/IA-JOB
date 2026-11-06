from datetime import datetime
from email.message import EmailMessage
import smtplib

import streamlit as st


def envoyer_candidature(
    destinataire_entreprise,
    email_candidat,
    entreprise,
    poste,
    lettre,
    cv,
    prenom_candidat="",
):
    """Envoie la candidature à l'entreprise, puis une confirmation au candidat.

    La valeur retournée indique si l'email de confirmation a également été remis.
    Une erreur sur l'envoi à l'entreprise est propagée à l'appelant.
    """
    smtp = st.secrets["smtp"]
    expediteur = smtp["email"]
    mot_de_passe = smtp.get("mot_de_passe_application") or smtp.get("password")
    if not mot_de_passe:
        raise KeyError(
            "Ajoutez mot_de_passe_application (ou password) dans la section [smtp] de secrets.toml."
        )

    message = EmailMessage()
    message["Subject"] = f"Candidature – {poste or 'Poste visé'} – {entreprise}"
    message["From"] = expediteur
    message["To"] = destinataire_entreprise
    message["Reply-To"] = email_candidat
    message.set_content(
        f"Bonjour,\n\n"
        f"Veuillez trouver ci-joint ma candidature pour le poste « {poste or 'Poste visé'} » chez {entreprise}.\n\n"
        f"{lettre.strip() or 'Vous trouverez mon CV en pièce jointe.'}\n\n"
        f"Cordialement,\n{email_candidat}"
    )

    cv_bytes = cv.getvalue()
    mime = cv.type or "application/octet-stream"
    type_principal, sous_type = mime.split("/", 1) if "/" in mime else ("application", "octet-stream")
    message.add_attachment(
        cv_bytes,
        maintype=type_principal,
        subtype=sous_type,
        filename=cv.name,
    )

    with smtplib.SMTP(smtp.get("serveur", "smtp.gmail.com"), int(smtp.get("port", 587))) as serveur:
        serveur.starttls()
        serveur.login(expediteur, mot_de_passe)
        refus = serveur.send_message(message)

    refus_normalises = {adresse.casefold() for adresse in refus}
    if destinataire_entreprise.casefold() in refus_normalises:
        raise smtplib.SMTPRecipientsRefused(refus)

    # La confirmation est un email séparé et ne reçoit ni CV ni lettre.
    confirmation = EmailMessage()
    confirmation["Subject"] = "Confirmation d'envoi de votre candidature – IA JOB"
    confirmation["From"] = expediteur
    confirmation["To"] = email_candidat
    confirmation.set_content(
        f"Bonjour {prenom_candidat.strip() or 'candidat'},\n\n"
        f"Nous vous confirmons que votre candidature a été envoyée avec succès "
        f"à l'entreprise {entreprise}.\n\n"
        "Votre CV et votre lettre de motivation ont bien été transmis à l'entreprise.\n\n"
        "Merci d'avoir utilisé IA JOB !\n\n"
        "Bonne chance pour votre candidature.\n\n"
        "L'équipe IA JOB"
    )
    try:
        with smtplib.SMTP(smtp.get("serveur", "smtp.gmail.com"), int(smtp.get("port", 587))) as serveur:
            serveur.starttls()
            serveur.login(expediteur, mot_de_passe)
            refus_confirmation = serveur.send_message(confirmation)
        return email_candidat.casefold() not in {
            adresse.casefold() for adresse in refus_confirmation
        }
    except Exception:
        # L'entreprise a déjà reçu la candidature : ne pas faire échouer le suivi.
        return False


def page_candidature():
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%); padding: 20px; border-radius: 12px; color: white; margin-bottom: 25px;">
            <h2 style="margin: 0;">🚀 Envoi de candidature - IA JOB</h2>
            <p style="margin-bottom: 0;">Le CV sera envoyé à l’entreprise au clic sur le bouton final.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "candidatures_list" not in st.session_state:
        st.session_state.candidatures_list = []

    with st.form("form_candidature_local", clear_on_submit=False):
        entreprise = st.text_input("Nom de l’entreprise")
        email_entreprise = st.text_input("E-mail de recrutement de l’entreprise")
        poste = st.text_input("Intitulé du poste")
        email_candidat = st.text_input("Votre adresse e-mail")
        lettre = st.text_area("Message / lettre de motivation (optionnel)")
        cv = st.file_uploader("Joignez votre CV (format PDF)", type=["pdf"])
        envoyer = st.form_submit_button("📤 Envoyer ma candidature avec mon CV", type="primary", use_container_width=True)

    if not envoyer:
        return

    champs_manquants = []
    if not entreprise.strip():
        champs_manquants.append("le nom de l’entreprise")
    if not email_entreprise.strip():
        champs_manquants.append("l’e-mail de l’entreprise")
    if not email_candidat.strip():
        champs_manquants.append("votre e-mail")
    if cv is None:
        champs_manquants.append("votre CV")

    if champs_manquants:
        st.error("Veuillez renseigner : " + ", ".join(champs_manquants) + ".")
        return

    if not cv.name.lower().endswith(".pdf") or not cv.getvalue().startswith(b"%PDF-"):
        st.error("Le fichier choisi n’est pas un PDF valide. Veuillez joindre un CV au format PDF.")
        return

    cle_candidature = (
        entreprise.strip().casefold(),
        (poste.strip() or "Non spécifié").casefold(),
    )
    doublon = any(
        (
            c.get("entreprise", "").casefold(),
            c.get("poste", "").casefold(),
        ) == cle_candidature
        for c in st.session_state.candidatures_list
    )
    if doublon:
        st.error("Une candidature pour ce poste chez cette entreprise existe déjà dans le suivi.")
        return

    try:
        confirmation_envoyee = envoyer_candidature(
            email_entreprise.strip(),
            email_candidat.strip(),
            entreprise.strip(),
            poste.strip(),
            lettre,
            cv,
        )
        st.session_state.candidatures_list.append({
            "entreprise": entreprise.strip(),
            "email_candidat": email_candidat.strip(),
            "poste": poste.strip() or "Non spécifié",
            "statut": "✅ Candidature envoyée",
            "date": datetime.today().strftime("%Y-%m-%d"),
            "notes": f"CV envoyé à {email_entreprise.strip()}",
        })
        if confirmation_envoyee:
            st.success(
                f"Candidature envoyée à {entreprise.strip()} avec le CV en pièce jointe. "
                "Un email de confirmation sans pièce jointe vous a été envoyé."
            )
        else:
            st.warning(
                f"La candidature a bien été envoyée à {entreprise.strip()}, "
                "mais l’email de confirmation n’a pas pu être remis."
            )
    except Exception as erreur:
        st.error(f"L’envoi a échoué : {erreur}. Vérifiez les paramètres SMTP dans les secrets Streamlit.")


if __name__ == "__main__":
    page_candidature()


