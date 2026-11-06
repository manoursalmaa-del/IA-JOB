import os
from openai import OpenAI

# Remplacez par votre clé API (ou définissez-la en variable d'environnement)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "VOTRE_CLE_API_ICI")

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_custom_cv(user_profile: dict, job_requirements: str, company_name: str) -> str:
    """
    Agent IA qui génère un CV personnalisé structuré en Markdown.
    """
    system_prompt = """
    Tu es un expert en recrutement IT & IA et rédaction de CV professionnels.
    Ton objectif est de générer un CV parfaitement adapté et optimisé (ATS-friendly) pour une opportunité spécifique.
    Met en valeur les compétences de l'utilisateur qui correspondent le mieux aux exigences de l'entreprise.
    Rédige le CV en Markdown clair avec des sections bien structurées.
    """

    user_prompt = f"""
    --- INFORMATIONS CANDIDAT ---
    Nom : {user_profile.get('nom', '')}
    Prénom : {user_profile.get('prenom', '')}
    Email : {user_profile.get('email', '')}
    Profil / Titre : {user_profile.get('profil_pro', '')}
    Ville : {user_profile.get('ville', 'Marrakech')}
    Compétences & Domaines : {user_profile.get('domaines_interet', '')}

    --- ENTREPRISE CIBLÉE ---
    Nom de l'entreprise : {company_name}
    Exigences & Compétences recherchées : {job_requirements}

    --- INSTRUCTIONS DE GÉNÉRATION ---
    1. Crée un Titre accrocheur adapté à l'offre.
    2. Rédige un Résumé professionnel (3-4 lignes) percutant aligné sur le besoin de l'entreprise.
    3. Mettez en avant les Compétences Clés (Techniques & Soft Skills) en correspondance directe avec le poste.
    4. Propose des Réalisations / Projets fictifs mais réalistes en rapport avec le profil et le poste.
    5. Ajoute une section Formation et Certifications recommandées.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # ou gpt-3.5-turbo
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content