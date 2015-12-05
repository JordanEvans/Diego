
from gi.repository import Gtk, Gdk

import _sceneItem
import _dialog

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
                self.control.sceneItemBox.toggleNumerated()
                return

            elif (event.keyval == 65293): # ctl + enter
                selectedRows = self.get_selected_rows()
                if len(selectedRows) == 1:
                    self.control.newScene(prepend=True)
                return

            elif (event.keyval == 65362): # ctl + up arrow
                selectedRows = self.get_selected_rows()
                if len(selectedRows) == 1:
                    self.control.moveCurrentSceneUp()
                return 1

            elif (event.keyval == 65364): # ctl + down arrow
                selectedRows = self.get_selected_rows()
                if len(selectedRows) == 1:
                    self.control.moveCurrentSceneDown()
                return 1

        else:

            if event.keyval == 65293:
                selectedRows = self.get_selected_rows()
                if len(selectedRows) == 0:
                    return
                elif len(selectedRows) == 1:
                    self.control.newScene()
                else:
                    self.unselect_all()

            elif (event.keyval == 65535): # delete
                selectedRows = self.get_selected_rows()
                rows = self.get_children()
                if len(rows) == 1:
                    return 1

                if len(selectedRows):
                    row = selectedRows[0]
                    index = rows.index(row)
                    _dialog.deleteSceneConfirmation(self.control, row, index)
                return 1

            else:
                return 1

    def do_row_selected(self, row):
        if row:
            self.resetAndLoadLowerListBoxes(row)
            self.control.app.window.show_all()

    def do_map(self):
        Gtk.ListBox.do_map(self)
        row = self.get_row_at_index(self.control.currentStory().index.scene)

        self.resetAndLoadLowerListBoxes(row)
        self.control.scriptView.show_all()

        if row:
            self.select_row(row)
            row.grab_focus()

    def resetAndLoadLowerListBoxes(self, row):

        self.control.pageItemBox.reset()
        self.control.scriptView.reset()

        currentStory = self.control.currentStory()

        currentStory.index.scene = self.get_children().index(row)
        currentStory.index.page = 0
        currentStory.index.line = 0

        self.control.pageItemBox.load()
        self.control.scriptView.load()
        self.control.scriptView.loadScene()

        currentStory.updateCompletionNames()

        self.control.category = 'scene'

        #Model index was set to 0, so the listboxes will select zero items.
        row = self.control.pageItemBox.rowAtIndex(0)
        self.control.pageItemBox.listbox.select_row(row)

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

class SceneItemBox(ScrolledListBox):

    def __init__(self, control):
        ScrolledListBox.__init__(self, control)
        self.control = control
        self.scenes = []
        self.numerated = True
        self.editing = False

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

    # def deleteScene(self, index):
    #     _dialog.deleteSceneConfirmation(self.control, index)

    def newScene(self):
        row = Gtk.ListBoxRow()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        row.add(hbox)
        sceneView = _sceneItem.View(self.control)
        self.scenes.append(sceneView)
        hbox.pack_start(sceneView, 1, 1, 0)
        self.listbox.add(row)

    def state(self):
        # return dictionary
        pass

    def data(self):
        # return dictionary
        pass

    def load(self):
        if len(self.control.stories):
            for scene in self.control.currentSequence().scenes:
                self.newScene()

            dataScenes = self.control.currentSequence().scenes

            prefix = ''
            for sceneNumber in range(len(self.scenes)):
                if self.numerated:
                    prefix = str(sceneNumber + 1) + '.  '
                self.scenes[sceneNumber].label.set_text(prefix + dataScenes[sceneNumber].title)

        # row = self.rowAtIndex(0)
        # self.listbox.select_row(row)
        #
        # row = self.control.pageItemBox.rowAtIndex(0)
        # self.control.pageItemBox.listbox.select_row(row)

    def reset(self):
        for row in self.listbox.get_children():
            self.listbox.remove(row)
        self.scenes = []

    def toggleNumerated(self):
        self.numerated = not self.numerated
        self.reset()
        self.load()
        self.show_all()
        self.loadSceneAtIndex()

    def updateNumberated(self):
        if self.numerated:
            self.reset()
            self.load()
            self.show_all()
            self.loadSceneAtIndex()

    def loadSceneAtIndex(self, index=None):

        currentStory = self.control.currentStory()

        if index == None:
            cs = self.control.currentScene()
            index = self.control.currentSequence().scenes.index(cs)

        row = self.control.sceneItemBox.listbox.get_row_at_index(index)

        self.control.sceneItemBox.listbox.resetAndLoadLowerListBoxes(row)

        if row:
            self.control.sceneItemBox.listbox.select_row(row)
            row.grab_focus()

        currentStory.updateCompletionNames()

    def editCurrentTitle(self):
        if self.editing == False:
            self.editing = True
            selectedRow = self.listbox.get_selected_row()
            child = selectedRow.get_child()
            view = child.get_children()[0]
            view.startEditMode()

    def getSelectedItem(self):
        row = self.listbox.get_selected_row()
        if row:
            rows = self.listbox.get_children()
            if row in rows:
                index = rows.index(row)
                return self.scenes[index]

    def rowAtIndex(self, index):
        return self.listbox.get_row_at_index(index)
