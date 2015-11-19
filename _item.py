
from gi.repository import Gtk, Gdk

class Item(Gtk.EventBox):

    def __init__(self, control):
        Gtk.EventBox.__init__(self)
        self.control = control

        self.widgets()
        self.connections()
        self.config()
        self.layout()

        self.saving = False
        self.editing = False

        self.connect('button-press-event', self.buttonPress)
        self.connect('button-release-event', self.buttonRelease)

        self.connect('leave-notify-event', self.leaveNotify)

    def leaveNotify(self, widget, event):
        if event.detail in [Gdk.NotifyType.ANCESTOR, Gdk.NotifyType.NONLINEAR] and self.control.sceneItemBox.editing:
            self.endEditMode()

    def buttonPress(self, widget, event):
        self.doubleClick = False
        if event.type == Gdk.EventType._2BUTTON_PRESS and not self.control.sceneItemBox.editing:
            self.doubleClick = True

    def buttonRelease(self, widget, event):
        if self.doubleClick and not self.control.sceneItemBox.editing:
            self.control.sceneItemBox.editing = True
            self.startEditMode()

    def widgets(self):
        self.hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.label = Gtk.Label()
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

    def connections(self):
        pass

    def config(self):
        self.hbox.set_border_width(10)

    def layout(self):
        self.hbox.pack_start(self.vbox, 0, 0, 0)
        self.add(self.hbox)
        self.vbox.pack_start(self.label, 0, 0, 0)

    def startEditMode(self):
        pass #override in superclass

    def labelKeyRelease(self, widget, event):
        if event.keyval == 65293:
            self.endEditMode()

    def endEditMode(self):
        pass #override

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

    def newItem(self):
        # override this
        pass

    def entryLeaveNotifyEvent(self, entry, eventCrossing):
        print "leaving"
        if not self.saving and self.editing:
            self.endEditMode()