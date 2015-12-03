
import os

from gi.repository import Gtk, Gdk

# app
import _appWindow

# data
from _config import Config
from _state import State
from _story import Story
from _preferences import Preferences

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
        self.app = app
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.stories = []
        self.index = 0
        self.historyEnabled = False
        self.printCount = 0
        self.category = 'sequence'
        self.saveDir = os.path.expanduser(('~'))
        self.verticalPanePosition = 150
        self.startingUpApp = True

        self.sequenceVisible = False

    def notImplemented(self):
        print "not implemented"

    def p(self, *args):
        self.printCount += 1
        print self.printCount, args

    def postInit(self, ):
        self.initData()
        self.initViews()

    def initData(self, ):
        self.config = Config(self)
        self.preferences = Preferences(self)
        self.state = State(self)

    def initViews(self, ):
        # Widgets directly tied to Control for implementation convenience.
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

        self.searchEntry = Gtk.SearchEntry()

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

        self.currentStory().findAndReplace("Harry", "Gordon")

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

