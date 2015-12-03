
from gi.repository import Gtk

class FindIter(object):

    def __init__(self, control, lines):
        self.control = control
        self.lines = lines
        self.index = 0

    def line(self):
        return self.lines[self.index]

    def increment(self):
        if self.index + 1 == len(self.lines):
            self.index = 0
        else:
            self.index += 1

    def previous(self):
        if self.index == 0:
            index = len(self.lines) -1
        else:
            index = self.index - 1
        return self.lines[index]

    def reset(self):
        self.index = 0

    def load(self, line=None):
        if line:
            index = self.lines.index(line)
            self.index = index
        else:
            self.index = 0

    def scroll(self):
        index = self.control.scriptView.lines.index(self.line)
        lineIter = self.control.scriptView.textView.iterAtLocation(index, 0)

        # Place character on line.
        self.buffer.place_cursor(lineIter)

        # Update the model so the current line is next line.
        currentLine = self.control.currentLine()
        lineIndex = self.control.currentPage().lines.index(currentLine)
        #self.control.currentStory().index.line = lineIndex + 1
        self.control.currentStory().index.offset = 0
        tag = self.control.currentLine().tag
        self.tagIter.load(tag)

        visibleRect = self.control.scriptView.textView.get_visible_rect()
        insertIter = self.control.scriptView.textView.insertIter()
        insertRect = self.control.scriptView.textView.get_iter_location(insertIter)
        if (insertRect.y >= visibleRect.y) and (insertRect.y + insertRect.height <= visibleRect.y + visibleRect.height):
            pass
        else:
            self.control.scriptView.textView.scroll_to_iter(insertIter, 0.1, False, 0.0, 0.0)

class View(Gtk.Box):

    def __init__(self, control):
        Gtk.Box.__init__(self)

        self.control = control

        self.entry = Gtk.SearchEntry()

        self.add(self.entry)

        self.entry.connect("key-release-event", self.keyRelease)


    def keyRelease(self, widget, event):
        if (event.keyval == 65293):
            find = self.entry.get_text()
            print find

            self.control.currentStory().addFindTags(find)
            self.control.scriptView.reset()

            if self.control.category == 'story':
                self.control.scriptView.loadStory()
            elif self.control.category == 'scene':
                self.control.scriptView.loadScene()
            elif self.control.category == 'page':
                self.control.scriptView.loadPage()
