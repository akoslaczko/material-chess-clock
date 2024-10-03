from kivy.app import App
from kivy.lang import Builder

kv = """
BoxLayout:
    orientation: 'vertical'
    ScrollView:
        size_hint_y: None
        height: dp(40)
        do_scroll_y: False
        Label:
            text: 'Horizontal Scroll Text ' * 20
            size_hint: None, None
            size: self.texture_size
    ScrollView:
        do_scroll_x: False
        Label:
            text: 'vertical scroll text \\n' * 50
            size_hint: None, None
            size: self.texture_size
"""
class HVScrollApp(App):
    def build(self):
        return Builder.load_string(kv)


HVScrollApp().run()