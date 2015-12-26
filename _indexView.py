
from gi.repository import Gtk

class IndexView(Gtk.Box):

    def __init__(self, control):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self.control = control
        self.items = []

        self.stack = Gtk.Stack()

    def postInit(self):

        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(250)

        self.stack.add_titled(self.control.storyItemBox, "story", "Stories")

        if self.control.sequenceVisible:
            self.stack.add_titled(self.control.sequenceItemBox, "sequence", "Sequence")

        self.stack.add_titled(self.control.sceneItemBox, "scene", "Scene")
        self.stack.add_titled(self.control.pageItemBox, "page", "Page")

        self.pack_start(self.stack, 1, 1, 0)

    def reset(self):
        pass

    def load(self):
        pass