
from gi.repository import Gtk, Gdk

import _sequenceItem

class IndexListBox(Gtk.ListBox):
    def __init__(self, control):
        Gtk.ListBox.__init__(self)
        self.control = control
        self.reloadControl = True
        self.editing = False

    def do_button_press_event(self, event):
        if not self.editing:
            if event.type != Gdk.EventType._2BUTTON_PRESS:
                Gtk.ListBox.do_button_press_event(self, event)

    def do_key_press_event(self, event):

        if event.state & Gdk.ModifierType.CONTROL_MASK:
            if (event.keyval == 51): # pound
                self.control.sequenceItemBox.toggleNumerated()
                return
            elif (event.keyval == 65293): # ctl + enter
                selectedRows = self.get_selected_rows()
                if len(selectedRows) == 1:
                    self.control.newSequence(prepend=True)
                return

            elif (event.keyval == 65362): # ctl + up arrow
                selectedRows = self.get_selected_rows()
                if len(selectedRows) == 1:
                    self.control.moveCurrentSequenceUp()
                return 1

            elif (event.keyval == 65364): # ctl + down arrow
                selectedRows = self.get_selected_rows()
                if len(selectedRows) == 1:
                    self.control.moveCurrentSequenceDown()
                return 1

        else:

            if event.keyval == 65293:
                selectedRows = self.get_selected_rows()
                if len(selectedRows) == 0:
                    return
                elif len(selectedRows) == 1:
                    self.control.newSequence()
                else:
                    self.unselect_all()
            else:
                return 1

    def do_row_selected(self, row):
        if row:
            self.resetAndLoadLowerListBoxes(row)
            self.control.app.window.show_all()

    def do_map(self):
        Gtk.ListBox.do_map(self)
        row = self.get_row_at_index(self.control.currentStory().index.sequence)

        self.resetAndLoadLowerListBoxes(row)
        self.control.scriptView.show_all()

        if row:
            self.select_row(row)
            row.grab_focus()

    def resetAndLoadLowerListBoxes(self, row):

        self.control.sceneItemBox.reset()
        self.control.pageItemBox.reset()
        self.control.scriptView.reset()

        self.control.currentStory().index.sequence = self.get_children().index(row)
        self.control.currentStory().index.scene = 0
        self.control.currentStory().index.page = 0
        self.control.currentStory().index.page = 0

        self.control.sceneItemBox.load()
        self.control.pageItemBox.load()
        self.control.scriptView.load()
        self.control.scriptView.loadSequence()
        self.control.category = 'sequence'

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

class SequenceItemBox(ScrolledListBox):

    def __init__(self, control):
        ScrolledListBox.__init__(self, control)
        self.control = control
        self.sequences = []
        self.numerated = True
        self.editing = False

        self.viewport.remove(self.listbox)
        self.listbox = IndexListBox(self.control)
        self.viewport.add(self.listbox)
        
    def postInit(self, ):
        self.layout()
        self.connections()
        self.config()
        
    def layout(self, ):
        pass

    def connections(self, ):
        pass

    def keyPress(self, widget, event):
        pass

    def config(self, ):
        pass

    def deleteSequence(self, index):
        self.control.currentStory().deleteSequence(index)

    def newSequence(self):
        row = Gtk.ListBoxRow()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        row.add(hbox)
        sequenceView = _sequenceItem.View(self.control)
        self.sequences.append(sequenceView)
        hbox.pack_start(sequenceView, 1, 1, 0)
        self.listbox.add(row)

    def state(self):
        # return dictionary
        pass

    def data(self):
        # return dictionary
        pass

    def load(self):
        if len(self.control.stories):
            for sequence in self.control.currentStory().sequences:
                self.newSequence()

            dataSequences = self.control.currentStory().sequences

            prefix = ''
            for sequenceNumber in range(len(self.sequences)):
                if self.numerated:
                    prefix = str(sequenceNumber + 1) + '.  '
                self.sequences[sequenceNumber].label.set_text(prefix + dataSequences[sequenceNumber].title)

    def reset(self):
        for row in self.listbox.get_children():
            self.listbox.remove(row)
        self.sequences = []

    def toggleNumerated(self):
        self.numerated = not self.numerated
        self.reset()
        self.load()
        self.show_all()
        self.loadSequenceAtIndex()

    def loadSequenceAtIndex(self, index=None):

        if index == None:
            cs = self.control.currentSequence()
            index = self.control.currentStory().sequences.index(cs)

        row = self.control.sequenceItemBox.listbox.get_row_at_index(index)

        self.control.sequenceItemBox.listbox.resetAndLoadLowerListBoxes(row)

        if row:
            self.control.sequenceItemBox.listbox.select_row(row)
            row.grab_focus()

    def editCurrentTitle(self):
        if self.editing == False:
            self.editing = True
            selectedRow = self.listbox.get_selected_row()
            child = selectedRow.get_child()
            view = child.get_children()[0]
            view.startEditMode()