
from gi.repository import Gtk, Gdk, GObject

import _item

class Data(object):

    def __init__(self, control):
        self.control = control

        self.name = ''
        self.intExt = ''
        self.location = ''
        self.time = ''
        self.notation = ''

    def load(self):
        pass

    def save(self,):
        pass

    def reset(self):
        pass


class View(_item.Item):

    def __init__(self, control):
        _item.Item.__init__(self, control)

    def startEditMode(self):
        self.editing = True
        self.control.sceneItemBox.editing = True

        title = self.label.get_text()
        if self.control.sceneItemBox.numerated:
            title = title.split()
            title.pop(0)
            title = ' '.join(title)
        self.startEditTitle = title

        self.vbox.remove(self.label)
        self.label = Gtk.Entry()
        self.label.connect('key-release-event', self.labelKeyRelease)

        self.label.set_text(title)
        self.vbox.pack_start(self.label, 0, 0, 0)
        self.label.show()

        GObject.timeout_add(200, self.label.grab_focus)

    def labelKeyRelease(self, widget, event):
        if event.keyval == 65293:
            self.endEditMode()

    def endEditMode(self):
        title = self.label.get_text()

        if len(title) == 0:
            title = self.startEditTitle

        self.vbox.remove(self.label)
        self.label = Gtk.Label()
        self.label.set_text(title)
        self.vbox.pack_start(self.label, 0, 0, 0)
        self.show_all()
        self.control.currentScene().title = title
        self.control.sceneItemBox.reset()
        self.control.sceneItemBox.load()
        self.control.sceneItemBox.show_all()
        self.control.sceneItemBox.loadSceneAtIndex()

        self.control.sceneItemBox.editing = False

    def leaveNotify(self, widget, event):
        editing = self.control.sceneItemBox.editing
        if event.detail in [Gdk.NotifyType.ANCESTOR, Gdk.NotifyType.NONLINEAR] and editing:
            self.endEditMode()

    def buttonPress(self, widget, event):
        self.doubleClick = False
        editing = self.control.sceneItemBox.editing
        if event.type == Gdk.EventType._2BUTTON_PRESS and not editing:
            self.doubleClick = True

    def buttonRelease(self, widget, event):
        editing = self.control.sceneItemBox.editing
        if self.doubleClick and not editing:
            self.control.sceneItemBox.editing = True
            self.startEditMode()