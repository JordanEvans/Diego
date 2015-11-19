
from gi.repository import Gtk

class IndexListBox(Gtk.ListBox):
    def __init__(self, control):
        Gtk.ListBox.__init__(self)
        self.control = control
        self.reloadControl = True

    def do_key_press_event(self, event):

        if event.keyval == 65293:
            selectedRows = self.get_selected_rows()
            if len(selectedRows) == 0:
                return
            elif len(selectedRows) == 1:
                self.newItem()
            else:
                self.unselect_all()

    def newItem(self):
        #print "selected rows", self.get_selected_rows()
        pass #override in subclass
