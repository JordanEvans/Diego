from gi.repository import Gtk


class Paned(Gtk.Paned):

    def __init__(self):
        Gtk.Paned.__init__(self, )

        self.connect('focus-out-event', self.test)

    def test(self):
        print self.get_position()

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

        # Add the Stack Switcher
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.stackSwitcherBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.control.stackSwitcher = Gtk.StackSwitcher(self.control)
        self.control.stackSwitcher.set_stack(self.control.indexView.stack)
        self.stackSwitcherBox.pack_start(self.control.stackSwitcher, 0, 0, 0)
        vbox.pack_start(self.stackSwitcherBox,0 ,0, 0)
        self.control.appHeaderBar.pack_start(vbox)

        # Add the Panel box
        self.panelLabelBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        # self.panelLabelBox.pack_start(self.control.panelLabel, 1, 1, 1)
        self.control.appHeaderBar.pack_start(self.panelLabelBox)

        # Add SearchEntry
        self.control.appHeaderBar.pack_end(self.control.searchView)

        # Add Screenplay Mode Switch
        # self.control.appHeaderBar.pack_end(self.control.screenplayModeSwitch)

        # Add Paned, which includes IndexView on left and ScriptView on right.
        self.paned = Paned()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        vbox.pack_start(hbox, 1, 1, 0)
        hbox.pack_start(self.paned, 1, 1, 0)
        self.paned.add1(self.control.indexView)
        self.paned.add2(self.control.scriptView)
        self.paned.set_position(150)
        self.pack_end(vbox, 1, 1, 0)

    def connections(self, ):
        pass
    
    def config(self, ):
        pass

    def reset(self):
        pass

    def load(self):
        pass