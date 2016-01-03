
import os, json

from gi.repository import Gtk, Gdk

import _story

HISTORY_ITEM_LIMIT_PER_FILE = 3


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

        if u'heading' in tags:
            tags = tags
            raise Exception()

        self.pushedOffHeading = False

    def viewUpdate(self, control):

        # control.scriptView.textView.buffer.begin_user_action()

        scene = control.currentSequence().scenes[self.scene]
        page = scene.pages[self.page]
        eventLine = page.lines[self.line]
        bufferIndex = control.scriptView.lines.index(eventLine)

        insertIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
        endIter = control.scriptView.textView.endIter()

        if insertIter.get_offset() == endIter.get_offset():
            insertIter.backward_char()

        control.scriptView.textView.iterInfo(insertIter)

        control.scriptView.textView.buffer.insert_interactive(insertIter, self.text, len(self.text), True)

        tags = list(self.tags)

        # for i in range(len(tags)):
        #     print "bufferIndex + i", bufferIndex + i
        #     line = control.scriptView.lines[bufferIndex + i]
        #     line.tag = tags[i]
        #     control.scriptView.textView.updateLineTag(bufferIndex + i)

        # This is done vs. just doing the lines that are modified due to an unknown bug
        # that corrupts the formating in the buffer on a multline insertion.
        for i in range(len(control.scriptView.lines)):
            if control.scriptView.lines[i].tag != 'heading':
                control.scriptView.textView.updateLineTag(i)

        if self.pushedOffHeading:
            insertIter = control.scriptView.textView.insertIter()
            insertIter.backward_char()
            control.scriptView.textView.buffer.place_cursor(insertIter)
        else:
            afterInsertIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
            afterInsertIter.forward_chars(len(self.text))
            endIter = control.scriptView.textView.endIter()
            if afterInsertIter.get_offset() == endIter.get_offset():
                afterInsertIter.backward_chars(1)
            control.scriptView.textView.buffer.place_cursor(afterInsertIter)

        # control.scriptView.textView.buffer.end_user_action()

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

            # If the line in which the past occurs is empty,
            # The line being pasted on it will override it's tag.
            if len(eventLine.text) == 0:
                eventLine.tag = self.tags[0]

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

        if u'heading' in tags:
            tags = tags
            raise Exception()

        self.isDeleteKey = False

    def viewUpdate(self, control):

        scene = control.currentSequence().scenes[self.scene]
        page = scene.pages[self.page]

        eventLine = page.lines[self.line]
        bufferIndex = control.scriptView.lines.index(eventLine)

        startIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)

        endIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
        endIter.forward_chars(len(self.text))

        if startIter.get_offset() == control.scriptView.textView.endIter().get_offset():
            startIter.backward_chars(2)
            endIter.backward_chars(1)

        control.scriptView.textView.buffer.delete(startIter, endIter)

        tags = list(self.tags)

        tags = tags[:1]

        # for i in range(len(tags)):
        #     control.scriptView.textView.updateLineTag(bufferIndex + i, tags[i])

        # This is done vs. just doing the lines that are modified.
        # This Insertion has a bug, so this is done as a precaution although may be unneccesary.
        for i in range(len(control.scriptView.lines)):
            if control.scriptView.lines[i].tag != 'heading':
                control.scriptView.textView.updateLineTag(i)

        afterDeleteIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)

        control.scriptView.textView.buffer.place_cursor(afterDeleteIter)

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
        control.scriptView.textView.buffer.place_cursor(afterDeleteIter)

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

        control.scriptView.textView.buffer.delete(startIter, endIter)

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

            # control.scriptView.textView.buffer.insert(insertIter, 'xxx', len('xxx'))

            # control.scriptView.textView.iterInfo(insertIter)
            control.scriptView.textView.buffer.insert(insertIter, self.text, len(self.text))

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
            control.scriptView.textView.buffer.place_cursor(moveIter)

        else:
            eventLine = page.lines[self.line]
            bufferIndex = control.scriptView.lines.index(eventLine)
            insertIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
            insertIter.backward_char()

            # view
            control.scriptView.textView.buffer.insert(insertIter, self.text, len(self.text))

            # model

            eventLine.text = eventLine.text[:self.offset] + self.text + eventLine.text[self.offset:]

            control.scriptView.textView.updateLineTag(bufferIndex)

            moveIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
            control.scriptView.textView.buffer.place_cursor(moveIter)

        control.scriptView.textView.grab_focus()

    def redo(self, control):

        control.category = 'scene'
        control.indexView.stack.set_visible_child_name("scene")

        self.viewUpdate(control)
        self.modelUpdate(control)

        control.scriptView.textView.grab_focus()

    def data(self, control):

        scene = control.currentStory().sequences[0].scenes[self.scene]
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
        control.scriptView.textView.buffer.place_cursor(afterEventIter)

        control.scriptView.textView.resetGlobalMargin(self.beforeTags[0])

    def redo(self, control):

        self.modelUpdate(control)
        self.viewUpdate(control)

        scene = control.currentSequence().scenes[self.scene]
        page = scene.pages[self.page]
        eventLine = page.lines[self.line]
        bufferIndex = control.scriptView.lines.index(eventLine)

        afterEventIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
        control.scriptView.textView.buffer.place_cursor(afterEventIter)

        control.scriptView.textView.resetGlobalMargin(self.tags[0]) # this may cause a problem, only a multiple line format, whatever does multiline should set tag on cursor line after format.


class Start(Event):

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


class Page(Event):

    def __init__(self, scene, page):
        Event.__init__(self)
        self.scene = scene # this is the index of the new page
        self.page = page

    def undo(self, control):

        control.currentScene().pages.pop(self.page)
        cs = control.currentStory()
        if self.page == 0:
            cs.index.page = 0
        else:
            cs.index.page = self.page - 1

        cs.index.line = 0
        cs.index.offset = 0

        row = control.pageItemBox.rowAtIndex(self.page)
        control.pageItemBox.listbox.remove(row)
        control.pageItemBox.updateNumberated()

        control.category = 'scene'
        control.indexView.stack.set_visible_child_name("scene")

        control.scriptView.resetAndLoad()
        control.scriptView.show_all()

        control.scriptView.textView.grab_focus()


    def redo(self, control):

        page = _story.Page()
        scene = control.currentSequence().scenes[self.scene]

        control.currentStory().index.page = self.page

        control.currentStory().index.line = 0
        control.currentStory().index.offset = 0
        scene.pages.insert(self.page, page)


        control.reset(data=False)
        control.scriptView.updateTitles()
        control.load(data=False)

        row = control.pageItemBox.rowAtIndex(self.page)
        control.pageItemBox.listbox.remove(row)
        control.pageItemBox.updateNumberated()

        control.category = 'scene'
        control.indexView.stack.set_visible_child_name("scene")

        control.scriptView.resetAndLoad()
        control.scriptView.show_all()

        control.scriptView.textView.grab_focus()


class EventManager(object):

    def __init__(self, control):
        self.control = control

    def addEvent(self, event):

        currentScene = self.control.currentScene()
        currentScene.eventCount += 1

        currentScene.saveIndex += 1

        # If an undone occured, then remove all events ahead of current event.
        if currentScene.hasUndone:
            currentScene.undoIndex = 0
            # currentScene.eventCount -= 1
            # currentScene.eventCount -= currentScene.undoIndex
            # currentScene.eventCount += 1

            if currentScene.saveIndex < 0:
                currentScene.saveIndex = 0

            currentScene.archiveManager.removeEventsAfterIndex(currentScene.eventIndex + 1)
            currentScene.archiveManager.removePathsAfterIndex(currentScene.archiveManager.pathIndex)
            currentScene.hasUndone = False
            currentScene.archiveManager.save()

        if self.control.scriptView.textView.undoing:

            if len(currentScene.archiveManager.events) == HISTORY_ITEM_LIMIT_PER_FILE:

                if currentScene.archiveManager.currentPathExists():
                    currentScene.archiveManager.save()

                    currentScene.archiveManager.events = {}
                    currentScene.eventIndex = 0
                    currentScene.archiveManager.events[currentScene.eventIndex] = event
                    currentScene.archiveManager.pathIndex += 1
                    currentScene.archiveManager.appendExistingPath()
                    currentScene.archiveManager.save()

                else:
                    currentScene.archiveManager.pathIndex += 1
                    currentScene.archiveManager.appendExistingPath()
                    currentScene.archiveManager.save()

                    currentScene.archiveManager.events = {}
                    currentScene.eventIndex = 0
                    currentScene.archiveManager.events[currentScene.eventIndex] = event
                    currentScene.archiveManager.pathIndex += 1
                    currentScene.archiveManager.appendExistingPath()
                    currentScene.archiveManager.save()

            else:

                if currentScene.archiveManager.currentPathExists():
                    currentScene.eventIndex += 1
                    currentScene.archiveManager.events[currentScene.eventIndex] = event
                    currentScene.archiveManager.save()

                else:
                    currentScene.eventIndex += 1
                    currentScene.archiveManager.events[currentScene.eventIndex] = event
                    currentScene.archiveManager.pathIndex += 1
                    currentScene.archiveManager.appendExistingPath()
                    currentScene.archiveManager.save()

        else:

            if len(currentScene.archiveManager.events) == HISTORY_ITEM_LIMIT_PER_FILE:

                if currentScene.archiveManager.currentPathExists():
                    currentScene.archiveManager.save()

                    currentScene.archiveManager.events = {}
                    currentScene.eventIndex = 0
                    currentScene.archiveManager.events[currentScene.eventIndex] = event
                    currentScene.archiveManager.pathIndex += 1
                    currentScene.archiveManager.appendExistingPath()
                    currentScene.archiveManager.save()

                else:
                    currentScene.archiveManager.pathIndex += 1
                    currentScene.archiveManager.appendExistingPath()
                    currentScene.archiveManager.save()

                    currentScene.archiveManager.events = {}
                    currentScene.eventIndex = 0
                    currentScene.archiveManager.events[currentScene.eventIndex] = event
                    currentScene.archiveManager.pathIndex += 1
                    currentScene.archiveManager.appendExistingPath()
                    currentScene.archiveManager.save()

            else:
                currentScene.eventIndex += 1
                currentScene.archiveManager.events[currentScene.eventIndex] = event

        self.control.searchView.reset()
        self.control.updateHistoryColor()
        self.control.currentStory().saved = False

    def undo(self):
        currentScene = self.control.currentScene()
        currentScene.undo(self.control)
        self.control.searchView.reset()
        self.control.updateHistoryColor()
        self.scroll()

    def redo(self):
        currentScene = self.control.currentScene()
        currentScene.redo(self.control)
        self.control.searchView.reset()
        self.control.updateHistoryColor()
        self.scroll()

    def scroll(self):
        lineIndex = self.control.scriptView.textView.insertIter().get_line()
        scrollIter = self.control.scriptView.textView.buffer.get_iter_at_line(lineIndex)
        self.control.scriptView.textView.scroll_to_iter(scrollIter, 0, 0, 0, True)


class View(object):
    pass
