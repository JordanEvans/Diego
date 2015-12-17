
from gi.repository import Gtk, Gdk

import _story

class Event(object):
    def __init__(self, chained=False):
        print self.__class__.__name__, "Event"
        self.chained = chained

        self.scene = None
        self.page = None
        self.line = None
        self.offset = None
        self.text = None
        self.tags = None

    def redo(self):
        pass

    def undo(self):
        pass

    def data(self, currentStory):
        data = {}
        data["name"] = self.__class__.__name__
        data["scene"] = currentStory.sequences[0].scenes.index(self.scene)
        data["page"] = self.scene.pages.index(self.page)
        data["line"] = self.line
        data["offset"] = self.offset
        data['text'] = self.text
        data['tags'] = self.tags
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

        self.modelUpdate(control)
        self.viewUpdate(control)

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
            carryText = firstLine.text[self.offset:]

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

                # self.newLines.append(newLine)
                index += 1

            # Last line will get the carry text.
            newLine.text += carryText


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

        eventLine = self.page.lines[self.line]
        bufferIndex = control.scriptView.lines.index(eventLine)

        startIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)

        endIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
        endIter.forward_chars(len(self.text))

        control.scriptView.textView.get_buffer().delete(startIter, endIter)

        control.scriptView.textView.updateLineTag(bufferIndex, self.tags[0])

        afterDeleteIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
        control.scriptView.textView.get_buffer().place_cursor(afterDeleteIter)

    def modelUpdate(self, control, isDeleteKey=False):

        eventLine = self.page.lines[self.line]
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

        eventLine = self.page.lines[self.line]
        bufferIndex = control.scriptView.lines.index(eventLine)

        startIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)
        startIter.backward_char()
        startIterOffset = startIter.get_line_offset()

        endIter = control.scriptView.textView.iterAtLocation(bufferIndex, self.offset)

        control.scriptView.textView.get_buffer().delete(startIter, endIter)

        control.scriptView.textView.updateLineTag(bufferIndex, self.tags[0])

    def modelUpdate(self, control, isBackspaceKey=False, isDeleteKey=False):

        eventLine = self.page.lines[self.line]
        bufferIndex = control.scriptView.lines.index(eventLine)

        if self.offset == 0:
            self.carryText = eventLine.text

            previousLine = self.page.lines[self.line - 1]
            previousLine.text += self.carryText

            self.page.lines.remove(eventLine)

            control.scriptView.lines.remove(eventLine)

        else:
            index = control.currentStory().index.offset
            eventLine.text = eventLine.text[:index-1] + eventLine.text[index:]

        return

    def undo(self, control):

        control.category = 'scene'
        control.indexView.stack.set_visible_child_name("scene")

        if self.offset == 0:
            # view
            previousLine = self.page.lines[self.line - 1]
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
            self.page.lines.insert(bufferIndex, newLine)

            # remove carry text from previous line
            previousLine.text = previousLine.text[:-len(self.carryText)]

            # ScriptView need a reference to each line as well.
            control.scriptView.lines.insert(bufferIndex + 1, newLine)

            control.scriptView.textView.updateLineTag(bufferIndex)

            moveIter = control.scriptView.textView.iterAtLocation(bufferIndex + 1, self.offset)
            control.scriptView.textView.get_buffer().place_cursor(moveIter)

        else:
            eventLine = self.page.lines[self.line]
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
        data = {}
        data["name"] = self.__class__.__name__
        data["scene"] = currentStory.sequences[0].scenes.index(self.scene)
        data["page"] = self.scene.pages.index(self.page)
        data["line"] = self.line
        data["offset"] = self.offset
        data['text'] = self.text
        data['tags'] = self.tags
        data['carryText'] = self.carryText
        return data


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
        currentScene = self.control.currentScene()

        # If went back in history and adding, slice off history ahead.
        if len(currentScene.events) > currentScene.eventIndex:
            currentScene.events = currentScene.events[:currentScene.eventIndex +1]
            self.control.updateColor()

        currentScene.events.insert(currentScene.eventIndex +1, event)
        currentScene.eventIndex +=1

    def undo(self):
        self.control.currentScene().undo(self.control)

        self.control.updateColor()

    def redo(self):
        self.control.currentScene().redo(self.control)

        self.control.updateColor()


    # def updateColor(self):
    #     val = 0.94
    #     selectColor = Gdk.RGBA(0.75, 0.75, 0.85, 1.0)
    #     forground = Gdk.RGBA(0.0, 0.0, 0.0, 1.0)
    #     if self.control.currentScene().eventIndex < len(self.control.currentScene().events) - 1:
    #         color = Gdk.RGBA(val, val, val, 1.0)
    #         self.control.scriptView.textView.modify_bg(Gtk.StateType.NORMAL, color.to_color())
    #         self.control.scriptView.textView.modify_bg(Gtk.StateType.SELECTED, selectColor.to_color())
    #         self.control.scriptView.textView.modify_fg(Gtk.StateType.SELECTED, forground.to_color())
    #     else:
    #         color = Gdk.RGBA(1.0, 1.0, 1.0, 1.0)
    #         self.control.scriptView.textView.modify_bg(Gtk.StateType.NORMAL, color.to_color())
    #         self.control.scriptView.textView.modify_bg(Gtk.StateType.SELECTED, selectColor.to_color())
    #         self.control.scriptView.textView.modify_fg(Gtk.StateType.SELECTED, forground.to_color())
    #
    #     self.control.scriptView.textView.descriptionTag.props.background_rgba = color
    #     self.control.scriptView.textView.characterTag.props.background_rgba = color
    #     self.control.scriptView.textView.dialogTag.props.background_rgba = color
    #     self.control.scriptView.textView.parentheticTag.props.background_rgba = color
    #     self.control.scriptView.textView.sceneHeadingTag.props.background_rgba = color
    #
    #     for he in self.control.scriptView.headingEntries:
    #         he.modify_bg(Gtk.StateType.NORMAL, color.to_color())
    #

class View(object):
    pass
