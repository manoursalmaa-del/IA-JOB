"""Matching de CV et offres réelles pour IA JOB."""

import re
import unicodedata
from html import escape

import pandas as pd
import streamlit as st

from fetch_jobs import load_or_create_jobs


SKILLS = {
    "python": ["python"], "java": ["java"], "sql": ["sql", "mysql", "postgresql", "postgres"],
    "machine learning": ["machine learning", "apprentissage automatique"],
    "deep learning": ["deep learning", "apprentissage profond"],
    "power bi": ["power bi"], "excel": ["excel", "microsoft excel"], "tableau": ["tableau"],
    "pandas": ["pandas"], "numpy": ["numpy"], "tensorflow": ["tensorflow"],
    "pytorch": ["pytorch"], "scikit-learn": ["scikit-learn", "sklearn"],
    "flask": ["flask"], "django": ["django"], "html": ["html"], "css": ["css"],
    "javascript": ["javascript", "js"], "typescript": ["typescript"], "react": ["react"],
    "git": ["git", "github", "gitlab"], "docker": ["docker"], "aws": ["aws", "amazon web services"],
    "azure": ["azure"], "c++": ["c++"], "c#": ["c#"], "r": ["r programming", "langage r"],
    "communication": ["communication"], "travail en équipe": ["travail en équipe", "esprit d'équipe"],
    "autonomie": ["autonomie", "autonome"], "gestion de projet": ["gestion de projet"],
}


def _norm(text):
    text = unicodedata.normalize("NFKD", str(text or "").casefold())
    return "".join(c for c in text if not unicodedata.combining(c))


def _find_skills(text):
    normalized = _norm(text)
    found = []
    for canonical, aliases in SKILLS.items():
        for alias in aliases:
            pattern = rf"(?<![\w+#]){re.escape(_norm(alias))}(?![\w+#])"
            if re.search(pattern, normalized):
                found.append(canonical)
                break
    return found


def _extract_pdf(uploaded_file):
    import io

    raw = uploaded_file.getvalue()
    for module_name in ("pypdf", "PyPDF2"):
        try:
            module = __import__(module_name)
            reader = module.PdfReader(io.BytesIO(raw))
            if getattr(reader, "is_encrypted", False):
                try:
                    reader.decrypt("")
                except Exception:
                    return "", "Ce PDF est protégé par un mot de passe."
            text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
            if not text:
                return "", "Aucun texte exploitable n’a été trouvé dans ce PDF (document peut-être scanné)."
            return text, None
        except ImportError:
            continue
        except Exception as exc:
            return "", f"Impossible de lire ce PDF : {exc}"
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages).strip()
        if text:
            return text, None
        return "", "Aucun texte exploitable n’a été trouvé dans ce PDF (document peut-être scanné)."
    except ImportError:
        return "", "Installez un extracteur PDF avec : py -m pip install pypdf."
    except Exception as exc:
        return "", f"Impossible de lire ce PDF : {exc}"


def _text_similarity(profile_text, offer_text):
    """Similarité cosinus TF-IDF si sklearn existe, sinon recouvrement de mots."""
    if not profile_text.strip() or not offer_text.strip():
        return 0.0
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        matrix = TfidfVectorizer(stop_words=None).fit_transform([profile_text, offer_text])
        return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
    except (ImportError, ValueError):
        words_a = set(re.findall(r"[a-zA-ZÀ-ÿ0-9+#]{3,}", _norm(profile_text)))
        words_b = set(re.findall(r"[a-zA-ZÀ-ÿ0-9+#]{3,}", _norm(offer_text)))
        return len(words_a & words_b) / max(1, len(words_a | words_b))


def page_matching_ia():
    st.title("🧠 Matching IA")
    st.caption("Découvrez les offres qui correspondent à votre profil, à partir de votre CV et des annonces disponibles dans IA JOB.")
    st.markdown("""
    <style>
    .matching-stat-card{box-sizing:border-box;min-height:108px;padding:16px 18px;border-radius:16px;box-shadow:0 8px 20px rgba(23,37,84,.10);display:flex;flex-direction:column;justify-content:center}
    .matching-stat-label{font-size:.86rem;font-weight:650;color:#334155}
    .matching-stat-value{font-size:1.9rem;font-weight:800;line-height:1.2;margin-top:8px;color:#172554}
    .matching-offer-card{box-sizing:border-box;margin:0 0 16px;padding:20px 22px;border-radius:18px;box-shadow:0 8px 22px rgba(23,37,84,.11);border:1px solid #dbe4f0;border-left:6px solid var(--match-accent);background:linear-gradient(135deg,var(--match-tint) 0%,#fff 78%);}
    .matching-offer-title{font-size:1.18rem;font-weight:800;color:#172554;margin:0 0 10px;line-height:1.4}
    .matching-offer-meta{color:#475569;font-size:.92rem;margin:0 0 10px;line-height:1.55}
    .matching-offer-badge{display:inline-block;margin:0 0 10px;padding:5px 10px;border-radius:999px;background:var(--match-badge);color:var(--match-accent);font-size:.82rem;font-weight:750}
    .matching-offer-description{color:#334155;line-height:1.6;margin:10px 0 14px;white-space:pre-wrap}
    .matching-offer-link{display:inline-block;padding:10px 16px;border-radius:10px;background:var(--match-accent);color:white!important;text-decoration:none!important;font-weight:700}
    .matching-offer-link:hover{filter:brightness(.94);text-decoration:none!important}
    </style>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.subheader("📄 Analysez votre profil")
        uploaded = st.file_uploader("Importer un CV au format PDF", type=["pdf"], key="matching_cv_upload")
        if uploaded:
            st.caption(f"Fichier sélectionné : {uploaded.name}")
        analyze = st.button("✨ Analyser mon CV", type="primary", disabled=uploaded is None, key="matching_analyze")

    if analyze and uploaded:
        text, error = _extract_pdf(uploaded)
        if error:
            st.error(error)
        else:
            st.session_state["matching_cv_text"] = text
            st.session_state["matching_cv_filename"] = uploaded.name
            detected = _find_skills(text)
            st.session_state["matching_detected_skills"] = detected
            st.session_state["matching_skills_edit"] = detected
            st.success("Le texte du CV a été extrait. Les compétences affichées sont celles réellement détectées.")

    cv_text = st.session_state.get("matching_cv_text", "")
    if not cv_text:
        st.info("Importez un CV PDF puis cliquez sur « Analyser mon CV » pour découvrir vos correspondances.")
        return

    st.caption(f"CV analysé : {st.session_state.get('matching_cv_filename', 'PDF')}")
    detected = st.session_state.get("matching_detected_skills", [])
    all_skills = sorted(SKILLS)
    selected = st.multiselect(
        "Compétences détectées — vous pouvez corriger ou compléter cette liste",
        all_skills,
        default=[skill for skill in detected if skill in all_skills],
        key="matching_skills_edit",
    )
    st.session_state["matching_detected_skills"] = selected

    lines = [line.strip() for line in cv_text.splitlines() if line.strip()]
    education = [line for line in lines if re.search(r"\b(bac|licence|master|doctorat|dipl[oô]me|universit[eé]|[eé]cole)\b", line, re.I)]
    experience = [line for line in lines if re.search(r"\b(stage|exp[eé]rience|emploi|analyste|d[eé]veloppeur|ing[eé]nieur|assistant)\b", line, re.I)]
    personal = [s for s in selected if s in {"communication", "travail en équipe", "autonomie", "gestion de projet"}]
    technical = [s for s in selected if s not in personal]

    st.subheader("👤 Mon profil détecté")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Compétences techniques**")
        st.write(", ".join(technical) if technical else "Aucune détectée ou ajoutée.")
    with c2:
        st.markdown("**Compétences personnelles**")
        st.write(", ".join(personal) if personal else "Aucune détectée ou ajoutée.")
    with c3:
        st.markdown("**Études et expériences repérées dans le CV**")
        st.write("\n".join((education[:3] + experience[:3])) or "Aucune mention reconnue dans le texte extrait.")

    if "offres_donnees_session" not in st.session_state:
        try:
            st.session_state["offres_donnees_session"] = load_or_create_jobs()
        except Exception as exc:
            st.error(f"Chargement des offres impossible : {exc}")
            return
    jobs = st.session_state["offres_donnees_session"]
    jobs = jobs.copy() if isinstance(jobs, pd.DataFrame) else pd.DataFrame(jobs)
    if jobs.empty:
        st.warning("Aucune offre réelle n’est actuellement disponible pour calculer les correspondances.")
        return

    for col in ("titre", "entreprise", "domaine", "type_offre", "ville", "description", "url", "source", "date_publication"):
        if col not in jobs.columns:
            jobs[col] = ""
        jobs[col] = jobs[col].fillna("").astype(str)

    matched = []
    profile_skills = set(selected)
    for _, job in jobs.iterrows():
        offer_text = " ".join(str(job.get(col, "")) for col in ("titre", "domaine", "description", "competences", "skills"))
        wanted = set(_find_skills(offer_text))
        overlap = profile_skills & wanted
        skill_score = len(overlap) / len(wanted) if wanted else 0.0
        similarity = _text_similarity(cv_text, offer_text)
        score = round(100 * (0.75 * skill_score + 0.25 * similarity))
        matched.append({**job.to_dict(), "score": score, "maitrisees": sorted(overlap), "manquantes": sorted(wanted - profile_skills), "_texte_offre": offer_text})
    results = pd.DataFrame(matched).sort_values("score", ascending=False).reset_index(drop=True)

    st.subheader("🎯 Votre compatibilité avec les offres")
    best_score = int(results.iloc[0]["score"]) if not results.empty else 0
    level = "Excellent match" if best_score >= 80 else "Bon match" if best_score >= 60 else "Match moyen" if best_score >= 40 else "Faible compatibilité"
    stat_cards = [
        ("🏆 Meilleure compatibilité", f"{best_score}%", "#dbeafe", "#bfdbfe", "#2563eb"),
        ("📋 Offres comparées", str(len(results)), "#ede9fe", "#ddd6fe", "#7c3aed"),
        ("🧠 Compétences renseignées", str(len(profile_skills)), "#cffafe", "#a5f3fc", "#0891b2"),
    ]
    for col, (label, value, tint, border, accent) in zip(st.columns(3), stat_cards):
        with col:
            st.markdown(
                f'<div class="matching-stat-card" style="background:linear-gradient(140deg,{tint},#fff 95%);border:1px solid {border};border-top:4px solid {accent};">'
                f'<div class="matching-stat-label">{label}</div><div class="matching-stat-value">{value}</div></div>',
                unsafe_allow_html=True,
            )
    st.caption("Méthode : 75 % de couverture des compétences détectées dans l’annonce + 25 % de similarité textuelle du CV et de l’offre. Si l’annonce ne mentionne aucune compétence reconnue, le score repose sur la similarité textuelle.")

    with st.expander("🎛️ Filtrer les recommandations", expanded=True):
        f1, f2, f3, f4 = st.columns(4)
        domains = sorted(x for x in results["domaine"].unique() if x.strip())
        types = sorted(x for x in results["type_offre"].unique() if x.strip())
        cities = sorted(x for x in results["ville"].unique() if x.strip())
        domain = f1.selectbox("Domaine", ["Tous"] + domains, key="matching_domain")
        offer_type = f2.selectbox("Type d’offre", ["Tous"] + types, key="matching_type")
        city = f3.selectbox("Localisation", ["Toutes"] + cities, key="matching_city")
        threshold = f4.selectbox("Compatibilité minimale", [0, 40, 60, 80], format_func=lambda n: f"{n}% et plus", key="matching_threshold")
    shown = results[results["score"] >= threshold].copy()
    if domain != "Tous":
        shown = shown[shown["domaine"] == domain]
    if offer_type != "Tous":
        shown = shown[shown["type_offre"] == offer_type]
    if city != "Toutes":
        shown = shown[shown["ville"] == city]

    st.subheader("🎯 Les meilleures opportunités pour vous")
    if shown.empty:
        st.info("Aucune offre réelle ne correspond à ces filtres.")
    for index, job in shown.iterrows():
        score = int(job["score"])
        badge = "🟢 Excellent match" if score >= 80 else "🔵 Bon match" if score >= 60 else "🟠 Match moyen" if score >= 40 else "🔴 À améliorer"
        tint, accent, badge_bg = ("#dcfce7", "#059669", "#ecfdf5") if score >= 80 else ("#dbeafe", "#2563eb", "#eff6ff") if score >= 60 else ("#fef3c7", "#d97706", "#fffbeb") if score >= 40 else ("#fee2e2", "#dc2626", "#fef2f2")
        title = escape(str(job["titre"] or "Poste non renseigné"))
        company = escape(str(job["entreprise"] or "Entreprise non renseignée"))
        city_name = escape(str(job["ville"] or "Lieu non renseigné"))
        offer_type_name = escape(str(job["type_offre"] or "Type non renseigné"))
        domain_name = escape(str(job["domaine"] or "Domaine non renseigné"))
        source_name = escape(str(job["source"] or "non renseignée"))
        date_name = escape(str(job["date_publication"] or "date inconnue"))
        description = escape(str(job["description"])[:600])
        mastered = escape(", ".join(job["maitrisees"]))
        missing = escape(", ".join(job["manquantes"]))
        card_html = (
            f'<div class="matching-offer-card" style="--match-tint:{tint};--match-accent:{accent};--match-badge:{badge_bg};">'
            f'<div class="matching-offer-title">🏢 {title} · {score}%</div>'
            f'<div class="matching-offer-meta"><strong>{company}</strong> · {city_name} · {offer_type_name}</div>'
            f'<div class="matching-offer-badge">{escape(badge)}</div>'
            f'<div class="matching-offer-meta">{domain_name} · Source : {source_name} · Publiée : {date_name}</div>'
        )
        if mastered:
            card_html += f'<div class="matching-offer-meta">✅ <strong>Compétences maîtrisées demandées :</strong> {mastered}</div>'
        if missing:
            card_html += f'<div class="matching-offer-meta">🟠 <strong>Compétences à développer :</strong> {missing}</div>'
        if description.strip():
            card_html += f'<div class="matching-offer-description">{description}</div>'
        url = str(job["url"]).strip()
        if url.startswith(("https://", "http://")):
            card_html += f'<a class="matching-offer-link" href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">🌐 Voir l’offre / postuler</a>'
        else:
            card_html += '<span class="matching-offer-meta">Lien original non disponible.</span>'
        card_html += '</div>'
        st.markdown(card_html, unsafe_allow_html=True)

    # Visualisations générées uniquement avec les offres réelles comparées.
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        with st.expander("📊 Analyse des correspondances", expanded=False):
            a, b = st.columns(2)
            bins = pd.cut(results["score"], bins=[-1, 39, 59, 79, 100], labels=["Faible", "Moyen", "Bon", "Excellent"])
            distribution = bins.value_counts().reindex(["Faible", "Moyen", "Bon", "Excellent"], fill_value=0).rename_axis("Compatibilité").reset_index(name="Offres")
            with a:
                fig = px.pie(distribution, names="Compatibilité", values="Offres", hole=.55, color="Compatibilité", color_discrete_map={"Faible": "#EF4444", "Moyen": "#F59E0B", "Bon": "#2563EB", "Excellent": "#10B981"})
                st.plotly_chart(fig, use_container_width=True, key="matching_distribution_chart")
            with b:
                fig = px.histogram(results, x="score", nbins=10, range_x=[0, 100], labels={"score": "Compatibilité (%)", "count": "Offres"}, color_discrete_sequence=["#7C3AED"])
                st.plotly_chart(fig, use_container_width=True, key="matching_score_histogram")

            requested = {}
            for skills in results["manquantes"].tolist() + results["maitrisees"].tolist():
                for skill in skills:
                    requested[skill] = requested.get(skill, 0) + 1
            if requested:
                top = pd.DataFrame(sorted(requested.items(), key=lambda item: item[1], reverse=True)[:10], columns=["Compétence", "Offres"])
                a, b = st.columns(2)
                with a:
                    fig = px.bar(top, x="Offres", y="Compétence", orientation="h", color="Offres", color_continuous_scale=["#93C5FD", "#7C3AED"], title="Compétences les plus demandées")
                    st.plotly_chart(fig, use_container_width=True, key="matching_skills_chart")
                with b:
                    radar_skills = top["Compétence"].head(8).tolist()
                    demand = [round(requested[s] * 100 / len(results)) for s in radar_skills]
                    candidate = [100 if s in profile_skills else 0 for s in radar_skills]
                    radar = go.Figure()
                    radar.add_trace(go.Scatterpolar(r=demand, theta=radar_skills, fill="toself", name="Demandes des offres"))
                    radar.add_trace(go.Scatterpolar(r=candidate, theta=radar_skills, fill="toself", name="Mon profil"))
                    radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), title="Profil et compétences demandées", height=380, margin=dict(t=55, b=25))
                    st.plotly_chart(radar, use_container_width=True, key="matching_radar_chart")

            a, b = st.columns(2)
            domain_counts = results["domaine"].replace("", "Domaine non renseigné").value_counts().rename_axis("Domaine").reset_index(name="Offres")
            if not domain_counts.empty:
                with a:
                    fig = px.pie(domain_counts, names="Domaine", values="Offres", hole=.55, title="Offres par domaine", color_discrete_sequence=["#2563EB", "#7C3AED", "#06B6D4", "#10B981", "#F59E0B"])
                    st.plotly_chart(fig, use_container_width=True, key="matching_domain_chart")
            with b:
                best = results.head(5).copy()
                best["Offre"] = best["titre"].replace("", "Poste non renseigné") + " · " + best["entreprise"].replace("", "Entreprise non renseignée")
                fig = px.bar(best.sort_values("score"), x="score", y="Offre", orientation="h", text="score", title="Top 5 des offres compatibles", labels={"score": "Compatibilité (%)"}, color="score", color_continuous_scale=["#F59E0B", "#2563EB", "#10B981"])
                fig.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True, key="matching_top_offers_chart")
            if not selected:
                st.info("Ajoutez les compétences réellement présentes dans votre CV pour rendre le radar plus personnalisé.")
    except ImportError:
        st.info("Installez Plotly pour afficher les graphiques : py -m pip install plotly")

    recommendations = sorted({skill for missing in shown["manquantes"] for skill in missing}) if not shown.empty else []
    st.subheader("💡 Conseils personnalisés")
    if recommendations:
        st.write("Les offres filtrées demandent notamment : " + ", ".join(recommendations[:8]) + ". Priorisez un mini-projet pratique et documentez-le dans votre CV.")
    elif selected:
        st.write("Vos compétences renseignées couvrent les compétences détectées dans les offres affichées. Continuez à adapter votre CV aux descriptions de poste.")
    else:
        st.write("Ajoutez les compétences présentes dans votre CV pour obtenir des conseils adaptés aux annonces réelles.")
