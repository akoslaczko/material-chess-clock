from kivymd.app import MDApp
from kivymd.uix.behaviors import DeclarativeBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.button import MDButton
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogIcon,
    MDDialogHeadlineText,
    MDDialogContentContainer,
)


class MCCRootLayout(MDBoxLayout, DeclarativeBehavior):
    """
    Declarative root
    """

class MCCQuickSetupLayout(MDBoxLayout):
    """
    Container for various quick setup options
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_options()

    def add_options(self):
        """
        Method for adding button widgets that represent the different options
        """
        for option in range(10):
            timecontrol_button = MDButton()
            self.add_widget(timecontrol_button)


class MCCApp(MDApp):
    """
    The main app of material-chess-clock (MCC)
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.quicksetup_dialog = MDDialog()

    def build(self):
        self.quicksetup_dialog = MDDialog(
            # ---------------------------------- Header ---------------------------------- #
            MDDialogIcon(
                icon="cog",
            ),
            MDDialogHeadlineText(
                text="Quick Setup",
            ),
            MDDialogContentContainer(
                MDScrollView(
                    MCCQuickSetupLayout(
                        adaptive_width=True,
                        orientation='horizontal',
                        spacing="30dp",
                        padding="30dp",
                        id="quicksetup_dialog_content_layout",
                    ),
                    size_hint_y=None,
                    width=1200,
                    id="quicksetup_dialog_content_scrollview",
                ),
                orientation="horizontal",
                id="quicksetup_dialog_content",
            ),
        )
        self.root = MCCRootLayout(
            MDButton(
                on_press=self.open_quicksetup
            ),
        )
        return self.root
    
    def open_quicksetup(self, *args):
        """
        Open the quick setup dialog
        """
        self.quicksetup_dialog.open()
    
app = MCCApp()
app.run()
