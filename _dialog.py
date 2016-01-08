import os

from gi.repository import Gtk

import _story

class SetAuthorAndContactDialog(Gtk.Dialog):

    def __init__(self, control, parent):
        Gtk.Dialog.__init__(self, "Set Author and Contact", parent, 0, ())
        self.control = control
        self.set_default_size(450, 180)
        self.set_modal(True)
        self.set_title("Set Author and Contact")

        self.connect("destroy", self.exit)

        ca = self.get_content_area()

        vbox = Gtk.VBox()
        ca.add(vbox)

        hbox = Gtk.HBox()
        label = Gtk.Label("Author")
        hbox.pack_start(label, 1, 1, 5)
        vbox.pack_start(hbox, 0, 0, 2)

        hbox = Gtk.HBox()
        self.authorEntry = Gtk.Entry()
        hbox.pack_start(self.authorEntry, 1, 1, 5)
        vbox.pack_start(hbox, 0, 0, 2)

        hbox = Gtk.VBox()
        label = Gtk.Label("Contact Info")
        hbox.pack_start(label, 0, 0, 5)
        self.contactTextView = Gtk.TextView()
        hbox.pack_end(self.contactTextView, 0, 0, 5)
        vbox.pack_start(hbox, 1, 1, 2)

        self.load()

        self.show_all()

    def load(self):
        self.authorEntry.set_text(self.control.state.author)
        insertIter = self.contactTextView.get_buffer().get_start_iter()
        self.contactTextView.get_buffer().insert(insertIter, self.control.state.contact)

    def exit(self, arg):
        self.control.state.author = self.authorEntry.get_text()

        startIter = self.contactTextView.get_buffer().get_start_iter()
        endIter = self.contactTextView.get_buffer().get_end_iter()
        text = self.contactTextView.get_buffer().get_text(startIter, endIter, False)
        self.control.state.contact = text

class FindAndReplaceDialog(Gtk.Dialog):

    def __init__(self, control, parent):
        Gtk.Dialog.__init__(self, "Find And Replace", parent, 0, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_FIND_AND_REPLACE, Gtk.ResponseType.APPLY))
        self.control = control
        self.set_default_size(600, 150)
        self.set_modal(True)
        self.set_title("Find And Replace")

        self.findEntry = Gtk.Entry()
        self.replaceEntry = Gtk.Entry()
        self.connect('key-release-event', self.replaceEntryKeyRelease)

        box = Gtk.HBox()
        box.pack_start(self.findEntry, 1, 1, 5)
        box.pack_end(self.replaceEntry, 1, 1, 5)

        ca = self.get_content_area()

        ca.add(box)

        self.show_all()

    def replaceEntryKeyRelease(self, widget, event):
        if (event.keyval == 65293):
            if len(self.findEntry.get_text()) and len(self.replaceEntry.get_text()):
                self.findAndReplace()
            self.destroy()

    def findAndReplace(self):
        self.control.scriptView.textView.forceWordEvent()
        self.control.currentStory().findAndReplace(self.findEntry.get_text(), self.replaceEntry.get_text())
        self.control.scriptView.resetAndLoad()
        self.control.scriptView.textView.show_all()

def saveFile(control):
    dialog = Gtk.FileChooserDialog("Save story", control.app.window,
        Gtk.FileChooserAction.SAVE,
        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
         Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
    dialog.set_current_folder(control.saveDir)

    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        fileName = dialog.get_filename()
        control.currentStory()._save(fileName)
    elif response == Gtk.ResponseType.CANCEL:
        pass

    dialog.destroy()

def chooseBackupDir(control):
    dialog = Gtk.FileChooserDialog("Choose Backup Direcroty", control.app.window,
        Gtk.FileChooserAction.SELECT_FOLDER,
        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
         Gtk.STOCK_APPLY, Gtk.ResponseType.OK))
    dialog.set_current_folder(control.saveDir)

    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        dirName = dialog.get_filename()
        control.state.backupDir = dirName
    elif response == Gtk.ResponseType.CANCEL:
        pass

    dialog.destroy()

def openFile(control):
    dialog = Gtk.FileChooserDialog("Please choose a file", control.app.window,
        Gtk.FileChooserAction.OPEN,
        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
         Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
    dialog.set_current_folder(control.saveDir)

    response = dialog.run()

    for story in control.stories:
        if story.path == dialog.get_filename():
            dialog.destroy()
            infoDialog(control, 'That Story is already open.')
            return

    if response == Gtk.ResponseType.OK:

        if os.path.exists(dialog.get_filename()):
            data = _story.Story(control, dialog.get_filename())
            control.stories.insert(0, data)
            control.index = 0
            data.load()
            control.reset(False)
            control.load(False)
            control.storyItemBox.loadStoryAtIndex(0)

    elif response == Gtk.ResponseType.CANCEL:
        pass

    dialog.destroy()

def unsavedUnamedFile(control):
    dialog = Gtk.MessageDialog(
        control.app.window,
        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        Gtk.MessageType.QUESTION,
        (Gtk.STOCK_YES, Gtk.ResponseType.OK, Gtk.STOCK_NO, Gtk.ResponseType.CANCEL
         ),
        None)

    dialog.set_markup('Would you like to save this document before closing it?')

    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        control.data.save()
    elif response == Gtk.ResponseType.CANCEL:
        pass

    dialog.destroy()

def unsavedFiles(control):
    dialog = Gtk.MessageDialog(
        control.app.window,
        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        Gtk.MessageType.QUESTION,
        (Gtk.STOCK_YES, Gtk.ResponseType.OK, Gtk.STOCK_NO, Gtk.ResponseType.CANCEL
         ),
        None)

    dialog.set_markup('Would you like to save your work before exiting?')

    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        control.app.saveUnsavedStories = True

    elif response == Gtk.ResponseType.CANCEL:
        control.app.cancelShutdown = False

    dialog.destroy()

def deleteSceneConfirmation(control, row, index):
    dialog = Gtk.MessageDialog(
        control.app.window,
        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        Gtk.MessageType.QUESTION,
        (Gtk.STOCK_YES, Gtk.ResponseType.OK, Gtk.STOCK_NO, Gtk.ResponseType.CANCEL
         ),
        None)

    dialog.set_markup('Confirm you want to delete this Scene?')

    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        control.sceneItemBox.listbox.remove(row)

        if index == len(control.currentSequence().scenes) - 1:
            control.currentStory().index.scene = index - 1

        control.currentSequence().scenes[index].archiveManager.clear()
        control.currentSequence().scenes.pop(index)

        # control.sceneItemBox.updateNumberated()

        control.reset(data=False)
        control.scriptView.updateTitles()
        control.load(data=False)
        index = control.currentStory().index.scene
        control.sceneItemBox.listbox.get_row_at_index(index).grab_focus()
        control.sceneItemBox.listbox.select_row(control.sceneItemBox.listbox.get_row_at_index(index))

    elif response == Gtk.ResponseType.CANCEL:
        pass

    dialog.destroy()

def deletePageConfirmation(control, row, index):
    dialog = Gtk.MessageDialog(
        control.app.window,
        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        Gtk.MessageType.QUESTION,
        (Gtk.STOCK_YES, Gtk.ResponseType.OK, Gtk.STOCK_NO, Gtk.ResponseType.CANCEL
         ),
        None)

    dialog.set_markup('Confirm you want to delete this Page?')

    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        control.pageItemBox.listbox.remove(row)
        if index == len(control.currentScene().pages) - 1:
            control.currentScene().pages.pop(index)
            control.currentStory().index.page = index - 1
        else:
            control.currentScene().pages.pop(index)

        control.pageItemBox.updateNumberated()

    elif response == Gtk.ResponseType.CANCEL:
        pass

    dialog.destroy()

def infoDialog(control, info=''):
    dialog = Gtk.MessageDialog(
        control.app.window,
        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        Gtk.MessageType.INFO,
        (Gtk.STOCK_OK, Gtk.ResponseType.OK),
        None)

    dialog.set_markup(info)
    dialog.run()
    dialog.destroy()

def infoDialog2(info=''):
    dialog = Gtk.MessageDialog(
        None,
        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        Gtk.MessageType.INFO,
        (Gtk.STOCK_OK, Gtk.ResponseType.OK),
        None)

    dialog.set_markup(info)
    dialog.run()
    dialog.destroy()
