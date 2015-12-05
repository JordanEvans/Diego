
from gi.repository import Gtk, Gdk

import _pageItem
import _dialog

class IndexListBox(Gtk.ListBox):
    def __init__(self, control):
        Gtk.ListBox.__init__(self)
        self.control = control
        self.reloadControl = True

    def do_key_press_event(self, event):

        if event.state & Gdk.ModifierType.CONTROL_MASK:
            if (event.keyval == 65293): # ctl + enter
                selectedRows = self.get_selected_rows()
                if len(selectedRows) == 1:
                    self.control.newPage(prepend=True)
                return

            elif (event.keyval == 65362): # ctl + up arrow
                selectedRows = self.get_selected_rows()
                if len(selectedRows) == 1:
                    self.control.moveCurrentPageUp()
                return 1

            elif (event.keyval == 65364): # ctl + down arrow
                selectedRows = self.get_selected_rows()
                if len(selectedRows) == 1:
                    self.control.moveCurrentPageDown()
                return 1

        else:

            if event.keyval == 65293:
                selectedRows = self.get_selected_rows()
                rows = self.get_children()
                if len(selectedRows) == 0:
                    return
                elif len(selectedRows) == 1:
                    self.control.newPage()
                else:
                    self.unselect_all()

            elif (event.keyval == 65535): # delete
                selectedRows = self.get_selected_rows()
                rows = self.get_children()
                if len(rows) == 1:
                    return 1

                row = selectedRows[0]
                index = rows.index(row)
                _dialog.deletePageConfirmation(self.control, row, index)
                return 1

            else:
                return 1

    def do_row_selected(self, row):

        if row:
            self.resetAndLoadLowerListBoxes(row)
            self.control.app.window.show_all()

    def do_map(self):
        Gtk.ListBox.do_map(self)
        row = self.get_row_at_index(self.control.currentStory().index.page)

        if row:
            self.resetAndLoadLowerListBoxes(row)
            self.control.scriptView.show_all()
            self.select_row(row)
            row.grab_focus()

    def resetAndLoadLowerListBoxes(self, row):

        self.control.scriptView.reset()

        self.control.currentStory().index.page = self.get_children().index(row)
        self.control.currentStory().index.line = 0

        self.control.scriptView.load()
        self.control.scriptView.loadPage()

        self.control.category = 'page'

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

class PageItemBox(ScrolledListBox):

    def __init__(self, control):
        ScrolledListBox.__init__(self, control)
        self.control = control
        self.pages = []

        # The listbox is subclassed , so it is replaced this object's superclass
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

    def deletePage(self, index):
        self.control.currentStory().deletePage(index)

    def newPage(self):
        row = Gtk.ListBoxRow()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        row.add(hbox)
        pageView = _pageItem.View(self.control)
        self.pages.append(pageView)
        hbox.pack_start(pageView, 1, 1, 0)
        self.listbox.add(row)

    def state(self):
        pass

    def data(self):
        pass

    def load(self):
        print "pload"
        if len(self.control.stories):
            pages = self.control.currentScene().pages
            for i in range(len(pages)):
                self.newPage()
            dataPages = self.control.currentScene().pages
            for pgNumber in range(len(self.pages)):
                self.pages[pgNumber].label.set_text(dataPages[pgNumber].title)

        else:
            self.reset()

        # row = self.rowAtIndex(0)
        # self.listbox.select_row(row)

    def reset(self):
        for row in self.listbox.get_children():
            self.listbox.remove(row)
        self.pages = []

    def updateNumberated(self):
        self.control.scriptView.updateTitles()
        self.reset()
        self.load()
        self.show_all()
        self.loadPageAtIndex()

    def loadPageAtIndex(self, index=None):

        if index == None:
            cp = self.control.currentPage()
            index = self.control.currentScene().pages.index(cp)

        row = self.control.pageItemBox.listbox.get_row_at_index(index)

        self.control.pageItemBox.listbox.resetAndLoadLowerListBoxes(row)

        if row:
            self.control.pageItemBox.listbox.select_row(row)
            row.grab_focus()

    def rowAtIndex(self, index):
        return self.listbox.get_row_at_index(index)
