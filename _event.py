
from gi.repository import Gtk, Gdk

import _story

class Event(object):
    def __init__(self, chained=False):
        # print self.__class__.__name__, "Event"
        self.chained = chained

        self.scene = None
        self.page = None
        self.line = None
        self.offset = None
        self.text = None
        self.tags = None

        self.beforeTags = []
        self.pushedOffHeading = False

    def redo(self):
        pass

    def undo(self):
        pass

    def data(self, currentStory):
        data = {}
        data["name"] = self.__class__.__name__
        data["scene"] = self.scene
        data["page"] = self.page
        data["line"] = self.line
        data["offset"] = self.offset
        data['text'] = self.text
        data['tags'] = self.tags

        data['beforeTags'] = self.beforeTags
        data['pushedOffHeading'] = self.pushedOffHeading
        return data


class Insertion(Event):
    def __init__(self, scene, page, line, offset, text, tags):
        Event.__init__(self)
        self.scene = scene
        self.page = page
        self.line = line # this the index of the page line
        self.offset = offset
        self.text = text
        self.tags = tags

        self.pushedOffHeading = False

    def viewUpdate(self, control):

        scene = control.currentSequence().scenes[self.scene]
        page = scene.pages[self.page]
        eventLine = page.lines[self.line]
        bufferIndex = control.scriptView.lines.index(eventLine)

        insertIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
        control.scriptView.textView.get_buffer().insert(insertIter, self.text, len(self.text))

        tags = list(self.tags)

        for i in range(len(tags)):
            line = control.scriptView.lines[bufferIndex + i]
            control.scriptView.lines[bufferIndex + i].tag = tags[i]
            control.scriptView.textView.updateLineTag(bufferIndex + i)

        if self.pushedOffHeading:
            insertIter = control.scriptView.textView.insertIter()
            insertIter.backward_char()
            control.scriptView.textView.get_buffer().place_cursor(insertIter)
        else:
            afterInsertIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
            afterInsertIter.forward_chars(len(self.text))
            control.scriptView.textView.get_buffer().place_cursor(afterInsertIter)

    def modelUpdate(self, control, pushedOffHeading=False):

        scene = control.currentSequence().scenes[self.scene]
        page = scene.pages[self.page]

        lines = self.text.split("\n")

        eventLine = page.lines[self.line]

        tags = list(self.tags)

        # Only inserting text, no new lines.
        if len(lines) == 1:
            word = lines[0]
            cs = control.currentStory()
            insertOffset = cs.index.offset
            first = eventLine.text[:self.offset]
            last = eventLine.text[self.offset:]
            text = first + word + last
            eventLine.text = text
            eventLine.tag = tags[0]

        else:

            # Inserting extra lines, carry text will be set.
            carryText = eventLine.text[self.offset:]

            # The line of insertion already exists, so it will not need to be made.
            eventLineAppendText = lines.pop(0)
            eventLineTag = tags.pop(0)

            # The carry text needs to be removed from the current line.
            eventLine.text = eventLine.text[:self.offset]

            # Append inserted text at the end of the first line.
            eventLine.text = eventLine.text + eventLineAppendText

            # Create and insert all new lines.
            insertIndex = page.lines.index(eventLine) + 1
            scriptLineIndex = control.scriptView.lines.index(eventLine) + 1

            for i in range(len(lines)):
                newLine = _story.Line(lines[i], tag=tags[i])
                newLine.heading = eventLine.heading
                page.lines.insert(insertIndex + i, newLine)

                # ScriptView need a reference to each line as well.
                control.scriptView.lines.insert(scriptLineIndex + i, newLine)

            # Last line will get the carry text.
            newLine.text += carryText

    def undo(self, control):
        control.category = 'scene'
        control.indexView.stack.set_visible_child_name("scene")

        scene = control.currentSequence().scenes[self.scene]
        page = scene.pages[self.page]

        undo = Deletion(self.scene, self.page, self.line, self.offset, self.text, self.beforeTags)
        undo.modelUpdate(control)
        undo.viewUpdate(control)

        control.scriptView.textView.grab_focus()

    def redo(self, control):

        control.category = 'scene'
        control.indexView.stack.set_visible_child_name("scene")

        self.modelUpdate(control)
        self.viewUpdate(control)

        control.scriptView.textView.grab_focus()


class Deletion(Event):
    def __init__(self, scene, page, line, offset, text, tags):
        Event.__init__(self)
        self.scene = scene
        self.page = page
        self.line = line
        self.offset = offset
        self.text = text
        self.tags = tags

        self.isDeleteKey = False

    def viewUpdate(self, control):

        scene = control.currentSequence().scenes[self.scene]
        page = scene.pages[self.page]

        eventLine = page.lines[self.line]
        bufferIndex = control.scriptView.lines.index(eventLine)

        startIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)

        endIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
        endIter.forward_chars(len(self.text))

        control.scriptView.textView.get_buffer().delete(startIter, endIter)

        tags = list(self.tags)

        tags = tags[:1]

        for i in range(len(tags)):
            control.scriptView.textView.updateLineTag(bufferIndex + i, tags[i])

        afterDeleteIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
        control.scriptView.textView.get_buffer().place_cursor(afterDeleteIter)

    def modelUpdate(self, control, isDeleteKey=False):

        scene = control.currentSequence().scenes[self.scene]
        page = scene.pages[self.page]

        eventLine = page.lines[self.line]
        bufferIndex = control.scriptView.lines.index(eventLine)

        firstLine = eventLine
        if isDeleteKey:
            self.isDeleteKey = isDeleteKey

        lines = self.text.split("\n")

        if len(lines) == 1:
            frontString = firstLine.text[:self.offset]
            endString = firstLine.text[self.offset+len(lines[0]):]
            firstLine.text = frontString + endString
            return firstLine

        elif len(lines) == 2:

            # Get the text on the first line beginning at the start of the selection.
            firstLineText = firstLine.text[:self.offset]
            firstLine.text = firstLineText

            endOffset = len(lines[1])

            if not isDeleteKey:
                firstLineIndex = control.scriptView.lines.index(firstLine)
                line2 =  control.scriptView.lines[firstLineIndex + len(lines) - 1]

            else:
                line2 = firstLine.after(control)

            # Get the text on the second line beginning up to the end of the selection.
            lastLineText = line2.text[endOffset:]
            lastLineCarryText = lastLineText

            # Remove the second line
            page.lines.remove(line2)
            control.scriptView.lines.remove(line2)

            # Line one will get the both texts appended.
            firstLine.text = firstLineText + lastLineText

        else:

            # Get the text on the first line beginning at the start of the selection.
            firstLineText = firstLine.text[:self.offset]
            firstLine.text = firstLineText

            lastLine = control.scriptView.lines[bufferIndex + len(lines) - 1]
            endOffset = len(lines[-1])

            # Get the text on the second line beginning up to the end of the selection.
            lastLineText = lastLine.text[endOffset:]

            # Gather lines to remove.
            removeLines = []
            for i in range(len(lines)-1):
                line = page.lines[self.line + i + 1]
                removeLines.append(line)

            # Remove the middle lines and last line
            for line in removeLines:
                page.lines.remove(line)
                control.scriptView.lines.remove(line)

            # Set the first line text.
            firstLine.text = firstLineText + lastLineText

        tags = list(self.tags)

        tags = tags[:1]

        for i in range(len(tags)):
            control.scriptView.textView.updateLineTag(bufferIndex + i, tags[i])

        for i in range(len(tags)):
            control.scriptView.lines[bufferIndex + i].tag = tags[i]

        return firstLine

    def undo(self, control):
        control.category = 'scene'
        control.indexView.stack.set_visible_child_name("scene")

        scene = control.currentSequence().scenes[self.scene]
        page = scene.pages[self.page]

        undo = Insertion(self.scene, self.page, self.line, self.offset, self.text, self.beforeTags)
        undo.modelUpdate(control)
        undo.viewUpdate(control)

        eventLine = page.lines[self.line]
        bufferIndex = control.scriptView.lines.index(eventLine)
        afterDeleteIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
        control.scriptView.textView.get_buffer().place_cursor(afterDeleteIter)

        control.scriptView.textView.grab_focus()

    def redo(self, control):
        control.category = 'scene'
        control.indexView.stack.set_visible_child_name("scene")

        self.viewUpdate(control)
        self.modelUpdate(control)

        control.scriptView.textView.grab_focus()


class Backspace(Event):
    def __init__(self, scene, page, line, offset, text, tags):
        Event.__init__(self)
        self.scene = scene
        self.page = page
        self.line = line
        self.offset = offset
        self.text = text
        self.tags = tags # First tag is previous line, next is where backspace occured.

        self.carryText = ''

    def viewUpdate(self, control):

        scene = control.currentSequence().scenes[self.scene]
        page = scene.pages[self.page]

        eventLine = page.lines[self.line]
        bufferIndex = control.scriptView.lines.index(eventLine)

        startIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
        startIter.backward_char()
        startIterOffset = startIter.get_line_offset()

        endIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)

        control.scriptView.textView.get_buffer().delete(startIter, endIter)

        if self.offset != 0:
            control.scriptView.textView.updateLineTag(bufferIndex, self.tags[0])

    def modelUpdate(self, control, isBackspaceKey=False, isDeleteKey=False):

        scene = control.currentSequence().scenes[self.scene]
        page = scene.pages[self.page]
        eventLine = page.lines[self.line]
        bufferIndex = control.scriptView.lines.index(eventLine)

        if self.offset == 0:
            self.carryText = eventLine.text

            previousLine = page.lines[self.line - 1]
            previousLine.text += self.carryText

            page.lines.remove(eventLine)

            control.scriptView.lines.remove(eventLine)

        else:
            index = control.currentStory().index.offset
            eventLine.text = eventLine.text[:index-1] + eventLine.text[index:]

        return

    def undo(self, control):

        control.category = 'scene'
        control.indexView.stack.set_visible_child_name("scene")

        scene = control.currentSequence().scenes[self.scene]
        page = scene.pages[self.page]

        if self.offset == 0:
            # view
            previousLine = page.lines[self.line - 1]
            bufferIndex = control.scriptView.lines.index(previousLine)
            insertIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
            insertIter.forward_to_line_end()

            zeroSpaceCharacterAdjustment = 0
            if insertIter.get_offset() == control.scriptView.textView.endIter().get_offset():
                zeroSpaceCharacterAdjustment = 1

            insertIter.backward_chars(len(self.carryText) + zeroSpaceCharacterAdjustment)

            # control.scriptView.textView.get_buffer().insert(insertIter, 'xxx', len('xxx'))

            # control.scriptView.textView.iterInfo(insertIter)
            control.scriptView.textView.get_buffer().insert(insertIter, self.text, len(self.text))

            # model
            newLine = _story.Line(self.carryText, tag=self.tags[1])
            newLine.heading = previousLine.heading
            page.lines.insert(bufferIndex, newLine)

            # remove carry text from previous line
            previousLine.text = previousLine.text[:-len(self.carryText)]

            # ScriptView need a reference to each line as well.
            control.scriptView.lines.insert(bufferIndex + 1, newLine)

            control.scriptView.textView.updateLineTag(bufferIndex)

            moveIter = control.scriptView.textView.iterAtLocation(bufferIndex + 1, self.offset)
            control.scriptView.textView.get_buffer().place_cursor(moveIter)

        else:
            eventLine = page.lines[self.line]
            bufferIndex = control.scriptView.lines.index(eventLine)
            insertIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
            insertIter.backward_char()

            # view
            control.scriptView.textView.get_buffer().insert(insertIter, self.text, len(self.text))

            # model

            eventLine.text = eventLine.text[:self.offset] + self.text + eventLine.text[self.offset:]

            control.scriptView.textView.updateLineTag(bufferIndex)

            moveIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
            control.scriptView.textView.get_buffer().place_cursor(moveIter)

        control.scriptView.textView.grab_focus()

    def redo(self, control):

        control.category = 'scene'
        control.indexView.stack.set_visible_child_name("scene")

        self.viewUpdate(control)
        self.modelUpdate(control)

        control.scriptView.textView.grab_focus()

    def data(self, currentStory):

        scene = currentStory.sequences[0].scenes[self.scene]
        page = scene.pages[self.page]

        data = {}
        data["name"] = self.__class__.__name__
        data["scene"] = self.scene
        data["page"] = self.page
        data["line"] = self.line
        data["offset"] = self.offset
        data['text'] = self.text
        data['tags'] = self.tags
        data['carryText'] = self.carryText
        return data


class FormatLines(Event):
    def __init__(self, scene, page, line, offset, text, tags):
        Event.__init__(self)
        self.scene = scene
        self.page = page
        self.line = line
        self.offset = offset
        self.text = text
        self.tags = tags

        self.beforeTags = []

    def viewUpdate(self, control):
        scene = control.currentSequence().scenes[self.scene]
        page = scene.pages[self.page]
        eventLine = page.lines[self.line]
        bufferIndex = control.scriptView.lines.index(eventLine)

        for i in range(len(self.tags)):
            control.scriptView.textView.updateLineTag(bufferIndex + i, self.tags[i])

    def modelUpdate(self, control):
        scene = control.currentSequence().scenes[self.scene]
        page = scene.pages[self.page]
        eventLine = page.lines[self.line]

        for i in range(len(self.tags)):
            eventLine.tag = self.tags[i]
            eventLine = eventLine.after(control)

    def undo(self, control):

        scene = control.currentSequence().scenes[self.scene]
        page = scene.pages[self.page]
        eventLine = page.lines[self.line]
        bufferIndex = control.scriptView.lines.index(eventLine)

        for i in range(len(self.beforeTags)):
            eventLine.tag = self.beforeTags[i]
            eventLine = eventLine.after(control)

        for i in range(len(self.beforeTags)):
            control.scriptView.textView.updateLineTag(bufferIndex + i, self.beforeTags[i])

        afterEventIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
        control.scriptView.textView.get_buffer().place_cursor(afterEventIter)

        control.scriptView.textView.resetGlobalMargin(self.beforeTags[0])

    def redo(self, control):

        self.modelUpdate(control)
        self.viewUpdate(control)

        scene = control.currentSequence().scenes[self.scene]
        page = scene.pages[self.page]
        eventLine = page.lines[self.line]
        bufferIndex = control.scriptView.lines.index(eventLine)

        afterEventIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
        control.scriptView.textView.get_buffer().place_cursor(afterEventIter)

        control.scriptView.textView.resetGlobalMargin(self.tags[0]) # this may cause a problem, only a multiple line format, whatever does multiline should set tag on cursor line after format.


class StartHistoryEvent(Event):

    def __init__(self, ):
        Event.__init__(self)

    def undo(self, control):
        pass

    def redo(self, control):
        pass

    def data(self, currentStory):
        data = {}
        data["name"] = str(self.__class__.__name__)
        data["scene"] = None
        data["page"] = None
        data["line"] = None
        data["offset"] = None
        data['text'] = None
        data['tags'] = None
        return data

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

    def initSceneHistory(self, scene, events=[]):
        scene.events = [StartHistoryEvent()]
        if len(events):
            scene.events = event
        scene.eventIndex = len(scene.events) -1

    def addEvent(self, event):

        self.control.searchView.reset()
        currentScene = self.control.currentScene()

        # If went back in history and adding, slice off history ahead.
        if len(currentScene.events) > currentScene.eventIndex:
            currentScene.events = currentScene.events[:currentScene.eventIndex +1]
            if self.control.currentScene().eventIndex < self.control.currentScene().sessionEventIndex:
                self.control.currentScene().sessionEventIndex = self.control.currentScene().eventIndex
            self.control.updateHistoryColor()

        currentScene.events.insert(currentScene.eventIndex +1, event)
        currentScene.eventIndex +=1

    def undo(self):
        self.control.searchView.reset()
        self.control.currentScene().undo(self.control)
        self.control.updateHistoryColor()
        self.scroll()

    def redo(self):
        self.control.searchView.reset()
        self.control.currentScene().redo(self.control)
        self.control.updateHistoryColor()
        self.scroll()

    def scroll(self):
        lineIndex = self.control.scriptView.textView.insertIter().get_line()
        scrollIter = self.control.scriptView.textView.get_buffer().get_iter_at_line(lineIndex)
        self.control.scriptView.textView.scroll_to_iter(scrollIter, 0, 0, 0, True)


class View(object):
    pass
