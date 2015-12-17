
from gi.repository import Gtk
from gi.repository import Gdk

import _dialog

class Window(Gtk.Window):

    def __init__(self, control):
        Gtk.Window.__init__(self, title="Diego")
        self.control = control

    def postInit(self):
        self.layout()
        self.connections()
        self.config() 
        
    def layout(self):
        self.add(self.control.appBox)
        
    def connections(self, ):
        self.connect("delete-event", self.control.app.shutdown)
        self.connect("key-press-event", self.keyPress)
        # self.connect("focus-in-event", self.focusIn)

    # def focusIn(self, window, event):
    #     self.control.sysClipboard.update()

    def config(self, ):
        self.resize(1000,600)

    def keyPress(self, widget, event):

        print event.keyval

        if event.state & Gdk.ModifierType.SHIFT_MASK:
            if event.state & Gdk.ModifierType.CONTROL_MASK:
                if event.keyval==83: # save as
                    _dialog.saveFile(self.control)
                    return 1

        if event.state & Gdk.ModifierType.CONTROL_MASK:

            if ( event.keyval == 49):
                self.newPage()


            elif(event.keyval==114): # Find And Replace
                dialog = _dialog.FindAndReplaceDialog(self.control, self)
                responseType = dialog.run()
                if responseType == Gtk.ResponseType.APPLY:
                    dialog.findAndReplace()

                dialog.destroy()

            elif ( event.keyval == 122):
                pass
                # self.control.eventManager.undo()

            elif ( event.keyval == 90):
                pass
                # self.control.eventManager.redo()
                
            elif ( event.keyval ==110) | (event.keyval == 78):
                self.control.app.unsavedFileCheck()
                self.newDocument()
                
            elif ( event.keyval ==115) | (event.keyval == 83):
                self.save()
                
            elif ( event.keyval ==113) | (event.keyval == 81):
                self.control.app.shutdown()

            elif ( event.keyval ==111) | (event.keyval == 79):
                self.control.app.unsavedFileCheck()
                _dialog.openFile(self.control)

            elif (event.keyval ==112):
                self.control.preferences.window()
        else:
            pass

    def newDocument(self):
        self.control.reset()
        self.control.load()
        self.control.currentStory().saved = False

    def save(self):
        self.control.currentStory().save()

    def newPage(self):
        self.control.currentStory().newPage()
        self.control.pageItemBox.newPage()
        # self.control.pageItemBox.show_all()

        self.newScene()
        self.newSequence()

    def newScene(self):
        # self.control.currentStory().newPage()
        self.control.sceneItemBox.newScene()
        # self.control.sceneItemBox.show_all()

    def newSequence(self):
        # self.control.currentStory().newPage()
        self.control.sequenceItemBox.newSequence()
        # self.control.sequenceItemBox.show_all()

    def load(self):
        pass

    def reset(self):
        pass
