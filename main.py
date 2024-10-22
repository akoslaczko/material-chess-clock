"""
Material Design style chess clock app using KivyMD
"""

# pylint: disable=E0611 # Disable the error related to importing from pxd files (temporary solution)

from datetime import timedelta

from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.utils import platform
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.properties import (
    ObjectProperty,
    OptionProperty,
    NumericProperty,
)

from kivymd.app import MDApp
from kivymd.uix.behaviors import DeclarativeBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.scrollview import MDScrollView
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
if platform not in ['android', 'ios']:
    Window.size = [1200, 600]

# ---------------------------------------------------------------------------- #
#                               Default variables                              #
# ---------------------------------------------------------------------------- #

REFRESH_TIME = 0.01 # in seconds

# ---------------------------------------------------------------------------- #
#                           Custom classes (main app)                          #
# ---------------------------------------------------------------------------- #


class MCCRootLayout(MDBoxLayout, DeclarativeBehavior):
    """
    The root widget of the app.
    Inherits from KivyMD's DeclarativeBehavior for coding the UI in Python declarative style
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
        self.font_size = dp(80)
        self.size_hint = (1, 1) # Fixes bug related to buttons being clickable while disabled
        # Setup clock time related attributes
        self.bind(time=self.on_change_time)
        self.time = app.starting_time
        self.is_warned = False

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.minimize_width()

    def minimize_width(self):
        """
        Dynamically adjust width based on max child widget size
        (It's too wide otherwise)
        """
        child_widths = [child.width for child in self.children if hasattr(child, 'width')]
        max_child_width = max(child_widths) if len(child_widths) > 0 else 0
        self.width = max_child_width


# ---------------------------------------------------------------------------- #
#                                 Reset dialog                                 #
# ---------------------------------------------------------------------------- #


class MCCResetDialog(MDDialog):
    """
    Reset Dialog
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ---------------------------------- Header ---------------------------------- #
        self.title = MDDialogHeadlineText(
            text="Reset Clock",
            halign="left",
        )
        self.add_widget(self.title)
        # ----------------------------------- Text ----------------------------------- #
        self.text = MDDialogSupportingText(
            text="Do you really want to reset the ongoing game?",
            halign="left",
        )
        self.add_widget(self.text)
        # ----------------------------- Button container ----------------------------- #
        self.buttons = MDDialogButtonContainer(
            Widget(),
            MDButton(
                MDButtonText(text="Cancel"),
                style="outlined",
                on_press=app.on_press_reset_dialog_cancel,
            ),
            MDButton(
                MDButtonText(text="Accept"),
                style="filled",
                on_press=app.on_press_reset_dialog_accept,
            ),
            spacing="8dp",
        )
        self.add_widget(self.buttons)


# ---------------------------------------------------------------------------- #
#                              Quick Setup dialog                              #
# ---------------------------------------------------------------------------- #


class MCCQuickSetupDialog(MDDialog):
    """
    Quick Setup Dialog
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ----------------------------------- Icon ----------------------------------- #
        self.icon = MDDialogIcon(
            icon="cog",
        )
        self.add_widget(self.icon)
        # ----------------------------------- Title ---------------------------------- #
        self.title = MDDialogHeadlineText(
            text="Quick Setup Game",
        )
        self.add_widget(self.title)
        # ---------------------------------- Options --------------------------------- #
        self.options = MDDialogContentContainer(
            MCCQuickSetupScrollView(
                MCCQuickSetupLayout(
                    height=dp(120),
                    adaptive_width=True,
                    spacing="10dp",
                    padding="10dp",
                    id="mcc_quicksetup_dialog_content_layout",
                ),
                size_hint_y=None,
                height=dp(120),
                id="mcc_quicksetup_dialog_content_scrollview",
            ),
            id="mcc_quicksetup_dialog_content",
        )
        self.add_widget(self.options)


class MCCQuickSetupScrollView(MDScrollView):
    """
    The scroll view containing the MCCQuickSetupLayout instance
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.height = max([child.height for child in self.children])
        Logger.info("MCCApp: MCCQuickSetupScrollView height=%s", self.height)


class MCCQuickSetupLayout(MDBoxLayout):
    """
    Container for various quick setup options
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timecontrol_options = [
            {
                'type': 'Bullet',
                'starting_time': 1,
                'increment': 0,
            },
            {
                'type': 'Bullet',
                'starting_time': 2,
                'increment': 1,
            },
            {
                'type': 'Blitz',
                'starting_time': 3,
                'increment': 0,
            },
            {
                'type': 'Blitz',
                'starting_time': 3,
                'increment': 2,
            },
            {
                'type': 'Blitz',
                'starting_time': 5,
                'increment': 0,
            },
            {
                'type': 'Blitz',
                'starting_time': 5,
                'increment': 3,
            },
            {
                'type': 'Rapid',
                'starting_time': 10,
                'increment': 0,
            },
            {
                'type': 'Rapid',
                'starting_time': 10,
                'increment': 5,
            },
            {
                'type': 'Rapid',
                'starting_time': 15,
                'increment': 10,
            },
            {
                'type': 'Classical',
                'starting_time': 30,
                'increment': 0,
            },
            {
                'type': 'Classical',
                'starting_time': 30,
                'increment': 20,
            },
        ]
        self.add_timecontrol_options()
        # self.height = max([child.height for child in self.children]) + dp(20)
        Logger.info("MCCApp: MCCQuickSetupLayout height=%s", self.height)

    def add_timecontrol_options(self):
        """
        Method for adding button widgets that represent the different timecontrol options
        """
        for i, option in enumerate(self.timecontrol_options):
            timecontrol_button = MCCQuickSetupButton(
                MDButtonText(
                    # text=str(option["starting_time"]) + " + " + str(option["increment"]) + "\n" + option["type"],
                    text=str(option["starting_time"]) + " + " + str(option["increment"]),
                    pos_hint={'center_x': 0.5,'center_y': 0.5},
                    font_style="Title"
                ),
                style="outlined",
                theme_width="Custom",
                theme_height="Custom",
                height=dp(100),
                width=dp(100),
                size_hint=(None, None),
                # Setting the actual time-control variables
                starting_time = option["starting_time"],
                increment = option["increment"],
                # ID
                id="quicksetup_button_" + str(i),
            )
            self.add_widget(timecontrol_button)


class MCCQuickSetupButton(MDButton):
    """
    Class for buttons that represent the Quick Setup options
    """
    starting_time = NumericProperty()
    increment = NumericProperty()

    def on_release(self, *args):
        """
        On press method for setup dialog accept button
        """
        Logger.info("MCCApp: Pressed quick setup dialog option with 'id': %s", self.id)
        # Updating default variables
        app.starting_time = timedelta(minutes=self.starting_time)
        app.increment = timedelta(seconds=self.increment)
        # Restart clock to apply effects
        app.reset_clock()
        app.quicksetup_dialog.dismiss()
        app.quicksetup_dialog = None # We will reinitialize it before opening


# ---------------------------------------------------------------------------- #
#                              Custom Setup dialog                             #
# ---------------------------------------------------------------------------- #


class MCCCustomSetupDialog(MDDialog):
    """
    Custom Setup dialog
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ----------------------------------- Icon ----------------------------------- #
        self.icon = MDDialogIcon(
            icon="cog",
        )
        self.add_widget(self.icon)
        # ----------------------------------- Title ---------------------------------- #
        self.title = MDDialogHeadlineText(
            text="Setup Custom Game",
        )
        self.add_widget(self.title)
        # ---------------------------------- Options --------------------------------- #
        self.options = MDDialogContentContainer(
            MDScrollView(
                MDBoxLayout(
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
                    adaptive_height=True,
                    spacing="30dp",
                    padding="30dp",
                    id="setup_dialog_content_layout",
                ),
                size_hint_y=None,
                # height=dp(100),
                id="setup_dialog_content_scrollview",
            ),
            id="setup_dialog_content",
        )
        self.add_widget(self.options)
        # ----------------------------- Button container ----------------------------- #
        self.buttons = MDDialogButtonContainer(
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
        )
        self.add_widget(self.buttons)


# ---------------------------------------------------------------------------- #
#                             The main application                             #
# ---------------------------------------------------------------------------- #


class MCCApp(MDApp):
    """
    The main app of material-chess-clock (MCC)
    """
    # Define new option property for keeping track of who is the active side
    active_player = OptionProperty("white", options=["white", "black"])
    starting_time = ObjectProperty(timedelta(seconds=15))
    increment = ObjectProperty(timedelta(seconds=5))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # State attributes
        self.running = False
        self.flagged = False
        # Scheduler
        self.refresh_event = None
        # Sounds
        self.clock_button_click = SoundLoader.load('assets/clock-button-press.mp3')
        self.control_button_click = SoundLoader.load('assets/control-button-press.mp3')
        self.warning_sound = SoundLoader.load('assets/warning-sound.mp3')
        self.flagging_sound = SoundLoader.load('assets/flagging-sound.mp3')
        # Dialogs
        self.reset_dialog = None
        self.customsetup_dialog = None
        self.quicksetup_dialog = None

    def build(self):
        # Theming
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        # ---------------------------------------------------------------------------- #
        #                           Root widget for the app                            #
        # ---------------------------------------------------------------------------- #
        self.root = MCCRootLayout(
            # -------------------------- Clock button for White -------------------------- #
            MCCClockButton(
                MCCTimeText(
                    id='mcc_time_text_white',
                ),
                disabled=False,
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
                disabled=True,
                on_press=self.on_press_clock_button,
                id="mcc_clock_button_black",
            ),
            md_bg_color=self.theme_cls.primaryContainerColor,
            padding="15dp",
            spacing="15dp",
            id="mcc_root_layout",
        )
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

    def refresh_active_players_time(self, dt):
        """
        Refresh active player time
        """
        # Get the active player's widgets
        if self.active_player == 'white':
            active_side = self.get_white_side()
        elif self.active_player == 'black':
            active_side = self.get_black_side()
        # Refresh player time
        if active_side['time_text'].time >= timedelta(seconds=dt):
            active_side['time_text'].time -= timedelta(seconds=dt)
            # Play warning sound if under critical time (but only when reaching the threshold)
            if active_side['time_text'].time <= timedelta(seconds=10):
                if not active_side['time_text'].is_warned:
                    self.warning_sound.play()
                    active_side['time_text'].is_warned = True
            else:
                active_side['time_text'].is_warned = False
        else:
            # Flagging
            active_side['time_text'].time = timedelta(milliseconds=0)
            self.stop_clock()
            self.flagged = True
            self.flagging_sound.play()

    def start_clock(self):
        """
        Start clock
        """
        self.running = True
        if not self.refresh_event:
            self.refresh_event = Clock.schedule_interval(self.refresh_active_players_time, REFRESH_TIME)
        self.update_control_buttons_disabled_state()


    def stop_clock(self):
        """
        Stop clock
        """
        self.running = False
        if self.refresh_event:
            Clock.unschedule(self.refresh_event)
            self.refresh_event = None
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
        self.active_player = 'white'
        self.get_white_side()['button'].disabled = False
        self.get_black_side()['button'].disabled = True
        self.get_white_side()['time_text'].time = self.starting_time
        self.get_black_side()['time_text'].time = self.starting_time

    def on_press_clock_button(self, *args):
        """
        On press method for clock buttons
        """
        if not self.flagged:
            self.clock_button_click.play()
            if len(args) > 0 and isinstance(args[0], MCCClockButton):
                button = args[0]
                if button == self.get_white_side()['button']:
                    self.active_player = "black"
                    self.get_white_side()['button'].disabled = True
                    self.get_black_side()['button'].disabled = False
                    if self.running:
                        self.get_white_side()['time_text'].time += self.increment
                elif button == self.get_black_side()['button']:
                    self.active_player = "white"
                    self.get_black_side()['button'].disabled = True
                    self.get_white_side()['button'].disabled = False
                    if self.running:
                        self.get_black_side()['time_text'].time += self.increment
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
        # Initialize dialog
        if not self.reset_dialog:
            self.reset_dialog = MCCResetDialog()
        self.reset_dialog.open()
        Logger.info("MCCApp: Pressed reset button")

    def on_press_setup_button(self, *args):
        """
        On press method for Setup button
        """
        self.control_button_click.play()
        # Initialize dialog
        if not self.quicksetup_dialog:
            self.quicksetup_dialog = MCCQuickSetupDialog()
        self.quicksetup_dialog.open()
        Logger.info("MCCApp: Pressed setup button")

    def on_press_reset_dialog_cancel(self, *args):
        """
        On press method for reset dialog cancel button
        """
        Logger.info("MCCApp: Pressed reset dialog 'Cancel' button")
        self.reset_dialog.dismiss()
        self.reset_dialog = None # We will reinitialize it before opening

    def on_press_reset_dialog_accept(self, *args):
        """
        On press method for reset dialog accept button
        """
        Logger.info("MCCApp: Pressed reset dialog 'Accept' button")
        self.reset_clock()
        self.reset_dialog.dismiss()
        self.reset_dialog = None # We will reinitialize it before opening

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
        self.starting_time = timedelta(minutes=starting_time)
        self.increment = timedelta(seconds=increment)
        # Restart clock to apply effects
        self.reset_clock()
        self.setup_dialog.dismiss()

    def on_stop(self):
        self.stop_clock()

# ---------------------------------------------------------------------------- #
#                                   Start app                                  #
# ---------------------------------------------------------------------------- #

app = MCCApp()

if __name__ == '__main__':
    app.run()
