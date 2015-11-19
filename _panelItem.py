
from gi.repository import Gtk, Gdk

class View(Gtk.Box):

    def __init__(self, control):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL)
        self.control = control

        # style_provider = Gtk.CssProvider ()
        # css = """GtkTextView
        # {
        #     font-size: 12px;
        #     color: black;
        # }"""
        # style_provider.load_from_data (css);
        # Gtk.StyleContext.add_provider_for_screen (Gdk.Screen.get_default(), style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION);

        self.label = Gtk.Label(xalign=0)

        # self.label.props.opacity = 0.9
        # self.label.props.wrap_mode = Gtk.WrapMode.WORD
        # self.label.modify_bg(Gtk.StateType.SELECTED, Gdk.RGBA(0.8,0.8,0.8).to_color())
        # self.label.modify_fg(Gtk.StateType.SELECTED, Gdk.RGBA(0.2,0.2,0.2).to_color())
        #
        #
        
                
        self.set_border_width(10)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.pack_start(vbox, 1, 1, 0)
        
        vbox.pack_start(self.label, 0, 0, 0)

    def state(self):
        # return dictionary
        pass

    def data(self):
        # return dictionary
        pass

    def load(self):
        pass

    def reset(self):
        pass


