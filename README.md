# IA-JOB
Plateforme intelligente de recherche d'emploi et de stages en informatique et intelligence artificielle à Marrakech.
IA JOB — Plateforme de carrière

Application de carrière réalisée avec Python et Streamlit. Elle regroupe les pages Entreprises, Offres, Analyse, Matching IA, Candidature, Suivi et Générateur de CV.

## Prérequis

- Python 3.10 ou une version plus récente
- `pip`
- Une connexion Internet pour charger les offres en ligne

Sous Windows, vérifiez Python avec :

```powershell
py --version
```

## Installation locale

Ouvrez PowerShell dans le dossier racine du projet, celui qui contient `frontend` et `backend`, puis exécutez :

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r frontend/requirements.txt
```

Si PowerShell bloque l’activation de l’environnement, vous pouvez installer les dépendances et lancer Streamlit avec `py -m` sans activer l’environnement.

## Configuration du courriel (facultatif)

Pour activer l’envoi des candidatures par Gmail, créez le fichier `frontend/.streamlit/secrets.toml` à partir de ce modèle :

```toml
[smtp]
email = "votre-adresse@gmail.com"
mot_de_passe_application = "votre-mot-de-passe-application-google"
serveur = "smtp.gmail.com"
port = 587
```

Utilisez un mot de passe d’application Google, pas le mot de passe normal du compte. Ne publiez jamais `secrets.toml` ou ses valeurs dans GitHub. Sur Streamlit Community Cloud, ajoutez les mêmes paramètres dans **App settings → Secrets**.

## Lancement

Depuis la racine du projet :

```powershell
py -m streamlit run frontend/entreprisecv.py
```

Streamlit affiche l’adresse locale dans le terminal, généralement `http://localhost:8501`. Arrêtez le serveur avec `Ctrl+C`.

## Déploiement sur Streamlit Community Cloud

1. Envoyez les fichiers du projet sur GitHub et poussez les changements sur la branche à déployer.
2. Dans Streamlit Community Cloud, sélectionnez le dépôt et cette branche.
3. Indiquez `frontend/entreprisecv.py` comme **Main file path**.
4. Ajoutez les secrets SMTP dans les paramètres de l’application si l’envoi de courriels est activé.
5. Déployez ou redémarrez l’application après chaque mise à jour du code.

Le fichier de dépendances Streamlit est `frontend/requirements.txt`. Les modifications locales n’apparaissent sur le site qu’après leur envoi sur la branche GitHub reliée à l’application.

## Données et confidentialité

Les fichiers CSV du dossier `frontend` fournissent les données locales initiales utilisées par l’application. Les données enregistrées dans `st.session_state` ne survivent pas à une nouvelle session. Pour conserver durablement les candidatures sur Streamlit Cloud, configurez une base de données persistante accessible depuis le déploiement.

Ne placez pas de clés API, mots de passe ou autres secrets dans les fichiers Python, CSV ou dans un dépôt GitHub public.
