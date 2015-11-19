
from gi.repository import Gtk
    
class View(Gtk.Box):

    def __init__(self, control):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL)
        self.control = control
        
        self.characterLabel = Gtk.Label()
        self.dialogLabel = Gtk.Label()
        
        self.set_border_width(10)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.pack_start(vbox, 1, 1, 0)
        
        vbox.pack_start(self.characterLabel, 0, 0, 0)

        vbox.pack_start(self.dialogLabel, 0, 0, 0)
        
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


