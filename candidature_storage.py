"""Persistance SQLite des comptes et candidatures IA JOB."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "marrakech_ai.db")


def _connect():
    connection = sqlite3.connect(DB_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_database():
    """Crée la base si nécessaire et complète les tables historiques."""
    with _connect() as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prenom VARCHAR(100) NOT NULL,
                nom VARCHAR(100) NOT NULL,
                email VARCHAR(150) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                profil_pro VARCHAR(100), ville VARCHAR(100),
                domaines_interet TEXT, cv_filename VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS candidatures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                entreprise_id INTEGER, offre_id INTEGER, message TEXT,
                statut VARCHAR(50), date_envoi DATETIME
            )"""
        )
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(candidatures)")
        }
        additions = {
            "nom_entreprise": "TEXT",
            "email_entreprise": "TEXT",
            "titre_poste": "TEXT",
            "date_candidature": "TEXT",
            "cv_nom": "TEXT",
            "lettre_motivation": "TEXT",
            "source_offre": "TEXT",
            "email_candidat": "TEXT",
            "nom_candidat": "TEXT",
            "telephone_candidat": "TEXT",
            "notes": "TEXT",
        }
        for column, sql_type in additions.items():
            if column not in columns:
                connection.execute(
                    f"ALTER TABLE candidatures ADD COLUMN {column} {sql_type}"
                )

        # Recopie les données des anciennes candidatures liées par entreprise_id.
        tables = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        if "entreprises" in tables and "offres_stages" in tables:
            connection.execute(
                """UPDATE candidatures
                   SET nom_entreprise = COALESCE(nom_entreprise, (SELECT nom FROM entreprises WHERE id = candidatures.entreprise_id)),
                       email_entreprise = COALESCE(email_entreprise, (SELECT email FROM entreprises WHERE id = candidatures.entreprise_id)),
                       titre_poste = COALESCE(titre_poste, (SELECT titre FROM offres_stages WHERE id = candidatures.offre_id)),
                       source_offre = COALESCE(source_offre, (SELECT source FROM offres_stages WHERE id = candidatures.offre_id)),
                       date_candidature = COALESCE(date_candidature, date_envoi),
                       lettre_motivation = COALESCE(lettre_motivation, message)
                   WHERE nom_entreprise IS NULL OR titre_poste IS NULL"""
            )
        elif "entreprises" in tables:
            connection.execute(
                """UPDATE candidatures
                   SET nom_entreprise = COALESCE(nom_entreprise, (SELECT nom FROM entreprises WHERE id = candidatures.entreprise_id)),
                       email_entreprise = COALESCE(email_entreprise, (SELECT email FROM entreprises WHERE id = candidatures.entreprise_id)),
                       date_candidature = COALESCE(date_candidature, date_envoi),
                       lettre_motivation = COALESCE(lettre_motivation, message)
                   WHERE nom_entreprise IS NULL"""
            )
        else:
            connection.execute(
                """UPDATE candidatures
                   SET date_candidature = COALESCE(date_candidature, date_envoi),
                       lettre_motivation = COALESCE(lettre_motivation, message)
                   WHERE date_candidature IS NULL OR lettre_motivation IS NULL"""
            )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS ix_candidatures_user ON candidatures(user_id)"
        )
        # L'index garantit l'unicité du couple utilisateur/entreprise/poste.
        try:
            connection.execute(
                """CREATE UNIQUE INDEX IF NOT EXISTS ux_candidatures_user_company_role
                   ON candidatures(user_id, lower(trim(nom_entreprise)), lower(trim(titre_poste)))
                   WHERE nom_entreprise IS NOT NULL AND titre_poste IS NOT NULL"""
            )
        except sqlite3.IntegrityError:
            # Des enregistrements historiques dupliqués n'empêchent pas leur lecture.
            pass
        try:
            connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email_normalized ON users(lower(trim(email)))"
            )
        except sqlite3.IntegrityError:
            # Le contrôle d'unicité des inscriptions reste fait par create_user.
            pass


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 310_000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> tuple[bool, str | None]:
    if stored_hash.startswith("pbkdf2_sha256$"):
        try:
            _, salt, expected = stored_hash.split("$", 2)
            actual = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), bytes.fromhex(salt), 310_000
            ).hex()
            return hmac.compare_digest(actual, expected), None
        except (ValueError, TypeError):
            return False, None
    # Compatibilité avec les comptes créés par l'ancienne page Profil (SHA-256).
    legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
    if hmac.compare_digest(legacy, stored_hash):
        return True, hash_password(password)
    return False, None


def create_user(profile: dict, password: str) -> int:
    init_database()
    with _connect() as connection:
        try:
            existing = connection.execute(
                "SELECT 1 FROM users WHERE lower(trim(email)) = ? LIMIT 1",
                (profile["email"].strip().casefold(),),
            ).fetchone()
            if existing:
                raise ValueError("Un compte existe déjà avec cette adresse e-mail. Connectez-vous.")
            cursor = connection.execute(
                """INSERT INTO users
                   (prenom, nom, email, password_hash, profil_pro, ville, domaines_interet, cv_filename)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    profile["prenom"].strip(), profile["nom"].strip(),
                    profile["email"].strip().casefold(), hash_password(password),
                    profile.get("profil_pro", ""), profile.get("ville", ""),
                    json.dumps(profile.get("domaines_interet", []), ensure_ascii=False),
                    profile.get("cv_filename"),
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("Un compte existe déjà avec cette adresse e-mail. Connectez-vous.") from exc
        return int(cursor.lastrowid)


def authenticate_user(email: str, password: str) -> dict | None:
    init_database()
    with _connect() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE lower(trim(email)) = ? LIMIT 1",
            (email.strip().casefold(),),
        ).fetchone()
        if row is None:
            return None
        valid, upgraded_hash = _verify_password(password, row["password_hash"] or "")
        if not valid:
            return None
        if upgraded_hash:
            connection.execute("UPDATE users SET password_hash = ? WHERE id = ?", (upgraded_hash, row["id"]))
        user = dict(row)
        user.pop("password_hash", None)
        try:
            user["domaines_interet"] = json.loads(user.get("domaines_interet") or "[]")
        except (TypeError, json.JSONDecodeError):
            user["domaines_interet"] = []
        user["is_logged_in"] = True
        return user


def has_duplicate(user_id: int, entreprise: str, poste: str) -> bool:
    init_database()
    with _connect() as connection:
        return connection.execute(
            """SELECT 1 FROM candidatures WHERE user_id = ?
               AND lower(trim(nom_entreprise)) = lower(trim(?))
               AND lower(trim(titre_poste)) = lower(trim(?)) LIMIT 1""",
            (int(user_id), entreprise.strip(), poste.strip()),
        ).fetchone() is not None


def save_candidature(user_id: int, candidature: dict) -> int:
    init_database()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    entreprise = str(candidature.get("nom_entreprise") or "").strip()
    poste = str(candidature.get("titre_poste") or "Non spécifié").strip()
    with _connect() as connection:
        try:
            cursor = connection.execute(
                """INSERT INTO candidatures
                   (user_id, message, statut, date_envoi, nom_entreprise,
                    email_entreprise, titre_poste, date_candidature, cv_nom,
                    lettre_motivation, source_offre, email_candidat,
                    nom_candidat, telephone_candidat, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    int(user_id), candidature.get("lettre_motivation", ""),
                    candidature.get("statut", "Postulé"), now, entreprise,
                    candidature.get("email_entreprise", ""), poste, now,
                    candidature.get("cv_nom", ""), candidature.get("lettre_motivation", ""),
                    candidature.get("source_offre", ""), candidature.get("email_candidat", ""),
                    candidature.get("nom_candidat", ""), candidature.get("telephone_candidat", ""),
                    candidature.get("notes", ""),
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("Cette candidature existe déjà dans votre suivi.") from exc
        return int(cursor.lastrowid)


def list_candidatures(user_id: int) -> list[dict]:
    init_database()
    with _connect() as connection:
        rows = connection.execute(
            """SELECT id, user_id, nom_entreprise, email_entreprise, titre_poste,
                      date_candidature, statut, cv_nom, lettre_motivation,
                      source_offre, email_candidat, nom_candidat,
                      telephone_candidat, message, notes
               FROM candidatures WHERE user_id = ? ORDER BY date_candidature DESC, id DESC""",
            (int(user_id),),
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item.update({
            "entreprise": item.get("nom_entreprise") or "",
            "poste": item.get("titre_poste") or "Non spécifié",
            "date": item.get("date_candidature") or "",
            "notes": item.get("notes") or "",
            "_suivi_id": str(item["id"]),
        })
        result.append(item)
    return result


def update_candidature(user_id: int, candidature_id: int, statut: str, notes: str) -> bool:
    init_database()
    with _connect() as connection:
        cursor = connection.execute(
            """UPDATE candidatures SET statut = ?, notes = ?
               WHERE id = ? AND user_id = ?""",
            (statut, notes, int(candidature_id), int(user_id)),
        )
        return cursor.rowcount == 1


def delete_candidature(user_id: int, candidature_id: int) -> bool:
    init_database()
    with _connect() as connection:
        cursor = connection.execute(
            "DELETE FROM candidatures WHERE id = ? AND user_id = ?",
            (int(candidature_id), int(user_id)),
        )
        return cursor.rowcount == 1


def delete_all_candidatures(user_id: int) -> int:
    init_database()
    with _connect() as connection:
        cursor = connection.execute("DELETE FROM candidatures WHERE user_id = ?", (int(user_id),))
        return cursor.rowcount
