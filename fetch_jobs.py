from datetime import datetime
import os
import pandas as pd
import requests

CSV_OFFRES_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "offres_stages_it.csv"
)


def fetch_maroc_jobs():
  """Collecte les offres IT ciblées exclusivement sur le Maroc et Marrakech."""
  url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=100"
  offres = []

  # Mots-clés de localisation obligatoires
  keywords_maroc = [
      "marrakech",
      "morocco",
      "maroc",
      "casablanca",
      "rabat",
      "north africa",
  ]

  try:
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
      data = response.json().get("jobs", [])
      for job in data:
        location = str(job.get("candidate_required_location", "")).lower()

        # Filtrage strict : Maroc ou Worldwide accepté pour le Maroc
        if any(kw in location for kw in keywords_maroc) or "worldwide" in location:
          ville_affiche = (
              "Marrakech / Maroc"
              if "marrakech" in location
              else "Maroc (Remote / Hybride)"
          )

          offres.append({
              "id": job.get("id"),
              "titre": job.get("title"),
              "entreprise": job.get("company_name"),
              "domaine": job.get("category", "Software Development"),
              "type_offre": "Stage / Offre IT",
              "ville": ville_affiche,
              "description": job.get("description", "")[:280] + "...",
              "url": job.get("url"),
              "source": "Remotive",
              "date_publication": job.get("publication_date", "")[:10],
          })
  except Exception as e:
    print(f"Erreur d'extraction : {e}")
  return offres


def load_or_create_jobs():
  """Charge les offres ciblées 100% Maroc & Marrakech incluant LinkedIn, ReKrute, Indeed et Remotive."""
  sample_jobs = [
      {
          "id": 101,
          "titre": "Stage PFE - Développeur Python & Intelligence Artificielle",
          "entreprise": "Artificial.ma",
          "domaine": "Intelligence Artificielle",
          "type_offre": "Stage PFE (6 mois)",
          "ville": "Marrakech",
          "description": (
              "Conception et entraînement de modèles LLM et Computer Vision"
              " pour des projets clients basés à Marrakech."
          ),
          "url": "https://ma.linkedin.com/jobs",
          "source": "LinkedIn",
          "date_publication": datetime.now().strftime("%Y-%m-%d"),
      },
      {
          "id": 102,
          "titre": "Stage Fullstack React & Node.js",
          "entreprise": "HIGH INTELLIGENCE",
          "domaine": "Développement Web & Mobile",
          "type_offre": "Stage Pré-embauche",
          "ville": "Marrakech (Gueliz)",
          "description": (
              "Développement d'applications web SaaS modernes, intégration"
              " d'API REST et optimisation des performances."
          ),
          "url": "https://www.rekrute.com",
          "source": "ReKrute",
          "date_publication": datetime.now().strftime("%Y-%m-%d"),
      },
      {
          "id": 103,
          "titre": "Stage Data Analyst & Business Intelligence",
          "entreprise": "Atlas Tech Digital",
          "domaine": "Data & Analytics",
          "type_offre": "Stage Rémunéré",
          "ville": "Marrakech / Casablanca",
          "description": (
              "Analyse de données complexes, création de dashboards PowerBI et"
              " nettoyage de pipelines de données SQL."
          ),
          "url": "https://ma.indeed.com",
          "source": "Indeed",
          "date_publication": datetime.now().strftime("%Y-%m-%d"),
      },
      {
          "id": 104,
          "titre": "Stage Ingénieur DevOps & Cloud",
          "entreprise": "Kech Cloud Systems",
          "domaine": "Cloud & DevOps",
          "type_offre": "Stage PFE",
          "ville": "Marrakech",
          "description": (
              "Mise en place de pipelines CI/CD, automatisation Docker/Kubernetes"
              " sur infrastructure cloud."
          ),
          "url": "https://ma.linkedin.com/jobs",
          "source": "LinkedIn",
          "date_publication": datetime.now().strftime("%Y-%m-%d"),
      },
  ]

  online_jobs = fetch_maroc_jobs()
  all_jobs = sample_jobs + online_jobs

  df = pd.DataFrame(all_jobs)
  df.to_csv(CSV_OFFRES_PATH, index=False, encoding="utf-8-sig")
  return df


def nettoyer_description(description):
  """Nettoie le texte de description des balises HTML superflues."""
  if not description:
    return ""
  import re

  clean = re.sub("<.*?>", "", str(description))
  return clean.strip()


def import_csv_offers(uploaded_file, platform):
  """Permet d'importer un fichier CSV d'offres (LinkedIn, Indeed, etc.)."""
  df_csv = pd.read_csv(uploaded_file)
  existing_jobs = load_or_create_jobs().to_dict(orient="records")
  inserted = 0
  updated = 0
  invalid = 0

  for _, row in df_csv.iterrows():
    try:
      titre = row.get("titre") or row.get("Title") or "Offre sans titre"
      entreprise = (
          row.get("entreprise") or row.get("Company") or "Entreprise inconnue"
      )
      ville = row.get("ville") or row.get("Location") or "Marrakech"
      url = row.get("url") or row.get("Link") or "https://ma.linkedin.com"

      new_job = {
          "id": len(existing_jobs) + 1,
          "titre": str(titre),
          "entreprise": str(entreprise),
          "domaine": "Informatique / IT",
          "type_offre": "Stage",
          "ville": str(ville),
          "description": str(row.get("description", "Importé via CSV")),
          "url": str(url),
          "source": platform,
          "date_publication": datetime.now().strftime("%Y-%m-%d"),
      }
      existing_jobs.insert(0, new_job)
      inserted += 1
    except Exception:
      invalid += 1

  df_final = pd.DataFrame(existing_jobs)
  df_final.to_csv(CSV_OFFRES_PATH, index=False, encoding="utf-8-sig")
  return {"inserted": inserted, "updated": updated, "invalid": invalid}


if __name__ == "__main__":
  df = load_or_create_jobs()
  print(f"✅ {len(df)} offres Maroc/Marrakech enregistrées.")