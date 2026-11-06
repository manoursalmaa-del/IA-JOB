from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# Format d'URL pour MySQL : mysql+pymysql://UTILISATEUR:MOT_DE_PASSE@localhost:3306/NOM_BDD
# Remplacez 'root' et 'votre_mot_de_passe' par vos identifiants MySQL réels :
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:votre_mot_de_passe@localhost:3306/marrakech_ai_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Crée automatiquement les tables SQL définies dans models.py"""
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()