
import re

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
            self.addFindTags(find)
            self.applyFindTags(find)

    def addFindTags(self, find):

        if self.control.category == 'story':
            for sq in self.control.currentStory().sequences:
                for scene in sq.scenes:
                    for page in scene.pages:
                        for line in page.lines:

                            if line.tag != 'heading':
                                line.findTags = []

                                splitText = re.findall(r"[\w']+|[ .,!?;]", line.text)

                                if find in splitText:
                                    offset = 0
                                    for word in splitText:
                                        if word == find:
                                            line.findTags.append(offset)
                                            lineIndex = self.control.scriptView.lines.index(line)
                                        offset += len(word)

        elif self.control.category == 'scene':
            for page in self.control.currentScene().pages:
                for line in page.lines:
                    line.findTags = []

                    splitText = re.findall(r"[\w']+|[ .,!?;]", line.text)

                    if find in splitText:
                        offset = 0
                        for word in splitText:
                            if word == find:
                                line.findTags.append(offset)
                                lineIndex = self.control.scriptView.lines.index(line)
                            offset += len(word)

        elif self.control.category == 'page':
            for line in self.control.currentPage().lines:
                line.findTags = []
                splitText = re.findall(r"[\w']+|[ .,!?;]", line.text)

                if find in splitText:
                    offset = 0
                    for word in splitText:
                        if word == find:
                            line.findTags.append(offset)
                            lineIndex = self.control.scriptView.lines.index(line)
                        offset += len(word)
        if len(find) == 0:
            pass

    def applyFindTags(self, find):

        if self.control.category == 'story':
            for sq in self.control.currentStory().sequences:
                for scene in sq.scenes:
                    for page in scene.pages:
                        for line in page.lines:
                            if line.tag != 'heading':
                                for offset in line.findTags:
                                    self.applyFindTag(line, word=find, offset=offset)

        elif self.control.category == 'scene':
            for page in self.control.currentScene().pages:
                for line in page.lines:
                    for offset in line.findTags:
                        self.applyFindTag(line, word=find, offset=offset)

        elif self.control.category == 'page':
            for line in self.control.currentPage().lines:
                for offset in line.findTags:
                    self.applyFindTag(line, word=find, offset=offset)

    def applyFindTag(self, line, word, offset):

        lineIndex = self.control.scriptView.lines.index(line)

        startIter = self.control.scriptView.textView.buffer.get_iter_at_line(lineIndex)
        startIter.forward_chars(offset)
        endIter = self.control.scriptView.textView.buffer.get_iter_at_line(lineIndex)
        endIter.forward_chars(offset + len(word))

        # sc,ec,soff, eoff, text = startIter.get_char(), endIter.get_char(), startIter.get_offset(), endIter.get_offset(), self.control.scriptView.textView.buffer.get_text(startIter, endIter, True)

        self.control.scriptView.textView.buffer.remove_all_tags(startIter, endIter)
        self.control.scriptView.textView.buffer.apply_tag_by_name(line.tag + "Find", startIter, endIter)
