"""AI Marrakech Ecosystem Intelligence - Application Streamlit complète.

Connectée au fichier : entreprises_marrakech_emails.csv
Lancer : streamlit run "app(8).py"
"""
import os
from urllib.parse import quote

import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================
st.set_page_config(page_title="AI Marrakech Ecosystem Intelligence",
                   page_icon="🧭", layout="wide")

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "entreprises_marrakech_emails.csv")
