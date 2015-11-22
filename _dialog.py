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
        print "row in",  control.sceneItemBox.listbox.get_children()
        control.sceneItemBox.listbox.remove(row)
        if index == len(control.currentSequence().scenes) - 1:
            control.currentSequence().scenes.pop(index)
            control.currentStory().index.scene = index - 1
        else:
            control.currentSequence().scenes.pop(index)

        control.sceneItemBox.updateNumberated()

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
