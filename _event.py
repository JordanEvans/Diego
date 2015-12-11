
import _story

class Event(object):
    def __init__(self, chained=False):
        print self.__class__.__name__, "Event"
        self.chained = chained

    def redo(self):
        print "redo ", self.__class__.__name__

    def undo(self):
        print "undo ", self.__class__.__name__


class StartHistoryEvent(Event):

    def __init__(self, ):
        Event.__init__(self)

    def undo(self, control):
        pass

    def redo(self, control):
        pass


class NewSequenceEvent(Event):

    def __init__(self, data, index):
        Event.__init__(self)
        self.data = data
        self.index = _story.StoryIndex(index.__dict__)

    def undo(self, control):
        control.currentStory().sequences.remove(self.data)
        control.reset(False)
        index = _story.StoryIndex(self.index)
        #index.sequence -= 1
        control.currentStory().index = index
        control.load(False)

    def redo(self, control):
        control.currentStory().sequences.insert(self.index.sequence +1, self.data)
        control.reset(False)
        control.currentStory().index = _story.StoryIndex(self.index)
        control.load(False)


class NewSceneEvent(Event):

    def __init__(self, data, index):
        Event.__init__(self)
        self.data = data
        self.index = _story.StoryIndex(index.__dict__)

    def undo(self, control):
        control.currentSequence().scenes.remove(self.data)
        control.reset(False)
        index = _story.StoryIndex(self.index)
        index.scene -=1
        control.currentStory().index = index
        control.load(False)

    def redo(self, control):
        control.currentSequence().scenes.insert(self.index.scene, self.data)
        control.reset(False)
        control.currentStory().index = _story.StoryIndex(self.index)
        control.load(False)


class NewPageEvent(Event):

    def __init__(self, data, index):
        Event.__init__(self)
        self.data = data
        self.index = _story.StoryIndex(index.__dict__)

    def undo(self, control):
        control.currentScene().pages.remove(self.data)
        control.reset(False)
        index = _story.StoryIndex(self.index)
        index.page -=1
        control.currentStory().index = index
        control.load(False)

    def redo(self, control):
        control.currentScene().pages.insert(self.index.page, self.data)
        control.reset(False)
        control.currentStory().index = _story.StoryIndex(self.index.__dict__)
        control.load(False)


class NewPanelEvent(Event):

    def __init__(self, data, index):
        Event.__init__(self)
        self.data = data
        self.index = _story.StoryIndex(index.__dict__)

    def undo(self, control):
        control.currentPage().elements.remove(self.data)
        control.reset(False)
        index = _story.StoryIndex(self.index)
        # index[3] -=1
        control.currentStory().index = index
        control.load(False)

    def redo(self, control):
        control.currentPage().elements.insert(self.index[3], self.data)
        control.reset(False)
        control.currentStory().index = _story.StoryIndex(self.index.__dict__)
        control.load(False)


class NewDialogEvent(Event):

    def __init__(self, data, index):
        Event.__init__(self)
        self.data = data
        self.index = _story.StoryIndex(index.__dict__)

    def undo(self, control):
        control.currentPage().elements.remove(self.data)
        control.reset(False)
        index = list(self.index)
        index[3] -=1
        control.currentStory().index = index
        control.load(False)

    def redo(self, control):
        control.currentPage().elements.insert(self.index[3], self.data)
        control.reset(False)
        control.currentStory().index = list(self.index)
        control.load(False)


class EventManager(object):

    def __init__(self, control):
        self.control = control
        self.cue = [StartHistoryEvent()]
        self.position = 0

    def addEvent(self, event):

        if len(self.cue) > self.position:
            self.cue = self.cue[:self.position +1]

        self.cue.insert(self.position +1, event)

        self.position +=1

        # print "history count", len(self.cue) -1

    def undo(self):
        if self.position > 0:
            self.cue[self.position].undo(self.control)
            self.position -=1

    def redo(self):

        if self.position < len(self.cue) -1:
            self.position +=1
            self.cue[self.position].redo(self.control)

    def reset(self):
        self.cue = [StartHistoryEvent()]
        self.position = 0


class View(object):
    pass


class NewLineEvent(Event):
    def __init__(self, control, carryText='', tag='description', fromHeading=False):
        Event.__init__(self)

        if fromHeading:
            cl = control.scriptView.currentLine()
            scriptLineIndex = control.scriptView.lines.index(cl)

            newLine = _story.Line(carryText, tag=tag)
            newLine.heading = cl.heading

            index = control.currentStory().index.line

            cp = control.currentPage()

            control.currentPage().lines.insert(index, newLine)
            control.scriptView.lines.insert(scriptLineIndex, newLine)

            # control.currentStory().index

        else:
            cl = control.scriptView.currentLine()
            scriptLineIndex = control.scriptView.lines.index(cl) +1

            if len(carryText):
                cl.text = cl.text[:len(cl.text)-len(carryText)]

            newLine = _story.Line(carryText, tag=tag)
            newLine.heading = cl.heading

            index = control.currentStory().index.line +1

            cp = control.currentPage()

            control.currentPage().lines.insert(index, newLine)
            control.scriptView.lines.insert(scriptLineIndex, newLine)

    def redo(self):
        Event.redo(self)

    def undo(self):
        Event.undo(self)


class BackspaceEvent(Event):
    def __init__(self, control, removedNewLine=False):
        Event.__init__(self)

        if removedNewLine:
            line = control.scriptView.currentLine()
            self.carryText = line.text

            previousLine = control.scriptView.previousLine()
            previousLine.text += self.carryText

            control.currentPage().lines.remove(line)
            control.scriptView.lines.remove(line)

        else:
            line = control.scriptView.currentLine()
            index = control.currentStory().index.offset
            line.text = line.text[:index-1] + line.text[index:]

    def redo(self):
        Event.redo(self)

    def undo(self):
        Event.undo(self)


class DeleteEvent(Event):
    def __init__(self, control, delChar):
        Event.__init__(self)
        line = control.scriptView.currentLine()
        index = control.currentStory().index.offset

        if delChar == '\n':
            if index == 0:
                # delete the line only
                control.scriptView.lines.remove(line)
                control.currentPage().lines.remove(line)
            else:
                # delete the line and add prepend the text to the next line
                lineText = line.text
                lineIndex = control.currentPage().lines.index(line)
                lineTag = line.tag
                nextLine = control.currentPage().lines[lineIndex + 1]
                nextLine.text = lineText + nextLine.text
                nextLine.tag = lineTag
                control.scriptView.lines.remove(line)
                control.currentPage().lines.remove(line)

                # control.scriptView.textView.updateLineTag(lineIndex + 1)

        else:
            line.text = line.text[:index] + line.text[index +1:]

            control.scriptView.textView.updateLineTag(index)

    def redo(self):
        Event.redo(self)

    def undo(self):
        Event.undo(self)


class WordEvent(Event):
    def __init__(self, control, word, duringKeyPressEvent=False):
        Event.__init__(self)

        cs = control.scriptView.currentStory()
        cl = control.scriptView.currentLine()

        updateToKeyReleasePosition = 0
        # if duringKeyPressEvent:
        #     updateToKeyReleasePosition = 1

        insertOffset = cs.index.offset - len(word)

        first = cl.text[:insertOffset + updateToKeyReleasePosition]
        last = cl.text[cs.index.offset + updateToKeyReleasePosition - len(word):]

        # text = text[:insertOffset + updateToKeyReleasePosition] + word + text[cs.index.offset + updateToKeyReleasePosition - 1 :]

        text = first + word + last

        cl.text = text

        self.index = _story.StoryIndex(cs.index.__dict__)

        # if not duringKeyPressEvent: # will do in TextView.keyRelease
        #     control.scriptView.updateCurrentStoryIndex()

    def redo(self):
        Event.redo(self)

    def undo(self):
        Event.undo(self)


class PasteEvent(Event):
    def __init__(self, control):
        Event.__init__(self)

        firstLine = control.currentLine()

        currentPage = control.currentPage()
        heading = currentPage.lines[0].heading

        # self.bufferLine is the index of the line of the insert iter.
        self.bufferLine = control.scriptView.textView.insertIter().get_line()

        # self.line is the index of the line of the inser iter in the current page.
        self.line = currentPage.lines.index(control.scriptView.lines[self.bufferLine])

        # for line in control.selectionClipboard.lines:
        #     line.heading = heading

        for line in control.copyClipboard.lines:
            line.heading = heading

        self.clipboardLines = list(control.copyClipboard.lines)

        self.selectedLines = []

        firstLine = control.currentLine()
        self.offset = control.scriptView.textView.insertIter().get_line_offset()
        self.carryText = firstLine.text[self.offset:]

        if len(control.scriptView.textView.selectedClipboard):
            control.scriptView.textView.deleteSelectedText()
            self.selectedLines = list(control.selectionClipboard.lines)

        self.lines = list(control.copyClipboard.lines)

        i = 0

        if len(self.clipboardLines) == 1:
            s1 = firstLine.text[:self.offset]
            firstLineText = self.clipboardLines[0].text
            s2 = firstLine.text[self.offset:]

            firstLine.text = s1 + firstLineText + s2

        elif len(self.clipboardLines) == 2:

            # Add the current line of buffer text up to the caret plus the first line of pasted text.
            frontOfLineText = firstLine.text[:self.offset]
            firstLineText = self.clipboardLines[0].text
            firstLine.text = frontOfLineText + firstLineText

            # Use the second line to create a new line.
            newLine = _story.Line(self.clipboardLines[1].text, tag=self.clipboardLines[1].tag)
            newLine.heading = heading
            newLine.text += self.carryText

            # Insert new line at the insertion iter's index.
            currentPage.lines.insert(self.line + 1, newLine)

            # Insert new line one past the insert iter's line.
            control.scriptView.lines.insert(self.bufferLine + 1, newLine)

        elif len(self.clipboardLines) > 1:

            # Add the current line of buffer text up to the caret plus the first line of pasted text.
            # The first clipboard line will be appended to the insert inter buffer line.
            frontOfLineText = firstLine.text[:self.offset]
            firstLineText = self.clipboardLines[0].text
            firstLine.text = frontOfLineText + firstLineText

            # Insert all the new lines, except the last one. Begin with the second line in clipboard lines.
            for i in range(len(self.clipboardLines)-2):
                line = self.clipboardLines[i+1]
                newLine = _story.Line(line.text, tag=line.tag)
                newLine.heading = heading
                currentPage.lines.insert(self.line + i + 1, newLine)
                control.scriptView.lines.insert(self.bufferLine + i + 1, newLine)
                pass

            # Insert the last new line.
            lastClipboardLine = self.clipboardLines[-1]
            newLine = _story.Line(lastClipboardLine.text, tag=lastClipboardLine.tag)
            newLine.text += self.carryText
            newLine.heading = heading
            currentPage.lines.insert(self.line + i + 2, newLine)
            control.scriptView.lines.insert(self.bufferLine + i + 2, newLine)

        return

    def redo(self):
        Event.redo(self)

    def undo(self):
        Event.undo(self)


class CutEvent(Event):
    def __init__(self, control):
        Event.__init__(self)

        currentPage = control.currentPage()

        # When more than one line is being cut, this is the leftover text of that cut line..
        self.firstLineCarryText = ''
        self.lastLineCarryText = ''

        selectionOffset1 = control.scriptView.textView.selectionIterStart.get_line_offset()
        selectionOffset2 = control.scriptView.textView.selectionIterEnd.get_line_offset()

        startSelectionLine = control.scriptView.textView.selectionIterStart.get_line()
        self.offset = selectionOffset1

        line1 = control.scriptView.lines[startSelectionLine]
        self.line = currentPage.lines.index(line1)
        self.textViewLine = control.scriptView.lines.index(line1)

        self.cutClipboard = list(control.selectionClipboard.lines)

        # control.scriptView.textView.copyClipboard = []
        # for line in self.cutClipboard:
        #     control.scriptView.textView.copyClipboard.append(_story.Line(line))

        if len(self.cutClipboard) == 1:
            
            # Only one line is selected. Cut the string between front and end.
            frontString = line1.text[:self.offset]
            endString = line1.text[self.offset+len(self.cutClipboard[0].text):]
            
            # Add the front and end string and set it to current line.
            line1.text = frontString + endString

        elif len(self.cutClipboard) == 2:

            # Get the text on the first line beginning at the start of the selection.
            firstLineText = line1.text[:self.offset]
            line1.text = firstLineText
            self.firstLineCarryText = firstLineText

            endOffset = control.scriptView.textView.selectionIterEnd.get_line_offset()

            line2 = control.scriptView.lines[startSelectionLine +1]

            # Get the text on the second line beginning up to the end of the selection.
            lastLineText = line2.text[endOffset:]
            line2.text = lastLineText
            self.lastLineCarryText = lastLineText

            # Remove the second line
            currentPage.lines.remove(line2)
            control.scriptView.lines.remove(line2)

            # Line one will get the both texts appended.
            line1.text = firstLineText + lastLineText

            # If the first line's text is all deleted, the tag on the second line will be used, unless it has no text.
            # The other two cases will keep line one's tag by default.
            if len(self.firstLineCarryText) == 0 and len(self.lastLineCarryText) > 0:
                line1.tag = line2.tag

        else:

            # Get the text on the first line beginning at the start of the selection.
            firstLineText = line1.text[:self.offset]
            line1.text = firstLineText
            self.firstLineCarryText = firstLineText

            lastLine = control.scriptView.lines[self.line + len(self.cutClipboard)]

            endOffset = control.scriptView.textView.selectionIterEnd.get_line_offset()
            
            # Get the text on the second line beginning up to the end of the selection.
            lastLineText = lastLine.text[endOffset:]
            lastLine.text = lastLineText
            self.lastLineCarryText = lastLineText

            # Gather lines to remove.
            removeLines = []
            for i in range(len(self.cutClipboard)-1):
                line = currentPage.lines[startSelectionLine + i]
                removeLines.append(line)

            # Remove the middle lines and last line
            for line in removeLines:
                currentPage.lines.remove(line)
                control.scriptView.lines.remove(line)

            # Set the first line text.
            line1.text = firstLineText + lastLineText

        return

    def redo(self):
        Event.redo(self)

    def undo(self):
        Event.undo(self)

class AutocompleteEvent(Event):
    def __init__(self, control, name):
        Event.__init__(self)

        self.index = _story.StoryIndex(control.currentStory().index.__dict__)
        self.name = name

    def redo(self):
        Event.redo(self)

    def undo(self):
        Event.undo(self)
