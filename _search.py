
import re

from gi.repository import Gtk

class Find(object):

    def __init__(self, line, offset):
        self.line = line
        self.offset = offset

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

        # connect removeFindTags, removeFindTagsFromBuffer to delete button

        self.find = None
        self.finds = []
        self.scrollFindOffSet = 0
        self.lastScrollFind = None

    def reset(self):
        self.lastScrollFind = None
        self.scrollFindOffSet = 0
        self.removeFindTags()
        self.removeFindTagsFromBuffer()
        self.finds = []

    def keyRelease(self, widget, event):
        if (event.keyval == 65293):
            find = self.entry.get_text()
            if self.find != find:
                self.find = find
                self.reset()
                self.addFindTags()
                self.applyFindTags()

            self.scrollToNextFindTag()

    def removeFindTags(self):
        for line in self.control.scriptView.lines:
            line.findTags = []

    def removeFindTagsFromBuffer(self):
        for i in range(len(self.control.scriptView.lines)):
            if self.control.scriptView.lines[i].tag != 'heading':
                self.control.scriptView.textView.updateLineTag(i)

    def scrollToNextFindTag(self):
        if len(self.finds):

            find = self.finds[self.scrollFindOffSet]
            lineIndex = self.control.scriptView.lines.index(find.line)
            findIter = self.control.scriptView.textView.buffer.get_iter_at_line(lineIndex)
            findIter.forward_chars(find.offset)
            self.control.scriptView.textView.scroll_to_iter(findIter, 0, 0, 0, True)
            if self.lastScrollFind:
                self.removeScrollTag(self.lastScrollFind.line, self.lastScrollFind.offset)
                self.applyFindTag(self.lastScrollFind.line, self.lastScrollFind.offset)
            self.applyScrollTag(find.line, find.offset)
            self.lastScrollFind = find

            if self.scrollFindOffSet == len(self.finds) - 1:
                self.scrollFindOffSet = 0
            else:
                self.scrollFindOffSet += 1

    def addFindTags(self):
        self.finds = []

        for line in self.control.scriptView.lines:
            if line.tag != 'heading':
                line.findTags = []
                splitText = re.findall(r"[\w']+|[ .,!?;-]", line.text)

                if self.find in splitText:
                    offset = 0
                    for w in splitText:
                        if w == self.find:
                            find = Find(line, offset)
                            line.findTags.append(find)
                            self.finds.append(find)

                        offset += len(w)

    def applyFindTags(self):

        for find in self.finds:
            self.applyFindTag(find.line, offset=find.offset)


    def applyFindTag(self, line, offset):

        lineIndex = self.control.scriptView.lines.index(line)

        startIter = self.control.scriptView.textView.buffer.get_iter_at_line(lineIndex)
        startIter.forward_chars(offset)
        endIter = self.control.scriptView.textView.buffer.get_iter_at_line(lineIndex)
        endIter.forward_chars(offset + len(self.find))

        # sc,ec,soff, eoff, text = startIter.get_char(), endIter.get_char(), startIter.get_offset(), endIter.get_offset(), self.control.scriptView.textView.buffer.get_text(startIter, endIter, True)

        self.control.scriptView.textView.buffer.remove_all_tags(startIter, endIter)
        self.control.scriptView.textView.buffer.apply_tag_by_name(line.tag + "Find", startIter, endIter)


    def applyScrollTag(self, line, offset):

        lineIndex = self.control.scriptView.lines.index(line)

        startIter = self.control.scriptView.textView.buffer.get_iter_at_line(lineIndex)
        startIter.forward_chars(offset)
        endIter = self.control.scriptView.textView.buffer.get_iter_at_line(lineIndex)
        endIter.forward_chars(offset + len(self.find))

        # sc,ec,soff, eoff, text = startIter.get_char(), endIter.get_char(), startIter.get_offset(), endIter.get_offset(), self.control.scriptView.textView.buffer.get_text(startIter, endIter, True)

        self.control.scriptView.textView.buffer.remove_all_tags(startIter, endIter)
        self.control.scriptView.textView.buffer.apply_tag_by_name(line.tag + "Scroll", startIter, endIter)

    def removeScrollTag(self, line, offset):

        lineIndex = self.control.scriptView.lines.index(line)

        startIter = self.control.scriptView.textView.buffer.get_iter_at_line(lineIndex)
        startIter.forward_chars(offset)
        endIter = self.control.scriptView.textView.buffer.get_iter_at_line(lineIndex)
        endIter.forward_chars(offset + len(self.find))

        # sc,ec,soff, eoff, text = startIter.get_char(), endIter.get_char(), startIter.get_offset(), endIter.get_offset(), self.control.scriptView.textView.buffer.get_text(startIter, endIter, True)

        self.control.scriptView.textView.buffer.remove_all_tags(startIter, endIter)
        self.control.scriptView.textView.buffer.apply_tag_by_name(line.tag, startIter, endIter)