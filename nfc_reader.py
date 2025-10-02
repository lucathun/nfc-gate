import threading
import time
from smartcard.System import readers
from smartcard.Exceptions import NoCardException
from kivy.clock import Clock

# APDU-Befehl für ACR122U: liefert die UID der aufgelegten Karte
GET_UID_APDU = [0xFF, 0xCA, 0x00, 0x00, 0x00]


def uid_to_hex(data):
    """Wandelt eine Liste von Bytes in einen Hex-String um."""
    return ''.join('{:02X}'.format(x) for x in data)


def get_reader_status():
    """
    Prüft einmalig, ob ein NFC-Lesegerät verfügbar ist.
    Rückgabe: Text für die Anzeige in der UI.
    """
    try:
        r = readers()
        if not r:
            return "Achtung: Kein NFC-Lesegerät gefunden"
        return f"Lesegerät bereit: {r[0]}"
    except Exception as e:
        return f"Fehler beim Initialisieren: {e}"


class NFCReaderThread(threading.Thread):
    """
    Hintergrund-Thread, der kontinuierlich den NFC-Lesegerät abfragt.
    - Liest UIDs von aufgelegten Karten
    - Ruft Kivy-Callbacks (uid_callback, error_callback) thread-sicher auf
    """

    def __init__(self, uid_callback, error_callback, stop_event):
        """
        Parameter:
        - uid_callback(uid_hex): wird aufgerufen, wenn eine Karte erkannt wird
        - error_callback(msg):   wird aufgerufen bei Fehlern oder fehlendem Lesegerät
        - stop_event:            threading.Event, um den Thread sauber zu stoppen
        """
        super().__init__(daemon=True)
        self.uid_callback = uid_callback
        self.error_callback = error_callback
        self.stop_event = stop_event

    def run(self):
        """Hauptschleife: Karten einlesen, bis stop_event gesetzt wird."""
        try:
            # Verfügbare Lesegeräte prüfen
            r = readers()
            if not r:
                Clock.schedule_once(
                    lambda dt: self.error_callback("Kein NFC-Lesegerät gefunden")
                )
                return

            reader = r[0]  # erstes gefundenes Lesegerät verwenden
            Clock.schedule_once(
                lambda dt: self.error_callback(f"Verwendes Lesegerät: {reader}")
            )
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self.error_callback(f"Fehler beim Initialisieren: {e}")
            )
            return

        # Endlosschleife: wiederholt nach Karten suchen
        while not self.stop_event.is_set():
            try:
                # Verbindung zum Lesegerät herstellen
                conn = reader.createConnection()
                conn.connect()

                # UID auslesen
                data, sw1, sw2 = conn.transmit(GET_UID_APDU)
                if sw1 == 0x90:  # Status 0x90 = OK
                    uid = uid_to_hex(data)
                    if uid:
                        # UID-Callback thread-sicher in Kivy-Loop posten
                        Clock.schedule_once(lambda dt: self.uid_callback(uid))
                        # kurze Pause, um versehentliches Doppelscannen zu vermeiden
                        time.sleep(1.5)

                conn.disconnect()

            except NoCardException:
                # keine Karte aufgelegt -> kleine Pause, dann weiter
                time.sleep(0.2)

            except Exception as e:
                # Fehler beim Lesen -> Meldung an UI + kurze Pause
                Clock.schedule_once(
                    lambda dt: self.error_callback(f"Lesefehler: {e}")
                )
                time.sleep(1.0)
