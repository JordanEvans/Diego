from gi.repository import Pango

import os
import json

import _story

class State(object):

    def __init__(self, control):
        self.control = control
        self.path = self.control.config.path + "/" + "state"
        # self.infoViewFontSize = 12
        self.author = ''
        self.contact = ''
        self.storyIds = []
        self.width = 1000
        self.height = 600
        self.scriptViewPanedPosition = 0
        self.lastCategory = "story"
        self.lastStoryIndex = _story.StoryIndex()
        self.lastSelection = (0,0)
        self.backupDir = '/home/dev/Documents'
        self.times = ["DAY", "NIGHT", "DUSK", "DAWN"]

        if not os.path.exists(self.path):
            self.defaultSave()

    def shutdown(self, ):
        self.save()

    def save(self):

        data = {}
        data['storyPaths'] = self.control.storyPaths()
        data['index'] = self.control.index
        data['verticalPanePostion'] = self.control.appBox.paned.get_position()
        data['fontSize'] = self.control.scriptView.textView.fontSize
        data['windowWidth'] = self.control.app.window.get_allocated_width()
        data['windowHeight'] = self.control.app.window.get_allocated_height()
        # data['infoViewFontSize'] = self.control.scriptView.infoViewFontSize
        # data['saveDir'] = self.control.saveDir
        data['windowPosition'] = self.control.app.window.get_position()
        data['storyIndex'] = self.control.index
        data['author'] = self.author
        data['contact'] = self.contact
        # data['scriptViewPanedPosition'] = self.control.scriptView.paned.get_position()
        data['storyIds'] = self.storyIds
        data['backupdir'] = self.backupDir
        data['times'] = self.times

        try:
            data['lastStoryIndex'] = self.control.currentStory().index.data()
        except:
            data['lastStoryIndex'] = _story.StoryIndex()

        data['lastCategory'] = self.control.category
        data['lastSelection'] = self.control.selectionOffsets()

        try:
            with open(self.path, 'w') as fp:
                json.dump(data, fp)
        except:
            print "State Save Failed."
            self.delfautSave()

    def defaultSave(self):

        print "defaultSave"

        data = {}
        data['storyPaths'] = []
        data['index'] = 0
        data['verticalPanePostion'] = 150
        data['fontSize'] = 16
        data['windowWidth'] = 1000
        data['windowHeight'] = 600
        # data['infoViewFontSize'] = 14
        # data['sav/eDir'] = self.control.saveDir
        data['windowPosition'] = (0,0)
        data['storyIndex'] = 0
        data['author'] = ''
        data['contact'] = ''
        data['backupdir'] = None

        data['lastStoryIndex'] = 0

        data['lastCategory'] = 'story'
        data['lastSelection'] = (None, None)
        data['times'] = ['DAY', 'NIGHT', 'DUSK', 'DAWN']

        try:
            with open(self.path, 'w') as fp:
                json.dump(data, fp)
        except:
            print 'Default State Save failed.'

    def load(self):
        if os.path.exists(self.control.config.path):

            if not os.path.exists(self.path):
                self.save()

            exceptionText = "State file loaded with error"

            if os.path.exists(self.path):

                try:
                    try:
                        with open(self.path, 'r') as fp:
                            data = json.load(fp)

                    except:
                        exceptionText = "JSON Load Error : State file did not load open. The state file data may be corrupted."
                        raise Exception()

                    try:

                        while None in data['storyPaths']:
                            data['storyPaths'].remove(None)

                        for storyPath in data['storyPaths']:
                            if storyPath and os.path.exists(storyPath):
                                story = _story.Story(self.control, storyPath)
                                # story.createId()

                                self.control.stories.append(story)
                            else:
                                print "state load", "the path", storyPath, "does not exist"
                    except:
                        exceptionText = "Story Path Error : State file did not load open. The state file data may be corrupted."
                        raise Exception()

                    try:
                        self.control.verticalPanePosition = data['verticalPanePostion']
                        self.control.scriptView.textView.fontSize = data['fontSize']
                        self.width = data['windowWidth']
                        self.height = data['windowHeight']
                        # self.control.scriptView.infoViewFontSize = data['infoViewFontSize']
                        # self.control.scriptView.infoTextView.modify_font(Pango.FontDescription("Courier Prime " + str(data['infoViewFontSize'])))
                        # self.control.saveDir = data['saveDir']
                        self.control.windowPosition = data['windowPosition']

                        self.author = data['author']
                        self.contact = data['contact']
                        # self.scriptViewPanedPosition = data['scriptViewPanedPosition']

                        if 'lastStoryIndex' in data.keys():
                            self.lastStoryIndex = _story.StoryIndex(data['lastStoryIndex'])
                        if 'lastCategory' in data.keys():
                            self.lastCategory = data['lastCategory']
                        if 'lastSelection' in data.keys():
                            self.lastSelection = data['lastSelection']
                        if 'storyIds' in data.keys():
                            self.storyIds = data['storyIds']

                        if 'backupdir' in data.keys():
                            self.backupDir = data['backupdir']

                        if 'times' in data.keys():
                            self.times = data['times']

                    except:
                        exceptionText = "State Data Error : State file did not load open. The state file data may be corrupted."
                        raise Exception()

                    self.control.index = 0
                    if data['storyIndex'] < len(self.control.stories):
                        self.control.index = data['storyIndex']
                    else:
                        exceptionText = "Story Index Error: State file did not load open. The state file data may be corrupted."
                        self.control.index = 0

                except:
                    print "state file failed to load : " + exceptionText
                    self.control.stories = []

                if len(self.control.stories) == 0:
                    defaultStory = _story.Story(self.control)
                    defaultStory.createId()
                    #defaultStory.makeHistoryDir()
                    defaultStory.load()
                    self.control.stories = [defaultStory]

    def reset(self):
        currentStory = self.control.currentStory()
        if currentStory:
            self.control.currentStory().path = None
        if os.path.exists(self.path):
            os.remove(self.path)