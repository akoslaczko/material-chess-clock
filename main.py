"""
Material Design style chess clock app using KivyMD
"""

# pylint: disable=E0611 # Disable the error related to importing from pxd files (temporary solution)

import threading
import time
from datetime import timedelta

from kivy.core.audio import SoundLoader
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.properties import (
    ObjectProperty,
    OptionProperty,
)

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

import helpers


# Window for testing
# Window.size = [1200, 600]

# ---------------------------------------------------------------------------- #
#                               Default variables                              #
# ---------------------------------------------------------------------------- #

REFRESH_TIME = 0.1 # in seconds
DEFAULT_CLOCK_TIME = 0.2  # in minutes
DEFAULT_INCREMENT = 5  # in seconds

# ---------------------------------------------------------------------------- #
#                                Custom classes                                #
# ---------------------------------------------------------------------------- #


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
        # Setting existing visual attributes"
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
    # Define a new property for clock time.
    # Necessary for automatically updating the related 'text' and 'color' attributes
    time = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setting existing visual attributes
        self.theme_font_size = "Custom"
        self.font_size = 80
        self.size_hint = (1, 1) # Fixes bug related to buttons being clickable while disabled
        # Setup clock time related attributes
        self.bind(time=self.on_change_time)
        self.time = timedelta(minutes=DEFAULT_CLOCK_TIME)
        self.increment = timedelta(seconds=DEFAULT_INCREMENT)

    def on_change_time(self, *args):
        """
        Bound method for updating the 'text' and 'color' attributes based on the 'time' attribute
        """
        self.text = helpers.convert_timedelta_to_clock_time_string(self.time)
        if not self.disabled:
            # If the clock button is not disabled we also change the text color under 10 sec
            if self.time < timedelta(seconds=10):
                self.color = self.theme_cls.errorColor
            elif self.time >= timedelta(seconds=10):
                self.color = self.theme_cls.primaryColor


class MCCControlButtonsLayout(MDFloatLayout):
    """
    Container widget for the clock control buttons (eg Play/Pause, Reset, etc...)
    """
    def adjust_width(self):
        """
        Dynamically adjust width based on max child widget size
        (It's too wide otherwise)
        """
        child_widths = [child.width for child in self.children if hasattr(child, 'width')]
        max_child_width = max(child_widths) if len(child_widths) > 0 else 0
        self.width = max_child_width


# ---------------------------------------------------------------------------- #
#                             The main application                             #
# ---------------------------------------------------------------------------- #


class MCCApp(MDApp):
    """
    The main app of material-chess-clock (MCC)
    """
    # Define new option property for keeping track of who is the active side
    active_player = OptionProperty("black", options=["white", "black"])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # State attributes
        self.running = False
        self.flagged = False
        # Threading
        self.thread = threading.Thread(target=self.refresh_active_players_time)
        # Sounds
        self.clock_button_click = SoundLoader.load('assets/clock-button-press.mp3')
        self.control_button_click = SoundLoader.load('assets/control-button-press.mp3')
        self.warning_sound = SoundLoader.load('assets/warning-sound.mp3')
        self.flagging_sound = SoundLoader.load('assets/flagging-sound.mp3')
        # Dialogs
        self.reset_dialog = MDDialog()
        self.setup_dialog = MDDialog()

    def build(self):
        # Theming
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        # ---------------------------------------------------------------------------- #
        #                           Root widget for the app                            #
        # ---------------------------------------------------------------------------- #
        self.root = MCCRootLayout(
            MCCClockLayout(
                # -------------------------- Clock button for White -------------------------- #
                MCCClockButton(
                    MCCTimeText(
                        id='mcc_time_text_white',
                    ),
                    disabled=True,
                    on_press=self.on_press_clock_button,
                    id="mcc_clock_button_white",
                ),
                # --------------------- Container for the control buttons -------------------- #
                MCCControlButtonsLayout(
                    # ----------------------------- Play/Pause button ---------------------------- #
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
                    # ------------------------------- Reset button ------------------------------- #
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
                    # ------------------------------- Setup button ------------------------------- #
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
                # -------------------------- Clock button for Black -------------------------- #
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
        # ---------------------------------------------------------------------------- #
        #                                 Reset dialog                                 #
        # ---------------------------------------------------------------------------- #
        self.reset_dialog = MDDialog(
            # ---------------------------------- Header ---------------------------------- #
            MDDialogHeadlineText(
                text="Reset clock confirmation",
                halign="left",
            ),
            # ----------------------------------- Text ----------------------------------- #
            MDDialogSupportingText(
                text="Do you really want to reset the ongoing game?",
                halign="left",
            ),
            # ----------------------------- Button container ----------------------------- #
            MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(text="Cancel"),
                    style="outlined",
                    on_press=self.on_press_reset_dialog_cancel,
                ),
                MDButton(
                    MDButtonText(text="Accept"),
                    style="filled",
                    on_press=self.on_press_reset_dialog_accept,
                ),
                spacing="8dp",
            ),
        )
        # ---------------------------------------------------------------------------- #
        #                                 Setup dialog                                 #
        # ---------------------------------------------------------------------------- #
        self.setup_dialog = MDDialog(
            # ---------------------------------- Header ---------------------------------- #
            MDDialogIcon(
                icon="cog",
            ),
            MDDialogHeadlineText(
                text="Setup new time-control",
            ),
            MDDialogSupportingText(
                text="CAUTION: accepting will reset the clock!",
            ),
            # ------------------------------- Input fields ------------------------------- #
            MDDialogContentContainer(
                # ------------------------------- Starting time ------------------------------ #
                MDTextField(
                    MDTextFieldLeadingIcon(
                        icon="clock",
                    ),
                    MDTextFieldHintText(
                        text="Starting time",
                    ),
                    MDTextFieldHelperText(
                        text="In the format of 'hh:mm'",
                        mode="persistent",
                    ),
                    MDTextFieldMaxLengthText(
                        max_text_length=5,
                    ),
                    mode="outlined",
                    validator="time",
                    text="00:01",
                    id="starting_time",
                ),
                # --------------------------------- Increment -------------------------------- #
                MDTextField(
                    MDTextFieldLeadingIcon(
                        icon="plus",
                    ),
                    MDTextFieldHintText(
                        text="Increment",
                    ),
                    MDTextFieldHelperText(
                        text="In the format of 'mm:ss'",
                        mode="persistent",
                    ),
                    MDTextFieldMaxLengthText(
                        max_text_length=5,
                    ),
                    mode="outlined",
                    validator="time",
                    text="00:05",
                    id="increment",
                ),
                orientation="vertical",
                spacing="30dp",
                padding="30dp",
                id="setup_dialog_content",
            ),
            # ----------------------------- Button container ----------------------------- #
            MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(text="Cancel"),
                    style="outlined",
                    on_press=self.on_press_setup_dialog_cancel,
                ),
                MDButton(
                    MDButtonText(text="Accept"),
                    style="filled",
                    on_release=self.on_press_setup_dialog_accept,
                ),
                spacing="8dp",
            ),
            # ---------------------------------------------------------------------------- #
        )
        # Adjust the width of the container of clock control buttons
        self.root.get_ids().mcc_control_buttons_layout.adjust_width()
        return self.root

    def get_white_side(self):
        """
        Getter method that returns the widgets belonging to White
        """
        return {
            'button': self.root.get_ids().mcc_clock_button_white,
            'time_text': self.root.get_ids().mcc_time_text_white,
        }

    def get_black_side(self):
        """
        Getter method that returns the widgets belonging to Black
        """
        return {
            'button': self.root.get_ids().mcc_clock_button_black,
            'time_text': self.root.get_ids().mcc_time_text_black,
        }

    def refresh_active_players_time(self):
        """
        Refresh active player time
        """
        while self.running:
            refresh_start = time.time()
            # Get the active player's widgets
            if self.active_player == 'white':
                active_side = self.get_white_side()
            elif self.active_player == 'black':
                active_side = self.get_black_side()
            # Refresh player time
            active_side['time_text'].time -= timedelta(seconds=REFRESH_TIME)
            # Play warning sound if under critical time
            if active_side['time_text'].time == timedelta(seconds=10):
                self.warning_sound.play()
            # Flagging
            if active_side['time_text'].time == timedelta(milliseconds=0):
                self.stop_clock()
                self.flagged = True
                self.flagging_sound.play()
                break
            # Sleep
            refresh_duration = time.time() - refresh_start
            time.sleep(REFRESH_TIME - refresh_duration if REFRESH_TIME > refresh_duration else 0)

    def start_clock(self):
        """
        Start clock
        """
        self.running = True
        self.thread = threading.Thread(target=self.refresh_active_players_time)
        self.thread.start()
        self.update_control_buttons_disabled_state()

    def stop_clock(self):
        """
        Stop clock
        """
        self.running = False
        # self.thread.join()
        self.update_control_buttons_disabled_state()

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

    def reset_clock(self):
        """
        Reset clock
        """
        if self.running:
            self.stop_clock()
        self.flagged = False
        self.active_player = 'black'
        self.get_white_side()['button'].disabled = True
        self.get_black_side()['button'].disabled = False
        self.get_white_side()['time_text'].time = timedelta(minutes=DEFAULT_CLOCK_TIME)
        self.get_black_side()['time_text'].time = timedelta(minutes=DEFAULT_CLOCK_TIME)

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
                if button == self.get_white_side()['button']:
                    self.get_white_side()['button'].disabled = True
                    self.get_white_side()['time_text'].time += self.get_white_side()['time_text'].increment
                    self.get_black_side()['button'].disabled = False
                    self.active_player = "black"
                elif button == self.get_black_side()['button']:
                    self.get_black_side()['button'].disabled = True
                    self.get_black_side()['time_text'].time += self.get_black_side()['time_text'].increment
                    self.get_white_side()['button'].disabled = False
                    self.active_player = "white"
            Logger.info("MCCApp: Pressed clock button")

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
        Logger.info("MCCApp: Pressed playpause button")

    def on_press_reset_button(self, *args):
        """
        On press method for Reset button
        """
        self.control_button_click.play()
        self.reset_dialog.open()
        Logger.info("MCCApp: Pressed reset button")

    def on_press_setup_button(self, *args):
        """
        On press method for Setup button
        """
        self.control_button_click.play()
        self.setup_dialog.open()
        Logger.info("MCCApp: Pressed setup button")

    def on_press_reset_dialog_cancel(self, *args):
        """
        On press method for reset dialog cancel button
        """
        Logger.info("MCCApp: Pressed reset dialog 'Cancel' button")
        self.reset_dialog.dismiss()

    def on_press_reset_dialog_accept(self, *args):
        """
        On press method for reset dialog accept button
        """
        Logger.info("MCCApp: Pressed reset dialog 'Accept' button")
        self.reset_clock()
        self.reset_dialog.dismiss()

    def on_press_setup_dialog_cancel(self, *args):
        """
        On press method for setup dialog cancel button
        """
        Logger.info("MCCApp: Pressed setup dialog 'Cancel' button")
        self.setup_dialog.dismiss()

    def on_press_setup_dialog_accept(self, *args):
        """
        On press method for setup dialog accept button
        """
        Logger.info("MCCApp: Pressed setup dialog 'Accept' button")
        # Converting starting time and increment inputs
        starting_time_text = self.setup_dialog.get_ids().starting_time.text
        increment_text = self.setup_dialog.get_ids().increment.text
        starting_time = helpers.convert_time_string_to_integer(starting_time_text)
        increment = helpers.convert_time_string_to_integer(increment_text)
        # Updating default variables
        global DEFAULT_CLOCK_TIME
        DEFAULT_CLOCK_TIME = starting_time
        global DEFAULT_INCREMENT
        DEFAULT_INCREMENT = increment
        # Restart clock to apply effects
        self.reset_clock()
        self.setup_dialog.dismiss()

    def on_stop(self):
        self.stop_clock()

# ---------------------------------------------------------------------------- #
#                                   Start app                                  #
# ---------------------------------------------------------------------------- #

if __name__ == '__main__':
    app = MCCApp()
    app.run()
