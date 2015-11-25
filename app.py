import sys
import os

from gi.repository import Gtk

from _control import Control

import _dialog
import _clipboard


class App(object):

    def __init__(self):
        print "PyGtk Version", Gtk.MAJOR_VERSION, Gtk.MINOR_VERSION, Gtk.MICRO_VERSION
        self.name = "Diego"
 
        self.control = Control(self)

        self.control.appClipboard = _clipboard.AppClipboard(self.control)
        self.control.sysClipboard = _clipboard.SysClipboard(self.control)

        self.control.copyClipboard = _clipboard.Clipboard(self.control)
        self.control.selectionClipboard = _clipboard.Clipboard(self.control)
        self.control.dragDropCutClipboard = _clipboard.Clipboard(self.control)

        self.control.postInit()

        self.window.postInit()  

        self.control.appBox.postInit()
        self.control.pageItemBox.postInit()
        self.control.sceneItemBox.postInit()
        self.control.sequenceItemBox.postInit()
        self.control.scriptView.postInit()
        self.control.storyItemBox.postInit()

        self.control.indexView.postInit()

        self.control.load()

        self.window.resize_to_geometry(self.control.state.width, self.control.state.height)
        self.control.scriptView.textView.resetTags()
        self.control.scriptView.infoTextView.props.left_margin = self.control.scriptView.textView.descriptionLeftMargin
        self.control.scriptView.infoTextView.props.right_margin = self.control.scriptView.textView.descriptionRightMargin

    def updateWindowTitle(self):

        try:
            title = os.path.split(self.control.currentStory().path)[-1] + " - Diego"
        except:
            title = "Diego"

        self.window.set_title(title)

    def open(self):
        pass

    def close(self):
        pass

    def reset(self):
        pass

    def shutdown(self, window=None, event=None):
        self.cancelShutdown = False
        self.shutdownUnsavedFileCheck()
        if not self.cancelShutdown:
            self.control.state.shutdown()
            sys.exit()

    def shutdownUnsavedFileCheck(self):
        return
        self.saveUnsavedStories = False
        unsavedStories = False
        for story in self.control.stories:
            if not story.saved:
                unsavedStories = True
                break

        if unsavedStories:
            _dialog.unsavedFiles(self.control)

        if self.cancelShutdown:
            return

        elif unsavedStories and self.saveUnsavedStories:
            for story in self.control.stories:
                if not story.saved:
                    story.save()

    def unsavedFileCheck(self):
        for story in self.control.stories:
            if not story.saved:
                story.save()

if __name__ == "__main__":
    app = App()
    Gtk.main()
