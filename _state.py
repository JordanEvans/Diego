from gi.repository import Pango

import os
import json

import _story

class State(object):

    def __init__(self, control):
        self.control = control
        self.path = self.control.config.path + "/" + "state"
        # self.infoViewFontSize = 12

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
        data['infoViewFontSize'] = self.control.scriptView.infoViewFontSize
        data['saveDir'] = self.control.saveDir
        try:
            with open(self.path, 'w') as fp:
                json.dump(data, fp)
        except:
            print 'unable to save state file'

    def load(self):
        if os.path.exists(self.control.config.path):

            if not os.path.exists(self.path):
                self.save()

            if os.path.exists(self.path):
                try:
                    with open(self.path, 'r') as fp:
                        data = json.load(fp)

                        for storyPath in data['storyPaths']:
                            if storyPath and os.path.exists(storyPath):
                                story = _story.Story(self.control, storyPath)
                                self.control.stories.append(story)
                            else:
                                print "state load", "the path", storyPath, "does not exist"

                        self.control.verticalPanePosition = data['verticalPanePostion']
                        self.control.scriptView.textView.fontSize = data['fontSize']
                        self.width = data['windowWidth']
                        self.height = data['windowHeight']
                        self.control.scriptView.infoViewFontSize = data['infoViewFontSize']
                        self.control.scriptView.infoTextView.modify_font(Pango.FontDescription("Sans " + str(data['infoViewFontSize'])))
                        self.control.saveDir = data['saveDir']
                except:
                    print "state file failed to load: " + self.path

                if len(self.control.stories) == 0:
                    defaultStory = _story.Story(self.control)
                    defaultStory.load()
                    self.control.stories = [defaultStory]



    def reset(self):
        currentStory = self.control.currentStory()
        if currentStory:
            self.control.currentStory().path = None
        if os.path.exists(self.path):
            os.remove(self.path)

