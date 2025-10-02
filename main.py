# main.py
# Einstiegspunkt der Anwendung.
# Startet die Kivy-App, indem die GateApp-Klasse aus ui/app.py aufgerufen wird.

from ui.app import GateApp

if __name__ == "__main__":
    # GateApp ist die zentrale Kivy-App (siehe ui/app.py)
    GateApp().run()
