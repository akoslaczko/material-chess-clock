"""
Material Design style chess clock app using KivyMD
"""

import threading
import time
from datetime import timedelta
import re

from kivy.core.audio import SoundLoader
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.logger import Logger

from kivymd.app import MDApp
from kivymd.uix.behaviors import DeclarativeBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.button import (
    MDButton,
    MDButtonText,
    MDExtendedFabButton,
    MDExtendedFabButtonText,
    MDExtendedFabButtonIcon,
)
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogIcon,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogButtonContainer,
    MDDialogContentContainer,
)
from kivymd.uix.textfield import (
    MDTextField,
    MDTextFieldLeadingIcon,
    MDTextFieldHintText,
    MDTextFieldHelperText,
    MDTextFieldMaxLengthText,
)

# Window for testing
# Window.size = [330, 600]
Window.size = [1200, 600]

REFRESH_TIME = 0.1 # in seconds
DEFAULT_CLOCK_TIME = 0.2  # in minutes
DEFAULT_INCREMENT = 5  # in seconds


class MCCRootLayout(MDBoxLayout, DeclarativeBehavior):
    """
    The root widget of the app.
    Inherits from KivyMD's DeclarativeBehavior for coding the UI in Python declarative style
    """


class MCCClockLayout(MDBoxLayout):
    """
    The layout containing the widgets for the actual clock
    """
    running = False
    flagged = False
    button_click = SoundLoader.load('assets/clock-button-press.mp3')
    warning_sound = SoundLoader.load('assets/warning-sound.mp3')
    flagging_sound = SoundLoader.load('assets/flagging-sound.mp3')


class MCCClockButton(MDExtendedFabButton):
    """
    The widget of the main clock buttons
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setting existing visual attributes
        self.theme_width = "Custom"
        self.theme_height = "Custom"
        self.size_hint = (1, 1)
        self.pos_hint = {"center_x": .5, "center_y": .5}
        self.halign = "center"
        self.valign = "center"
        self.theme_elevation_level = "Custom"
        self.elevation_level = 5

    # New attributes
    time = timedelta(minutes=DEFAULT_CLOCK_TIME)
    increment = timedelta(seconds=DEFAULT_INCREMENT)


class MCCTimeText(MDExtendedFabButtonText):
    """
    Widget representing the remaining time of the players
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Visual attributes
        self.theme_font_size = "Custom"
        self.font_size = 80


class MCCApp(MDApp):
    """
    The main app of material-chess-clock (MCC)
    """
    def build(self):
        # Theming
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        # App root widget
        self.root = MCCRootLayout(
            MCCClockLayout(
                MCCClockButton(
                    disabled=True,
                    id="mcc_clock_button_white",
                ),
                MCCClockButton(
                    disabled=False,
                    id="mcc_clock_button_black",
                ),
                orientation="horizontal",
                padding="15dp",
                spacing="15dp",
                id="mcc_clock_layout",
            ),
            md_bg_color=self.theme_cls.inversePrimaryColor,
            orientation="vertical", #TODO: Do we need this?
            id="mcc_root_layout",
        )
        return self.root

    def on_stop(self):
        self.root.clock_layout.stop_clock()


if __name__ == '__main__':
    app = MCCApp()
    app.run()
