import sys
import os
import string
import fcntl

from gi.repository import Gtk, GObject, Gdk

from _control import Control

import _dialog

class App(object):

    def __init__(self):
        # The whole app is initialized and brought up here.

        print "PyGtk Version", Gtk.MAJOR_VERSION, Gtk.MINOR_VERSION, Gtk.MICRO_VERSION
        self.name = "Diego"

        # Control's purpose is to connect everything. Control.__init__ contains app-wide variables
        # for the pupose of short variable indirection during implementation.
        self.control = Control(self)

        # Creates Data and Widgets
        # self.control.postInit()

        self.control.state.load()

        # Configures and packs Widgets.
        self.window.postInit()

        self.window.resize(self.control.state.width, self.control.state.height)

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

        self.control.scriptView.textView.resetTags()
        # self.control.scriptView.infoTextView.props.left_margin = self.control.scriptView.textView.descriptionLeftMargin
        # self.control.scriptView.infoTextView.props.right_margin = self.control.scriptView.textView.descriptionRightMargin

        try:
            self.control.app.window.move(self.control.windowPosition[0], self.control.windowPosition[1])
        except:
            pass

        try:
            self.loadTrie()
            self.loadAddWordTrie()
            self.loadRemoveWordTrie()
            self.control.scriptView.textView.completionManager.trie = self.control.trie
        except:
            print "spellcheck not active"

        self.control.category = self.control.state.lastCategory
        self.control.indexView.stack.set_visible_child_name(self.control.state.lastCategory)

        if self.control.state.lastSelection[0] is not None:
            self.control.timedSelect(self.control.state.lastSelection[0], self.control.state.lastSelection[1], 100)

        self.timedFontReset()
        # self.timedScroll() # not working

    def timedFontReset(self):
        a = Gdk.Rectangle(self.control.windowPosition[0], self.control.windowPosition[1], self.control.state.width, self.control.state.height)
        # This may need to be larger than the scroll time, not sure entirely what the bug is.
        GObject.timeout_add(1000, self.control.scriptView.textView.do_size_allocate, a)

    def timedScroll(self):
        GObject.timeout_add(500, self.scroll)

    def scroll(self):

        if self.control.state.lastStoryIndex.story > len(self.control.stories) - 1:
            self.control.state.lastStoryIndex.story = 0
            self.control.state.lastStoryIndex.scene = 0
            self.control.state.lastStoryIndex.page = 0
            self.control.state.lastStoryIndex.line = 0
            self.control.state.lastStoryIndex.offset = 0
        story = self.control.stories[self.control.state.lastStoryIndex.story]

        sequence = story.sequences[0]

        if self.control.state.lastStoryIndex.scene > len(sequence.scenes) - 1:
            self.control.state.lastStoryIndex.scene = 0
            self.control.state.lastStoryIndex.page = 0
            self.control.state.lastStoryIndex.line = 0
            self.control.state.lastStoryIndex.offset = 0
        scene = sequence.scenes[self.control.state.lastStoryIndex.scene]

        if self.control.state.lastStoryIndex.page > len(scene.pages) - 1:
            self.control.state.lastStoryIndex.page = 0
            self.control.state.lastStoryIndex.line = 0
            self.control.state.lastStoryIndex.offset = 0
        page = scene.pages[self.control.state.lastStoryIndex.page]

        if self.control.state.lastStoryIndex.line > len(page.lines) - 1:
            self.control.state.lastStoryIndex.line = 0
            self.control.state.lastStoryIndex.offset = 0
        line = page.lines[self.control.state.lastStoryIndex.line]

        if self.control.state.lastStoryIndex.offset > len(line.text) - 1:
            self.control.state.lastStoryIndex.offset = 0
        offset = self.control.state.lastStoryIndex.offset

        if line in self.control.scriptView.lines:
            lineIndex = self.control.scriptView.lines.index(line)

            # self.control.p("scroll line", line.text, lineIndex)

            scrollIter = self.control.scriptView.textView.iterAtLocation(lineIndex, offset)
            scrollMark = self.control.scriptView.textView.iterMark(scrollIter)
            self.control.scriptView.textView.scroll_to_mark(scrollMark, 0.1, False, 0.0, 0.0)


    def select(self):
        if self.control.state.lastSelection[0] is not None:
            self.control.timedSelect(self.control.state.lastSelection[0], self.control.state.lastSelection[1], 500)

    def loadTrie(self):
        import marisa_trie
        path = '/usr/share/dict/american-english'
        f = open(path, 'r')
        words = f.read().split('\n') + list(string.punctuation) + [' ']
        wordList = [unicode(word, 'utf-8') for word in words]
        self.control.trie = marisa_trie.Trie(wordList)

        self.loadAddWordTrie()
        self.control.remove = marisa_trie.Trie()

    def loadAddWordTrie(self):
        import marisa_trie
        f = open(self.control.addWordPath, 'r')
        words = f.read().split('\n')
        wordList = [unicode(word, 'utf-8') for word in words]
        self.control.addTrie = marisa_trie.Trie(wordList)

    def loadRemoveWordTrie(self):
        import marisa_trie
        f = open(self.control.removeWordPath, 'r')
        words = f.read().split('\n')
        wordList = [unicode(word, 'utf-8') for word in words]
        self.control.removeTrie = marisa_trie.Trie(wordList)

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

        if self.control.state.backupDir and not os.path.exists(self.control.state.backupDir):
            _dialog.infoDialog(self.control, "Your backup directory cannot be found:\n\n" + self.control.state.backupDir)

        self.control.currentStory().save()

        for story in self.control.stories:
            if not story.saved:
                story.save()
            story.close()

        return

    def unsavedFileCheck(self):
        for story in self.control.stories:
            if not story.saved:
                story.save()

if __name__ == "__main__":

    pid_file = 'program.pid'
    fp = open(pid_file, 'w')
    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        _dialog.infoDialog2("Diego is already running.")
        sys.exit(0)

    app = App()
    Gtk.main()
