import pandas as pd
import requests
import os

CSV_OFFRES_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "offres_stages_it.csv"
)

def fetch_maroc_jobs():
    """Collecte les offres IT ciblées exclusivement sur le Maroc et Marrakech."""
    url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=100"
    offres = []
    
    # Mots-clés de localisation obligatoires
    keywords_maroc = ["marrakech", "morocco", "maroc", "casablanca", "rabat", "north africa"]
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json().get("jobs", [])
            for job in data:
                location = str(job.get("candidate_required_location", "")).lower()
                title = str(job.get("title", "")).lower()
                
                # Filtrage strict : Maroc ou Worldwide accepté pour le Maroc
                if any(kw in location for kw in keywords_maroc) or "worldwide" in location:
                    ville_affiche = "Marrakech / Maroc" if "marrakech" in location else "Maroc (Remote / Hybride)"
                    
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
                        "date_publication": job.get("publication_date", "")[:10]
                    })
    except Exception as e:
        print(f"Erreur d'extraction : {e}")
    return offres

def load_or_create_jobs():
    """Charge les offres réellement renvoyées par la source Remotive."""
    online_jobs = fetch_maroc_jobs()
    colonnes = [
        "id", "titre", "entreprise", "domaine", "type_offre", "ville",
        "description", "url", "source", "date_publication",
    ]
    df = pd.DataFrame(online_jobs, columns=colonnes)
    df.to_csv(CSV_OFFRES_PATH, index=False, encoding="utf-8-sig")
    return df

if __name__ == "__main__":
    df = load_or_create_jobs()
    print(f"✅ {len(df)} offres Maroc/Marrakech enregistrées.")
