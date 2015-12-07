
from gi.repository import Gtk

class Switch(Gtk.Switch):

    def __init__(self, control):
        Gtk.Switch.__init__(self)
        self.control = control

        self.connect("notify::active", self.on_switch_activated)
        self.set_active(False)

    def on_switch_activated(self, switch, gparam):
        if switch.get_active():
            self.control.indexView.stack.remove(self.control.pageItemBox)
        else:
            self.control.indexView.stack.add_titled(self.control.pageItemBox, "page", "Page")

