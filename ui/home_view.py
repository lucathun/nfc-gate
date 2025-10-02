from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen

# Verfügbare Teams, zwischen denen der Kassierer wechseln kann
TEAMS = ["1. Herren", "2. Herren", "Damen"]


class HomeView(Screen):
    def __init__(self, switch_to_gate, **kwargs):
        """
        Startbildschirm der App.
        - Auswahl des Teams
        - Start-Button für Zutrittskontrolle
        - Anzeige, ob ein NFC-Lesegerät erkannt wurde

        switch_to_gate(team): Callback, wird aufgerufen wenn "Start" gedrückt wird.
        """
        super().__init__(**kwargs)
        self.name = "home"
        self.team_idx = 0                  # Index für aktuelles Team
        self.switch_to_gate = switch_to_gate

        # Layout: vertikal mit Abstand
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        # Titel der App
        self.title_lbl = Label(
            text="Karten-Scanner",
            font_size='36sp',
            size_hint=(1, 0.2)
        )
        # Button zur Team-Auswahl (wechselt bei Klick)
        self.team_btn = Button(
            text=TEAMS[self.team_idx],
            font_size='32sp',
            size_hint=(1, 0.25)
        )
        # Button zum Starten des Scan-Bildschirms
        self.start_btn = Button(
            text="Start",
            font_size='48sp',
            size_hint=(1, 0.35)
        )
        # Statusanzeige: NFC-Lesegerät (erkannt/nicht erkannt)
        self.status_lbl = Label(
            text="Lesegerät: unbekannt",
            font_size='20sp',
            size_hint=(1, 0.2)
        )

        # Button-Events verbinden
        self.team_btn.bind(on_release=self.next_team)
        self.start_btn.bind(on_release=self.on_start)

        # Widgets zum Layout hinzufügen
        layout.add_widget(self.title_lbl)
        layout.add_widget(self.team_btn)
        layout.add_widget(self.start_btn)
        layout.add_widget(self.status_lbl)

        self.add_widget(layout)

    def next_team(self, *_):
        """Wechselt zum nächsten Team in der Liste."""
        self.team_idx = (self.team_idx + 1) % len(TEAMS)
        self.team_btn.text = TEAMS[self.team_idx]

    def on_start(self, *_):
        """Ruft Callback auf, um GateView für das gewählte Team zu öffnen."""
        team = TEAMS[self.team_idx]
        self.switch_to_gate(team)

    def update_status(self, msg):
        """Aktualisiert den Text des Lesegerätstatus (z.B. 'Lesegerät erkannt')."""
        self.status_lbl.text = msg
