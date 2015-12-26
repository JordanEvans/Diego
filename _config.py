
import os
from os.path import expanduser

class Config(object):

    def __init__(self, control):
        self.control = control
        self.path = expanduser("~") + "/.config" + "/" + self.control.app.name.lower()
        self.makeDir()
        self.makeStoryDir()
        self.makeHistoryDir()

    def makeHistoryDir(self):
        historyDir = expanduser("~") + "/.config/diego/History"
        if not os.path.exists(historyDir):
            try:
                os.mkdir(historyDir)
                self.control.historyDir = historyDir
            except:
                print "failed to make history dir: " + historyDir
        else:
            self.control.historyDir = historyDir

    def makeStoryDir(self):
        storyDir = os.path.realpath(os.curdir) + "/Stories"
        if not os.path.exists(storyDir):
            try:
                os.mkdir(storyDir)
            except:
                print "failed to make config dir: " + storyDir

    def makeDir(self):
        if not os.path.exists(self.path):
            try:
                os.mkdir(self.path)
            except:
                print "failed to make config dir: " + self.path

        try:
            if not os.path.exists(self.control.addWordPath):
                f = open(self.control.addWordPath, "w")
                f.close()
        except:
            print "Could not make addWord path " + self.control.addWordPath

        try:
            if not os.path.exists(self.control.removeWordPath):
                f = open(self.control.removeWordPath, "w")
                f.close()
        except:
            print "Could not make removeWord path " + self.control.removeWordPath

    def reset(self):
        pass

    def load(self):
        pass