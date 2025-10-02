# NFC Gate – Karten-Scanner für Fußballverein

Dieses Projekt ist eine Python/Kivy-Anwendung zur Zutrittskontrolle mit NFC-Karten.
Es läuft auf einem **Raspberry Pi** mit angeschlossenem **ACR122U NFC-Lesegerät** und einem **Touchdisplay**.

## Funktionsweise

- Zuschauer halten ihre NFC-Karte an das Lesegerät.
- Die App prüft:

  - Ob die Karte registriert ist.
  - Ob sie im gültigen Zeitraum liegt.
  - Ob sie für das gewählte Team freigeschaltet ist.
  - Ob sie in der letzten Stunde schon benutzt wurde (inkl. 1-Minuten-Schutzfrist).

- Ergebnis wird groß und farbig auf dem Touchdisplay angezeigt:

  - ✅ **Zutritt erlaubt** (mit Name, Kartentyp, Ablaufdatum, ggf. Notizen).
  - ❌ **Zutritt verweigert** (mit detaillierten Gründen).

- Alle Versuche werden in einer SQLite-Datenbank geloggt.

## Voraussetzungen

- Python 3.10+ (getestet mit 3.13 auf Windows, später für Raspberry Pi gedacht)
- [Kivy](https://kivy.org/)
- [pyscard](https://pyscard.sourceforge.io/) für den Zugriff auf das NFC-Lesegerät
- ACR122U NFC-Lesegerät + libusb-Treiber
- SQLite (bereits in Python enthalten)

## Installation

1. Repository/Projektordner vorbereiten und virtuelle Umgebung erstellen:

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows
```

2. Abhängigkeiten installieren:

```bash
pip install kivy smartcard
```

3. Optional: Kivy-Abhängigkeiten für Windows nachinstallieren (falls nötig):

```bash
pip install kivy_deps.sdl2 kivy_deps.glew kivy_deps.angle
```

## Raspberry Pi Setup

Für Raspberry Pi OS müssen zusätzlich Systempakete installiert werden:

```bash
chmod +x setup_pi.sh
./setup_pi.sh
```

## Datenbank und Kartenverwaltung

- Karten werden in `cards.csv` gepflegt (im Projekt-Hauptordner).
- Beim Start importiert die App die CSV in eine SQLite-Datenbank (`db/cards.db`).
- CSV-Format (Semikolon-getrennt):

```csv
uid;name;card_type;valid_from;valid_until;teams;notes
3B8D5603;Max Mustermann;Dauerkarte;2025-01-01;2026-01-01;"*";TestKarte
650A5703;Erika Musterfrau;Partnerkarte;2024-08-01;2024-12-31;"1.Herren";TestKarte
```

- `*` bei `teams` bedeutet, die Karte gilt für **alle Teams**.
- Mehrere Teams können per Komma getrennt angegeben werden, z. B. `"1.Herren,2.Herren"`.

## Start der Anwendung

```bash
python main.py
```

## Bedienung

1. Auf der Startseite:

   - Team auswählen (Button wechselt zwischen „1. Herren“, „2. Herren“, „Damen“).
   - „Start“-Button drücken.
   - Status des NFC-Lesegeräts wird angezeigt.

2. Im Gate-Modus:

   - Karte vorhalten.
   - Ergebnis (erlaubt/verweigert) wird angezeigt.
   - „Zurück“-Button bringt wieder zur Startseite.

## Logs & Auswertung

- Alle Eintrittsversuche werden in `entries` in der SQLite-DB gespeichert:

  - `uid`, `timestamp`, `allowed` (1/0), `reason`

- Damit sind spätere Auswertungen möglich (z. B. Nutzungshäufigkeit, Statistiken).

---

## ToDo / Ideen

- Erweiterte Auswertungen (CSV-Export der Logs).
- Admin-Oberfläche direkt im UI zum Karten-Management.
- Automatischer CSV-Import beim Start optional deaktivierbar.
- Unit Tests für DB-Funktionen.

---

## Lizenz

Projekt für Vereinsnutzung entwickelt. Kein offizielles Produkt.
Verwendung auf eigene Gefahr ⚽️
