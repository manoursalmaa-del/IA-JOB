from datetime import date
from html import escape
import re

import pandas as pd
import streamlit as st
from candidature_storage import (
    delete_all_candidatures,
    delete_candidature,
    list_candidatures,
    update_candidature,
)

try:
    import plotly.express as px
except ImportError:
    px = None


STATUTS = ["Postulé", "En attente", "Entretien", "Accepté", "Refusé"]

COULEURS_STATUT = {
    "Postulé": "#2563EB",
    "En attente": "#F59E0B",
    "Entretien": "#7C3AED",
    "Accepté": "#10B981",
    "Refusé": "#EF4444",
}


def _normaliser_statut(statut):
    """Convertit les anciens libellés en statuts utilisés dans le tableau."""
    texte = str(statut or "").strip().casefold()

    if any(mot in texte for mot in ("entretien", "interview")):
        return "Entretien"
    if any(mot in texte for mot in ("accept", "recrut", "embauch", "offre")):
        return "Accepté"
    if any(mot in texte for mot in ("refus", "rejet")):
        return "Refusé"
    if "attente" in texte or "réponse" in texte or "reponse" in texte:
        return "En attente"
    if any(mot in texte for mot in ("postul", "envoy", "candidature")):
        return "Postulé"

    return "En attente"


def _date_candidature(valeur):
    """Renvoie une date exploitable, ou None si la valeur est invalide."""
    if not valeur:
        return None
    try:
        valeur_date = pd.to_datetime(valeur, errors="coerce")
        if pd.isna(valeur_date):
            return None
        return valeur_date.date()
    except (TypeError, ValueError):
        return None


def _email_candidat(candidature):
    email = str(candidature.get("email_candidat") or "").strip()
    if email:
        return email
    # Les anciens enregistrements peuvent contenir l’adresse uniquement dans les notes.
    notes = str(candidature.get("notes") or "")
    marqueur = re.search(r"candidat\s*:\s*(.*)", notes, flags=re.IGNORECASE)
    if not marqueur:
        return ""
    correspondance = re.search(
        r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
        marqueur.group(1),
        flags=re.IGNORECASE,
    )
    return correspondance.group(0) if correspondance else ""


def _reinitialiser_filtres():
    st.session_state["suivi_recherche"] = ""
    st.session_state["suivi_filtre_entreprise"] = "Toutes"
    st.session_state["suivi_filtre_statut"] = "Tous les statuts"
    st.session_state["suivi_filtre_type"] = "Tous"
    st.session_state["suivi_periode"] = st.session_state.get(
        "_suivi_periode_defaut", (date.today(), date.today())
    )


def _aller_aux_entreprises():
    st.session_state.page = "Entreprises"


def _enregistrer_modification(identifiant, cle_statut, cle_notes):
    profile = st.session_state.get("user_profile") or {}
    user_id = profile.get("id")
    if not user_id:
        st.session_state["_suivi_message"] = "Reconnectez-vous pour modifier votre suivi."
        return
    try:
        updated = update_candidature(
            user_id, int(identifiant),
            st.session_state.get(cle_statut, "En attente"),
            st.session_state.get(cle_notes, "").strip(),
        )
    except (TypeError, ValueError):
        updated = False
    if not updated:
        st.session_state["_suivi_message"] = "Cette candidature n’a pas pu être mise à jour."
        return
    for candidature in st.session_state.get("candidatures_list", []):
        if isinstance(candidature, dict) and candidature.get("_suivi_id") == identifiant:
            candidature["statut"] = st.session_state.get(cle_statut, "En attente")
            candidature["notes"] = st.session_state.get(cle_notes, "").strip()
            st.session_state["_suivi_message"] = "La candidature a été mise à jour."
            return


def _supprimer_candidature(identifiant):
    profile = st.session_state.get("user_profile") or {}
    user_id = profile.get("id")
    try:
        deleted = bool(user_id) and delete_candidature(user_id, int(identifiant))
    except (TypeError, ValueError):
        deleted = False
    st.session_state.candidatures_list[:] = [
        candidature
        for candidature in st.session_state.get("candidatures_list", [])
        if not isinstance(candidature, dict)
        or candidature.get("_suivi_id") != identifiant
    ]
    st.session_state["_suivi_message"] = (
        "La candidature a été supprimée." if deleted
        else "Cette candidature n’a pas pu être supprimée."
    )


def _demander_effacement_total():
    st.session_state.suivi_confirmer_effacement = True


def _effacer_tout_historique():
    profile = st.session_state.get("user_profile") or {}
    count = delete_all_candidatures(profile["id"]) if profile.get("id") else 0
    st.session_state.candidatures_list = []
    st.session_state.suivi_confirmer_effacement = False
    st.session_state["_suivi_message"] = f"{count} candidature(s) supprimée(s) de votre suivi permanent."


def _annuler_effacement_total():
    st.session_state.suivi_confirmer_effacement = False


def _afficher_entete(total):
    st.markdown(
        f"""
        <div class="suivi-header">
            <div class="suivi-header-icon">📊</div>
            <div class="suivi-header-copy">
                <div class="suivi-eyebrow">IA JOB · ESPACE CANDIDAT</div>
                <h1>Suivi de mes candidatures</h1>
                <p>Gérez et suivez toutes vos opportunités professionnelles au même endroit.</p>
            </div>
            <div class="suivi-total-badge">✉️ &nbsp; {total} candidature(s)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _afficher_statistiques(total, attente, entretiens, acceptees, refusees, entreprises):
    cartes = [
        ("Total des candidatures", total, "📨", "blue"),
        ("En attente", attente, "⏳", "orange"),
        ("Entretiens", entretiens, "🤝", "purple"),
        ("Acceptées", acceptees, "🎉", "green"),
        ("Refusées", refusees, "📭", "orange"),
        ("Entreprises contactées", entreprises, "🏢", "purple"),
    ]
    for debut in range(0, len(cartes), 3):
        colonnes = st.columns(3)
        for colonne, (titre, valeur, icone, couleur) in zip(colonnes, cartes[debut:debut + 3]):
            with colonne:
                st.markdown(
                    f"""
                    <div class="suivi-metric suivi-metric-{couleur}">
                        <div class="suivi-metric-top">
                            <span>{escape(titre)}</span>
                            <span class="suivi-metric-icon">{icone}</span>
                        </div>
                        <div class="suivi-metric-value">{valeur}</div>
                        <div class="suivi-metric-foot">Données de votre suivi permanent</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def _afficher_graphiques(candidatures):
    st.markdown(
        '<div class="suivi-section-title"><span>📈</span><div><h2>Vue analytique</h2>'
        '<p>Une lecture rapide de votre activité de candidature.</p></div></div>',
        unsafe_allow_html=True,
    )

    if px is None:
        st.warning("Les graphiques nécessitent Plotly. Installez-le avec : py -m pip install plotly")
        return

    colonnes = st.columns([1, 1.25])

    statuts = [_normaliser_statut(c.get("statut")) for c in candidatures]
    compte_statuts = (
        pd.Series(statuts, name="Statut")
        .value_counts()
        .rename_axis("Statut")
        .reset_index(name="Candidatures")
    )

    with colonnes[0]:
        with st.container(border=True):
            st.markdown("#### Répartition par statut")
            if not compte_statuts.empty:
                fig = px.pie(
                    compte_statuts,
                    names="Statut",
                    values="Candidatures",
                    color="Statut",
                    color_discrete_map=COULEURS_STATUT,
                    hole=0.68,
                )
                fig.update_traces(
                    textposition="inside",
                    textinfo="percent",
                    marker=dict(line=dict(color="#FFFFFF", width=3)),
                    hovertemplate="%{label}<br>%{value} candidature(s)<extra></extra>",
                )
                fig.update_layout(
                    height=310,
                    margin=dict(l=8, r=8, t=12, b=8),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h", yanchor="bottom", y=-0.12),
                    font=dict(color="#172554"),
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with colonnes[1]:
        with st.container(border=True):
            st.markdown("#### Candidatures par entreprise")
            par_entreprise = {}
            for candidature in candidatures:
                nom = str(candidature.get("entreprise") or "Entreprise non précisée").strip()
                par_entreprise[nom] = par_entreprise.get(nom, 0) + 1

            df_entreprises = (
                pd.DataFrame(
                    [{"Entreprise": nom, "Candidatures": nombre}
                     for nom, nombre in par_entreprise.items()]
                )
                .sort_values("Candidatures", ascending=True)
            )
            if not df_entreprises.empty:
                fig = px.bar(
                    df_entreprises,
                    x="Candidatures",
                    y="Entreprise",
                    orientation="h",
                    text="Candidatures",
                    color="Candidatures",
                    color_continuous_scale=["#93C5FD", "#2563EB", "#7C3AED"],
                )
                fig.update_traces(
                    textposition="outside",
                    hovertemplate="%{y}<br>%{x} candidature(s)<extra></extra>",
                )
                fig.update_layout(
                    height=max(310, min(540, 42 * len(df_entreprises) + 100)),
                    margin=dict(l=8, r=24, t=12, b=8),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    coloraxis_showscale=False,
                    xaxis_title=None,
                    yaxis_title=None,
                    font=dict(color="#172554"),
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    dates = [
        {"Date": _date_candidature(c.get("date"))}
        for c in candidatures
        if _date_candidature(c.get("date")) is not None
    ]
    with st.container(border=True):
        st.markdown("#### Évolution des candidatures dans le temps")
        if dates:
            df_dates = (
                pd.DataFrame(dates)
                .groupby("Date")
                .size()
                .reset_index(name="Candidatures")
                .sort_values("Date")
            )
            fig = px.line(
                df_dates,
                x="Date",
                y="Candidatures",
                markers=True,
                color_discrete_sequence=["#06B6D4"],
            )
            fig.update_traces(
                line=dict(width=3),
                fill="tozeroy",
                fillcolor="rgba(6,182,212,0.16)",
                hovertemplate="%{x|%d/%m/%Y}<br>%{y} candidature(s)<extra></extra>",
            )
            fig.update_layout(
                height=270,
                margin=dict(l=8, r=8, t=12, b=8),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title=None,
                yaxis_title=None,
                font=dict(color="#172554"),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.caption("Les candidatures enregistrées n’ont pas de date exploitable.")


def page_suivi_candidatures():
    st.markdown(
        """
        <style>
        .suivi-header {
            display: flex; align-items: center; gap: 20px; flex-wrap: wrap;
            padding: 28px 32px; margin: 4px 0 24px;
            color: #fff; border-radius: 24px;
            background: linear-gradient(120deg, #172554 0%, #2563EB 58%, #7C3AED 100%);
            box-shadow: 0 14px 34px rgba(37, 99, 235, .20);
            animation: suivi-enter .45s ease-out;
        }
        .suivi-header-icon {
            display: grid; place-items: center; flex: 0 0 60px; height: 60px;
            font-size: 30px; border-radius: 18px;
            background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.22);
        }
        .suivi-header-copy { flex: 1 1 350px; }
        .suivi-eyebrow { font-size: .72rem; font-weight: 800; letter-spacing: .13em; opacity: .75; }
        .suivi-header h1 { color: #fff; margin: 5px 0 3px; font-size: clamp(1.55rem, 3vw, 2.1rem); }
        .suivi-header p { color: rgba(255,255,255,.82); margin: 0; }
        .suivi-total-badge {
            padding: 10px 15px; border-radius: 999px; font-weight: 750;
            background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.25);
        }
        .suivi-metric {
            min-height: 148px; box-sizing: border-box; padding: 19px;
            border-radius: 20px; margin-bottom: 18px; color: #172554;
            border: 1px solid rgba(255,255,255,.8);
            box-shadow: 0 10px 24px rgba(23,37,84,.07);
            transition: transform .18s ease, box-shadow .18s ease;
            animation: suivi-enter .4s ease-out;
        }
        .suivi-metric:hover { transform: translateY(-3px); box-shadow: 0 14px 28px rgba(23,37,84,.12); }
        .suivi-metric-blue { background: linear-gradient(135deg,#EFF6FF,#DBEAFE); }
        .suivi-metric-orange { background: linear-gradient(135deg,#FFFBEB,#FEF3C7); }
        .suivi-metric-purple { background: linear-gradient(135deg,#F5F3FF,#EDE9FE); }
        .suivi-metric-green { background: linear-gradient(135deg,#ECFDF5,#D1FAE5); }
        .suivi-metric-top { display:flex; justify-content:space-between; align-items:center; font-weight:700; color:#334155; }
        .suivi-metric-icon { display:grid; place-items:center; width:38px; height:38px; border-radius:12px; background:rgba(255,255,255,.72); font-size:19px; }
        .suivi-metric-value { font-size:2.2rem; line-height:1.15; font-weight:850; margin-top:11px; color:#172554; }
        .suivi-metric-foot { margin-top:5px; font-size:.78rem; color:#64748B; }
        .suivi-section-title { display:flex; gap:12px; align-items:center; margin: 24px 0 12px; }
        .suivi-section-title > span { font-size:1.8rem; }
        .suivi-section-title h2 { margin:0; color:#172554; font-size:1.35rem; }
        .suivi-section-title p { margin:3px 0 0; color:#64748B; font-size:.9rem; }
        .suivi-app-head { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; flex-wrap:wrap; }
        .suivi-app-head h3 { margin:0; color:#172554; font-size:1.12rem; }
        .suivi-app-head p { margin:5px 0 0; color:#64748B; }
        .suivi-status {
            display:inline-block; padding:5px 11px; border-radius:999px;
            font-size:.78rem; font-weight:800; white-space:nowrap;
        }
        .suivi-empty {
            padding: 42px 24px; text-align:center; border-radius:24px;
            border:1px solid #E0E7FF; background:linear-gradient(135deg,#fff,#F5F7FF);
            box-shadow:0 12px 28px rgba(23,37,84,.06);
        }
        .suivi-empty-icon { font-size:3.2rem; margin-bottom:8px; }
        .suivi-empty h2 { color:#172554; margin:0 0 8px; }
        .suivi-empty p { color:#64748B; margin:0 0 14px; }
        @keyframes suivi-enter { from { opacity:0; transform:translateY(7px); } to { opacity:1; transform:translateY(0); } }
        @media (max-width: 700px) {
            .suivi-header { padding:22px 18px; border-radius:18px; gap:13px; }
            .suivi-header-copy { flex-basis:100%; }
            .suivi-total-badge { margin-left:0; }
            .suivi-metric { min-height:132px; padding:15px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    profile = st.session_state.get("user_profile") or {}
    user_id = profile.get("id")
    if not user_id:
        st.info("Connectez-vous à votre compte pour consulter votre suivi personnel.")
        if st.button("🔐 Aller à la connexion", key="suivi_go_profile"):
            st.session_state["page"] = "Profil"
            st.rerun()
        return

    try:
        candidatures = list_candidatures(user_id)
    except Exception as erreur:
        st.error(f"Impossible de charger votre suivi depuis SQLite : {erreur}")
        return
    # Miroir de session pour compatibilité ; la base SQLite reste la source de vérité.
    st.session_state["candidatures_list"] = candidatures

    _afficher_entete(len(candidatures))

    message = st.session_state.pop("_suivi_message", None)
    if message:
        st.success(message)

    statuts_normalises = [_normaliser_statut(c.get("statut")) for c in candidatures]
    total = len(candidatures)
    en_attente = sum(s in ("Postulé", "En attente") for s in statuts_normalises)
    entretiens = statuts_normalises.count("Entretien")
    acceptees = statuts_normalises.count("Accepté")
    refusees = statuts_normalises.count("Refusé")
    entreprises = len({str(c.get("entreprise") or "").strip().casefold() for c in candidatures if c.get("entreprise")})
    _afficher_statistiques(total, en_attente, entretiens, acceptees, refusees, entreprises)

    if not candidatures:
        st.markdown(
            """
            <div class="suivi-empty">
                <div class="suivi-empty-icon">🚀</div>
                <h2>Aucune candidature pour le moment</h2>
                <p>Commencez à postuler aux entreprises pour suivre votre progression ici.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            "🏢 Découvrir les entreprises",
            type="primary",
            on_click=_aller_aux_entreprises,
        )
        return

    _afficher_graphiques(candidatures)

    dates_valides = [
        d for d in (_date_candidature(c.get("date")) for c in candidatures)
        if d is not None
    ]
    periode_defaut = (
        min(dates_valides) if dates_valides else date.today(),
        max(dates_valides) if dates_valides else date.today(),
    )
    st.session_state["_suivi_periode_defaut"] = periode_defaut
    st.session_state.setdefault("suivi_recherche", "")
    st.session_state.setdefault("suivi_filtre_statut", "Tous les statuts")
    st.session_state.setdefault("suivi_periode", periode_defaut)

    st.markdown(
        '<div class="suivi-section-title"><span>🔎</span><div><h2>Mes candidatures</h2>'
        '<p>Recherchez, filtrez et mettez à jour chaque dossier.</p></div></div>',
        unsafe_allow_html=True,
    )

    col_recherche, col_entreprise, col_statut, col_type, col_dates, col_reset = st.columns([1.5, 1.1, 1, 1.1, 1.5, 0.8])
    with col_recherche:
        st.text_input(
            "Recherche",
            placeholder="Entreprise ou poste…",
            key="suivi_recherche",
        )
    with col_entreprise:
        entreprises_options = sorted({str(c.get("entreprise") or "").strip() for c in candidatures if str(c.get("entreprise") or "").strip()})
        entreprise_choisie = st.selectbox("Entreprise", ["Toutes"] + entreprises_options, key="suivi_filtre_entreprise")
    with col_statut:
        st.selectbox(
            "Statut",
            ["Tous les statuts"] + STATUTS,
            key="suivi_filtre_statut",
        )
    with col_type:
        types_options = sorted({str(c.get("poste") or "").strip() for c in candidatures if str(c.get("poste") or "").strip()})
        type_choisi = st.selectbox("Type / poste", ["Tous"] + types_options, key="suivi_filtre_type")
    with col_dates:
        st.date_input(
            "Période",
            key="suivi_periode",
            help="Choisissez une date de début et une date de fin.",
        )
    with col_reset:
        st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
        st.button(
            "Réinitialiser",
            key="suivi_reset_filtres",
            on_click=_reinitialiser_filtres,
            use_container_width=True,
        )

    recherche = st.session_state.get("suivi_recherche", "").strip().casefold()
    statut_choisi = st.session_state.get("suivi_filtre_statut", "Tous les statuts")
    periode = st.session_state.get("suivi_periode", periode_defaut)

    if isinstance(periode, (tuple, list)) and len(periode) == 2:
        date_debut, date_fin = periode
    elif isinstance(periode, date):
        date_debut = date_fin = periode
    else:
        date_debut, date_fin = periode_defaut

    filtres = []
    for candidature in candidatures:
        nom = str(candidature.get("entreprise") or "")
        poste = str(candidature.get("poste") or "")
        date_cand = _date_candidature(candidature.get("date"))
        statut = _normaliser_statut(candidature.get("statut"))

        correspond_recherche = not recherche or recherche in f"{nom} {poste}".casefold()
        correspond_entreprise = entreprise_choisie == "Toutes" or nom == entreprise_choisie
        correspond_type = type_choisi == "Tous" or poste == type_choisi
        correspond_statut = statut_choisi == "Tous les statuts" or statut == statut_choisi
        correspond_date = date_cand is not None and date_debut <= date_cand <= date_fin
        if correspond_recherche and correspond_entreprise and correspond_type and correspond_statut and correspond_date:
            filtres.append(candidature)

    st.caption(f"{len(filtres)} candidature(s) correspondent aux filtres.")

    if not filtres:
        st.info("Aucune candidature ne correspond à ces filtres.")
    else:
        for candidature in filtres:
            identifiant = candidature["_suivi_id"]
            entreprise = str(candidature.get("entreprise") or "Entreprise non précisée")
            poste = str(candidature.get("poste") or "Poste non précisé")
            statut = _normaliser_statut(candidature.get("statut"))
            couleur = COULEURS_STATUT[statut]
            date_cand = _date_candidature(candidature.get("date"))
            date_affichee = date_cand.strftime("%d/%m/%Y") if date_cand else "Date non renseignée"
            email = _email_candidat(candidature)
            email_entreprise = str(candidature.get("email_entreprise") or "").strip()
            cv_nom = str(candidature.get("cv_nom") or "").strip()
            source_offre = str(candidature.get("source_offre") or "").strip()
            notes = str(candidature.get("notes") or "")

            with st.container(border=True):
                st.markdown(
                    f"""
                    <div class="suivi-app-head">
                        <div>
                            <h3>{escape(entreprise)}</h3>
                            <p>{escape(poste)} &nbsp;·&nbsp; 📅 {escape(date_affichee)}</p>
                        </div>
                        <span class="suivi-status" style="color:{couleur}; background:{couleur}18; border:1px solid {couleur}44;">
                            {escape(statut)}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if email:
                    st.caption(f"✉️ E-mail du candidat : {email}")
                if email_entreprise:
                    st.caption(f"🏢 Destinataire : {email_entreprise}")
                if cv_nom:
                    st.caption(f"📎 CV transmis : {cv_nom}")
                if source_offre:
                    st.caption(f"🔗 Origine : {source_offre}")
                if notes:
                    st.caption(f"🗒️ Notes : {notes}")

                with st.form(key=f"form_suivi_{identifiant}"):
                    col_statut_edit, col_notes_edit = st.columns([1, 2])
                    with col_statut_edit:
                        nouveau_statut = st.selectbox(
                            "Modifier le statut",
                            STATUTS,
                            index=STATUTS.index(statut),
                            key=f"statut_edit_{identifiant}",
                        )
                    with col_notes_edit:
                        nouvelles_notes = st.text_area(
                            "Modifier les notes",
                            value=notes,
                            key=f"notes_edit_{identifiant}",
                            height=80,
                        )
                    st.form_submit_button(
                        "💾 Enregistrer les changements",
                        on_click=_enregistrer_modification,
                        args=(
                            identifiant,
                            f"statut_edit_{identifiant}",
                            f"notes_edit_{identifiant}",
                        ),
                    )

                col_delete, _ = st.columns([1, 5])
                with col_delete:
                    st.button(
                        "🗑️ Supprimer",
                        key=f"supprimer_{identifiant}",
                        type="secondary",
                        on_click=_supprimer_candidature,
                        args=(identifiant,),
                    )

    st.markdown("---")
    if not st.session_state.get("suivi_confirmer_effacement", False):
        st.button(
            "🗑️ Réinitialiser tout l’historique",
            type="secondary",
            on_click=_demander_effacement_total,
        )
    else:
        st.warning("Confirmez-vous la suppression de toutes les candidatures ?")
        col_confirmer, col_annuler = st.columns(2)
        with col_confirmer:
            st.button(
                "Oui, tout effacer",
                type="primary",
                on_click=_effacer_tout_historique,
            )
        with col_annuler:
            st.button("Annuler", on_click=_annuler_effacement_total)


if __name__ == "__main__":
    page_suivi_candidatures()
