import streamlit as st
import urllib.parse

def afficher_carte_google_maps(adresse_ou_nom, ville="Marrakech"):
    """
    Affiche une carte Google Maps interactive intégrée dans Streamlit.
    """
    # Construction de la requête de recherche Google Maps
    query = f"{adresse_ou_nom}, {ville}"
    query_encoded = urllib.parse.quote(query)
    
    # URL d'intégration Google Maps Embed (Gratuit et sans clé API)
    maps_url = f"https://maps.google.com/maps?q={query_encoded}&t=&z=15&ie=UTF8&iwloc=&output=embed"
    
    # Affichage de l'iframe dans Streamlit
    st.components.v1.iframe(maps_url, height=300, scrolling=False)