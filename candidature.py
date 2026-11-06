from datetime import datetime
from email.message import EmailMessage
import smtplib

import streamlit as st


def envoyer_candidature(destinataire_entreprise, email_candidat, entreprise, poste, lettre, cv):
    """Envoie le CV et le message de candidature après validation du formulaire."""
    smtp = st.secrets["smtp"]
    expediteur = smtp["email"]
    mot_de_passe = smtp["mot_de_passe_application"]

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
        serveur.send_message(message)


def page_candidature():
    st.title("🚀 Envoyer une candidature")
    st.write("Remplissez le formulaire et joignez votre CV. L’envoi se fait au clic sur le bouton final.")

    if "candidatures_list" not in st.session_state:
        st.session_state.candidatures_list = []

    with st.form("form_candidature", clear_on_submit=False):
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
        envoyer_candidature(
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
        st.success(f"Candidature envoyée à {entreprise.strip()} avec le CV en pièce jointe.")
    except Exception as erreur:
        st.error(f"L’envoi a échoué : {erreur}. Vérifiez les paramètres SMTP dans les secrets Streamlit.")


if __name__ == "__main__":
    page_candidature()

