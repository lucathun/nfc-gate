import sqlite3
import os
import csv
from datetime import datetime

# Pfad zur SQLite-Datenbank (liegt im selben Ordner wie diese Datei)
DB_PATH = os.path.join(os.path.dirname(__file__), "cards.db")


def init_db():
    """
    Erstellt (falls nicht vorhanden):
      - Tabelle cards: enthält alle NFC-Karten
      - Tabelle entries: Log für alle Zutrittsversuche
    Gibt eine aktive DB-Verbindung zurück.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Haupttabelle für Karten
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY,
            uid TEXT UNIQUE,        -- Karten-ID (UID vom NFC-Chip)
            name TEXT,              -- Name des Besitzers
            card_type TEXT,         -- Kartentyp (z.B. Dauerkarte, Partnerkarte)
            valid_from TEXT,        -- Startdatum (ISO-Format)
            valid_until TEXT,       -- Enddatum (ISO-Format)
            teams TEXT,             -- Liste von Teams (Komma-separiert)
            notes TEXT              -- Freitext-Notizen
        )
        """
    )
    # Logtabelle für Eintrittsversuche
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY,
            uid TEXT,               -- Karten-ID
            timestamp TEXT,         -- Zeitpunkt des Scans (ISO-Format)
            allowed INTEGER,        -- 1 = Zutritt, 0 = verweigert
            reason TEXT             -- Grund / Zusatzinfo
        )
        """
    )
    conn.commit()
    return conn


def import_from_csv(conn, csv_path):
    """
    Liest Karten aus einer CSV-Datei (Semicolon-getrennt) und schreibt sie in die DB.
    Bei doppelten UIDs werden die Daten aktualisiert (Upsert).
    """
    cur = conn.cursor()
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            try:
                cur.execute("""
                    INSERT INTO cards(uid, name, card_type, valid_from, valid_until, teams, notes)
                    VALUES(?,?,?,?,?,?,?)
                    ON CONFLICT(uid) DO UPDATE SET
                        name=excluded.name,
                        card_type=excluded.card_type,
                        valid_from=excluded.valid_from,
                        valid_until=excluded.valid_until,
                        teams=excluded.teams,
                        notes=excluded.notes
                """, (
                    row["uid"].strip().upper(),
                    row["name"],
                    row["card_type"],
                    row["valid_from"] or None,
                    row["valid_until"] or None,
                    row["teams"],
                    row["notes"]
                ))
            except Exception as e:
                print(f"Fehler bei UID {row['uid']}: {e}")
    conn.commit()


def lookup_card(conn, uid_hex):
    """
    Sucht eine Karte anhand ihrer UID.
    Gibt ein Dict mit allen Feldern zurück oder None, wenn Karte unbekannt.
    """
    cur = conn.cursor()
    cur.execute(
        "SELECT uid, name, card_type, valid_from, valid_until, teams, notes FROM cards WHERE uid=?",
        (uid_hex,),
    )
    row = cur.fetchone()
    if row:
        return {
            "uid": row[0],
            "name": row[1],
            "card_type": row[2],
            "valid_from": row[3],
            "valid_until": row[4],
            "teams": row[5].split(",") if row[5] else [],
            "notes": row[6],
        }
    return None


def is_valid_date_range(valid_from, valid_until):
    """
    Prüft, ob eine Karte aktuell gültig ist.
    - Noch nicht gültig -> False
    - Abgelaufen -> False
    - Sonst -> True
    """
    now = datetime.now().date()
    try:
        if valid_from:
            vf = datetime.fromisoformat(valid_from).date()
            if now < vf:
                return False
        if valid_until:
            vu = datetime.fromisoformat(valid_until).date()
            if now > vu:
                return False
        return True
    except Exception:
        return False


# --- Logging-Funktionen --- #

def log_entry(conn, uid, allowed, reason=""):
    """
    Fügt einen Eintrag in die Tabelle entries ein.
    - uid: Karten-ID
    - allowed: True/False (1/0)
    - reason: Grund für die Entscheidung (z.B. "OK", "abgelaufen")
    """
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO entries(uid, timestamp, allowed, reason)
        VALUES(?,?,?,?)
        """,
        (uid, datetime.now().isoformat(), 1 if allowed else 0, reason),
    )
    conn.commit()


def last_entry(conn, uid):
    """
    Gibt den letzten Eintrag einer Karte zurück.
    Rückgabe-Dict:
      { "timestamp": datetime|None, "allowed": bool, "reason": str }
    oder None, wenn kein Eintrag vorhanden ist.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT timestamp, allowed, reason
        FROM entries
        WHERE uid=?
        ORDER BY timestamp DESC
        LIMIT 1
        """,
        (uid,),
    )
    row = cur.fetchone()
    if row:
        try:
            ts = datetime.fromisoformat(row[0])
        except Exception:
            ts = None
        return {
            "timestamp": ts,
            "allowed": bool(row[1]),
            "reason": row[2]
        }
    return None
