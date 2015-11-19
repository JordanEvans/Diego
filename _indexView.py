
from gi.repository import Gtk

class StackSwitcher(Gtk.StackSwitcher):
    def __init__(self, control):
        Gtk.StackSwitcher.__init__(self)
        self.control = control
        self.count = 0

class IndexView(Gtk.Box):

    def __init__(self, control):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self.control = control
        self.items = []

    def postInit(self):
        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack.set_transition_duration(250)

        stack.add_titled(self.control.storyItemBox, "stories", "Stories")
        if self.control.sequenceVisible:
            stack.add_titled(self.control.sequenceItemBox, "sequence", "Sequence")
        stack.add_titled(self.control.sceneItemBox, "scene", "Scene")
        stack.add_titled(self.control.pageItemBox, "page", "Page")

        stackSwitcherBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        stack_switcher = StackSwitcher(self.control)
        stack_switcher.set_stack(stack)
        stackSwitcherBox.pack_start(stack_switcher, 0, 0, 0)

        self.pack_start(stack, 1, 1, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        hbox.pack_start(stackSwitcherBox, 1, 1, 0)
        self.control.appBox.stackSwitcherBox.pack_start(hbox, 0, 0, 0)

    def reset(self):
        pass

    def load(self):
        pass