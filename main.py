from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import hashlib

from database import get_db, init_db
from models import User, Entreprise, OffreStage, Candidature
from schemas import UserCreate, UserResponse, EntrepriseSchema
from typing import List
from pydantic import BaseModel
from ai_cv_agent import generate_custom_cv

# Schéma de requête
class CVPromptRequest(BaseModel):
    user_profile: dict
    company_name: str
    job_requirements: str

@app.post("/api/generate-cv")
def api_generate_cv(data: CVPromptRequest):
    try:
        cv_markdown = generate_custom_cv(
            user_profile=data.user_profile,
            job_requirements=data.job_requirements,
            company_name=data.company_name
        )
        return {"success": True, "cv_markdown": cv_markdown}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app = FastAPI(
    title="AI Marrakech Ecosystem API",
    description="API Backend de gestion des profils, entreprises et offres d'emploi Tech à Marrakech",
    version="1.0.0"
)

# Autoriser les requêtes CORS (pour faire communiquer Streamlit / React avec FastAPI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation des tables SQL au démarrage de l'API
@app.on_event("startup")
def startup_event():
    init_db()

# ============================================================
# ENDPOINTS (ROUTES API)
# ============================================================

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API AI Marrakech Ecosystem"}

# 1. Inscription / Création de profil
@app.post("/api/users/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Vérifier si l'email existe déjà
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Un compte existe déjà avec cette adresse email.")

    # Hachage du mot de passe en SHA-256
    hashed_pwd = hashlib.sha256(user_data.password.encode('utf-8')).hexdigest()
    domaines_str = ",".join(user_data.domaines_interet) if user_data.domaines_interet else ""

    new_user = User(
        prenom=user_data.prenom,
        nom=user_data.nom,
        email=user_data.email,
        password_hash=hashed_pwd,
        profil_pro=user_data.profil_pro,
        ville=user_data.ville,
        domaines_interet=domaines_str
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# 2. Récupérer toutes les entreprises
@app.get("/api/entreprises", response_model=List[EntrepriseSchema])
def get_entreprises(domaine: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Entreprise)
    if domaine:
        query = query.filter(Entreprise.domaine == domaine)
    return query.all()

# 3. Récupérer les offres de stage
@app.get("/api/stages")
def get_stages(db: Session = Depends(get_db)):
    return db.query(OffreStage).all()