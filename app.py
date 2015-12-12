import sys
import os, string

from gi.repository import Gtk

from _control import Control

import _dialog

class App(object):

    def __init__(self):
        # The whole app is initialized and brought up here.

        print "PyGtk Version", Gtk.MAJOR_VERSION, Gtk.MINOR_VERSION, Gtk.MICRO_VERSION
        self.name = "Diego"

        # Control's purpose is to connect everything. Control.__init__ contains app-wide variables
        # for the pupose of shorten variable indirection during implementation.
        self.control = Control(self)

        # Creates Data and Widgets
        # self.control.postInit()

        # Configures and packs Widgets.
        self.window.postInit()
        self.control.appBox.postInit()
        self.control.pageItemBox.postInit()
        self.control.sceneItemBox.postInit()
        self.control.sequenceItemBox.postInit()
        self.control.scriptView.postInit()
        self.control.storyItemBox.postInit()
        self.control.indexView.postInit()

        # Now that Data and View objects have been created and packed,
        # control.load will load the data into the views. No arg is passed here,
        # but control.state may provide stories to load,
        # if app was previously opened and stories were made.

        self.control.load()

        # Some misc follow up stuff.
        try:
            self.window.resize_to_geometry(self.control.state.width, self.control.state.height)
        except:
            self.window.resize_to_geometry(600, 400)

        self.control.scriptView.textView.resetTags()
        self.control.scriptView.infoTextView.props.left_margin = self.control.scriptView.textView.descriptionLeftMargin
        self.control.scriptView.infoTextView.props.right_margin = self.control.scriptView.textView.descriptionRightMargin

        try:
            self.control.app.window.move(self.control.windowPosition[0], self.control.windowPosition[1])
        except:
            pass

        try:
            self.loadTrie()
        except:
            print "spellcheck not active"

        pass

    def loadTrie(self):
        import marisa_trie

        path = '/usr/share/dict/american-english'
        f = open(path, 'r')

        words = f.read().split('\n') + list(string.punctuation) + [' ']

        wordList = [unicode(word, 'utf-8') for word in words]

        self.control.trie = marisa_trie.Trie(wordList)

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
