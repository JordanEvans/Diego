import os
import json

from gi.repository import Gtk

class Preferences(object):

    def __init__(self, control):
        self.control = control
        self.path = self.control.config.path + "/" + "preferences"

        self.autocompleteAsDialog = True

    def window(self):
        Window(self.control)

    def save(self):
        data = {}
        data['autocompleteAsDialog'] = self.autocompleteAsDialog

        try:
            with open(self.path, 'w') as fp:
                json.dump(data, fp)
        except:
            print 'unable to save preferences file'

    def load(self):
        if os.path.exists(self.control.config.path):
            if os.path.exists(self.path):
                try:
                    with open(self.path, 'r') as fp:
                        data = json.load(fp)
                        self.DialogTextView = data['autocompleteAsDialog']
                except:
                    print "preferences file failed to load: " +self.path
                    self.reset()

    def reset(self):
        if os.path.exists(self.path):
            os.remove(self.path)

class Window(Gtk.Window):

    def __init__(self, control):
        Gtk.Window.__init__(self, title="Preferences")
        self.control = control

        self.layout()
        self.connections()
        self.config()
        self.load()

        # self.show_all()

    def layout(self):
        pass

    def connections(self, ):
        pass

    def config(self, ):
        self.resize(600,600)

    def save(self):
        self.control.preferences.save()

    def load(self):
        # loads preference data into widgets
        pass

    def reset(self):
        pass

