__author__ = 'dev'
__doc__ = """How The Clipboard Works (Only AppClipboard is working now.)

Two clipboards are used to handle cut and copy events. When a cut/copy has occured outside the app (or the app starts with something on the clipboard), the SysClipboard is used. When a cut/copy has occured inside the app, AppClipboard is used.

When a cut or copy event in the text view occurs, AppClipboard.override to True and the line(s) are copied to AppClipboard.lines. When a paste event occurs, the override variable will force the AppClipboard to be used.

If the user leaves the app, and adds something to the clipboard, upon returning to the AppWindow, the AppWindow will recieve a focus-in-event. This will turn off AppClipboard.override to False. Now, the imported text will be pasted. (By default the AppClipboard."""


class SysClipboard(object):

    def __init__(self, control):
        self.control = control
        self.text = ''
        self.update()

    def update(self):
        return
        text = self.control.clipboard.wait_for_text()
        if self.text != text:
            self.text = text
            self.control.appClipboard.override = False
        if text == None:
            self.text = ''


class AppClipboard(object):

    def __init__(self, control):
        self.control = control
        self.override = False
        self.lines = []


class Clipboard(object):

    def __init__(self, control):
        self.control = control
        self.lines = []
