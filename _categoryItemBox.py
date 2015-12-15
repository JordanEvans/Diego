
from gi.repository import Gtk

import _event

class CategoryItemBox(Gtk.Box):

    def __init__(self, control):
        Gtk.Box.__init__(self)
        self.control = control
        self.items = []
        
    def postInit(self, ):
        self.layout()
        self.connections()
        self.config()
        
    def layout(self, ):

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.pack_start(vbox, 1, 1, 0)
        
        self.scrolledWindow = Gtk.ScrolledWindow()
        vbox.pack_start(self.scrolledWindow, 1, 1, 0)
        
        self.viewport = Gtk.Viewport()
        self.scrolledWindow.add(self.viewport)
        
        self.listbox = Gtk.ListBox()
        self.viewport.add(self.listbox)
        
        hadjustment = self.viewport.get_hadjustment()
        self.scrolledWindow.set_hadjustment(hadjustment)
        vadjustment = self.viewport.get_vadjustment()
        self.scrolledWindow.set_vadjustment(vadjustment)
        
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        
    def connections(self, ):
        pass
        # self.connect("key-press-event", self.keyPress)

    # def keyPress(self, widget, event):
    #
    #     if (event.keyval == 65535):
    #         index = 0 # selected page
    #         self.deleteItem(index)
    #
    #     print event.keyval
    #
    #     #print event.state, Gdk.ModifierType.CONTROL_MASK
    
    def config(self, ):
        pass

    def deleteItem(self, index):
        # override

        self.control.currentStory().deletePage(index)

    def newItem(self, index, view):

        row = Gtk.ListBoxRow()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        row.add(hbox)
        
        if index == -1:
            self.items.append(view)
        else:
            self.items.insert(index, view)

        hbox.pack_start(view, 1, 1, 0)

        self.listbox.add(row)

        self.control.eventManager.newPageEvent(_event.Event())

    def state(self):
        # return dictionary
        pass

    def data(self):
        # return dictionary
        pass

    def load(self):
        return

    def reset(self):
        pass


