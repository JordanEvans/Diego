
from gi.repository import Gtk, Gdk

import _storyItem

class IndexListBox(Gtk.ListBox):
    def __init__(self, control):
        Gtk.ListBox.__init__(self)
        self.control = control
        self.editing = False

    def do_button_press_event(self, event):
        self.editing = False
        Gtk.ListBox.do_button_press_event(self, event)
        type = event.type
        if type == Gdk.EventType._2BUTTON_PRESS and not self.control.sceneItemBox.editing:
            self.editing = True

    def do_button_release_event(self, event):
        self.control.p("dbr", self.editing)
        Gtk.ListBox.do_button_release_event(self, event)
        if self.editing:
            self.control.storyItemBox.editCurrentTitle()

    def do_key_press_event(self, event):

        if event.state & Gdk.ModifierType.CONTROL_MASK:

            if (event.keyval == 51): # pound
                self.control.storyItemBox.toggleNumerated()
                return
        else:

            if (event.keyval == 65535):
                self.control.storyItemBox.deleteItem()

            elif event.keyval == 65293:
                selectedRows = self.get_selected_rows()
                if len(selectedRows) == 0:
                    return
                elif len(selectedRows) == 1:
                    self.control.newStory()
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
        row = self.get_row_at_index(self.control.index)

        self.resetAndLoadLowerListBoxes(row)

        self.control.scriptView.show_all()

        if row:
            self.select_row(row)
            row.grab_focus()

    def resetAndLoadLowerListBoxes(self, row):

        print "resetAndLoadLowerListBoxes"

        self.control.sequenceItemBox.reset()
        self.control.sceneItemBox.reset()
        self.control.pageItemBox.reset()
        self.control.scriptView.reset()

        self.control.index = self.get_children().index(row)
        self.control.currentStory().index.sequence = 0
        self.control.currentStory().index.scene = 0
        self.control.currentStory().index.page = 0
        self.control.currentStory().index.line = 0

        self.control.sequenceItemBox.load()
        self.control.sceneItemBox.load()
        self.control.pageItemBox.load()
        self.control.scriptView.load()
        self.control.scriptView.loadStory()
        self.control.scriptView.updateTitles()
        self.control.category = 'story'
        self.control.app.updateWindowTitle()

        print self.control.currentStory().title, self.control.currentStory().names
        self.control.currentStory().updateCompletionNames()

        self.control.scriptView.paned.set_position(self.control.currentStory().horizontalPanePosition)

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

class StoryItemBox(ScrolledListBox):

    def __init__(self, control):
        ScrolledListBox.__init__(self, control)
        self.control = control
        self.items = []
        self.numerated = False
        self.editing = False

        # The listbox is subclassed , so it is replaced this object's superclass
        self.viewport.remove(self.listbox)
        self.listbox = IndexListBox(self.control)
        self.viewport.add(self.listbox)

    def postInit(self, ):
        self.layout()
        self.connections()
        self.config()
        # self.show_all()

    def layout(self, ):
        pass

    def connections(self, ):
        pass

    def deleteItem(self):
        cs = self.control.currentStory()
        index = self.control.stories.index(cs)
        if len(self.items) > 1:
            self.items.pop(index)
            self.control.stories.pop(index)
            self.reset()
            self.load()
            self.show_all()

            if index == 0 or len(self.items) == 1:
                rowIndex = 0
            else:
                if len(self.items) == index:
                    rowIndex = index - 1
                else:
                    rowIndex = index

            self.loadStoryAtIndex(rowIndex)

    def loadStoryAtIndex(self, index=None):

        if index == None:
            cs = self.control.currentStory()
            index = self.control.stories.index(cs)

        row = self.control.storyItemBox.listbox.get_row_at_index(index)

        self.control.storyItemBox.listbox.resetAndLoadLowerListBoxes(row)

        if row:
            self.control.storyItemBox.listbox.select_row(row)
            row.grab_focus()

    def config(self, ):
        pass

    def deleteStory(self, index):
        self.control.currentStory().deleteStory(index)

    def newStoryItem(self):
        row = Gtk.ListBoxRow()
        storyView = _storyItem.View(self.control)
        row.add(storyView)
        self.items.append(storyView)
        self.listbox.add(row)

    def state(self):
        # return dictionary
        pass

    def data(self):
        # return dictionary
        pass

    def load(self):
        for story in self.control.stories:
            self.newStoryItem()
            
        dataStories = self.control.stories
        prefix = ''
        for storyNumber in range(len(self.items)):
            if self.numerated:
                prefix = str(storyNumber + 1) + '.  '
            self.items[storyNumber].label.set_text(prefix + dataStories[storyNumber].title)
        
        self.listbox.unselect_all()

    def reset(self):
        for row in self.listbox.get_children():
            self.listbox.remove(row)
        self.items = []

    def updateStoryLabelAtIndex(self, index):
        self.items[index].label.set_text(self.control.stories[index].title)

    def loadStoryAtIndex(self, index=None):

        if index == None:
            cs = self.control.currentStory()
            index = self.control.stories.index(cs)

        row = self.control.storyItemBox.listbox.get_row_at_index(index)

        self.control.storyItemBox.listbox.resetAndLoadLowerListBoxes(row)

        if row:
            self.control.storyItemBox.listbox.select_row(row)
            row.grab_focus()

    def toggleNumerated(self):
        self.numerated = not self.numerated
        self.reset()
        self.load()
        self.show_all()
        self.loadStoryAtIndex()

    def editCurrentTitle(self):
        if self.editing == False:
            self.editing = True
            selectedRow = self.listbox.get_selected_row()
            child = selectedRow.get_child()
            child.startEditMode()