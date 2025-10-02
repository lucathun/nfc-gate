from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, NoTransition

from ui.home_view import HomeView
from ui.gate_view import GateView
from nfc_reader import NFCReaderThread, get_reader_status

from db.database import init_db, import_from_csv, lookup_card, log_entry, last_entry

import threading
import os
from datetime import datetime, timedelta


def _norm_team(s: str) -> str:
    """Team-Namen vereinheitlichen: ohne Leerzeichen/Punkte, Kleinschreibung."""
    if not s:
        return ""
    return s.replace(" ", "").replace(".", "").strip().lower()


class GateApp(App):
    def build(self):
        """Initialisiert App, DB, Screens und NFC-Thread."""
        self.stop_event = threading.Event()     # Steuerung für NFC-Thread
        self.reader_thread = None               # NFC-Lesegerät läuft im Hintergrund
        self.current_team = None                # Aktuell ausgewähltes Team

        # Datenbank initialisieren
        self.conn = init_db()

        # Karten aus CSV-Datei importieren (falls vorhanden)
        base_dir = os.path.dirname(os.path.dirname(__file__))  # eine Ebene über /ui/
        csv_path = os.path.join(base_dir, "cards.csv")
        if os.path.exists(csv_path):
            import_from_csv(self.conn, csv_path)

        # ScreenManager ohne Transition (direkter Wechsel)
        self.sm = ScreenManager(transition=NoTransition())

        # Screens hinzufügen
        self.home = HomeView(switch_to_gate=self.switch_to_gate)
        self.gate = GateView(switch_to_home=self.switch_to_home)
        self.sm.add_widget(self.home)
        self.sm.add_widget(self.gate)

        # Lesegerätstatus beim Start prüfen und auf Home anzeigen
        self.last_status = get_reader_status()
        self.home.update_status(self.last_status)

        return self.sm

    def switch_to_gate(self, team):
        """Wechselt von Home zu Gate und startet ggf. den NFC-Lesegerät-Thread."""
        self.current_team = team
        self.sm.current = "gate"

        if not self.reader_thread:
            self.stop_event.clear()
            self.reader_thread = NFCReaderThread(
                uid_callback=self.on_uid,       # Callback bei neuer Karte
                error_callback=self.on_error,   # Callback bei Fehler
                stop_event=self.stop_event
            )
            self.reader_thread.start()

    def switch_to_home(self):
        """Wechselt von Gate zurück zu Home und zeigt aktuellen Status an."""
        self.sm.current = "home"
        self.home.update_status(self.last_status)

    def on_uid(self, uid_hex):
        """
        Callback wenn eine Karte gelesen wurde.
        Prüft Berechtigungen, Zeitfenster (gültig, schon verwendet),
        zeigt Ergebnis in der UI und loggt den Versuch in DB.
        """
        card = lookup_card(self.conn, uid_hex)

        # --- Unbekannte Karte ---
        if card is None:
            msg = (
                "Zutritt verweigert\n"
                f"Unbekannte Karte ({uid_hex})\nGrund: Karte nicht registriert"
            )
            self.gate.show_result(msg, color="red")
            log_entry(self.conn, uid_hex, False, "Karte nicht registriert")
            return

        reasons = []

        # --- Datumsprüfung ---
        now = datetime.now().date()
        if card["valid_from"]:
            try:
                vf = datetime.fromisoformat(card["valid_from"]).date()
                if now < vf:
                    reasons.append(f"Karte noch nicht gültig (ab {card['valid_from']})")
            except Exception:
                reasons.append("Ungültiges Startdatum")

        if card["valid_until"]:
            try:
                vu = datetime.fromisoformat(card["valid_until"]).date()
                if now > vu:
                    reasons.append(f"Karte abgelaufen (gültig bis {card['valid_until']})")
            except Exception:
                reasons.append("Ungültiges Enddatum")

        # --- Teamprüfung ---
        current_team_norm = _norm_team(self.current_team)
        teams_norm = [_norm_team(t) for t in card["teams"]]
        if "*" not in teams_norm and current_team_norm not in teams_norm:
            reasons.append(f"Keine Berechtigung für {self.current_team}")

        # Zusatzinfos aus DB
        card_type = card.get("card_type") or "-"
        notes = f"\nHinweis: {card['notes']}" if card["notes"] else ""

        # --- Wenn Gründe gefunden -> Zutritt verweigert ---
        if reasons:
            details = f"{card['name']} ({card_type})\n" + "\n".join(reasons) + notes
            self.gate.show_result("Zutritt verweigert\n" + details, color="red")
            log_entry(self.conn, uid_hex, False, "; ".join(reasons))
            return

        # --- Karte ist gültig: Doppel-Scan-Prüfung ---
        last = last_entry(self.conn, uid_hex)
        if last and last["timestamp"]:
            delta = datetime.now() - last["timestamp"]
            if delta < timedelta(minutes=1) and last["allowed"]:
                # Innerhalb 1 Minute -> Schutzfrist -> erneut erlauben
                until = card["valid_until"] or "unbegrenzt"
                details = f"{card['name']} ({card_type})\nGültig bis: {until}" + notes
                self.gate.show_result("Zutritt erlaubt\n" + details, color="green")
                log_entry(self.conn, uid_hex, True, "Schutzfrist erneuter Scan")
                return
            elif delta < timedelta(hours=1) and last["allowed"]:
                # Innerhalb 1 Stunde -> verweigern
                minutes = delta.seconds // 60
                details = (
                    f"{card['name']} ({card_type})\n"
                    f"Karte wurde schon vor {minutes} Minuten verwendet" + notes
                )
                self.gate.show_result("Zutritt verweigert\n" + details, color="red")
                log_entry(self.conn, uid_hex, False, f"Schon vor {minutes} Minuten verwendet")
                return

        # --- Standardfall: Zutritt erlaubt ---
        until = card["valid_until"] or "unbegrenzt"
        details = f"{card['name']} ({card_type})\nGültig bis: {until}" + notes
        self.gate.show_result("Zutritt erlaubt\n" + details, color="green")
        log_entry(self.conn, uid_hex, True, "OK")

    def on_error(self, msg):
        """Callback bei NFC-Lesegerät-Fehlern: zeigt Status auf Home an."""
        self.last_status = msg
        self.home.update_status(msg)

    def on_stop(self):
        """Wird beim Beenden aufgerufen: NFC-Thread stoppen, DB schließen."""
        self.stop_event.set()
        self.conn.close()
        return super().on_stop()
