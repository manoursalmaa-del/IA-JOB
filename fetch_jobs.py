import pandas as pd
import requests
import os
import re
from html import unescape
from html.parser import HTMLParser

CSV_OFFRES_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "offres_stages_it.csv"
)


class _HTMLDescriptionParser(HTMLParser):
    """Convertit les descriptions HTML des flux d'offres en texte lisible."""

    BLOCK_TAGS = {"p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignored_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.ignored_depth += 1
        elif not self.ignored_depth and tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.ignored_depth:
            self.ignored_depth -= 1
        elif not self.ignored_depth and tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        if not self.ignored_depth and tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.ignored_depth:
            self.parts.append(data)


def nettoyer_description(description):
    """Retire les balises HTML et garde les paragraphes et entités lisibles."""
    raw = str(description or "").strip()
    if not raw:
        return ""
    # Certains flux renvoient les balises HTML échappées (&lt;p&gt;...).
    if re.search(r"&lt;\s*/?\s*(?:p|div|br|li|ul|ol|h[1-6])\b", raw, flags=re.IGNORECASE):
        raw = unescape(raw)
    parser = _HTMLDescriptionParser()
    try:
        parser.feed(raw)
        parser.close()
        text = "".join(parser.parts)
    except Exception:
        text = raw
    text = unescape(text).replace("\xa0", " ")
    lines = [re.sub(r"[\t\r ]+", " ", line).strip() for line in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(line for line in lines if line)).strip()

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
                        "description": nettoyer_description(job.get("description", "")),
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
