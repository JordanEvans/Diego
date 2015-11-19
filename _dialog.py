import os

from gi.repository import Gtk

import _story

def saveFile(control):
    dialog = Gtk.FileChooserDialog("Save story", control.app.window,
        Gtk.FileChooserAction.SAVE,
        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
         Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
    dialog.set_current_folder(control.saveDir)

    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        control.currentStory()._save(dialog.get_filename())
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

