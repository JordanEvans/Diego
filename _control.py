
import os

from gi.repository import Gtk, GObject, Gdk

# app
import _appWindow
import _search
import _screenplayModeSwitch
import _event

# data
from _config import Config
from _state import State
from _story import Story
from _preferences import Preferences

import _clipboard

# views
from _appBox import AppBox
from _indexView import IndexView
from _pageItemBox import PageItemBox
from _sceneItemBox import SceneItemBox
from _sequenceItemBox import SequenceItemBox
# from _scriptItemBox import ScriptItemBox
from _script import ScriptView

from _storyItemBox import StoryItemBox

# import _input

class Control(object):

    def __init__(self, app):

        # Data objects
        self.app = app
        self.stories = []
        self.index = 0
        self.historyEnabled = False
        self.printCount = 0
        self.category = 'sequence'
        self.saveDir = os.path.realpath(os.curdir) + '/Stories/'
        self.verticalPanePosition = 150
        self.startingUpApp = True
        self.sequenceVisible = False
        self.testingTags = True
        self.updateNamesGlobally = True
        self.eventManager = _event.EventManager(self)

        self.addWordPath = os.path.expanduser(('~')) + '/.config/diego/addedWords'
        self.removeWordPath = os.path.expanduser(('~')) + '/.config/diego/removeWords'

        self.config = Config(self)
        self.preferences = Preferences(self)
        self.state = State(self)
        self.copyClipboard = _clipboard.Clipboard(self)
        self.selectionClipboard = _clipboard.Clipboard(self)

        # View objects
        self.app.window = _appWindow.Window(self)
        self.appBox = AppBox(self)
        self.panelLabel = Gtk.Label()
        self.indexView = IndexView(self)
        self.pageItemBox = PageItemBox(self)
        self.sceneItemBox = SceneItemBox(self)
        self.sequenceItemBox = SequenceItemBox(self)
        self.storyItemBox = StoryItemBox(self)
        self.scriptView = ScriptView(self)
        self.appHeaderBar = Gtk.HeaderBar()
        self.headerBar = Gtk.HeaderBar()
        self.pathLabel = Gtk.Label()
        self.searchView = _search.View(self)
        self.screenplayModeSwitch = _screenplayModeSwitch.Switch(self)

        self.doMarkSetIndexUpdate = True

        self.trie = None
        self.auxTries = []
        self.mispelledLine = None
        self.addTrie = None
        self.removeTrie = None

        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

    def mispelledTimer(self):
        GObject.timeout_add(1000, self.removeMispelledTags)

    def removeMispelledTags(self):
        if self.mispelledLine:
            try:
                index = self.scriptView.lines.index(self.mispelledLine)
            except:
                self.mispelledLine = None
            else:
                self.scriptView.textView.updateLineTag(index)
                self.mispelledLine = None

    def wordMispelled(self, word):

        word = unicode(word)

        # If word comes in in all lower, then it must be in the dict as all lower or it's mispelled.
        allLower = True
        for c in word:
            if not c.islower():
                allLower = False

        if allLower:
            if word not in self.trie and word not in self.addTrie:
                return True

            if word in self.removeTrie:
                return True

            return False

        # The dict does not contain uppercase version of words, the capitalized version will be checked. All upper will be check as well for screenplay character names, locations and times.

        lower = word.lower()
        capitalized = word[0].upper()
        if len(word) > 1:
            capitalized += word[1:].lower()

        lower = unicode(lower)
        capitalized = unicode(capitalized)

        notInTrie = word not in self.trie and lower not in self.trie and capitalized not in self.trie
        notInAddTrie = word not in self.addTrie and lower not in self.addTrie and capitalized not in self.addTrie

        if notInTrie and notInAddTrie:
            return True

        if word in self.removeTrie or lower in self.removeTrie or capitalized in self.removeTrie:
            return True

        return False

    def notImplemented(self):
        print "not implemented"

    def p(self, *args):
        self.printCount += 1
        print self.printCount, args

        raiseException = 0
        if raiseException == self.printCount:
            raise Exception()

    def load(self, data=True):
        self.historyEnabled = False

        if data:
            self.config.load()
            self.preferences.load()

            self.state.load()

            for story in self.stories:
                story.load()

            self.scriptView.updateTitles()

        self.appBox.load()

        self.indexView.load()
        self.storyItemBox.load()
        self.sequenceItemBox.load()
        self.sceneItemBox.load()
        self.pageItemBox.load()
        self.scriptView.load()

        self.app.updateWindowTitle()

        for story in self.stories:
            self.scriptView.updateTitles(story)

        self.app.window.show_all()
        self.startingUpApp = False

        self.appBox.paned.set_position(self.verticalPanePosition)
        self.scriptView.paned.set_position(self.currentStory().horizontalPanePosition)

        self.historyEnabled = True

    def reset(self, data=True):
        if data:
            self.config.reset()
            self.preferences.reset()
            self.stories = []
            self.index = 0
            self.historyEnabled = False
            self.state.reset()

        self.appBox.reset()

        self.indexView.reset()
        self.pageItemBox.reset()
        self.sceneItemBox.reset()
        self.sequenceItemBox.reset()
        self.storyItemBox.reset()

        self.scriptView.reset()

    def currentStory(self):
        if len(self.stories):
            return self.stories[self.index]
        else:
            return None

    def currentIssue(self):
        pass

    def currentSequence(self):
        return self.currentStory().currentSequence()

    def currentScene(self):
        return self.currentStory().currentScene()

    def currentPage(self):
        return self.currentStory().currentPage()

    def currentLine(self):
        return self.currentStory().currentLine()

    def currentPanel(self):
        cp = self.currentPage()
        cl = self.currentLine()
        panelNumber = 0
        for line in cp.lines:
            if line.tag == 'description':
                panelNumber += 1
            if line == cl:
                break
        return panelNumber

    def storyPaths(self):
        return [story.path for story in self.stories]

    def newStory(self):
        story = Story(self)
        story.load()
        story.saved = False
        self.index +=1
        self.stories.insert(self.index, story)
        self.reset(data=False)
        self.scriptView.updateTitles()
        self.load(data=False)
        self.storyItemBox.listbox.get_row_at_index(self.index).grab_focus()
        self.storyItemBox.listbox.select_row(self.storyItemBox.listbox.get_row_at_index(self.index))

    def newSequence(self, prepend=False):
        self.currentStory().newSequence(prepend)
        self.reset(data=False)
        self.scriptView.updateTitles()
        self.load(data=False)
        index = self.currentStory().index.sequence
        self.sequenceItemBox.listbox.get_row_at_index(index).grab_focus()
        self.sequenceItemBox.listbox.select_row(self.sequenceItemBox.listbox.get_row_at_index(index))

    def newScene(self, prepend=False):
        self.currentStory().newScene(prepend)
        self.reset(data=False)
        self.scriptView.updateTitles()
        self.load(data=False)
        index = self.currentStory().index.scene
        self.sceneItemBox.listbox.get_row_at_index(index).grab_focus()
        self.sceneItemBox.listbox.select_row(self.sceneItemBox.listbox.get_row_at_index(index))

    def newPage(self, prepend=False):
        self.currentStory().newPage(prepend)
        self.reset(data=False)
        self.scriptView.updateTitles()
        self.load(data=False)
        index = self.currentStory().index.page
        self.pageItemBox.listbox.get_row_at_index(index).grab_focus()
        self.pageItemBox.listbox.select_row(self.pageItemBox.listbox.get_row_at_index(index))

    def newPanel(self):
        self.currentStory().newPanel()
        self.reset(data=False)
        self.load(data=False)

    def newDialog(self):
        self.currentStory().newDialog()
        self.reset(data=False)
        self.load(data=False)

    def moveCurrentSequenceUp(self):
        self.p('mcsu')

    def moveCurrentSequenceDown(self):
        self.p('mcsd')

    def moveCurrentSceneUp(self):
        self.p('mcscu')

    def moveCurrentSceneDown(self):
        self.p('mcscd')

    def moveCurrentPageUp(self):
        self.p('mcpu')

    def moveCurrentPageDown(self):
        self.p('mcpd')

    def screenplayMode(self):
        return self.screenplayModeSwitch.get_active()

    def updateColor(self):
        val = 0.94
        selectColor = Gdk.RGBA(0.75, 0.75, 0.85, 1.0)
        forground = Gdk.RGBA(0.0, 0.0, 0.0, 1.0)
        if self.currentScene().eventIndex < len(self.currentScene().events) - 1:
            if self.currentScene().eventIndex < self.currentScene().sessionEventIndex:
                rg = 0.95
                color = Gdk.RGBA(1.0, rg, rg, 1.0)
            else:
                color = Gdk.RGBA(val, val, val, 1.0)
            self.scriptView.textView.modify_bg(Gtk.StateType.NORMAL, color.to_color())
            self.scriptView.textView.modify_bg(Gtk.StateType.SELECTED, selectColor.to_color())
            self.scriptView.textView.modify_fg(Gtk.StateType.SELECTED, forground.to_color())
        else:
            color = Gdk.RGBA(1.0, 1.0, 1.0, 1.0)
            self.scriptView.textView.modify_bg(Gtk.StateType.NORMAL, color.to_color())
            self.scriptView.textView.modify_bg(Gtk.StateType.SELECTED, selectColor.to_color())
            self.scriptView.textView.modify_fg(Gtk.StateType.SELECTED, forground.to_color())

        self.scriptView.textView.descriptionTag.props.background_rgba = color
        self.scriptView.textView.characterTag.props.background_rgba = color
        self.scriptView.textView.dialogTag.props.background_rgba = color
        self.scriptView.textView.parentheticTag.props.background_rgba = color
        self.scriptView.textView.sceneHeadingTag.props.background_rgba = color

        for he in self.scriptView.headingEntries:
            he.modify_bg(Gtk.StateType.NORMAL, color.to_color())

