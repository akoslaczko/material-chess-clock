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


class MCCTimeText(MDExtendedFabButtonText):
    """
    Widget representing the remaining time of the players
    """
    def __init__(self, *args, **kwargs):
        # New attributes
        self.time = timedelta(minutes=DEFAULT_CLOCK_TIME)
        self.increment = timedelta(seconds=DEFAULT_INCREMENT)
        super().__init__(*args, **kwargs)
        self.refresh_text()
        # Setting existing visual attributes
        self.theme_font_size = "Custom"
        self.font_size = 80

    def refresh_text(self):
        """
        Method for updating the 'text' attribute based on the 'time' attribute
        @property way currently doesn't work
        """
        # Split timedelta string
        time_list = re.split("[:.]", str(self.time))
        time_text = ""
        # Adding hours if necessary
        if int(time_list[0]) > 0:
            time_text += time_list[0] + ":"
        # Adding minutes and seconds
        time_text += time_list[1] + ":" + time_list[2]
        # Under 10 sec we increase the resolution
        if self.time < timedelta(seconds=10):
            time_text += "."
            if len(time_list) >= 4:
                time_text += time_list[3][0]
            else:
                time_text += "0"
        self.text = time_text
        if not self.disabled:
            # If the clock button is not disabled we also change the text color under 10 sec
            if self.time < timedelta(seconds=10):
                self.color = self.theme_cls.errorColor
            elif self.time >= timedelta(seconds=10):
                self.color = self.theme_cls.primaryColor


class MCCControlButtonsLayout(MDFloatLayout):
    """
    Control buttons layout
    """
    def adjust_width(self):
        """
        Dynamically adjust width based on max child widget size
        """
        child_widths = [child.width for child in self.children if hasattr(child, 'width')]
        max_child_width = max(child_widths) if len(child_widths) > 0 else 0
        self.width = max_child_width

class MCCApp(MDApp):
    """
    The main app of material-chess-clock (MCC)
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # State attributes
        self.running = False
        self.flagged = False
        # Threading
        self.thread = threading.Thread(target=self.refresh_time_text)
        # Sounds
        self.clock_button_click = SoundLoader.load('assets/clock-button-press.mp3')
        self.control_button_click = SoundLoader.load('assets/control-button-press.mp3')
        self.warning_sound = SoundLoader.load('assets/warning-sound.mp3')
        self.flagging_sound = SoundLoader.load('assets/flagging-sound.mp3')
        # Pointer attributes
        self.white_side = {}
        self.black_side = {}

    def build(self):
        # Theming
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        # The root widget for the app
        self.root = MCCRootLayout(
            MCCClockLayout(
                MCCClockButton(
                    MCCTimeText(
                        id='mcc_time_text_white',
                    ),
                    disabled=True,
                    on_press=self.on_press_clock_button,
                    id="mcc_clock_button_white",
                ),
                MCCControlButtonsLayout(
                    MDExtendedFabButton(
                        MDExtendedFabButtonIcon(
                            icon="play-pause"
                        ),
                        pos_hint={"center_x": .5, "center_y": .75},
                        theme_elevation_level="Custom",
                        elevation_level=3,
                        disabled=False,
                        on_press=self.on_press_playpause_button,
                        id="mcc_play_pause_button",
                    ),
                    MDExtendedFabButton(
                        MDExtendedFabButtonIcon(
                            icon="refresh"
                        ),
                        pos_hint={"center_x": .5, "center_y": .5},
                        theme_elevation_level="Custom",
                        elevation_level=3,
                        disabled=False,
                        on_press=self.on_press_reset_button,
                        id="mcc_reset_button",
                    ),
                    MDExtendedFabButton(
                        MDExtendedFabButtonIcon(
                            icon="cog"
                        ),
                        pos_hint={"center_x": .5, "center_y": .25},
                        theme_elevation_level="Custom",
                        elevation_level=3,
                        disabled=False,
                        on_press=self.on_press_setup_button,
                        id="mcc_setup_button",
                    ),
                    theme_width="Custom",
                    adaptive_width=True,
                    id="mcc_control_buttons_layout",
                ),
                MCCClockButton(
                    MCCTimeText(
                        id='mcc_time_text_black',
                    ),
                    disabled=False,
                    on_press=self.on_press_clock_button,
                    id="mcc_clock_button_black",
                ),
                orientation="horizontal",
                padding="15dp",
                spacing="15dp",
                id="mcc_clock_layout",
            ),
            md_bg_color=self.theme_cls.inversePrimaryColor,
            id="mcc_root_layout",
        )
        self.white_side = {
            'button': self.root.get_ids().mcc_clock_button_white,
            'time_text': self.root.get_ids().mcc_time_text_white,
            }
        self.black_side = {
            'button': self.root.get_ids().mcc_clock_button_black,
            'time_text': self.root.get_ids().mcc_time_text_black,
        }
        return self.root

    def refresh_time_text(self):
        """
        Refresh active player time
        """
        while self.running:
            refresh_start = time.time()
            for side in (self.white_side, self.black_side):
                if not side['button'].disabled:
                    side['time_text'].time -= timedelta(seconds=REFRESH_TIME)
                    side['time_text'].refresh_text()
                    Logger.info("MCCApp: time: %s", side['time_text'].text)
                    if side['time_text'].time == timedelta(seconds=10):
                        self.warning_sound.play()
                    if side['time_text'].time == timedelta(milliseconds=0):
                        self.stop_clock()
                        self.flagging_sound.play()
                        self.flagged = True
                        side['button'].disabled = True
            refresh_duration = time.time() - refresh_start
            time.sleep(REFRESH_TIME - refresh_duration if REFRESH_TIME > refresh_duration else 0)

    def start_clock(self):
        """
        Start clock
        """
        self.running = True
        self.thread = threading.Thread(target=self.refresh_time_text)
        self.thread.start()
        self.update_control_buttons_disabled_state()

    def stop_clock(self):
        """
        Stop clock
        """
        self.running = False
        self.thread.join()
        self.update_control_buttons_disabled_state()

    def reset_clock(self):
        """
        Reset clock
        """
        self.stop_clock()  # Should be already stopped, but just in case
        self.flagged = False
        self.white_side['button'].disabled = True
        self.black_side['button'].disabled = False
        self.white_side['time_text'].time = timedelta(minutes=DEFAULT_CLOCK_TIME)
        self.black_side['time_text'].time = timedelta(minutes=DEFAULT_CLOCK_TIME)

    def on_press_clock_button(self, *args):
        """
        On press method for clock buttons
        """
        if not self.flagged:
            self.clock_button_click.play()
            if not self.running:
                self.start_clock()
            if len(args) > 0 and isinstance(args[0], MCCClockButton):
                button = args[0]
                if button == self.white_side['button']:
                    self.white_side['button'].disabled = True
                    self.white_side['time_text'].time += self.white_side['time_text'].increment
                    self.white_side['time_text'].refresh_text()
                    self.black_side['button'].disabled = False
                elif button == self.black_side['button']:
                    self.black_side['button'].disabled = True
                    self.black_side['time_text'].time += self.white_side['time_text'].increment
                    self.black_side['time_text'].refresh_text()
                    self.white_side['button'].disabled = False
            Logger.info("ChessClockApp: Pressed clock button")

    def on_press_playpause_button(self, *args):
        """
        On press method for Play/Pause button
        """
        if not self.flagged:
            self.control_button_click.play()
            if self.running:
                self.stop_clock()
            elif not self.running:
                self.start_clock()
        Logger.info("ChessClockApp: Pressed playpause button")

    def on_press_reset_button(self, *args):
        """
        On press method for Reset button
        """
        self.control_button_click.play()
        Logger.info("ChessClockApp: Pressed reset button")

    def on_press_setup_button(self, *args):
        """
        On press method for Setup button
        """
        self.control_button_click.play()
        Logger.info("ChessClockApp: Pressed setup button")

    def update_control_buttons_disabled_state(self):
        """
        Update clock button's disabled state
        """
        if self.running:
            self.root.get_ids().mcc_reset_button.disabled = True
            self.root.get_ids().mcc_setup_button.disabled = True
        elif not self.running:
            self.root.get_ids().mcc_reset_button.disabled = False
            self.root.get_ids().mcc_setup_button.disabled = False

    def on_stop(self):
        self.stop_clock()


if __name__ == '__main__':
    app = MCCApp()
    app.run()
