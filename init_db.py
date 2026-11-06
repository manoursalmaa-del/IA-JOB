import pandas as pd
import os
from database import engine, SessionLocal, init_db
from models import Entreprise

# Créer les tables SQL si ce n'est pas fait
init_db()

db = SessionLocal()

csv_path = "../entreprises_marrakech_emails.csv"
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df.columns = [c.strip().lower() for c in df.columns]

    for _, row in df.iterrows():
        ent = Entreprise(
            nom=str(row.get("nom", "")),
            type_acteur=str(row.get("type_acteur", "")),
            secteur=str(row.get("secteur", "")),
            sous_secteur=str(row.get("sous_secteur", "")),
            adresse=str(row.get("adresse", "")),
            telephone=str(row.get("telephone", "")),
            site_web=str(row.get("site_web", "")),
            email=str(row.get("email", "")),
            note_num=float(pd.to_numeric(row.get("note"), errors="coerce") or 0.0),
            nombre_avis=int(pd.to_numeric(row.get("nombre_avis"), errors="coerce") or 0),
            domaine=str(row.get("domaine", "Informatique & Technologies"))
        )
        db.add(ent)

    db.commit()
    print("✅ Données des entreprises insérées avec succès dans la base SQL !")
else:
    print("⚠️ Fichier CSV non trouvé.")

db.close()