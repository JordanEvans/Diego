
from gi.repository import Gtk

import _panelItem
import _dialogItem

class IndexListBox(Gtk.ListBox):
    def __init__(self, control):
        Gtk.ListBox.__init__(self)
        self.control = control

    def do_key_press_event(self, event):

        if event.keyval == 65293:
            selectedRows = self.get_selected_rows()
            if len(selectedRows) == 0:
                return
            elif len(selectedRows) == 1:
                if self.control.preferences.autocompleteAsDialog:
                    self.newDialog()
                else:
                    self.newPanel()
            else:
                self.unselect_all()
        else:
            return 1

    def newPanel(self):
        self.control.newPanel()

    def newDialog(self):
        self.control.newDialog()

    def do_row_selected(self, row):

        if row:
            self.control.currentStory().index.line = self.get_children().index(row)
            self.control.app.window.show_all()

    def do_map(self):
        Gtk.ListBox.do_map(self)
        row = self.get_row_at_index(self.control.currentStory().index.line)
        if row:
            self.select_row(row)
            row.grab_focus()

class ScrolledListBox(Gtk.Box):

    def __init__(self, control):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self.control = control

        self.listbox = IndexListBox(self.control)
        self.viewport = Gtk.Viewport()
        self.scrolledWindow = Gtk.ScrolledWindow()

        self.pack_start(self.scrolledWindow, 1, 1, 0)
        self.scrolledWindow.add(self.viewport)
        self.viewport.add(self.listbox)

        hadjustment = self.viewport.get_hadjustment()
        self.scrolledWindow.set_hadjustment(hadjustment)
        vadjustment = self.viewport.get_vadjustment()
        self.scrolledWindow.set_vadjustment(vadjustment)

        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)

class ScriptItemBox(ScrolledListBox):

    def __init__(self, control):
        ScrolledListBox.__init__(self, control)
        self.control = control
        self.elements = []

        self.viewport.remove(self.listbox)
        self.listbox = IndexListBox(self.control)
        self.viewport.add(self.listbox)

    def postInit(self, ):
        self.layout()
        self.connections()
        self.config()

    def layout(self, ):
        return

    def newPanel(self, description):
        row = Gtk.ListBoxRow()
        panelView = _panelItem.View(self.control)
        panelView.label.set_text(description)
        self.elements.append(panelView)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        row.add(hbox)
        hbox.pack_start(panelView, 1, 1, 0)
        self.listbox.add(row)
        return panelView

    def newDialog(self, character, dialog):
        row = Gtk.ListBoxRow()
        dialogView = _dialogItem.View(self.control)
        dialogView.characterLabel.set_text(character)
        dialogView.dialogLabel.set_text(dialog)
        self.elements.append(dialogView)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        row.add(hbox)
        hbox.pack_start(dialogView, 1, 1, 0)
        self.listbox.add(row)

    def connections(self, ):
        pass
    
    def config(self, ):
        pass

    def state(self):
        # return dictionary
        pass

    def data(self):
        # return dictionary
        pass

    def load(self):
        if len(self.control.stories):
            elements = self.control.currentPage().elements

            for element in elements:
                if element.__class__.__name__=="Panel":
                    self.newPanel(element.description)

                elif element.__class__.__name__=="Dialog":
                    self.newDialog(element.character, element.dialog)
        else:
            self.reset()

    def reset(self):
        self.viewport.remove(self.listbox)
        self.listbox = IndexListBox(self.control)
        self.viewport.add(self.listbox)
        self.elements = []
