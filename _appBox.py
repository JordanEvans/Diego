from gi.repository import Gtk

class AppBox(Gtk.Box):

    def __init__(self, control):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self.control = control
        
    def postInit(self, ):
        self.layout()
        self.connections()
        self.config()
    
    def layout(self):

        self.pack_start(self.control.appHeaderBar, 0, 0, 0)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        self.stackSwitcherBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        vbox.pack_start(self.stackSwitcherBox,0 ,0, 0)

        vbox.pack_start(hbox,0, 0, 0)

        self.control.appHeaderBar.pack_start(vbox)

        panelLabelBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        panelLabelBox.pack_start(self.control.panelLabel, 1, 1, 1)

        self.control.appHeaderBar.pack_start(panelLabelBox)

        self.control.appHeaderBar.pack_end(self.control.searchEntry)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.pack_start(vbox, 1, 1, 0)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        vbox.pack_start(hbox, 1, 1, 0)
        
        self.paned = Gtk.Paned()
        hbox.pack_start(self.paned, 1, 1, 0)
        
        self.paned.add1(self.control.indexView)

        self.paned.add2(self.control.scriptView)

        self.paned.set_position(150)

    def connections(self, ):
        pass
    
    def config(self, ):
        pass

    def reset(self):
        pass

    def load(self):
        pass