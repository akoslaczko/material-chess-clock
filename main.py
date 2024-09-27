"""
Material Design style chess clock app using KivyMD
"""

import threading
import time
from datetime import timedelta
import re

from kivy.core.audio import SoundLoader
# from kivy.core.window import Window

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.button import MDFabButton, MDExtendedFabButton, MDExtendedFabButtonText

# Window for testing
# Window.size = [330, 600]
# Window.size = [600, 330]

REFRESH_TIME = 0.1
DEFAULT_CLOCK_TIME = 0.1  # in minutes
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
                    # print(btn.text)
                    if btn.time == timedelta(milliseconds=0):
                        self.stop_clock()
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
        print("pressed clock button")


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
        # Functional attributes
        self.time = timedelta(minutes=DEFAULT_CLOCK_TIME)
        self.increment = timedelta(seconds=DEFAULT_INCREMENT)
        self.time_text = MDExtendedFabButtonText(theme_font_size="Custom", font_size=40)
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
        # Updating attribute
        self.time_text.text = t_text

    def on_press(self):
        self.time += self.increment
        self.update_text_from_time()
        print(self.time_text.text)


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
            print("pressed playpause button")

    def on_press_reset(self, button_obj):
        """
        On press method for Reset button
        """
        if isinstance(button_obj, ResetButton):
            self.button_click.play()
            self.parent.reset_clock()
            print("pressed reset button")

    def on_press_setup(self, button_obj):
        """
        On press method for Setup button
        """
        if isinstance(button_obj, SetupButton):
            self.button_click.play()
            print("pressed setup button")

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


class PlayPauseButton(MDFabButton):
    """
    Play/Pause button
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Visual attributes
        self.icon = "play-pause"
        self.pos_hint = {"center_x": .5, "center_y": .75}
        # Functional attributes
        self.disabled = False


class ResetButton(MDFabButton):
    """
    Reset button
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Visual attributes
        self.icon = "refresh"
        self.pos_hint = {"center_x": .5, "center_y": .5}
        # Functional attributes
        self.disabled = False


class SetupButton(MDFabButton):
    """
    Setup button
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Visual attributes
        self.icon = "dots-horizontal"
        self.pos_hint = {"center_x": .5, "center_y": .25}
        # Functional attributes
        self.disabled = False


class ClockApp(MDApp):
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
    app = ClockApp()
    app.run()
