
import _story

class Event(object):
    def __init__(self, chained=False):
        print self.__class__.__name__, "Event"
        self.chained = chained

    def redo(self):
        print "redo ", self.__class__.__name__

    def undo(self):
        print "undo ", self.__class__.__name__


class Insertion(Event):
    def __init__(self, scene, page, line, offset, text, tags):
        Event.__init__(self)
        self.scene = scene
        self.page = page
        self.line = line # this the index of the page line
        self.offset = offset
        self.text = text
        self.tags = tags

        self.carryText = None
        self.newLines = []

    def undo(self, control):
        control.category = 'scene'
        control.indexView.stack.set_visible_child_name("scene")

        undo = Deletion(self.scene, self.page, self.line, self.offset, self.text, self.tags)
        undo.viewUpdate(control)
        undo.modelUpdate(control)

        control.scriptView.textView.grab_focus()

    def redo(self, control):

        control.category = 'scene'
        control.indexView.stack.set_visible_child_name("scene")

        redo = Insertion(self.scene, self.page, self.line, self.offset, self.text, self.tags)

        redo.modelUpdate(control)
        redo.viewUpdate(control)

        control.scriptView.textView.grab_focus()

    def viewUpdate(self, control, pushedOffHeading=False):

        eventLine = self.page.lines[self.line]
        bufferIndex = control.scriptView.lines.index(eventLine)

        insertIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
        control.scriptView.textView.get_buffer().insert(insertIter, self.text, len(self.text))

        firstLine = eventLine

        index = control.scriptView.lines.index(firstLine)
        for tag in self.tags:
            control.scriptView.lines[index].tag = tag
            control.scriptView.textView.updateLineTag(index)
            index += 1

        if pushedOffHeading:
            insertIter = control.scriptView.textView.insertIter()
            insertIter.backward_char()
            control.scriptView.textView.get_buffer().place_cursor(insertIter)
        else:
            afterInsertIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
            afterInsertIter.forward_chars(len(self.text))
            control.scriptView.textView.get_buffer().place_cursor(afterInsertIter)

    def modelUpdate(self, control, pushedOffHeading=False):

        lines = self.text.split("\n")

        eventLine = self.page.lines[self.line]

        firstLine = eventLine

        # Only inserting text, no new lines.
        if len(lines) == 1:
            word = lines[0]
            cs = control.currentStory()
            insertOffset = cs.index.offset
            first = firstLine.text[:self.offset]
            last = firstLine.text[self.offset:]
            text = first + word + last
            firstLine.text = text
            firstLine.tag = self.tags[0]

        else:
            if pushedOffHeading:
                self.tags[1] = self.tags[0]
                self.tags[0] = 'description'

            lineTags = list(self.tags)

            # Inserting extra lines, carry text will be set.
            self.carryText = firstLine.text[self.offset:]

            # The line of insertion already exists, so it will not need to be made.
            firstLineAppendText = lines.pop(0)
            firstLineTag = lineTags.pop(0)

            # The carry text needs to be removed from the current line.
            firstLine.text = firstLine.text[:self.offset]

            # Append inserted text at the end of the first line.
            firstLine.text = firstLine.text + firstLineAppendText

            # Create and insert all new lines.
            insertIndex = self.page.lines.index(firstLine) + 1
            scriptLineIndex = control.scriptView.lines.index(firstLine) + 1
            index = 0
            firstLine.tag = firstLineTag

            for line in lines:
                newLine = _story.Line(lines[index], tag=lineTags[index])
                newLine.heading = firstLine.heading
                self.page.lines.insert(insertIndex + index, newLine)

                # ScriptView need a reference to each line as well.
                control.scriptView.lines.insert(scriptLineIndex + index, newLine)

                self.newLines.append(newLine)
                index += 1

            # Last line will get the carry text.
            newLine.text += self.carryText

    def data(self):
        return None


class Deletion(Event):
    def __init__(self, scene, page, line, offset, text, tags):
        Event.__init__(self)
        self.scene = scene
        self.page = page
        self.line = line
        self.offset = offset
        self.text = text
        self.tags = tags

        self.isBackspaceKey = False
        self.isDeleteKey = False

    def viewUpdate(self, control):

        eventLine = self.page.lines[self.line]
        bufferIndex = control.scriptView.lines.index(eventLine)

        startIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)

        endIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
        endIter.forward_chars(len(self.text))

        control.scriptView.textView.get_buffer().delete(startIter, endIter)

        control.scriptView.textView.updateLineTag(bufferIndex, self.tags[0])

        afterDeleteIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
        control.scriptView.textView.get_buffer().place_cursor(afterDeleteIter)

    def modelUpdate(self, control, isBackspaceKey=False, isDeleteKey=False):

        eventLine = self.page.lines[self.line]
        bufferIndex = control.scriptView.lines.index(eventLine)

        firstLine = eventLine
        if isDeleteKey:
            self.isDeleteKey = isDeleteKey

        if isBackspaceKey:
            self.isBackspaceKey = isBackspaceKey
            if self.offset == 0:
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
            return

        lines = self.text.split("\n")

        if len(lines) == 1:
            frontString = firstLine.text[:self.offset]
            endString = firstLine.text[self.offset+len(lines[0]):]
            firstLine.text = frontString + endString
            return firstLine

        elif len(lines) == 2:
            # if not isDeleteKey:
            #     startLineIndex = control.scriptView.textView.selectionIterStart.get_line()
            #     firstLine = control.scriptView.lines[startLineIndex]
            #     self.offset = control.scriptView.textView.selectionIterStart.get_line_offset()

            # Get the text on the first line beginning at the start of the selection.
            firstLineText = firstLine.text[:self.offset]
            firstLine.text = firstLineText
            # firstLineCarryText = firstLineText

            # endOffset = control.scriptView.textView.selectionIterEnd.get_line_offset()
            endOffset = len(lines[1])

            if not isDeleteKey:
                firstLineIndex = control.scriptView.lines.index(firstLine)
                line2 =  control.scriptView.lines[firstLineIndex + len(lines) - 1]

                # line2 = control.scriptView.lines[startSelectionLine +1]
                # line2 = control.scriptView.lines[endLineIndex]
            else:
                line2 = firstLine.after(control)

            # Get the text on the second line beginning up to the end of the selection.
            lastLineText = line2.text[endOffset:]
            # line2.text = lastLineText
            lastLineCarryText = lastLineText

            # Remove the second line
            self.page.lines.remove(line2)
            control.scriptView.lines.remove(line2)

            # Line one will get the both texts appended.
            firstLine.text = firstLineText + lastLineText

            # If the first line's text is all deleted, the tag on the second line will be used, unless it has no text.
            # The other two cases will keep line one's tag by default.
            # if len(firstLineCarryText) == 0 and len(lastLineCarryText) > 0:
            #     firstLine.tag = line2.tag

        else:

            # Get the text on the first line beginning at the start of the selection.
            firstLineText = firstLine.text[:self.offset]
            firstLine.text = firstLineText
            # self.firstLineCarryText = firstLineText

            lastLine = control.scriptView.lines[bufferIndex + len(lines) - 1]
            endOffset = len(lines[-1])

            # Get the text on the second line beginning up to the end of the selection.
            lastLineText = lastLine.text[endOffset:]
            # lastLine.text = lastLineText

            # Gather lines to remove.
            removeLines = []
            for i in range(len(lines)-1):
                line = self.page.lines[self.line + i + 1]
                removeLines.append(line)

            # Remove the middle lines and last line
            for line in removeLines:
                self.page.lines.remove(line)
                control.scriptView.lines.remove(line)

            # Set the first line text.
            firstLine.text = firstLineText + lastLineText

        return firstLine

    def undo(self, control):
        control.category = 'scene'
        control.indexView.stack.set_visible_child_name("scene")

        redo = Insertion(self.scene, self.page, self.line, self.offset, self.text, self.tags)

        redo.modelUpdate(control)

        redo.viewUpdate(control)
        eventLine = self.page.lines[self.line]
        bufferIndex = control.scriptView.lines.index(eventLine)
        afterDeleteIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
        control.scriptView.textView.get_buffer().place_cursor(afterDeleteIter)

        control.scriptView.textView.grab_focus()

    def redo(self, control):
        control.category = 'scene'
        control.indexView.stack.set_visible_child_name("scene")

        redo = Deletion(self.scene, self.page, self.line, self.offset, self.text, self.tags)

        redo.viewUpdate(control)
        redo.modelUpdate(control)

        control.scriptView.textView.grab_focus()

    def data(self):
        return None


class Format(Event):
    def __init__(self, scene, page, line, oldTag, newTag):
        Event.__init__(self)
        self.scene = scene
        self.page = page
        self.line = line
        self.oldTag = oldTag
        self.newTag = newTag


class StartHistoryEvent(Event):

    def __init__(self, ):
        Event.__init__(self)

    def undo(self, control):
        pass

    def redo(self, control):
        pass

    def data(self):
        return None


# class NewPageEvent(Event):
#
#     def __init__(self, data, index):
#         Event.__init__(self)
#         self.data = data
#         self.index = _story.StoryIndex(index.__dict__)
#
#     def undo(self, control):
#         control.currentScene().pages.remove(self.data)
#         control.reset(False)
#         index = _story.StoryIndex(self.index)
#         index.page -=1
#         control.currentStory().index = index
#         control.load(False)
#
#     def redo(self, control):
#         control.currentScene().pages.insert(self.index.page, self.data)
#         control.reset(False)
#         control.currentStory().index = _story.StoryIndex(self.index.__dict__)
#         control.load(False)


class EventManager(object):

    def __init__(self, control):
        self.control = control
        # self.cue = [StartHistoryEvent()]
        # self.position = 0

    def initSceneHistory(self, scene, events=[]):
        scene.events = [StartHistoryEvent()]
        if len(events):
            scene.events = event
        scene.eventIndex = len(scene.events) -1

    def addEvent(self, event):

        cs = self.control.currentScene()

        # If went back in history and adding, slice off history ahead.
        if len(cs.events) > cs.eventIndex:
            cs.events = cs.events[:cs.eventIndex +1]

        cs.events.insert(cs.eventIndex +1, event)
        cs.eventIndex +=1

    def undo(self):

        cs = self.control.currentScene()

        if cs.eventIndex > 0:
            cs.events[cs.eventIndex].undo(self.control)
            cs.eventIndex -=1

    def redo(self):

        cs = self.control.currentScene()

        if cs.eventIndex < len(cs.events) -1:
            cs.eventIndex +=1
            cs.events[cs.eventIndex].redo(self.control)

    def reset(self):
        self.cue = [StartHistoryEvent()]
        self.position = 0


class View(object):
    pass
