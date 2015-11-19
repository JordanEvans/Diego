
import os
from os.path import expanduser

class Config(object):

    def __init__(self, control):
        self.control = control
        self.path = expanduser("~") + "/.config" + "/" + self.control.app.name.lower()
        self.makeDir()

    def makeDir(self):
        if not os.path.exists(self.path):
            try:
                os.mkdir(self.path)
            except:
                print "failed to make config dir: " + self.path

    def reset(self):
        pass

    def load(self):
        pass