from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# ============================================================
# TABLE 1 : USERS (Utilisateurs / Profils)
# ============================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    prenom = Column(String(100), nullable=False)
    nom = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    profil_pro = Column(String(100))
    ville = Column(String(100), default="Marrakech")
    domaines_interet = Column(Text)  # Stocké sous forme de texte séparé par des virgules
    cv_filename = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    candidatures = relationship("Candidature", back_populates="user")

# ============================================================
# TABLE 2 : ENTREPRISES (Annuaire Tech / IA)
# ============================================================
class Entreprise(Base):
    __tablename__ = "entreprises"

    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(String(100), nullable=True)
    nom = Column(String(200), nullable=False)
    type_acteur = Column(String(100), nullable=True)
    secteur = Column(String(100), nullable=True)
    sous_secteur = Column(String(100), nullable=True)
    services_ia = Column(Text, nullable=True)
    adresse = Column(Text, nullable=True)
    quartier = Column(String(100), nullable=True)
    telephone = Column(String(50), nullable=True)
    site_web = Column(String(255), nullable=True)
    email = Column(String(150), nullable=True)
    note_num = Column(Float, default=0.0)
    nombre_avis = Column(Integer, default=0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    domaine = Column(String(100), default="Informatique & Technologies")

# ============================================================
# TABLE 3 : OFFRES_STAGES (Opportunités IT & IA)
# ============================================================
class OffreStage(Base):
    __tablename__ = "offres_stages"

    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String(200), nullable=False)
    entreprise_nom = Column(String(200))
    domaine = Column(String(100))
    type_offre = Column(String(100), default="Stage PFE")
    ville = Column(String(100), default="Marrakech")
    description = Column(Text)
    url_offre = Column(Text, nullable=True)
    source = Column(String(100), default="Plateforme")
    date_publication = Column(String(50))

# ============================================================
# TABLE 4 : CANDIDATURES (Liaison Utilisateur <-> Offre)
# ============================================================
class Candidature(Base):
    __tablename__ = "candidatures"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    entreprise_id = Column(Integer, ForeignKey("entreprises.id", ondelete="SET NULL"), nullable=True)
    offre_id = Column(Integer, ForeignKey("offres_stages.id", ondelete="SET NULL"), nullable=True)
    message = Column(Text, nullable=True)
    statut = Column(String(50), default="Envoyé")
    date_envoi = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="candidatures")