
from gi.repository import Gtk

class Switch(Gtk.Switch):

    def __init__(self, control):
        Gtk.Switch.__init__(self)
        self.control = control
        self.connect("notify::active", self.on_switch_activated)
        self.set_active(False)
        self.activating = False
        self.set_tooltip_text("Sceenplay Mode Not Active")

    def on_switch_activated(self, switch, gparam):

        self.activating = True
        self.control.indexView.stack.set_focus_child(self.control.storyItemBox)
        self.control.indexView.stack.set_visible_child(self.control.storyItemBox)
        self.control.storyItemBox.listbox.do_map()

        if switch.get_active():
            self.control.indexView.stack.remove(self.control.pageItemBox)
            self.control.currentStory().isScreenplay = True
            self.set_tooltip_text("Sceenplay Mode Is Active")
        else:
            self.control.indexView.stack.add_titled(self.control.pageItemBox, "page", "Page")
            self.control.currentStory().isScreenplay = False
            self.set_tooltip_text("Sceenplay Mode Is Not Active")

        self.control.scriptView.textView.tagIter.updateMode(self.control)

        self.control.indexView.stack.set_focus_child(self.control.storyItemBox)
        self.control.storyItemBox.listbox.do_map()

        self.control.scriptView.resetAndLoad()
        self.control.app.window.show_all()
        self.activating = False
