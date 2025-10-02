from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen


class GateView(Screen):
    def __init__(self, switch_to_home, **kwargs):
        super().__init__(**kwargs)
        self.name = "gate"
        self.switch_to_home = switch_to_home

        layout = BoxLayout(orientation="vertical", padding=20, spacing=20)

        # Status-Label (groß, farbig)
        self.status_lbl = Label(
            text="Warte auf Karte...",
            font_size="36sp",
            halign="center",
            valign="middle",
            size_hint=(1, 0.3),
        )
        self.status_lbl.bind(size=self._update_text_width)

        # Detail-Label (Name, Typ, Gründe, Notizen)
        self.detail_lbl = Label(
            text="",
            font_size="22sp",
            halign="center",
            valign="top",
            size_hint=(1, 0.5),
        )
        self.detail_lbl.bind(size=self._update_text_width)

        # Zurück-Button
        self.back_btn = Button(text="Zurück", font_size="24sp", size_hint=(1, 0.2))
        self.back_btn.bind(on_release=lambda *_: self.switch_to_home())

        layout.add_widget(self.status_lbl)
        layout.add_widget(self.detail_lbl)
        layout.add_widget(self.back_btn)

        self.add_widget(layout)

    def _update_text_width(self, instance, size):
        """Sorgt für automatischen Zeilenumbruch."""
        instance.text_size = (instance.width - 20, None)

    def show_result(self, msg, color="white"):
        """
        Erwartetes Format: erste Zeile = Status (Zutritt erlaubt/verweigert),
        Rest = Details.
        """
        lines = msg.split("\n", 1)
        status = lines[0]
        details = lines[1] if len(lines) > 1 else ""

        if color == "red":
            self.status_lbl.color = (1, 0, 0, 1)
        elif color == "green":
            self.status_lbl.color = (0, 1, 0, 1)
        else:
            self.status_lbl.color = (1, 1, 1, 1)

        self.status_lbl.text = status
        self.detail_lbl.text = details
