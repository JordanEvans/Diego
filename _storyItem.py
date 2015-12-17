import os

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
        self.count = 0
        self.saving = False
        self.editing = False
        # self.set_border_width(10)

    def newItem(self):
        self.control.newStory()

    def startEditMode(self):
        self.editing = True
        self.control.storyItemBox.editing = True

        title = self.label.get_text()
        if self.control.storyItemBox.numerated:
            title = title.split()
            title.pop(0)
            title = "".join(title)
        self.startEditTitle = title

        self.vbox.remove(self.label)
        self.label = Gtk.Entry()
        self.label.connect('key-release-event', self.labelKeyRelease)
        self.label.set_text(title)
        self.vbox.pack_start(self.label, 0, 0, 0)
        self.show_all()

        GObject.timeout_add(200, self.label.grab_focus)


    def labelKeyRelease(self, widget, event):
        if event.keyval == 65293:
            self.endEditMode()
        else:
            self.control.currentStory().title = self.label.get_text()

    def endEditMode(self):
        title = self.label.get_text()

        if len(title) == 0:
            title = self.startEditTitle

        self.control.currentStory().path = None

        # storyPath = self.control.currentStory().path
        #
        # if storyPath == None:
        self.saving = True
        self.control.currentStory().save()
        self.saving = False
        title = self.control.currentStory().title

        self.vbox.remove(self.label)
        self.label = Gtk.Label()
        self.label.set_text(title)
        self.vbox.pack_start(self.label, 0, 0, 0)
        self.show_all()
        self.control.currentStory().title = title
        self.control.storyItemBox.reset()
        self.control.storyItemBox.load()
        self.control.storyItemBox.show_all()
        self.control.storyItemBox.loadStoryAtIndex()

        self.control.storyItemBox.editing = False
        self.editing = False
        self.doubleClick = False

    def leaveNotify(self, widget, event):
        editing = self.control.storyItemBox.editing
        if event.detail in [Gdk.NotifyType.ANCESTOR, Gdk.NotifyType.NONLINEAR] and editing:
            self.endEditMode()

    def buttonPress(self, widget, event):
        self.doubleClick = False
        editing = self.control.storyItemBox.editing
        if event.type == Gdk.EventType._2BUTTON_PRESS and not editing:
            self.doubleClick = True

    def buttonRelease(self, widget, event):
        editing = self.control.storyItemBox.editing
        if self.doubleClick and not editing:
            self.control.storyItemBox.editing = True
            self.startEditMode()