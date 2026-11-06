from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# Schéma pour la création d'un profil
class UserCreate(BaseModel):
    prenom: str
    nom: str
    email: str
    password: str
    profil_pro: str
    ville: str
    domaines_interet: Optional[List[str]] = []

class UserResponse(BaseModel):
    id: int
    prenom: str
    nom: str
    email: str
    profil_pro: str
    ville: str
    created_at: datetime

    class Config:
        from_attributes = True

# Schéma Entreprise
class EntrepriseSchema(BaseModel):
    id: int
    nom: str
    type_acteur: Optional[str]
    secteur: Optional[str]
    adresse: Optional[str]
    telephone: Optional[str]
    site_web: Optional[str]
    email: Optional[str]
    note_num: float
    nombre_avis: int
    domaine: str

    class Config:
        from_attributes = True