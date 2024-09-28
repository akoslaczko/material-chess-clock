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

REFRESH_TIME = 0.1
DEFAULT_CLOCK_TIME = 0.2  # in minutes
DEFAULT_INCREMENT = 5  # in seconds


class MainLayout(MDBoxLayout):
    """
    Main layout
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Visual attributes
        self.md_bg_color = self.theme_cls.inversePrimaryColor
        self.orientation = "vertical"
        # Functional attributes
        # Child widgets
        self.clock_layout = ClockLayout()
        # self.add_widget(self.clock_toolbar)
        self.add_widget(self.clock_layout)



class ClockLayout(MDBoxLayout):
    """
    Clock layout
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Visual attributes
        self.orientation = "horizontal"
        self.padding = "15dp"
        self.spacing = "15dp"
        # Functional attributes
        self.press_count = 0
        self.running = False
        self.flagged = False
        self.button_click = SoundLoader.load('assets/clock-button-press.mp3')
        self.warning_sound = SoundLoader.load('assets/warning-sound.mp3')
        self.flagging_sound = SoundLoader.load('assets/flagging-sound.mp3')
        # Child widgets
        self.control_buttons_layout = ControlButtonsLayout()
        self.clock_button1 = ClockButton(disabled=True)
        self.clock_button2 = ClockButton(disabled=False)
        self.add_widget(self.clock_button1)
        self.add_widget(self.control_buttons_layout)
        self.add_widget(self.clock_button2)
        # Binding events
        self.clock_button1.bind(on_press=self.on_clock_button_press)
        self.clock_button2.bind(on_press=self.on_clock_button_press)

    def start_threading(self, *args):
        """
        Threading
        """
        threading.Thread(target=self.refresh_buttons).start()

    def refresh_buttons(self):
        """
        Refresh buttons
        """
        while self.running:
            refresh_start = time.time()
            for btn in (self.clock_button1, self.clock_button2):
                if btn.disabled is False:
                    btn.time -= timedelta(seconds=REFRESH_TIME)
                    btn.update_text_from_time()
                    if btn.time == timedelta(seconds=10):
                        self.warning_sound.play()
                    if btn.time == timedelta(milliseconds=0):
                        self.stop_clock()
                        self.flagging_sound.play()
                        self.flagged = True
                        btn.disabled = True
            refresh_duration = time.time() - refresh_start
            time.sleep(REFRESH_TIME - refresh_duration if REFRESH_TIME > refresh_duration else 0)

    def start_clock(self):
        """
        Start clock
        """
        self.running = True
        self.start_threading(1)
        self.control_buttons_layout.update_control_buttons_disabled_state()

    def stop_clock(self):
        """
        Stop clock
        """
        self.running = False
        self.control_buttons_layout.update_control_buttons_disabled_state()

    def reset_clock(self):
        """
        Reset clock
        """
        self.stop_clock()  # Should be already stopped, but just in case
        self.flagged = False
        self.clock_button1.disabled = True
        self.clock_button2.disabled = False
        self.clock_button1.time = timedelta(minutes=DEFAULT_CLOCK_TIME)
        self.clock_button2.time = timedelta(minutes=DEFAULT_CLOCK_TIME)
        self.clock_button1.update_text_from_time()
        self.clock_button2.update_text_from_time()

    def on_clock_button_press(self, button_obj):
        """
        On press method for clock buttons
        """
        self.press_count += 1
        self.button_click.play()
        Logger.info("ChessClockApp: Pressed clock button, 'disabled_state' before: %s", button_obj.disabled)
        if not self.flagged:
            if not self.running:
                self.start_clock()
            if isinstance(button_obj, ClockButton):
                if button_obj == self.clock_button1:
                    self.clock_button1.disabled = True
                    self.clock_button2.disabled = False
                elif button_obj == self.clock_button2:
                    self.clock_button2.disabled = True
                    self.clock_button1.disabled = False
        Logger.info("ChessClockApp: Pressed clock button, 'disabled_state' after: %s", button_obj.disabled)


class ClockButton(MDExtendedFabButton):
    """
    Clock button
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Visual attributes
        self.theme_width = "Custom"
        self.theme_height = "Custom"
        self.size_hint = (1, 1)
        self.pos_hint = {"center_x": .5, "center_y": .5}
        self.halign = "center"
        self.valign = "center"
        self.theme_elevation_level = "Custom"
        self.elevation_level = 5
        # Functional attributes
        self.time = timedelta(minutes=DEFAULT_CLOCK_TIME)
        self.increment = timedelta(seconds=DEFAULT_INCREMENT)
        # Child widgets
        self.time_text = MDExtendedFabButtonText(
            theme_font_size="Custom",
            font_size=80,
            ) # For debugging: theme_bg_color="Custom", md_bg_color=self.theme_cls.primaryFixedColor
        self.add_widget(self.time_text)
        self.update_text_from_time()

    def update_text_from_time(self):
        """
        Update the clock button's time-text
        """
        # Split timedelta string
        t_list = re.split("[:.]", str(self.time))
        t_text = ""
        # Adding hours if necessary
        if int(t_list[0]) > 0:
            t_text += t_list[0] + ":"
        # Adding minutes and seconds
        t_text += t_list[1] + ":" + t_list[2]
        # Under 10 sec we increase the resolution
        if self.time < timedelta(seconds=10):
            t_text += "."
            if len(t_list) >= 4:
                t_text += t_list[3][0]  # + t_list[3][1]
            else:
                t_text += "0"  # "00"
        # Updating attributes
        self.time_text.text = t_text
        if self.disabled is not True:
            # If the button is not disabled we also change the text color under 10 sec
            if self.time < timedelta(seconds=10):
                self.time_text.color = self.theme_cls.errorColor
            elif self.time >= timedelta(seconds=10):
                self.time_text.color = self.theme_cls.primaryColor

    def on_press(self):
        self.time += self.increment
        self.update_text_from_time()
        Logger.info("ChessClockApp: Pressed clock button, 'time_text.text': %s", self.time_text.text)


class ControlButtonsLayout(MDFloatLayout):
    """
    Control buttons layout
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Visual attributes
        self.orientation = "vertical"
        self.halign = "center"
        self.valign = "center"
        # Functional attributes
        self.button_click = SoundLoader.load('assets/control-button-press.mp3')
        # Child widgets
        self.playpause_button = PlayPauseButton()
        self.reset_button = ResetButton()
        self.setup_button = SetupButton()
        self.add_widget(self.playpause_button)
        self.add_widget(self.reset_button)
        self.add_widget(self.setup_button)
        # Adjust width
        self.theme_width = "Custom"
        self.adaptive_width = True
        self.adjust_width()
        # Binding
        self.playpause_button.bind(on_press=self.on_press_playpause)
        self.reset_button.bind(on_press=self.on_press_reset)
        self.setup_button.bind(on_press=self.on_press_setup)

    def adjust_width(self):
        """
        Dynamically adjust width based on max child widget size
        """
        child_widths = [child.width for child in self.children if hasattr(child, 'width')]
        max_child_width = max(child_widths) if len(child_widths) > 0 else 0
        self.width = max_child_width

    def on_press_playpause(self, button_obj):
        """
        On press method for Play/Pause button
        """
        if isinstance(button_obj, PlayPauseButton):
            if not self.parent.flagged:
                self.button_click.play()
                if self.parent.running:
                    self.parent.stop_clock()
                elif not self.parent.running:
                    self.parent.start_clock()
            Logger.info("ChessClockApp: Pressed playpause button")

    def on_press_reset(self, button_obj):
        """
        On press method for Reset button
        """
        if isinstance(button_obj, ResetButton):
            self.button_click.play()
            self.parent.reset_clock()
            Logger.info("ChessClockApp: Pressed reset button")

    def on_press_setup(self, button_obj):
        """
        On press method for Setup button
        """
        if isinstance(button_obj, SetupButton):
            self.button_click.play()
            Logger.info("ChessClockApp: Pressed setup button")

    def update_control_buttons_disabled_state(self):
        """
        Update clock button's disabled state
        """
        if self.parent.running:
            self.reset_button.disabled = True
            self.setup_button.disabled = True
        elif not self.parent.running:
            self.reset_button.disabled = False
            self.setup_button.disabled = False


class PlayPauseButton(MDExtendedFabButton):
    """
    Play/Pause button
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Visual attributes
        self.pos_hint = {"center_x": .5, "center_y": .75}
        self.theme_elevation_level = "Custom"
        self.elevation_level = 3
        # Functional attributes
        self.disabled = False
        # Child Widgets
        self.icon = MDExtendedFabButtonIcon(icon="play-pause")
        self.add_widget(self.icon)


class ResetButton(MDExtendedFabButton):
    """
    Reset button
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Visual attributes
        self.pos_hint = {"center_x": .5, "center_y": .5}
        self.theme_elevation_level = "Custom"
        self.elevation_level = 3
        # Functional attributes
        self.disabled = False
        # Child Widgets
        self.icon = MDExtendedFabButtonIcon(icon="refresh")
        self.add_widget(self.icon)


class SetupButton(MDExtendedFabButton):
    """
    Setup button
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Visual attributes
        self.pos_hint = {"center_x": .5, "center_y": .25}
        self.theme_elevation_level = "Custom"
        self.elevation_level = 3
        # Functional attributes
        self.disabled = False
        # Child Widgets
        self.icon = MDExtendedFabButtonIcon(icon="cog")
        self.add_widget(self.icon)
        self.dialog = MDDialog(
            # ----------------------------Icon-----------------------------
            MDDialogIcon(
                icon="cog",
            ),
            # -----------------------Headline text-------------------------
            MDDialogHeadlineText(
                text="Setup new time-control",
            ),
            # -----------------------Supporting text-----------------------
            MDDialogSupportingText(
                text="CAUTION: accepting will reset the clock!",
            ),
            # -----------------------Custom content------------------------
            MDDialogContentContainer(
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
            # ---------------------Button container------------------------
            MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(text="Cancel"),
                    style="outlined",
                    on_press=self.on_press_dialog_cancel,
                ),
                MDButton(
                    MDButtonText(text="Accept"),
                    style="filled",
                    on_release=self.on_press_dialog_accept,
                ),
                spacing="8dp",
            ),
            # -------------------------------------------------------------
        )

    def on_press(self):
        self.dialog.open()

    def on_press_dialog_accept(self, *args):
        """
        On press fuction for setup dialog accept button
        """
        # Converting starting time and increment inputs      
        starting_time, increment = [int(time_list[0])*60 + int(time_list[1]) for time_list in [re.split("[:.]", time_string) for time_string in [self.dialog.get_ids().starting_time.text, self.dialog.get_ids().increment.text]]]
        Logger.info("ChessClockApp: Pressed setup dialog 'Accept' button, 'starting_time' and 'increment': %s", [starting_time, increment])
        # Updating default variables
        global DEFAULT_CLOCK_TIME
        DEFAULT_CLOCK_TIME = starting_time
        global DEFAULT_INCREMENT
        DEFAULT_INCREMENT = increment
        # Restart clock to apply effects
        self.parent.parent.reset_clock()
        self.dialog.dismiss()

    def on_press_dialog_cancel(self, *args):
        """
        On press fuction for setup dialog cancel button
        """
        Logger.info("ChessClockApp: Pressed setup dialog 'Cancel' button")
        self.dialog.dismiss()


class ChessClockApp(MDApp):
    """
    Main app
    """
    def build(self):
        # Visual attributes
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        # Functional attributes
        # Child widgets
        self.root = MainLayout()

        return self.root

    def on_stop(self):
        self.root.clock_layout.stop_clock()


if __name__ == '__main__':
    app = ChessClockApp()
    app.run()
