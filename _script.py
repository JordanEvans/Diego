import string, os, re

from gi.repository import Gtk, Gdk, GLib, Pango, GObject

import _event
import _story
import _dialog

ZERO_WIDTH_SPACE = u'\u200B'.encode('utf-8')
HEADING = '\xef\xbf\xbc'
NON_WORD_CHARACTERS = list(""" \\/~!@#$%^&*()_+=-{}|[]:";'<>?,.`\n""") + [HEADING]

DESCRIPTION_WIDTH = 52.0
CHARACTER_WIDTH_FACTOR = 0.35
DIALOG_WIDTH_FACTOR = 0.5
PARENTHETIC_WIDTH_FACTOR = 0.50

DIALOG_LEFT_FACTOR = 0.34
CHARACTER_LEFT_FACTOR = 0.536
PARENTHETIC_LEFT_FACTOR = 0.45

TEXT_VIEW_FACTOR = 1.41667

class CompletionManager(object):

    def __init__(self, control):
        self.control = control
        self.trie = None
        self.prefix = ''
        self.iter = None
        self.punctuation = NON_WORD_CHARACTERS

        self.hasInserted = False

    def insert(self):
        pass

    def delete(self):
        pass

    def cursorPrefix(self):

        insertIter = self.control.scriptView.textView.insertIter()

        prefix = ''
        moved = insertIter.backward_char()
        char = insertIter.get_char()
        prefix = ''

        while char not in self.punctuation:
            prefix = char + prefix
            moved = insertIter.backward_char()
            if moved:
                char = insertIter.get_char()
            else:
                break

        try:
            unicode(prefix)
        except:
            prefix = ''

        return prefix

    def updateIter(self):
        cursorPrefix = self.cursorPrefix()
        if len(cursorPrefix) > 1 and cursorPrefix != self.prefix:
            suffixes = [item[0] for item in self.trie.items(unicode(cursorPrefix))]
            self.iter = CompletionIter(suffixes)
            if len(suffixes) and len(cursorPrefix) == len(suffixes[0]):
                self.forward()
        self.prefix = cursorPrefix

    def forward(self):
        if self.iter is not None:
            self.iter.forward()

    def backward(self):
        if self.iter is not None:
            self.iter.backward()

    def suffix(self):
        if self.iter is not None:
            return self.iter.suffix()[len(self.prefix):]
        return ''

    def reset(self):
        self.prefix = ''
        self.iter = None


class CompletionIter(object):

    def __init__(self, suffixes):
        self.suffixes = suffixes
        self.index = 0

    def forward(self):
        if self.index + 1 < len(self.suffixes):
            self.index += 1
        else:
            self.index = 0

    def backward(self):
        if self.index - 1 >= 0:
            self.index -= 1
        else:
            self.index = len(self.suffixes) - 1

    def suffix(self):
        if len(self.suffixes):
            return self.suffixes[self.index]
        return ''


class Completion(object):

    def __init__(self, control, pageLineIndex, offset, suffix, sceneIndex, pageIndex):
        self.control = control
        self.pageLineIndex = pageLineIndex
        self.offset = offset
        self.suffix = suffix
        self.sceneIndex = sceneIndex
        self.pageIndex = pageIndex

    def insert(self):
        line = self.control.currentStory().sequences[0].scenes[self.sceneIndex].pages[self.pageIndex].lines[self.pageLineIndex]
        event = _event.Insertion(self.sceneIndex,
            self.pageIndex,
            self.pageLineIndex,
            self.offset,
            self.suffix,
            [line.tag])
        event.beforeTags = [line.tag]
        self.control.eventManager.addEvent(event)
        event.modelUpdate(self.control)
        event.viewUpdate(self.control)

    def delete(self):
        line = self.control.currentStory().sequences[0].scenes[self.sceneIndex].pages[self.pageIndex].lines[self.pageLineIndex]
        print "delete", line
        event = _event.Deletion(self.sceneIndex,
            self.pageIndex,
            self.pageLineIndex,
            self.offset,
            self.suffix,
            [line.tag])
        event.beforeTags = [line.tag]
        self.control.eventManager.addEvent(event)
        event.modelUpdate(self.control)
        event.viewUpdate(self.control)


class TagIter(object):

    def __init__(self):
        self.tags = ['description', 'character', 'dialog', 'parenthetic']#, 'sceneHeading']
        self.index = 0

    def tag(self):
        return self.tags[self.index]

    def increment(self):
        if self.index + 1 == len(self.tags):
            self.index = 0
        else:
            self.index += 1

    def reset(self):
        self.index = 0

    def load(self, tag='description'):
        if tag not in self.tags:
            tag = 'description'
        index = self.tags.index(tag)
        self.index = index

    def updateMode(self, control):
        self.index = 0
        if control.currentStory().isScreenplay:
            self.tags = ['description', 'character', 'dialog', 'parenthetic']#, 'sceneHeading']
        else:
            self.tags = ['description', 'character', 'dialog', 'parenthetic']


class SceneHeading(object):
    def __init__self(self, intExt='', location='', time='', notation =''):
        self.intExt = intExt
        self.location = location
        self.time = time
        self.notation = notation

    def componentsFromString(self, text):
        if len(text) == 0:
            return ['','','','']

        intExt = ''
        location = ''
        time = ''
        notation = ''

        split = text.split('.')

        if len(split) > 1 and split[0] == "INT" and split[1] == "/EXT":
            intExt = "INT./EXT."
        else:
            intExt = split[0]

        if len(split) > 1:
            split2 = "".join(split[1:]).split('-')
            if len(split2) == 1:
                location = split2[0]
            elif len(split2) == 2:
                location, time = split2[0], split2[1]
            else:
                location, time = split2[0], split2[1]
                notation = " - ".join(split2[2:])

        #if intExt == 'INT./EXT.':
        location.lstrip('/EXT')
        if len(location) > 3:
            if location[:4] == '/EXT':
                location = location[4:]

        components = intExt, location, time, notation
        stripped = []
        for component in components:
            stripped.append(component.lstrip().rstrip())
        components = stripped

        # print "x", intExt
        if intExt not in ["INT", "EXT", "INT./EXT."]:
            components = ['','','','','']

        return components

    def cursorComponent(self, text, offset):

        component = 'intExt'
        hitLocation = False
        hitTime = False

        split = text.split(" ")

        if len(split) == 1:
            return component
        else:
            if split[0] == '':
                return component
            elif offset <= len(split[0]):
                return component
            else:
                for ie in ['INT.', 'EXT.', 'INT./EXT.']:
                    if ie in split[0]:
                        if offset <= len(ie):
                            return component

        for i in range(len(text)):

            if offset == i:
                return component

            c = text[i]

            if c == ' ' and component not in ['location', 'time', 'notation']:
                component = 'location'

            elif c == '-' and component not in ['time', 'notation']:
                component = 'time'

            elif c == '-' and component in ['time']:
                component = 'notation'

        return component

    # def completeLine(self, line, offset):
    #     #components = self.componentsFromString(line.text)
    #     print self.cursorComponent(line, offset)

    def location(self, text):
        components = self.componentsFromString(text)
        if len(components) > 1:
            return components[1]
        else:
            return ""

    def time(self, text):
        components = self.componentsFromString(text)
        if len(components) > 2:
            return components[2]
        else:
            return ""


class NameIter(object):

    def __init__(self, names, initChar):
        self.names = names
        self.initChar = initChar
        self.index = 0

    def name(self):
        return self.names[self.index]

    def increment(self):
        if self.index + 1 == len(self.names):
            self.index = 0
        else:
            self.index += 1

    def previous(self):
        if self.index == 0:
            index = len(self.names) -1
        else:
            index = self.index - 1
        return self.names[index]

    def reset(self):
        self.index = 0

    def load(self, name=''):
        index = self.names.index(names)
        self.index = index


class Heading(object):
    def __init__(self, story, sequence, scene, page):
        self.story = story
        self.sequence = sequence
        self.scene = scene
        self.page = page
        self.tag = 'heading'


class TextView(Gtk.TextView):
    def __init__(self, control):
        Gtk.TextView.__init__(self)

        self.control = control

        self.completionManager = CompletionManager(self.control)
        self.completion = None
        self.completing = False
        self.completeReset = False

        self.selectionMarkStart = None
        self.selectionMarkEnd = None

        self.word = []

        self.tagIter = TagIter()

        self.settingMargin = False

        self.fontSize = 10
        self.width = 749
        self.descriptionWidth = int(DESCRIPTION_WIDTH * self.fontSize) #549
        self.characterWidth = self.descriptionWidth * CHARACTER_WIDTH_FACTOR
        self.dialogWidth = self.descriptionWidth * DIALOG_WIDTH_FACTOR

        descriptionLeftMargin = self.descriptionWidth * 0.1
        characterLeftMargin = self.descriptionWidth * CHARACTER_LEFT_FACTOR
        dialogLeftMargin = self.descriptionWidth * DIALOG_LEFT_FACTOR
        parentheticLeftMargin = self.descriptionWidth * PARENTHETIC_LEFT_FACTOR

        self.descriptionLeftMargin = descriptionLeftMargin
        self.characterLeftMargin = characterLeftMargin
        self.dialogLeftMargin = dialogLeftMargin
        self.parentheticLeftMargin = parentheticLeftMargin

        self.descriptionRightMargin = self.width - (self.descriptionLeftMargin + self.descriptionWidth)
        self.characterRightMargin = self.width - (self.characterLeftMargin + self.characterWidth)
        self.dialogRightMargin = self.width - (self.characterLeftMargin + self.characterWidth)

        drm = self.descriptionRightMargin
        crm = self.characterRightMargin
        ddrm = self.dialogRightMargin

        self.props.left_margin = self.descriptionLeftMargin
        self.props.right_margin = self.descriptionRightMargin

        self.set_wrap_mode(Gtk.WrapMode.WORD)

        self.props.pixels_below_lines = 10
        self.props.pixels_above_lines = 10

        self.connections()
        self.createTags()
        self.resetTags()

        self.forcingWordEvent = False
        self.newLineEvent = False
        self.deleteEvent = False
        self.backspaceEvent = False
        self.arrowPress = False
        self.cutPress = False
        self.formatingLine = False

        self.nameIter = None
        self.sceneHeadingIter = None

        self.intExts = ["INT.", "EXT.", "INT./EXT."]
        self.selectionTags = []
        self.selectedClipboard = []

    # Press/Release Handling
    def buttonPress(self, widget, event):
        self.forceWordEvent()
        if self.control.currentLine().tag == 'sceneHeading':
            self.updateNameLocationAndTime()

    def buttonRelease(self, widget, event):

        buttonReleaseScene = self.control.currentScene()

        self.removeCrossPageSelection()

        self.control.scriptView.updateCurrentStoryIndex()
        self.tagIter.load(self.control.currentLine().tag)

        tag = self.updateLineTag()
        self.selectedClipboard = []

        self.updatePanel()

        tag = self.tagIter.tag()
        # tag = self.control.currentLine().tag
        self.resetGlobalMargin(tag)

        # This forces the cursor before the ZERO_WIDTH_SPACE
        insertIter = self.insertIter()
        if insertIter.get_offset() == self.endIter().get_offset():
            insertIter.backward_char()
            bounds = self.get_buffer().get_selection_bounds()
            if bounds:
                startMark = self.iterMark(bounds[0])
                bounds[1].backward_char()
                endMark = self.iterMark(bounds[1])
            self.get_buffer().place_cursor(insertIter)
            if bounds:
                self.get_buffer().select_range(self.markIter(startMark), self.markIter(endMark))

        if tag == 'sceneHeading':
            self.updateNameLocationAndTime()

    def keyPress(self, widget, event):

        if self.completion:
            if event.string.isalpha() and event.string != ' ' or event.keyval in [65289, 65288, 65535]: # tab, backspace, del
                self.completion.delete()

                if event.keyval == 65289: # tab
                    pass
                else:
                    self.completeReset = True
                    self.completion = None
                    self.completionManager.reset()

        self.forcingWordEvent = False
        self.newLineEvent = False
        self.deleteEvent = False
        self.backspaceEvent = False
        self.arrowPress = False
        self.cutPress = False
        self.formatingLine = False
        self.undoing = False

        insertIter = self.insertIter()

        currentLine = self.control.currentLine()

        currentCharIsHeading = False
        currentTags = insertIter.get_tags()
        names = [name.props.name for name in currentTags]
        if "heading" in names:
            currentCharIsHeading = True

        backwardIter = self.insertIter()
        canGoBackward = backwardIter.backward_char()
        backwardChar = backwardIter.get_char()

        prevCharIsHeading = False
        if canGoBackward:
            backwardTags = backwardIter.get_tags()
            names = [name.props.name for name in backwardTags]
            if "heading" in names or backwardChar == HEADING:
                prevCharIsHeading = True

        forwardIter = self.insertIter()
        canGoForward = forwardIter.forward_char()
        forwardChar = forwardIter.get_char()

        nextCharIsHeading = False
        if canGoForward:
            forwardTags = forwardIter.get_tags()
            names = [name.props.name for name in forwardTags]
            if "heading" in names or backwardChar == HEADING:
                nextCharIsHeading = True

        if self.removeCrossPageSelection():
            self.keyPressFollowUp(event)
            return 1

        if event.state & Gdk.ModifierType.SHIFT_MASK:
            if event.state & Gdk.ModifierType.CONTROL_MASK:

                if event.keyval==75: # kill app
                    import sys
                    sys.exit()

                if event.keyval==90: # redo
                    self.forceWordEvent()
                    self.control.eventManager.redo()
                    self.keyPressFollowUp(event)

                return 1

            if event.keyval >= 65 and event.keyval <= 90:
                if self.control.currentLine().tag == 'sceneHeading':
                    returnValue = self.completeSceneHeading(event)
                    self.keyPressFollowUp(event)
                    if returnValue:
                        return 1
                else:
                    returnValue = self.completeName(event)
                    if returnValue:
                        return 1

        elif event.state & Gdk.ModifierType.CONTROL_MASK:
            self.nameIter = None
            self.sceneHeadingIter = None

            if event.keyval == 118: # pasting
                self.pasteClipboard()

            elif event.keyval == 99: #copy
                self.do_copy_clipboard()

            elif event.keyval == 120: #cut
                self.do_cut_clipboard()

            elif event.keyval == 45: # minus key
                if self.fontSize > 4:
                    self.fontSize -= 1
                    self.resetTags()
                    return 1

            elif event.keyval==61: # equal key
                self.fontSize += 1
                self.resetTags()
                return 1

            elif event.keyval==65535: # Control + Del, Clear History
                self.clearHistory(None, self.control)

            elif event.keyval==122: # undo
                self.completion = None
                self.completionManager.reset()

                self.undoing = True
                self.forceWordEvent()
                self.control.eventManager.undo()

            self.keyPressFollowUp(event)
            return 1

        self.nameIter = None
        self.sceneHeadingIter = None

        if event.keyval == 65289: # tab

            self.completing = True

            self.forceWordEvent()

            self.completionManager.updateIter()

            if self.completionManager.iter:

                currentLine = self.control.currentLine()

                cp = self.control.currentPage()
                pageLineIndex = cp.lines.index(currentLine)

                sceneIndex = self.control.currentSequence().scenes.index(self.control.currentScene())
                pageIndex = self.control.currentScene().pages.index(self.control.currentPage())
                offset = self.control.currentStory().index.offset
                suffix = self.completionManager.suffix()

                self.completion = Completion(self.control, pageLineIndex, offset, suffix, sceneIndex, pageIndex)

                self.completion.insert()

                self.applyCompletionTag(currentLine, offset, suffix)

            else:
                self.completion = None

            self.completionManager.forward()
            self.keyPressFollowUp(event)
            return 1

        if event.keyval == 65307: # esc
            self.clearFindTags()
            return

        if event.keyval == 65470: # F1 press
            self.control.currentStory().printTags()
            return 1

        if event.keyval == 65471: # F2 press
            self.control.currentStory().correspond(self.control, verbose=1)
            self.keyPressFollowUp(event)
            return 1

        if self.insertingOnFirstIter(event):
            self.keyPressFollowUp(event)
            return 1

        if event.keyval == 32 and insertIter.get_line_offset() == 0: # format line
            self.formatPress(currentLine)
            self.keyPressFollowUp(event)
            return 1

        if (event.keyval == 65293): # new line
            return self.returnPress()

        elif (event.keyval == 65288): # backspace
            # self.completionManager.reset()
            # self.completion = None
            # self.completing = False
            # self.completeReset = False

            self.backspacePress()
            self.keyPressFollowUp(event)
            return 1

        elif (event.keyval == 65535): # delete
            self.completionManager.reset()
            self.completion = None
            self.completing = False
            self.completeReset = False

            self.deletePress()
            self.keyPressFollowUp(event)
            return 1

        elif event.keyval in [65361,65362,65363,65364]: # arrow key
            self.forceWordEvent()
            self.arrowPress = True
            self.updateNameLocationAndTime()
            self.keyPressFollowUp(event)
            return 0

        if self.pressOnHeading():
            self.keyPressFollowUp(event)
            return 1

        # if not self.deleteEvent and not self.backspaceEvent and not self.arrowPress and self.isPrintable(event.string):
        if self.isPrintable(event.string):

            self.control.currentStory().index.offset += 1

            character = event.string
            if self.control.currentLine().tag == 'sceneHeading':
                character = event.string.upper()

            self.setSelectionClipboard()
            cutEvent = self.chainDeleteSelectedTextEvent()
            insertIter = self.insertIter()

            self.get_buffer().insert(insertIter, character, 1)

            self.updateLineTag()

            self.addCharToWord(character, duringKeyPressEvent=True)

            if cutEvent:
                self.forceWordEvent()

        if event.keyval == 32:
            self.forcingWordEvent = True
            self.currentLineMispelled()

        # Do this to spellcheck check parenthetic.
        if event.keyval == 41:
            self.currentLineMispelled()

        self.keyPressFollowUp(event)

        return 1

    def clearFindTags(self):
        for line in self.control.scriptView.lines:
            if line.__class__.__name__ != "Heading":
                line.findTags = []
                lineIndex = self.control.scriptView.lines.index(line)
                self.updateLineTag(lineIndex)

    def keyRelease(self, widget, event):
        self.undoing = False


        return

    def keyPressFollowUp(self, event):

        visibleRect = self.get_visible_rect()
        insertIter = self.insertIter()
        insertRect = self.get_iter_location(insertIter)
        if (insertRect.y >= visibleRect.y) and (insertRect.y + insertRect.height <= visibleRect.y + visibleRect.height):
            pass
        else:
            self.scroll_to_iter(insertIter, 0.1, False, 0.0, 0.0)

        self.control.scriptView.updateCurrentStoryIndex()

        if self.backspaceEvent or self.deleteEvent:
            self.updateLineTag()

        if self.arrowPress or self.formatingLine or self.newLineEvent or self.deleteEvent or self.backspaceEvent:
            self.updatePanel()

        if self.arrowPress:
            # In case the line has changed, TagIter needs current line tag.
            self.tagIter.load(self.control.currentLine().tag)

        if event.string == ' ':
            self.completionManager.reset()
            self.completion = None
            self.completing = False
            self.completeReset = False

        if self.completionManager.iter is None:
            self.completion = None
            self.completing = False

        if self.completeReset:
            self.forceWordEvent()

            self.completionManager.reset()
            self.completionManager.updateIter()

            currentLine = self.control.currentLine()

            cp = self.control.currentPage()
            pageLineIndex = cp.lines.index(currentLine)

            sceneIndex = self.control.currentSequence().scenes.index(self.control.currentScene())
            pageIndex = self.control.currentScene().pages.index(self.control.currentPage())
            offset = self.control.currentStory().index.offset
            suffix = self.completionManager.suffix()

            print 'offset', offset

            self.completion = Completion(self.control, pageLineIndex, offset, suffix, sceneIndex, pageIndex)

            self.completion.insert()

            self.applyCompletionTag(currentLine, offset, suffix)

            self.completeReset = False

        return

    def returnPress(self):

        insertIter = self.insertIter()
        previousLineIndex = insertIter.get_line()
        currentChar = insertIter.get_char()
        currentCharIsNewLine = currentChar == '\n'
        offset = insertIter.get_line_offset()

        currentCharIsHeading = False
        currentTags = insertIter.get_tags()
        names = [name.props.name for name in currentTags]
        if "heading" in names:
            currentCharIsHeading = True

        forwardIter = self.insertIter()
        canGoForward = forwardIter.forward_char()
        forwardChar = forwardIter.get_char()

        backwardIter = self.insertIter()
        canGoBackward = backwardIter.backward_char()
        backwardChar = backwardIter.get_char()

        nextCharIsHeading = False
        prevCharIsHeading = False

        currentLine = self.control.currentLine()
        currentLineTag = currentLine.tag

        if canGoForward:
            forwardTags = forwardIter.get_tags()
            names = [name.props.name for name in forwardTags]
            if "heading" in names or backwardChar == HEADING:
                nextCharIsHeading = True

        if canGoBackward:
            backwardTags = backwardIter.get_tags()
            names = [name.props.name for name in backwardTags]
            if "heading" in names or backwardChar == HEADING:
                prevCharIsHeading = True

        self.forceWordEvent()

        self.updateNameLocationAndTime()

        # In case the cursor is at the end of a heading line, allow a new line to be created.
        if currentCharIsHeading:
            # return

            # Push the cursor to the next line.
            insertIter = self.insertIter()
            insertIter.forward_char()
            self.get_buffer().place_cursor(insertIter)

            # Update the model so the current line is next line.
            lineIndex = self.control.currentPage().lines.index(currentLine)
            #self.control.currentStory().index.line = lineIndex + 1
            self.control.currentStory().index.offset = 0
            tag = currentLine.tag
            self.tagIter.load(tag)

            # After moving cursor forward the previous line index needs updated.
            previousLineIndex += 1


        # Deletes a selection if needed.
        cutEvent = self.chainDeleteSelectedTextEvent()
        if cutEvent != None :
            cutEvent.chained = False

        # If the offset is at the end of the line, try to predict the next tag.
        if offset == len(currentLine.text):
            newLineTag = 'description'
            if currentLine.tag in ['character', 'parenthetic']:
                newLineTag = 'dialog'
            elif currentLine.tag == 'dialog':
                newLineTag = 'description'

        # When just brings a whole line or part of a  line down, keep it's tag,
        else:
            newLineTag = currentLine.tag

        # If it's a scene heading, updates time and location components.
        if currentLine.tag == 'sceneHeading':
            newLineTag = 'description'
            self.updateLocationAndTime(currentLine)

        self.tagIter.load(newLineTag)

        if currentCharIsNewLine:

            if currentCharIsHeading:

                nextLineTag = newLineTag
                newLineTag = 'description'

                insertIter = self.insertIter()
                lineIndex = insertIter.get_line()

                if self.control.currentStory().isScreenplay:
                    tags = ["sceneHeading", "description"]
                else:
                    tags = ['description', currentLineTag]

                cp = self.control.currentPage()
                pageLineIndex = cp.lines.index(currentLine)

                lineIndex = self.control.scriptView.lines.index(currentLine)
                sceneIndex = self.control.currentSequence().scenes.index(self.control.currentScene())
                pageIndex = self.control.currentScene().pages.index(self.control.currentPage())
                newLineEvent = _event.Insertion(sceneIndex,
                    pageIndex,
                    pageLineIndex,
                    self.control.currentStory().index.offset,
                    '\n',
                    tags)

                newLineEvent.beforeTags = [currentLineTag]
                newLineEvent.pushedOffHeading = True

                self.control.eventManager.addEvent(newLineEvent)
                newLineEvent.modelUpdate(self.control)
                newLineEvent.viewUpdate(self.control)

            else:
                tags = [currentLineTag, newLineTag ]

                cp = self.control.currentPage()
                pageLineIndex = cp.lines.index(currentLine)
                sceneIndex = self.control.currentSequence().scenes.index(self.control.currentScene())
                pageIndex = self.control.currentScene().pages.index(self.control.currentPage())
                lineIndex = self.control.scriptView.lines.index(currentLine)
                event = _event.Insertion(sceneIndex,
                    pageIndex,
                    pageLineIndex,
                    self.control.currentStory().index.offset,
                    '\n',
                    tags)
                event.beforeTags = [currentLineTag]
                event.modelUpdate(self.control)
                event.viewUpdate(self.control)
                self.control.eventManager.addEvent(event)

        else:

            tags = [currentLineTag, newLineTag]
            cp = self.control.currentPage()
            sceneIndex = self.control.currentSequence().scenes.index(self.control.currentScene())
            pageIndex = self.control.currentScene().pages.index(self.control.currentPage())
            pageLineIndex = cp.lines.index(currentLine)
            newLineEvent = _event.Insertion(sceneIndex,
                pageIndex,
                pageLineIndex,
                self.control.currentStory().index.offset,
                '\n',
                tags)

            newLineEvent.beforeTags = [currentLineTag]

            newLineEvent.modelUpdate(self.control)
            self.control.eventManager.addEvent(newLineEvent)

            newLineEvent.viewUpdate(self.control)

        self.newLineEvent = True



        return 1

    def deletePress(self):

        insertIter = self.insertIter()
        currentChar = insertIter.get_char()
        currentCharIsNewLine = currentChar == '\n'

        forwardIter = self.insertIter()
        canGoForward = forwardIter.forward_char()
        forwardChar = forwardIter.get_char()

        backwardIter = self.insertIter()
        canGoBackward = backwardIter.backward_char()
        backwardChar = backwardIter.get_char()

        nextCharIsHeading = False
        prevCharIsHeading = False

        currentLine = self.control.currentLine()
        currentLineOffset = insertIter.get_line_offset()
        lineEmpty = len(currentLine.text) == 0

        bounds = self.get_buffer().get_selection_bounds()
        if len(bounds):
            selectStart, selectEnd = bounds
            if selectEnd.get_char() == HEADING:
                return 1

            startCanGoBackward = selectStart.backward_char()
            if startCanGoBackward:
                if selectStart.get_char() == HEADING:
                    return 1

        if currentChar:# and not nextCharIsHeading:
            self.forceWordEvent()
            self.setSelectionClipboard()
            cutEvent = self.chainDeleteSelectedTextEvent()

            if cutEvent:
                self.updateLineTag()
                return 1

        if canGoForward:
            forwardTags = forwardIter.get_tags()
            names = [name.props.name for name in forwardTags]
            if "heading" in names or backwardChar == HEADING:
                nextCharIsHeading = True

        if canGoBackward:
            backwardTags = backwardIter.get_tags()
            names = [name.props.name for name in backwardTags]
            if "heading" in names or backwardChar == HEADING:
                prevCharIsHeading = True

        if currentChar == ZERO_WIDTH_SPACE:
            return 1

        if nextCharIsHeading: # delete on heading, or just before
            movedIter = self.insertIter()

            if currentChar == '\n' and currentLineOffset == 1:
                movedIter.forward_chars(1)

            elif currentChar == '\n':
                movedIter.forward_chars(3)

            else:
                movedIter.forward_chars(2)

            self.get_buffer().place_cursor(movedIter)

            self.control.scriptView.updateCurrentStoryIndex()
            return 1

        if currentChar:
            self.deleteEvent = True

            cp = self.control.currentPage()
            pageLineIndex = cp.lines.index(currentLine)
            tags = [currentLine.tag]
            if currentChar == '\n':
                tags = [currentLine.tag, currentLine.after(self.control).tag]
            sceneIndex = self.control.currentSequence().scenes.index(self.control.currentScene())
            pageIndex = self.control.currentScene().pages.index(self.control.currentPage())
            event = _event.Deletion(sceneIndex,
                pageIndex,
                pageLineIndex,
                self.control.currentStory().index.offset,
                currentChar,
                tags)
            event.beforeTags = [currentLine.tag, currentLine.after(self.control).tag]
            event.viewUpdate(self.control)
            event.modelUpdate(self.control, isDeleteKey=True)
            self.control.eventManager.addEvent(event)

            self.control.scriptView.updateCurrentStoryIndex()

        else:
            return 1

    def backspacePress(self):
        insertIter = self.insertIter()
        currentChar = insertIter.get_char()
        currentCharIsNewLine = currentChar == '\n'

        currentLine = self.control.currentLine()
        currentLineOffset = insertIter.get_line_offset()
        currentCharOffset = insertIter.get_offset()
        lineEmpty = len(currentLine.text) == 0
        currentLineIndex = insertIter.get_line()
        lastIterOffset = self.get_buffer().get_end_iter().get_offset()
        currentPage = self.control.currentPage()

        insertIter = self.insertIter()
        characterCount = insertIter.get_chars_in_line()

        currentCharIsHeading = False
        currentTags = insertIter.get_tags()
        names = [name.props.name for name in currentTags]
        if "heading" in names:
            currentCharIsHeading = True

        backwardIter = self.insertIter()
        canGoBackward = backwardIter.backward_char()
        backwardChar = backwardIter.get_char()

        prevCharIsHeading = False
        if canGoBackward:
            backwardTags = backwardIter.get_tags()
            names = [name.props.name for name in backwardTags]
            if "heading" in names or backwardChar == HEADING:
                prevCharIsHeading = True

        forwardIter = self.insertIter()
        canGoForward = forwardIter.forward_char()
        forwardChar = forwardIter.get_char()

        nextCharIsHeading = False
        if canGoForward:
            forwardTags = forwardIter.get_tags()
            names = [name.props.name for name in forwardTags]
            if "heading" in names or backwardChar == HEADING:
                nextCharIsHeading = True

        self.control.scriptView.textView.markSet()
        self.setSelectionClipboard()

        if currentLineIndex == 0:
            return 1

        if currentLineIndex == 1 and currentLineOffset == 0 and len(currentPage.lines) == 1:
            return 1

        if prevCharIsHeading and lineEmpty and (lastIterOffset - 1) != currentCharOffset and not nextCharIsHeading: # backspace on heading
            self.deletePress()
            return 1

        elif currentCharIsHeading and canGoBackward: # backspace on heading
            movedIter = self.insertIter()
            if currentLineOffset == 1:
                movedIter.backward_chars(2)
            else:
                movedIter.backward_char()
            self.get_buffer().place_cursor(movedIter)
            self.control.scriptView.updateCurrentStoryIndex()
            return 1

        elif len(self.selectedClipboard) == 0 and prevCharIsHeading and currentLineIndex > 1: # backspace on heading
            movedIter = self.insertIter()
            movedIter.backward_chars(3)
            self.get_buffer().place_cursor(movedIter)
            self.control.scriptView.updateCurrentStoryIndex()
            return 1

        elif prevCharIsHeading and currentLineIndex == 1 and len(self.selectedClipboard) == 0:
            return 1

        self.forceWordEvent()
        cutEvent = self.chainDeleteSelectedTextEvent()
        self.updateLineTag()
        if cutEvent:
            self.get_buffer().place_cursor(self.insertIter())
            return 1

        self.backspaceEvent = True

        insertIter = self.insertIter()
        backIter = self.insertIter()
        backIter.backward_char()

        if backIter.get_char() == '\n':
            removedNewLine = True
        else:
            removedNewLine = False

        cl = self.control.currentLine()
        cp = self.control.currentPage()
        pageLineIndex = cp.lines.index(cl)

        tags = [cl.before(self.control).tag, cl.tag]

        sceneIndex = self.control.currentSequence().scenes.index(self.control.currentScene())
        pageIndex = self.control.currentScene().pages.index(self.control.currentPage())
        event = _event.Backspace(sceneIndex,
            pageIndex,
            pageLineIndex,
            self.control.currentStory().index.offset,
            backIter.get_char(),
            tags)

        self.control.eventManager.addEvent(event)
        event.viewUpdate(self.control)
        event.modelUpdate(self.control)

        self.control.scriptView.updateCurrentStoryIndex()

    def pressOnHeading(self):
        if 'heading' in [tag.props.name for tag in self.insertIter().get_tags()]:
            return 1

    def formatPress(self, line):
        if line.tag not in ['heading', 'sceneHeading']:

            beforeTags = [line.tag]

            self.tagIter.increment()
            self.tagIter.tag()
            newTags = [self.tagIter.tag()]

            self.formatingLine = True

            cl = self.control.currentLine()
            cp = self.control.currentPage()
            pageLineIndex = cp.lines.index(cl)
            sceneIndex = self.control.currentSequence().scenes.index(self.control.currentScene())
            pageIndex = self.control.currentScene().pages.index(self.control.currentPage())
            offset = self.control.currentStory().index.offset
            event = _event.FormatLines(sceneIndex,
                pageIndex,
                pageLineIndex,
                offset,
                '',
                newTags)
            event.beforeTags = beforeTags

            event.modelUpdate(self.control)
            event.viewUpdate(self.control)

            self.control.eventManager.addEvent(event)

            self.resetGlobalMargin(newTags[0])


    # Autocomplete
    def updateNameLocationAndTime(self, line=None):

        if not line:
            line = self.control.currentLine()
        tag = line.tag

        # Update the character names if on a character line.
        if tag == "character":
            self.control.currentStory().addName(line.text)

        # Update location and time if coming from a scene heading
        if tag == 'sceneHeading':
            self.updateLocationAndTime(line)

    def currentLineMispelled(self):
        if self.control.trie:
            currentLine = self.control.currentLine()
            currentLine.updateMispelled(self.control)
            currentLine.applyMispelledTags(self.control, cursorWordOnly=True)
            self.control.mispelledLine = currentLine
            self.control.mispelledTimer()

    def lineWords(self, line=None):
        if line==None:
            line = self.control.currentLine()

        words = re.findall(r"[\w']+|[ .,!?;-]", line.text)

        return words

    def completeSceneHeading(self, event):

        insertIter = self.insertIter()

        prefix = ''
        moved = insertIter.backward_char()
        char = insertIter.get_char()

        if moved:
            prefixes = []
            character = chr(event.keyval).upper()
            wordHasLength = len(self.word)
            if (char == character and wordHasLength) or self.sceneHeadingIter != None:
                sh = SceneHeading()
                component = sh.cursorComponent(self.control.currentLine().text, self.control.currentStory().index.offset)

                if component == 'intExt':
                    prefixBase = self.intExts
                elif component == 'location':
                    prefixBase = self.control.currentStory().locations
                elif component == 'time':
                    prefixBase = self.control.currentStory().times
                else:
                    # Notation will not have completion
                    return

                for prefix in prefixBase:
                    if prefix.startswith(character) and prefix not in prefixes:
                        prefixes.append(prefix)

                # Add empty string at the end, so users have a reset at end of completion list.
                if len(prefixes):
                    prefixes.append("")

                if len(prefixes):

                    insideWord = False
                    secondMove = insertIter.backward_char()
                    if secondMove:
                        if insertIter.get_char().isalpha():
                            insideWord = True

                    # Here we begin the first completion.
                    if self.sceneHeadingIter == None and not insideWord:

                        self.sceneHeadingIter = NameIter(prefixes, character)

                        # get rid of first upper case that is in self.word
                        self.word.pop(-1)
                        wordHasLength = len(self.word)

                        # write the word to the model.
                        self.forceWordEvent()

                        # remove the first upper from the buffer, corresponding with model
                        startIter = self.insertIter()
                        endIter = self.insertIter()
                        startIter.backward_chars(1)
                        self.get_buffer().delete(startIter,endIter)

                        # complete the current iters name
                        self.completeWordOnLine(self.sceneHeadingIter.name(),
                            wordHasLength=wordHasLength,
                            isSceneHeading=True,
                            isFirstCompletion=True)

                        return 1

                    elif self.sceneHeadingIter == None:
                        pass

                    else:

                        startIter = self.insertIter()
                        deleteOffset = startIter.get_line_offset() - len(self.sceneHeadingIter.name())
                        currentLine = self.control.currentLine()

                        cp = self.control.currentPage()
                        pageLineIndex = cp.lines.index(currentLine)
                        tags = [currentLine.tag]
                        sceneIndex = self.control.currentSequence().scenes.index(self.control.currentScene())
                        pageIndex = self.control.currentScene().pages.index(self.control.currentPage())
                        event = _event.Deletion(sceneIndex,
                            pageIndex,
                            pageLineIndex,
                            deleteOffset,
                            self.sceneHeadingIter.name(),
                            tags)
                        event.beforeTags = [currentLine.tag]
                        event.viewUpdate(self.control)
                        event.modelUpdate(self.control)
                        self.control.eventManager.addEvent(event)

                        # The index must be updated where the deletion began.
                        self.control.currentStory().index.offset = deleteOffset

                        # Here means we atleast autocompleted once and continue to do so.
                        if self.sceneHeadingIter.initChar == character:

                            # Bring the next name forward and complete it.
                            self.sceneHeadingIter.increment()
                            self.completeWordOnLine(self.sceneHeadingIter.name(), 0, True)

                            return 1

                        # Here we have been completing, but changed the start letter of the character name.
                        else:

                            # Reset the NameIter and complete
                            self.sceneHeadingIter = NameIter(prefixes, character)
                            self.completeWordOnLine(self.sceneHeadingIter.name(), 0, True)

                            return 1

    def completeName(self, event):
        insertIter = self.insertIter()

        prefix = ''
        moved = insertIter.backward_char()
        char = insertIter.get_char()

        if moved:
            prefixes = []
            character = chr(event.keyval).upper()
            wordHasLength = len(self.word)

            if (char == character and wordHasLength) or self.nameIter != None:

                for name in self.control.currentScene().names(self.control):
                    if name.startswith(character) and name not in prefixes:
                        prefixes.append(name)

                # Add empty string at the end, so users have a reset at end of completion list.
                if len(prefixes):
                    prefixes.append("")

                if len(prefixes):

                    insideWord = False
                    secondMove = insertIter.backward_char()
                    if secondMove:
                        if insertIter.get_char().isalpha():
                            insideWord = True

                    # Here we begin the first completion.
                    if self.nameIter == None and not insideWord:

                        self.nameIter = NameIter(prefixes, character)

                        # get rid of first upper case that is in self.word
                        self.word.pop(-1)
                        wordHasLength = len(self.word)

                        # write the word to the model.
                        self.forceWordEvent()

                        # remove the first upper from the buffer, corresponding with model
                        startIter = self.insertIter()
                        endIter = self.insertIter()
                        startIter.backward_chars(1)
                        self.get_buffer().delete(startIter,endIter)

                        # complete the current iters name
                        self.completeWordOnLine(self.nameIter.name(),
                            wordHasLength=wordHasLength,
                            isSceneHeading=False,
                            isFirstCompletion=True)

                        return 1


                    elif self.nameIter == None:
                        pass


                    else:

                        startIter = self.insertIter()
                        deleteOffset = startIter.get_line_offset() - len(self.nameIter.name())
                        currentLine = self.control.currentLine()

                        cp = self.control.currentPage()
                        pageLineIndex = cp.lines.index(currentLine)
                        tags = [currentLine.tag]
                        sceneIndex = self.control.currentSequence().scenes.index(self.control.currentScene())
                        pageIndex = self.control.currentScene().pages.index(self.control.currentPage())
                        event = _event.Deletion(sceneIndex,
                            pageIndex,
                            pageLineIndex,
                            deleteOffset,
                            self.nameIter.name(),
                            tags)
                        event.beforeTags = [currentLine.tag]
                        event.viewUpdate(self.control)
                        event.modelUpdate(self.control)
                        self.control.eventManager.addEvent(event)

                        # The index must be updated where the deletion began.
                        self.control.currentStory().index.offset = deleteOffset

                        # Here means we atleast autocompleted once and continue to do so.
                        if self.nameIter.initChar == character:

                            # Bring the next name forward and complete it.
                            self.nameIter.increment()
                            self.completeWordOnLine(self.nameIter.name(), 0, isSceneHeading=False)

                            return 1

                        # Here we have been completing, but changed the start letter of the character name.
                        else:

                            # Reset the NameIter and complete
                            self.nameIter = NameIter(prefixes, character)
                            self.completeWordOnLine(self.nameIter.name(), 0, isSceneHeading=False)

                            return 1

    def completeWordOnLine(self, name, wordHasLength, isSceneHeading=False, isFirstCompletion=False):

        cl = self.control.currentLine()

        # Lower case letters in words that are not the first character of a word and not upper case.
        if cl.tag not in ["character", "sceneHeading"]:
            lowered = []
            first = True
            for c in name:
                if c.isupper() and not first:
                    lowered.append(c.lower())
                else:
                    lowered.append(c)
                    first = False
                if c == ' ':
                    first = True
            name = "".join(lowered)

        completionOffsetAdjustment = 0
        if isFirstCompletion:
            completionOffsetAdjustment = 1
        cp = self.control.currentPage()
        sceneIndex = self.control.currentSequence().scenes.index(self.control.currentScene())
        pageIndex = self.control.currentScene().pages.index(self.control.currentPage())
        pageLineIndex = cp.lines.index(cl)
        pasteEvent = _event.Insertion(sceneIndex,
            pageIndex,
            pageLineIndex,
            self.control.currentStory().index.offset - completionOffsetAdjustment,
            name,
            [cl.tag])
        self.control.eventManager.addEvent(pasteEvent)
        pasteEvent.beforeTags = [cl.tag]
        pasteEvent.viewUpdate(self.control)
        pasteEvent.modelUpdate(self.control)

        index = self.control.scriptView.lines.index(cl)

        # if len(name):
        #     tag = self.tagIter.tag()
        #     if isSceneHeading:
        #         tag = "sceneHeading"
        #     self.control.scriptView.lines[index].tag = tag
        #     self.control.scriptView.textView.updateLineTag(index)

        self.control.currentStory().index.offset = self.control.currentStory().index.offset - completionOffsetAdjustment + len(name)

    def insertPrefix(self):

        spaceCount = 0

        cs = self.control.currentStory()

        insertIter = self.insertIter()

        prefix = ''
        moved = insertIter.backward_char()
        char = insertIter.get_char()

        if char in NON_WORD_CHARACTERS:
            return prefix

        while moved:
            prefix = char + prefix
            moved = insertIter.backward_char()
            char = insertIter.get_char()

            if char in NON_WORD_CHARACTERS:
                break

        return prefix


    # Tags
    def resetTags(self, width=None):

        try:
            self.control.scriptView
        except:
            return

        self.settingMargin = True

        if width == None:
            width = self.get_allocated_width()
        self.width = width

        descriptionWidth = int(DESCRIPTION_WIDTH * self.fontSize)
        self.control.scriptView.scrolledWindow2.set_size_request(self.descriptionWidth * TEXT_VIEW_FACTOR, 0)

        centeringFactor = 0
        if self.width:
            centeringFactor = (self.width - descriptionWidth) / 2.55

        characterWidth = self.descriptionWidth * CHARACTER_WIDTH_FACTOR
        dialogWidth = self.descriptionWidth * DIALOG_WIDTH_FACTOR
        parentheticWidth = self.descriptionWidth * PARENTHETIC_WIDTH_FACTOR

        descriptionLeftMargin = descriptionWidth * 0.1 + centeringFactor
        characterLeftMargin = descriptionWidth * CHARACTER_LEFT_FACTOR + centeringFactor
        dialogLeftMargin = descriptionWidth * DIALOG_LEFT_FACTOR + centeringFactor
        parentheticLeftMargin = descriptionWidth * PARENTHETIC_LEFT_FACTOR + centeringFactor

        descriptionRightMargin = self.width - (descriptionLeftMargin + descriptionWidth) #- centeringFactor
        characterRightMargin = self.width - (characterLeftMargin + characterWidth) #+ centeringFactor
        dialogRightMargin = self.width - (dialogLeftMargin + dialogWidth)# + centeringFactor
        parentheticRightMargin = self.width - (dialogLeftMargin + parentheticWidth)# + centeringFactor

        self.descriptionLeftMargin = descriptionLeftMargin
        self.characterLeftMargin = characterLeftMargin
        self.dialogLeftMargin = dialogLeftMargin
        self.parentheticLeftMargin = parentheticLeftMargin

        if descriptionRightMargin < 1:
            return
        # if characterLeftMargin < 0:
        #     return
        # if dialogLeftMargin < 0:
        #     return

        self.descriptionWidth = descriptionWidth
        self.characterWidth = characterWidth
        self.dialogWidth = dialogWidth
        self.parentheticWidth = parentheticWidth

        self.descriptionLeftMargin = descriptionLeftMargin
        self.characterLeftMargin = characterLeftMargin
        self.dialogLeftMargin = dialogLeftMargin
        self.parentheticLeftMargin = parentheticLeftMargin

        self.descriptionRightMargin = descriptionRightMargin
        self.characterRightMargin = characterRightMargin
        self.dialogRightMargin = dialogRightMargin
        self.parentheticRightMargin = parentheticRightMargin

        self.props.left_margin = self.descriptionLeftMargin
        self.props.right_margin = self.descriptionRightMargin

        self.descriptionTag.props.left_margin = self.descriptionLeftMargin
        self.characterTag.props.left_margin = self.characterLeftMargin
        self.dialogTag.props.left_margin = self.dialogLeftMargin
        self.parentheticTag.props.left_margin = self.parentheticLeftMargin
        self.headingTag.props.left_margin = self.descriptionLeftMargin
        self.sceneHeadingTag.props.left_margin = self.descriptionLeftMargin

        self.descriptionFindTag.props.left_margin = self.descriptionLeftMargin
        self.characterFindTag.props.left_margin = self.characterLeftMargin
        self.dialogFindTag.props.left_margin = self.dialogLeftMargin
        self.parentheticFindTag.props.left_margin = self.parentheticLeftMargin
        self.sceneHeadingFindTag.props.left_margin = self.descriptionLeftMargin

        self.descriptionScrollTag.props.left_margin = self.descriptionLeftMargin
        self.characterScrollTag.props.left_margin = self.characterLeftMargin
        self.dialogScrollTag.props.left_margin = self.dialogLeftMargin
        self.parentheticScrollTag.props.left_margin = self.parentheticLeftMargin
        self.sceneHeadingScrollTag.props.left_margin = self.descriptionLeftMargin

        self.descriptionCompletionTag.props.left_margin = self.descriptionLeftMargin
        self.characterCompletionTag.props.left_margin = self.characterLeftMargin
        self.dialogCompletionTag.props.left_margin = self.dialogLeftMargin
        self.parentheticCompletionTag.props.left_margin = self.parentheticLeftMargin
        self.sceneHeadingCompletionTag.props.left_margin = self.descriptionLeftMargin

        self.sceneHeadingMispelledTag.props.left_margin = self.descriptionLeftMargin
        self.descriptionMispelledTag.props.left_margin = self.descriptionLeftMargin
        self.characterMispelledTag.props.left_margin = self.characterLeftMargin
        self.dialogMispelledTag.props.left_margin = self.dialogLeftMargin
        self.parentheticMispelledTag.props.left_margin = self.parentheticLeftMargin

        self.descriptionTag.props.right_margin = self.descriptionRightMargin
        self.characterTag.props.right_margin = self.characterRightMargin
        self.dialogTag.props.right_margin = self.dialogRightMargin
        self.parentheticTag.props.right_margin = self.parentheticRightMargin
        self.sceneHeadingTag.props.right_margin = self.descriptionRightMargin

        self.descriptionFindTag.props.right_margin = self.descriptionRightMargin
        self.characterFindTag.props.right_margin = self.characterRightMargin
        self.dialogFindTag.props.right_margin = self.dialogRightMargin
        self.parentheticFindTag.props.right_margin = self.parentheticRightMargin
        self.sceneHeadingFindTag.props.right_margin = self.descriptionRightMargin

        self.descriptionScrollTag.props.right_margin = self.descriptionRightMargin
        self.characterScrollTag.props.right_margin = self.characterRightMargin
        self.dialogScrollTag.props.right_margin = self.dialogRightMargin
        self.parentheticScrollTag.props.right_margin = self.parentheticRightMargin
        self.sceneHeadingScrollTag.props.right_margin = self.descriptionRightMargin

        self.descriptionCompletionTag.props.right_margin = self.descriptionRightMargin
        self.characterCompletionTag.props.right_margin = self.characterRightMargin
        self.dialogCompletionTag.props.right_margin = self.dialogRightMargin
        self.parentheticCompletionTag.props.right_margin = self.parentheticRightMargin
        self.sceneHeadingCompletionTag.props.right_margin = self.descriptionRightMargin

        self.descriptionTag.props.font = "Courier Prime " + str(self.fontSize)
        self.characterTag.props.font = "Courier Prime " + str(self.fontSize)
        self.dialogTag.props.font = "Courier Prime " + str(self.fontSize)
        self.parentheticTag.props.font = "Courier Prime " + str(self.fontSize)
        self.sceneHeadingTag.props.font = "Courier Prime " + str(self.fontSize)

        self.descriptionFindTag.props.font = "Courier Prime " + str(self.fontSize)
        self.characterFindTag.props.font = "Courier Prime " + str(self.fontSize)
        self.dialogFindTag.props.font = "Courier Prime " + str(self.fontSize)
        self.parentheticFindTag.props.font = "Courier Prime " + str(self.fontSize)
        self.sceneHeadingFindTag.props.font = "Courier Prime " + str(self.fontSize)

        self.descriptionScrollTag.props.font = "Courier Prime " + str(self.fontSize)
        self.characterScrollTag.props.font = "Courier Prime " + str(self.fontSize)
        self.dialogScrollTag.props.font = "Courier Prime " + str(self.fontSize)
        self.parentheticScrollTag.props.font = "Courier Prime " + str(self.fontSize)
        self.sceneHeadingScrollTag.props.font = "Courier Prime " + str(self.fontSize)


        self.descriptionCompletionTag.props.font = "Courier Prime " + str(self.fontSize)
        self.characterCompletionTag.props.font = "Courier Prime " + str(self.fontSize)
        self.dialogCompletionTag.props.font = "Courier Prime " + str(self.fontSize)
        self.parentheticCompletionTag.props.font = "Courier Prime " + str(self.fontSize)
        self.sceneHeadingCompletionTag.props.font = "Courier Prime " + str(self.fontSize)

        self.descriptionMispelledTag.props.font = "Courier Prime " + str(self.fontSize)
        self.characterMispelledTag.props.font = "Courier Prime " + str(self.fontSize)
        self.dialogMispelledTag.props.font = "Courier Prime " + str(self.fontSize)
        self.parentheticMispelledTag.props.font = "Courier Prime " + str(self.fontSize)
        self.sceneHeadingMispelledTag.props.font = "Courier Prime " + str(self.fontSize)

        # Fixing last line tag issue.
        self.modify_font(Pango.FontDescription("Courier Prime " + str(self.fontSize)))
        self.props.left_margin = self.descriptionLeftMargin

        self.control.scriptView.scrolledWindow2.set_size_request(self.descriptionWidth * TEXT_VIEW_FACTOR, 0)

        self.settingMargin = False

    def createTags(self):
        pixelsInsideWrap = 2
        testing = False
        if testing:
            descriptionBackground = Gdk.RGBA(0.0, 0.0, 1.0, 0.1)
            characterBackground = Gdk.RGBA(0.0, 1.0, 0.0, 0.1)
            dialogBackground = Gdk.RGBA(1.0, 0.0, 0.0, 0.1)
        else:
            whiteColor = Gdk.RGBA(1.0, 1.0, 1.0, 1.0)
            descriptionBackground = whiteColor
            characterBackground = whiteColor
            dialogBackground = whiteColor

        findColor = Gdk.RGBA(0.0, 0.1, 1.8, 0.15)
        scrollColor = Gdk.RGBA(0.3, 0.7, 0.3, 0.8)
        completionColor = Gdk.RGBA(0.8, 0.8, 0.8, 0.8)

        self.descriptionTag = self.get_buffer().create_tag("description",
                                                     background_rgba=descriptionBackground,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=10,
                                                     pixels_below_lines=10,
                                                     left_margin=self.descriptionLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize))

        self.characterTag = self.get_buffer().create_tag("character",
                                                   background_rgba=characterBackground,
                                                   left_margin=self.characterLeftMargin,
                                                   right_margin=self.characterRightMargin,
                                                   justification=Gtk.Justification.LEFT,
                                                   pixels_inside_wrap=pixelsInsideWrap,
                                                   pixels_above_lines=10,
                                                   pixels_below_lines=0,
                                                   font="Courier Prime " + str(self.fontSize))

        self.dialogTag = self.get_buffer().create_tag("dialog",
                                                background_rgba=dialogBackground,
                                                left_margin=self.dialogLeftMargin,
                                                right_margin=self.dialogRightMargin,
                                                pixels_inside_wrap=pixelsInsideWrap,
                                                pixels_above_lines=0,
                                                pixels_below_lines=10,
                                                font="Courier Prime " + str(self.fontSize))

        self.parentheticTag = self.get_buffer().create_tag("parenthetic",
                                                     background_rgba=descriptionBackground,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=0,
                                                     pixels_below_lines=0,
                                                     left_margin=self.parentheticLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize))

        self.headingTag = self.get_buffer().create_tag("heading",
                                                     background_rgba=descriptionBackground,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=10,
                                                     pixels_below_lines=10,
                                                     left_margin=self.descriptionLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize),
                                                     editable=False)

        self.sceneHeadingTag = self.get_buffer().create_tag("sceneHeading",
                                                     background_rgba=descriptionBackground, #Gdk.RGBA(0.0, 0.0, 1.0, 0.1), #descriptionBackground,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=10,
                                                     pixels_below_lines=10,
                                                     left_margin=self.descriptionLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize))


        ## Find Tags

        self.descriptionFindTag = self.get_buffer().create_tag("descriptionFind",
                                                     background_rgba=findColor,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=10,
                                                     pixels_below_lines=10,
                                                     left_margin=self.descriptionLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize))

        self.characterFindTag = self.get_buffer().create_tag("characterFind",
                                                   background_rgba=findColor,
                                                   left_margin=self.characterLeftMargin,
                                                   right_margin=self.characterRightMargin,
                                                   justification=Gtk.Justification.LEFT,
                                                   pixels_inside_wrap=pixelsInsideWrap,
                                                   pixels_above_lines=10,
                                                   pixels_below_lines=0,
                                                   font="Courier Prime " + str(self.fontSize))

        self.dialogFindTag = self.get_buffer().create_tag("dialogFind",
                                                background_rgba=findColor,
                                                left_margin=self.dialogLeftMargin,
                                                right_margin=self.dialogRightMargin,
                                                pixels_inside_wrap=pixelsInsideWrap,
                                                pixels_above_lines=0,
                                                pixels_below_lines=10,
                                                font="Courier Prime " + str(self.fontSize))

        self.parentheticFindTag = self.get_buffer().create_tag("parentheticFind",
                                                     background_rgba=findColor,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=0,
                                                     pixels_below_lines=0,
                                                     left_margin=self.parentheticLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize))


        self.sceneHeadingFindTag = self.get_buffer().create_tag("sceneHeadingFind",
                                                     background_rgba=Gdk.RGBA(0.0, 0.0, 1.0, 0.1), #descriptionBackground,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=10,
                                                     pixels_below_lines=10,
                                                     left_margin=self.descriptionLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize))


        # Mispelled Tags

        self.descriptionMispelledTag = self.get_buffer().create_tag("descriptionMispelled",
                                                     background_rgba=descriptionBackground,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=10,
                                                     pixels_below_lines=10,
                                                     left_margin=self.descriptionLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize),
                                                     underline=Pango.Underline.ERROR)

        self.characterMispelledTag = self.get_buffer().create_tag("characterMispelled",
                                                   background_rgba=characterBackground,
                                                   left_margin=self.characterLeftMargin,
                                                   right_margin=self.characterRightMargin,
                                                   justification=Gtk.Justification.LEFT,
                                                   pixels_inside_wrap=pixelsInsideWrap,
                                                   pixels_above_lines=10,
                                                   pixels_below_lines=0,
                                                   font="Courier Prime " + str(self.fontSize),
                                                     underline=Pango.Underline.ERROR)

        self.dialogMispelledTag = self.get_buffer().create_tag("dialogMispelled",
                                                background_rgba=dialogBackground,
                                                left_margin=self.dialogLeftMargin,
                                                right_margin=self.dialogRightMargin,
                                                pixels_inside_wrap=pixelsInsideWrap,
                                                pixels_above_lines=0,
                                                pixels_below_lines=10,
                                                font="Courier Prime " + str(self.fontSize),
                                                     underline=Pango.Underline.ERROR)

        self.parentheticMispelledTag = self.get_buffer().create_tag("parentheticMispelled",
                                                     background_rgba=descriptionBackground,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=0,
                                                     pixels_below_lines=0,
                                                     left_margin=self.parentheticLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize),
                                                     underline=Pango.Underline.ERROR)

        self.sceneHeadingMispelledTag = self.get_buffer().create_tag("sceneHeadingMispelled",
                                                     background_rgba=descriptionBackground, #Gdk.RGBA(0.0, 0.0, 1.0, 0.1), #descriptionBackground,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=10,
                                                     pixels_below_lines=10,
                                                     left_margin=self.descriptionLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize),
                                                     underline=Pango.Underline.ERROR)


        ## Scroll Tags

        self.descriptionScrollTag = self.get_buffer().create_tag("descriptionScroll",
                                                     background_rgba=scrollColor,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=10,
                                                     pixels_below_lines=10,
                                                     left_margin=self.descriptionLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize))

        self.characterScrollTag = self.get_buffer().create_tag("characterScroll",
                                                   background_rgba=scrollColor,
                                                   left_margin=self.characterLeftMargin,
                                                   right_margin=self.characterRightMargin,
                                                   justification=Gtk.Justification.LEFT,
                                                   pixels_inside_wrap=pixelsInsideWrap,
                                                   pixels_above_lines=10,
                                                   pixels_below_lines=0,
                                                   font="Courier Prime " + str(self.fontSize))

        self.dialogScrollTag = self.get_buffer().create_tag("dialogScroll",
                                                background_rgba=scrollColor,
                                                left_margin=self.dialogLeftMargin,
                                                right_margin=self.dialogRightMargin,
                                                pixels_inside_wrap=pixelsInsideWrap,
                                                pixels_above_lines=0,
                                                pixels_below_lines=10,
                                                font="Courier Prime " + str(self.fontSize))

        self.parentheticScrollTag = self.get_buffer().create_tag("parentheticScroll",
                                                     background_rgba=scrollColor,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=0,
                                                     pixels_below_lines=0,
                                                     left_margin=self.parentheticLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize))


        self.sceneHeadingScrollTag = self.get_buffer().create_tag("sceneHeadingScroll",
                                                     background_rgba=scrollColor, #descriptionBackground,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=10,
                                                     pixels_below_lines=10,
                                                     left_margin=self.descriptionLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize))



        ## Completion Tags

        self.descriptionCompletionTag = self.get_buffer().create_tag("descriptionCompletion",
                                                     foreground_rgba=completionColor,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=10,
                                                     pixels_below_lines=10,
                                                     left_margin=self.descriptionLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize))

        self.characterCompletionTag = self.get_buffer().create_tag("characterCompletion",
                                                   foreground_rgba=completionColor,
                                                   left_margin=self.characterLeftMargin,
                                                   right_margin=self.characterRightMargin,
                                                   justification=Gtk.Justification.LEFT,
                                                   pixels_inside_wrap=pixelsInsideWrap,
                                                   pixels_above_lines=10,
                                                   pixels_below_lines=0,
                                                   font="Courier Prime " + str(self.fontSize))

        self.dialogCompletionTag = self.get_buffer().create_tag("dialogCompletion",
                                                foreground_rgba=completionColor,
                                                left_margin=self.dialogLeftMargin,
                                                right_margin=self.dialogRightMargin,
                                                pixels_inside_wrap=pixelsInsideWrap,
                                                pixels_above_lines=0,
                                                pixels_below_lines=10,
                                                font="Courier Prime " + str(self.fontSize))

        self.parentheticCompletionTag = self.get_buffer().create_tag("parentheticCompletion",
                                                     foreground_rgba=completionColor,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=0,
                                                     pixels_below_lines=0,
                                                     left_margin=self.parentheticLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize))


        self.sceneHeadingCompletionTag = self.get_buffer().create_tag("sceneHeadingCompletion",
                                                     foreground_rgba=completionColor, #descriptionBackground,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=10,
                                                     pixels_below_lines=10,
                                                     left_margin=self.descriptionLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize))

    def applyCompletionTag(self, line, offset, word):

        lineIndex = self.control.scriptView.lines.index(line)

        print "act index", lineIndex, line.tag

        startIter = self.control.scriptView.textView.get_buffer().get_iter_at_line(lineIndex)
        startIter.forward_chars(offset)
        endIter = self.control.scriptView.textView.get_buffer().get_iter_at_line(lineIndex)
        endIter.forward_chars(offset + len(word))

        self.control.scriptView.textView.get_buffer().remove_all_tags(startIter, endIter)
        self.control.scriptView.textView.get_buffer().apply_tag_by_name(line.tag + "Completion", startIter, endIter)

    def removeCompletionTag(self, line, offset, word):

        lineIndex = self.control.scriptView.lines.index(line)

        startIter = self.control.scriptView.textView.get_buffer().get_iter_at_line(lineIndex)
        startIter.forward_chars(offset)
        endIter = self.control.scriptView.textView.get_buffer().get_iter_at_line(lineIndex)
        endIter.forward_chars(offset + len(word))

        self.control.scriptView.textView.get_buffer().remove_all_tags(startIter, endIter)
        self.control.scriptView.textView.get_buffer().apply_tag_by_name(line.tag, startIter, endIter)

    def resetGlobalMargin(self, tag):
        margin = None
        if tag == 'description':
            margin = self.descriptionLeftMargin
        elif tag == 'character':
            margin = self.characterLeftMargin
        elif tag == 'dialog':
            margin = self.dialogLeftMargin
        elif tag == 'parenthetic':
            margin = self.parentheticLeftMargin
        elif tag == 'sceneHeading':
            margin = self.descriptionLeftMargin

        if margin != None:
            self.props.left_margin = margin

    def updateLineTag(self, line=None, formatingLastLineWhenEmpty=False, autoSceneHeading=True):

        if line is not None:
            updateLine = self.control.scriptView.lines[line]
            bufferIndex = self.control.scriptView.lines.index(updateLine)
        else:
            updateLine = self.control.currentLine()
            bufferIndex = self.control.scriptView.lines.index(updateLine)

        onLastLine = False
        if bufferIndex == len(self.control.scriptView.lines) - 1:
            onLastLine = True

        startIter = self.get_buffer().get_iter_at_line(bufferIndex)
        endIter = self.get_buffer().get_iter_at_line(bufferIndex +1)

        if endIter.get_char() == ZERO_WIDTH_SPACE:
            endIter.forward_char()

        if onLastLine:
            endIter.forward_to_line_end()

        text = self.get_buffer().get_text(startIter, endIter, True)
        # self.control.p(text)

        self.get_buffer().remove_all_tags(startIter, endIter)

        startIter = self.get_buffer().get_iter_at_line(bufferIndex)
        endIter = self.get_buffer().get_iter_at_line(bufferIndex +1)

        if endIter.get_char() == ZERO_WIDTH_SPACE:
            endIter.forward_char()

        if onLastLine:
            endIter.forward_to_line_end()

        tag = updateLine.tag
        if autoSceneHeading:
            screenplayMode = self.control.currentStory().isScreenplay
            if not screenplayMode and tag == 'sceneHeading':
                tag = 'description'
            if screenplayMode:
                if updateLine.before(self.control).tag == 'heading':
                    tag = "sceneHeading"
                    updateLine.tag = 'sceneHeading'

        self.get_buffer().apply_tag_by_name(tag, startIter, endIter)

        return updateLine.tag


    # Clipboard
    def pasteClipboard(self, widget=None):

        self.forceWordEvent()

        insertIter = self.insertIter()
        lineIndex = insertIter.get_line()
        scriptLine = self.control.scriptView.lines[lineIndex]
        if scriptLine.tag == 'heading':
            return

        self.copiedText = self.control.clipboard.wait_for_text()
        if self.copiedText == None:
            return
        self.copiedText =  self.copiedText.rstrip(ZERO_WIDTH_SPACE)
        copiedLines = self.copiedText.split('\n')

        if len(self.selectedClipboard) >= 2:
            beforeTags = [l.tag for l in self.selectedClipboard]
        else:
            beforeTags = [self.control.currentLine().tag]

        tags = self.selectionTags
        if len(tags) == 0 or len(self.selectionTags) != len(copiedLines):
            tags = ['description' for i in range(len(copiedLines))]

        if len(self.selectionTags) != len(copiedLines):
            self.selectionTags = []

        # if self.control.currentStory().index.offset > 0:
        tags[0] = beforeTags[0]

        if len(self.control.copyClipboard.lines) == 0:
            return

        self.setSelectionClipboard()
        cutEvent = self.chainDeleteSelectedTextEvent()
        if cutEvent:
            self.updateLineTag()

        cl = self.control.currentLine()
        cp = self.control.currentPage()
        pageLineIndex = cp.lines.index(cl)
        sceneIndex = self.control.currentSequence().scenes.index(self.control.currentScene())
        pageIndex = self.control.currentScene().pages.index(self.control.currentPage())
        pasteEvent = _event.Insertion(sceneIndex,
            pageIndex,
            pageLineIndex,
            self.control.currentStory().index.offset,
            self.copiedText,
            tags)

        pasteEvent.beforeTags = beforeTags

        pasteEvent.modelUpdate(self.control)
        self.control.eventManager.addEvent(pasteEvent)

        pasteEvent.viewUpdate(self.control)

    def setSelectionClipboard(self):

        bounds = self.get_buffer().get_selection_bounds()

        self.selectedClipboard = []


        if len(bounds):

            startIter, endIter = bounds

            # Do not allow selection of zero space char at end of buffer.
            if self.endIter().get_offset() == endIter.get_offset():
                endIter.backward_char()

            startMark = self.iterMark(startIter)
            endMark = self.iterMark(endIter)

            self.selectionIterStart = self.markIter(startMark)
            self.selectionIterEnd = self.markIter(endMark)

            self.get_buffer().place_cursor(self.selectionIterStart)
            self.get_buffer().select_range(self.selectionIterStart, self.selectionIterEnd)

            startLine = self.selectionIterStart.get_line()
            endLine = self.selectionIterEnd.get_line()

            for i in range(startLine, endLine + 1):
                tag = self.control.scriptView.lines[i].tag
                self.selectedClipboard.append(_story.Line(tag=tag))

            if len(self.selectedClipboard) == 1:
                self.selectedClipboard[0].text = self.get_buffer().get_text(startIter, endIter, True)


            elif len(self.selectedClipboard) == 2:
                end = self.lineEndIter(startIter.get_line())
                self.selectedClipboard[0].text = self.get_buffer().get_text(startIter, end, True)

                start = self.lineIter(endIter.get_line())
                self.selectedClipboard[1].text = self.get_buffer().get_text(start, endIter, True)

            else:
                lastLine = self.selectedClipboard.pop(-1)

                lineIndex = startIter.get_line()

                end = self.lineEndIter(startIter.get_line())
                self.selectedClipboard[0].text = self.get_buffer().get_text(startIter, end, True)

                lineIndex += 1

                for i in range(len(self.selectedClipboard) -1):
                    start = self.lineIter(lineIndex)
                    end = self.lineEndIter(lineIndex)
                    self.selectedClipboard[i+1].text = self.get_buffer().get_text(start, end, True)
                    lineIndex += 1

                self.selectedClipboard.append(lastLine)

                start = self.lineIter(lineIndex)
                self.selectedClipboard[-1].text = self.get_buffer().get_text(start, endIter, True)

            self.control.selectionClipboard.lines = list(self.selectedClipboard)

    def chainDeleteSelectedTextEvent(self):

        if len(self.control.scriptView.textView.selectedClipboard):
            return self.deleteSelectedText()

    def deleteSelectedText(self):
        if len(self.selectedClipboard):
            self.forceWordEvent()

            self.cutClipboard = list(self.selectedClipboard)

            # cutEvent = _event.CutEvent(self.control)
            text = self.get_buffer().get_text(self.selectionIterStart, self.selectionIterEnd, True)

            beforeTags = [line.tag for line in self.cutClipboard]

            startLineIndex = self.control.scriptView.textView.selectionIterStart.get_line()
            line = self.control.scriptView.lines[startLineIndex]
            offset = self.control.scriptView.textView.selectionIterStart.get_line_offset()

            cl = self.control.currentLine()
            cp = self.control.currentPage()
            pageLineIndex = cp.lines.index(cl)
            sceneIndex = self.control.currentSequence().scenes.index(self.control.currentScene())
            pageIndex = self.control.currentScene().pages.index(self.control.currentPage())

            if len(self.selectedClipboard) > 1:
                tags = [l.tag for l in self.selectedClipboard]
            else:
                tags = [cl.tag]

            # alternateFirst = None
            # if self.control.currentStory().index.offset > 0:
            #     alternateFirst = beforeTags[0]

            event = _event.Deletion(sceneIndex,
                pageIndex,
                pageLineIndex,
                self.control.currentStory().index.offset,
                text,
                tags)

            event.beforeTags = beforeTags
            # event.alternateFirst = alternateFirst

            updateLine = event.modelUpdate(self.control)
            self.control.eventManager.addEvent(event)

            # cutEvent.chained = True

            # Stop the deletion of the ZERO_WIDTH_SPACE
            endOffset = self.endIter().get_offset()
            if self.selectionIterEnd.get_offset() == endOffset:
                self.selectionIterEnd.backward_char()

            self.get_buffer().delete(self.selectionIterStart, self.selectionIterEnd)
            # self.control.eventManager.addEvent(cutEvent)

            self.control.scriptView.updateCurrentStoryIndex()

            return event

    def dragDropPaste(self):

        dragLines = self.control.copyClipboard.lines

        #pasteIter = self.iterAtLocation(self.dragBeginLocation[0], self.dragBeginLocation[1]) # - len(dragLines[-1].text))

        cl = self.currentLocation()

        if len(dragLines) == 1:
            line = cl[0]
            offset = cl[1] - len(dragLines[0].text)

        else:
            line = cl[0] - len(dragLines)
            lineIter = self.lineIter(line)
            lineEndIter = self.lineIter(line)
            lineEndIter.forward_to_line_end()
            lineText = self.get_buffer().get_text(lineIter, lineEndIter, False)
            offset = len(lineText) - len(dragLines[0].text)

        cs = self.control.scriptView.currentStory()
        cs.index.line = line
        cs.index.offset = offset

        # pasteIter = self.iterAtLoation(line, offset)
        #
        # self.get_buffer().place_cursor(pasteIter)

        # self.control.scriptView.updateCurrentStoryIndex()

        pasteEvent = _event.PasteEvent(self.control)
        self.control.eventManager.addEvent(pasteEvent)


    # Model Updating
    def forceWordEvent(self):
        if len(self.word):
            word = ''.join(self.word)
            if len(word):
                self.control.scriptView.updateCurrentStoryIndex()

                cl = self.control.currentLine()
                cp = self.control.currentPage()
                pageLineIndex = cp.lines.index(cl)
                tags = [cl.tag]
                sceneIndex = self.control.currentSequence().scenes.index(self.control.currentScene())
                pageIndex = self.control.currentScene().pages.index(self.control.currentPage())
                event = _event.Insertion(sceneIndex,
                    pageIndex,
                    pageLineIndex,
                    self.control.currentStory().index.offset - len(word),
                    word,
                    tags)
                event.beforeTags = [cl.tag]
                event.modelUpdate(self.control)
                self.control.eventManager.addEvent(event)
                if word.isupper():
                    cl.updateStoryNames(self.control)

                self.word = []

    def addCharToWord(self, character, duringKeyPressEvent=False):

        self.word.append(character)

        if character == ' ':
            word = ''.join(self.word)
            self.control.scriptView.updateCurrentStoryIndex()

            cl = self.control.currentLine()
            cp = self.control.currentPage()
            pageLineIndex = cp.lines.index(cl)
            tags = [cl.tag]
            sceneIndex = self.control.currentSequence().scenes.index(self.control.currentScene())
            pageIndex = self.control.currentScene().pages.index(self.control.currentPage())
            event = _event.Insertion(sceneIndex,
                pageIndex,
                pageLineIndex,
                self.control.currentStory().index.offset - len(word),
                word,
                tags)
            event.beforeTags = [cl.tag]

            event.modelUpdate(self.control)
            self.control.eventManager.addEvent(event)
            if word.isupper():
                cl.updateStoryNames(self.control)
            self.word = []

    def updateLocationAndTime(self, line):
        sh = SceneHeading()
        cs = self.control.currentScene()
        cs.updateLocations(sh, self.control.currentStory())
        cs.updateTimes(sh, self.control.currentStory())


    # Misc./Debugging
    def printTags(self):
        charIter = self.startIter()
        print
        print
        print "printTags"

        tagNames = [name.props.name for name in charIter.get_tags()]
        self.control.p(charIter.get_char(), tagNames)

        character = charIter.forward_char()
        while character:
            tagNames = [name.props.name for name in charIter.get_tags()]
            self.control.p(charIter.get_char(), tagNames)
            character = charIter.forward_char()

    def updatePanel(self):
        paneNumber = self.control.currentPanel()
        pad = " " * 30
        panelCount = str(self.control.currentPage().panelCount())
        self.control.panelLabel.set_text(pad + "PANEL " + str(paneNumber) + " / " + panelCount)

    def isPrintable(self, character):
        if len(character) and character in string.printable and ord(character) < 127:
            return True
        else:
            return False

    def config(self, ):
        pass

    def help(self):
        pass


    # Context Menu
    def addWord(self, arg, word):
        f = open(self.control.addWordPath, 'r')
        addWords = f.read().split('\n')
        f.close()

        f = open(self.control.removeWordPath, 'r')
        removeWords = f.read().split('\n')
        f.close()

        while '' in addWords:
            addWords.remove('')

        while '' in removeWords:
            removeWords.remove('')

        if word in removeWords:
            removeWords.remove(word)
            f = open(self.control.removeWordPath, 'w')
            for word in removeWords:
                f.write(word.rstrip().lstrip() + '\n')
            f.close()
            self.control.app.loadRemoveWordTrie()

        if self.control.wordMispelled(word):

            addWords.append(word)
            f = open(self.control.addWordPath, 'w')
            for word in addWords:
                f.write(word.rstrip().lstrip() + '\n')
            f.close()
            self.control.app.loadAddWordTrie()

    def removeWord(self, arg, word):

        f = open(self.control.addWordPath, 'r')
        addWords = f.read().split('\n')
        f.close()

        f = open(self.control.removeWordPath, 'r')
        removeWords = f.read().split('\n')
        f.close()

        while '' in addWords:
            addWords.remove('')

        while '' in removeWords:
            removeWords.remove('')

        if word in addWords:
            addWords.remove(word)
            f = open(self.control.addWordPath, 'w')
            for word in addWords:
                f.write(word.rstrip().lstrip() + '\n')
            f.close()
            self.control.app.loadAddWordTrie()

        removeWords.append(word)
        f = open(self.control.removeWordPath, 'w')
        for word in removeWords:
            f.write(word.rstrip().lstrip() + '\n')
        f.close()

        self.control.app.loadRemoveWordTrie()

    def addSelectedWord(self):
        word = ''
        self.setSelectionClipboard()
        if len(self.selectedClipboard):

            # Stop the deletion of the ZERO_WIDTH_SPACE
            endOffset = self.endIter().get_offset()
            if self.selectionIterEnd.get_offset() == endOffset:
                self.selectionIterEnd.backward_char()

            word = self.get_buffer().get_text(self.selectionIterStart, self.selectionIterEnd, False)

            if len(word.split(" ")) > 1:
                return ''

            if not self.control.wordMispelled(word):
                word = ''

        return word

    def removeSelectedWord(self):
        word = ''
        self.setSelectionClipboard()
        if len(self.selectedClipboard):

            # Stop the deletion of the ZERO_WIDTH_SPACE
            endOffset = self.endIter().get_offset()
            if self.selectionIterEnd.get_offset() == endOffset:
                self.selectionIterEnd.backward_char()

            word = self.get_buffer().get_text(self.selectionIterStart, self.selectionIterEnd, False)

            if len(word.split(" ")) > 1:
                return ''

            if self.control.wordMispelled(word):
                word = ''

        return word

    def authorContact(self, arg):
        _dialog.SetAuthorAndContactDialog(self.control, self.control.app.window)


    # Iter/Mark/Line
    def currentLocation(self):
        insertIter = self.insertIter()
        line = insertIter.get_line()
        offset = insertIter.get_line_offset()
        return line, offset

    def insertingOnFirstIter(self, event):
        isStartIter = self.insertIter().is_start()
        if isStartIter:
            if event.keyval not in [65361, 65362, 65363, 65364, 65366, 65367, 65535]: # allow arrows, pageup/down,
                return 1
        return 0

    def iterInfo(self, iter):
        info = ['line', iter.get_line()], ['line offset', iter.get_line_offset()], ['buffer offset', iter.get_offset()], ["at char", iter.get_char()],["tags", [name.props.name for name in iter.get_tags()]]
        print "insert", info
        return info

    def insertIter(self):
        return self.get_buffer().get_iter_at_mark(self.get_buffer().get_insert())

    def insertMark(self, name=None):
        return self.get_buffer().create_mark(name, self.insertIter(), True )

    def lineIter(self, index):
        return self.get_buffer().get_iter_at_line(index)

    def lineEndIter(self, line):
        lineIter = self.lineIter(line)
        if lineIter.ends_line():
            return lineIter
        else:
            lineIter.forward_to_line_end()
            return lineIter

    def startIter(self):
        return self.get_buffer().get_start_iter()

    def endIter(self):
        return self.get_buffer().get_end_iter()

    def markIter(self, mark):
        return self.get_buffer().get_iter_at_mark(mark)

    def iterMark(self, textIter, name=None):
        return self.get_buffer().create_mark(name, textIter, True )

    def iterAtLocation(self, line, offset):
        lineIter = self.lineIter(line)
        lineIter.forward_chars(offset)
        return lineIter

    def lineText(self, index):
        lineIter = self.lineIter(index)
        lineEndIter = self.lineEndIter(index)
        return self.get_buffer().get_text(lineIter, lineEndIter, False)

    def lineTags(self, index):
        tags = []
        moveIter = self.lineIter(index)
        lineEndIter = self.lineEndIter(index)
        offset = 0
        endOffset = lineEndIter.get_line_offset()
        while offset < endOffset + 1:
            currentTags = moveIter.get_tags()
            tagNames = [name.props.name for name in currentTags]
            for tn in tagNames:
                if tn not in tags:
                    tags.append(tn)
            offset += 1
            moveIter.forward_char()
        return tags


    # Handlers
    def connections(self, ):
        self.connect("key-press-event", self.keyPress)
        self.connect("key-release-event", self.keyRelease)

        self.connect("focus-out-event",self.focusOut)
        self.connect("focus-in-event",self.focusIn)
        self.add_events(Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK)

        self.connect("button-press-event",self.buttonPress)
        self.connect("button-release-event",self.buttonRelease)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)

        self.connect("leave-notify-event",self.leaveNotify)
        self.connect("enter-notify-event",self.enterNotify)

        self.connect_after("select-all", self.selectAll)

        self.get_buffer().connect("mark-set", self.markSet)

        self.connect("populate-popup", self.populatePopup)

    def removeCrossPageSelection(self):
        bounds = self.get_buffer().get_selection_bounds()
        if len(bounds):
            startLine = self.control.scriptView.lines[bounds[0].get_line()]
            endLine = self.control.scriptView.lines[bounds[1].get_line()]
            if startLine.__class__.__name__=='Line':
                startPage = startLine.heading.page
            else:
                self.get_buffer().select_range(bounds[0], bounds[0])
                return 1

            if endLine.__class__.__name__=="Line":
                endPage = endLine.heading.page
            else:
                self.get_buffer().select_range(bounds[0], bounds[0])
                return 1

            if startPage != endPage:
                self.get_buffer().select_range(bounds[0], bounds[0])
                return 1
        return 0

    def selectAllCurrentPage(self):
        pass

    def selectAll(self, widget, event):
        self.selectAllCurrentPage()
        self.get_buffer().select_range(self.endIter(), self.endIter())

    def populatePopup(self, textView, popup):

        sep = Gtk.SeparatorMenuItem()
        popup.append(sep)
        sep.show()

        addSelectedWord = self.addSelectedWord()
        if len(addSelectedWord):
            addWord = Gtk.MenuItem("Add " + addSelectedWord + " to Dictionary")
            popup.append(addWord)
            addWord.show()
            addWord.connect('activate', self.addWord, addSelectedWord)

        removeSelectedWord = self.removeSelectedWord()
        if len(removeSelectedWord):
            removeWord = Gtk.MenuItem("Remove " + removeSelectedWord + " from Dictionary")
            popup.append(removeWord)
            removeWord.show()
            removeWord.connect('activate', self.removeWord, removeSelectedWord)

        clearHistory = Gtk.MenuItem("Clear History")
        popup.append(clearHistory)
        clearHistory.show()
        clearHistory.connect('activate', self.clearHistory, self.control)

        authorContact = Gtk.MenuItem("Set Author/Contact")
        popup.append(authorContact)
        authorContact.show()
        authorContact.connect('activate', self.authorContact)

        help = Gtk.MenuItem("Help")
        popup.append(help)
        help.show()
        help.connect('activate', self.help)

    def clearHistory(self, event, control):
        for scene in self.control.currentSequence().scenes:
            scene.clearHistory(control)
        self.completionManager.reset()
        self.completion = None
        self.completing = False
        self.completeReset = False
        self.control.updateHistoryColor()

    def leaveNotify(self, widget, event):
        self.forceWordEvent()
        #self.tagIter.reset()

    def enterNotify(self, widget, event):
        pass

    def focusOut(self, widget, event):
        self.forceWordEvent()
        self.completionManager.reset()
        self.completion = None
        self.completing = False
        self.completeReset = False

    def focusIn(self, widget, event):
        pass

    def do_paste_clipboard(self):
        self.pasteClipboard()

    def do_size_allocate(self, allocation):

        # if not self.control.settingPanedWithEsc:
        #     self.control.scriptViewPanedPosition = self.control.scriptView.paned.get_position()

        if self.settingMargin:
            self.settingMargin = False
        else:
            Gtk.TextView.do_size_allocate(self, allocation)
            self.resetTags(allocation.width)
            self.settingMargin = True

    def do_cut_clipboard(self):

        self.do_copy_clipboard()

        if len(self.selectedClipboard):

            self.forceWordEvent()

            self.control.copyClipboard.lines = list(self.selectedClipboard)

            beforeTags = [line.tag for line in self.selectedClipboard]

            text = self.get_buffer().get_text(self.selectionIterStart, self.selectionIterEnd, True)

            startLineIndex = self.control.scriptView.textView.selectionIterStart.get_line()
            line =self.control.scriptView.lines[startLineIndex]
            offset =self.control.scriptView.textView.selectionIterStart.get_line_offset()

            cl = self.control.currentLine()
            cp = self.control.currentPage()
            pageLineIndex = cp.lines.index(cl)
            sceneIndex = self.control.currentSequence().scenes.index(self.control.currentScene())
            pageIndex = self.control.currentScene().pages.index(self.control.currentPage())

            if len(self.selectedClipboard) > 1:
                tags = [l.tag for l in self.selectedClipboard]
            else:
                tags = [cl.tag]

            event = _event.Deletion(sceneIndex,
                pageIndex,
                pageLineIndex,
                self.control.currentStory().index.offset,
                text,
                tags)
            event.beforeTags = beforeTags
            # event.alternateFirst = alternateFirst
            event.modelUpdate(self.control)
            event.viewUpdate(self.control)
            self.control.eventManager.addEvent(event)

            Gtk.TextView.do_cut_clipboard(self)

            self.selectedClipboard = []

            # self.updateLineTag(updateLine, self.control.scriptView.lines[updateLine].tag)

            self.control.scriptView.updateCurrentStoryIndex()

    def do_copy_clipboard(self):
        Gtk.TextView.do_copy_clipboard(self)
        self.setSelectionClipboard()
        if len(self.selectedClipboard):
            self.selectionTags = [line.tag for line in self.selectedClipboard]
        else:
            self.selectionTags = []

        self.control.copyClipboard.lines = list(self.selectedClipboard)

    def do_drag_drop(self, context, x, y, time):
        self.control.notImplemented()
        return

        self.forceWordEvent()

        self.setSelectionClipboard()
        self.control.copyClipboard.lines = list(self.selectedClipboard)

        cutEvent = _event.CutEvent(self.control)
        self.control.eventManager.addEvent(cutEvent)

        self.cutPress = True

        Gtk.TextView.do_drag_drop(self, context, x, y, time)

        self.selectedClipboard = []

        self.formatLine(cutEvent.textViewLine, self.control.scriptView.lines[cutEvent.textViewLine].tag)

        self.control.scriptView.updateCurrentStoryIndex()

    def markSet(self, buffer=None, anIter=None, mark=None):
        # This is being done so the index is immediately updated after a selection is deselected.

        if self.control.doMarkSetIndexUpdate:
            try:
                self.control.scriptView.updateCurrentStoryIndex()
            except:
                pass

        return

    def resetSettingPanedWithEsc(self):
        self.control.settingPanedWithEsc = False


class ScriptView(Gtk.Box):

    def __init__(self, control):
        Gtk.Box.__init__(self)
        self.control = control
        self.off = True

        self.lines = []
        self.headingEntries = []

        # self.paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        # self.paned.connect('map-event', self.acceptPosition)
        # self.pack_start(self.paned, 1, 1, 0)

        # self.infoTextView = Gtk.TextView()
        # self.infoViewFontSize = 16
        # self.infoTextView.connect('key-release-event', self.updateInfo)
        # self.infoTextView.connect('key-press-event', self.infoTextViewKeyPress)

        # self.scrolledWindow = Gtk.ScrolledWindow()
        # self.scrolledWindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # props = self.infoTextView.props

        # vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        #
        # eventBox = Gtk.EventBox()
        # eventBox.modify_bg(Gtk.StateFlags.NORMAL, Gdk.RGBA(1.0, 1.0, 1.0, 0.0).to_color())
        # eventBox.add(vbox)
        # self.paned.add1(eventBox)
        # self.pack_start(eventBox, 1, 1, 0)

        # children = self.scrolledWindow2.get_children()
        # self.scrolledWindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        # self.scrolledWindow.set_size_request(700, 400)
        # self.scrolledWindow.set_halign(Gtk.Align.CENTER)
        # hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        # hbox.pack_start(self.scrolledWindow, 1, 1, 0)
        # vbox.pack_start(hbox, 1, 1, 0)

        # self.scrolledWindow.add(self.infoTextView)

        # self.paned.add1(self.scrolledWindow)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        eventBox = Gtk.EventBox()
        eventBox.modify_bg(Gtk.StateFlags.NORMAL, Gdk.RGBA(1.0, 1.0, 1.0, 0.0).to_color())
        eventBox.add(vbox)
        # self.paned.add2(eventBox)
        self.pack_start(eventBox, 1, 1, 0)

        self.scrolledWindow2 = Gtk.ScrolledWindow()
        self.scrolledWindow2.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        # self.scrolledWindow2.set_size_request(200, 400)
        # self.scrolledWindow2.set_halign(Gtk.Align.CENTER)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.pack_start(self.scrolledWindow2, 1, 1, 0)
        vbox.pack_start(hbox, 1, 1, 0)

        self.createTextView()
        self.scrolledWindow2.add(self.textView)

        # self.infoTextView.props.left_margin = 25
        # self.infoTextView.props.right_margin = 100
        # self.infoTextView.props.wrap_mode = Gtk.WrapMode.WORD
        # self.infoTextView.props.pixels_below_lines = 10
        # self.infoTextView.props.pixels_above_lines = 10
        # self.infoTextView.props.left_margin = self.textView.descriptionLeftMargin
        # self.infoTextView.props.right_margin = self.textView.descriptionRightMargin

    def loadStory(self):

        self.lines = []
        self.headingEntries = []

        st = self.control.currentStory()
        pages = []
        headings = []
        for sq in st.sequences:
            for sc in sq.scenes:
                for pg in sc.pages:
                    pages.append(pg)
                    headings.append(Heading(st,sq,sc,pg))

        firstPage = pages.pop(0)
        firstHeading = headings.pop(0)

        pageText = " > " + firstHeading.page.title
        if self.control.currentStory().isScreenplay:
            pageText = ""

        if self.control.sequenceVisible:
            self.insertHeading(firstHeading.sequence.title + " > " + firstHeading.scene.title + pageText)
        else:
            self.insertHeading(firstHeading.scene.title + pageText)

        self.lines.append(firstHeading)
        self.insertPageText(firstPage)
        self.lines += firstPage.lines
        for ln in firstPage.lines:
            ln.heading = firstHeading

        for i in range(len(pages)):
            pg = pages[i]
            heading = headings[i]
            self.textBuffer.insert(self.textView.insertIter(), '\n', len('\n'))

            pageText = " > " + heading.page.title
            if self.control.currentStory().isScreenplay:
                pageText = ""

            if self.control.sequenceVisible:
                self.insertHeading(heading.sequence.title + " > " + heading.scene.title + pageText)
            else:
                self.insertHeading(heading.scene.title + pageText)

            x = heading.scene.title + pageText

            self.lines.append(heading)
            self.insertPageText(pg)
            self.lines += pg.lines
            for ln in pg.lines:
                ln.heading = heading

        lastTag = self.applyTags()
        self.textView.updatePanel()

        # self.infoTextView.get_buffer().delete(self.infoTextView.get_buffer().get_start_iter(), self.infoTextView.get_buffer().get_end_iter())
        # self.infoTextView.get_buffer().insert(self.infoTextView.get_buffer().get_start_iter(), st.info)

        self.control.currentStory().updateMispelled()

        self.control.searchView.reset()
        self.control.searchView.find = None

        self.control.updateHistoryColor()

        return lastTag

    def addZeroWidthSpace(self, lastTag):
        # This fixes a bug with the last line of buffer that has no text.
        # The line will not show it's margin visually unless there is text on it.
        # An empty line in Gtk.TextView will not show margin unless,
        # the character directly following it has that margin. usually it's newline,
        # but the last line can't have a new line following it so... ZWS.

        # This must only be called at the very end of inserting text in a reloading of TextView.

        insertIter = self.textView.insertIter()
        self.textBuffer.insert_with_tags_by_name(insertIter, ZERO_WIDTH_SPACE, lastTag)
        insertIter = self.textView.insertIter()
        insertIter.backward_chars(1)

        self.control.doMarkSetIndexUpdate = False
        self.textBuffer.place_cursor(insertIter)
        self.control.doMarkSetIndexUpdate = True

    def loadScene(self):
        self.lines = []
        self.headingEntries = []

        pages = []
        headings = []
        st = self.control.currentStory()
        currentScene = self.control.currentScene()
        for sq in self.control.currentStory().sequences:
            for sc in sq.scenes:
                for pg in sc.pages:
                    if currentScene == sc:
                        pages.append(pg)
                        headings.append(Heading(st,sq,sc,pg))

        firstPage = pages.pop(0)
        firstHeading = headings.pop(0)

        pageText = " > " + firstHeading.page.title
        if self.control.currentStory().isScreenplay:
            pageText = ""

        if self.control.sequenceVisible:
            self.insertHeading(firstHeading.sequence.title + " > " + firstHeading.scene.title + pageText)
        else:
            self.insertHeading(firstHeading.scene.title + pageText)

        self.lines.append(firstHeading)
        self.insertPageText(firstPage)
        self.lines += firstPage.lines
        for ln in firstPage.lines:
            ln.heading = firstHeading

        if not self.currentStory().isScreenplay:
            for i in range(len(pages)):
                pg = pages[i]
                heading = headings[i]
                self.textBuffer.insert(self.textView.insertIter(), '\n', len('\n'))

                pageText = " > " + heading.page.title
                if self.control.currentStory().isScreenplay:
                    pageText = ""

                if self.control.sequenceVisible:
                    self.insertHeading(heading.sequence.title + " > " + heading.scene.title + pageText)
                else:
                    self.insertHeading(heading.scene.title + pageText)

                self.lines.append(heading)
                self.insertPageText(pg)
                self.lines += pg.lines
                for ln in pg.lines:
                    ln.heading = heading

        lastTag = self.applyTags()
        self.textView.updatePanel()
        # self.infoTextView.get_buffer().delete(self.infoTextView.get_buffer().get_start_iter(), self.infoTextView.get_buffer().get_end_iter())
        # self.infoTextView.get_buffer().insert(self.infoTextView.get_buffer().get_start_iter(), currentScene.info)

        self.control.doMarkSetIndexUpdate = False
        # self.addZeroWidthSpace(lastTag)
        self.control.doMarkSetIndexUpdate = True

        self.control.searchView.reset()
        self.control.searchView.find = None

        self.control.updateHistoryColor()

        self.control.currentStory().updateTimes()
        self.control.currentStory().updateLocations()

        return lastTag

    def loadPage(self):
        self.lines = []
        self.headingEntries = []

        pages = []
        headings = []
        st = self.control.currentStory()
        currentPage = self.control.currentPage()
        for sq in st.sequences:
            for sc in sq.scenes:
                for pg in sc.pages:
                    if currentPage == pg:
                        pages.append(pg)
                        headings.append(Heading(st,sq,sc,pg))

        firstPage = pages.pop(0)
        firstHeading = headings.pop(0)

        if self.control.sequenceVisible:
            self.insertHeading(firstHeading.sequence.title + " > " + firstHeading.scene.title + " > " + firstHeading.page.title)
        else:
            self.insertHeading(firstHeading.scene.title + " > " + firstHeading.page.title)

        self.lines.append(firstHeading)
        self.insertPageText(firstPage)
        self.lines += firstPage.lines
        for ln in firstPage.lines:
            ln.heading = firstHeading

        for i in range(len(pages)):
            pg = pages[i]
            heading = headings[i]
            self.textBuffer.insert(self.textView.insertIter(), '\n', len('\n'))

            if self.control.sequenceVisible:
                self.insertHeading(heading.sequence.title + " > " + heading.scene.title + " > " + heading.page.title)
            else:
                self.insertHeading(heading.scene.title + " > " + heading.page.title)

            self.lines.append(heading)
            self.insertPageText(pg)
            self.lines += pg.lines
            for ln in pg.lines:
                ln.heading = heading

        lastTag = self.applyTags()
        self.textView.updatePanel()
        # self.infoTextView.get_buffer().delete(self.infoTextView.get_buffer().get_start_iter(), self.infoTextView.get_buffer().get_end_iter())
        # self.infoTextView.get_buffer().insert(self.infoTextView.get_buffer().get_start_iter(), currentPage.info)

        self.control.doMarkSetIndexUpdate = False
        # self.addZeroWidthSpace(lastTag)
        self.control.doMarkSetIndexUpdate = True

        self.control.searchView.reset()
        self.control.searchView.find = None

        self.control.updateHistoryColor()

        return lastTag

    # def infoTextViewKeyPress(self, widget, event):
    #
    #     if event.state & Gdk.ModifierType.CONTROL_MASK:
    #
    #         if event.keyval == 45: # minus key
    #             if self.control.scriptView.infoViewFontSize > 4:
    #                 self.infoViewFontSize -= 1
    #                 self.infoTextView.modify_font(Pango.FontDescription("Courier Prime " + str(self.infoViewFontSize)))
    #                 self.infoTextView.props.left_margin = self.textView.descriptionLeftMargin
    #                 self.infoTextView.props.right_margin = self.textView.descriptionRightMargin
    #
    #         elif event.keyval==61: # equal key
    #             self.infoViewFontSize += 1
    #             self.infoTextView.modify_font(Pango.FontDescription("Courier Prime " + str(self.infoViewFontSize)))
    #             self.infoTextView.props.left_margin = self.textView.descriptionLeftMargin
    #             self.infoTextView.props.right_margin = self.textView.descriptionRightMargin

    def acceptPosition(self):
        pass

    def createTextView(self):

        self.textView = TextView(self.control)

        self.textBuffer = self.textView.get_buffer()

        self.textTagTable = self.textBuffer.get_tag_table()

    def postInit(self):
        pass

    def insertHeading(self, text):

        startMark = self.textView.insertMark()

        anchor = self.textBuffer.create_child_anchor(self.textView.insertIter())
        entry = Gtk.Label()
        entry.set_markup("""<span font_family='monospace' font='9.0' foreground='#bbbbbb' >""" + text + """</span>""")

        self.headingEntries.append(entry)

        self.textView.add_child_at_anchor(entry, anchor)

        self.textBuffer.insert(self.textView.insertIter(), '\n', len('\n'))

        startIter = self.textView.insertIter()
        startIter.backward_chars(2)
        endIter = self.textView.insertIter()
        endIter.forward_char()

        self.textView.get_buffer().apply_tag_by_name('heading', startIter, endIter)

        self.textBuffer.place_cursor(self.textView.insertIter())

        self.textBuffer.delete_mark(startMark)

    def insertPageText(self, pg):

        lineCount = len(pg.lines)
        line = pg.lines[0]
        text = ''.join(line.text)

        self.textView.get_buffer().insert(self.textView.insertIter(), text, len(text))

        for i in range(lineCount-1):
            line = pg.lines[i +1]
            text = '\n' + ''.join(line.text)
            self.textView.get_buffer().insert(self.textView.insertIter(), text, len(text))

    def applyTags(self):

        for i in range(len(self.lines)):
            line = self.lines[i]

            if line.__class__.__name__ == "Line":

                startIter = self.textView.get_buffer().get_iter_at_line(i)
                endIter = self.textView.get_buffer().get_iter_at_line(i)
                endIter.forward_to_line_end()
                endIter.forward_char()

                self.textView.get_buffer().remove_all_tags(startIter, endIter)

                startIter = self.textView.get_buffer().get_iter_at_line(i)
                endIter = self.textView.get_buffer().get_iter_at_line(i)
                endIter.forward_to_line_end()
                endIter.forward_char()

                self.textView.get_buffer().apply_tag_by_name(line.tag, startIter, endIter)
            elif line.__class__.__name__ == "Heading":

                startIter = self.textView.get_buffer().get_iter_at_line(i)

                endIter = self.textView.get_buffer().get_iter_at_line(i)
                endIter.forward_to_line_end()
                endIter.forward_char()

                self.textView.get_buffer().remove_all_tags(startIter, endIter)

                startIter = self.textView.get_buffer().get_iter_at_line(i)

                endIter = self.textView.get_buffer().get_iter_at_line(i)
                endIter.forward_to_line_end()
                endIter.forward_char()

                self.textView.get_buffer().apply_tag_by_name('heading', startIter, endIter)

        return line.tag

    # def updateInfo(self, textView, eventKey):
    #
    #     if eventKey.keyval == 65307: # esc
    #         self.control.settingPanedWithEsc = True
    #
    #         panePosition = self.control.scriptView.paned.get_position()
    #
    #         if panePosition > self.get_allocated_height() -10:
    #
    #             self.control.scriptViewPanedPosition = 150
    #
    #             self.control.scriptView.paned.set_position(self.control.scriptViewPanedPosition)
    #         else:
    #
    #             self.control.scriptView.paned.set_position(self.get_allocated_height())
    #
    #         GObject.timeout_add(2000, self.textView.resetSettingPanedWithEsc)
    #         return 1
    #
    #
    #     # text = self.infoTextView.get_buffer().get_text(self.infoTextView.get_buffer().get_start_iter(), self.infoTextView.get_buffer().get_end_iter(), True)
    #
    #     # if self.control.category == 'story':
    #     #     self.currentStory().info = text
    #     # elif self.control.category == 'sequence':
    #     #     self.currentSequence().info = text
    #     # elif self.control.category == 'scene':
    #     #     self.currentScene().info = text
    #     # elif self.control.category == 'page':
    #     #     self.currentPage().info = text

    def load(self):
        pass

    def resetAndLoad(self):

        self.reset()
        category = self.control.category

        if category == 'story':
            lastTag = self.control.scriptView.loadStory()
        elif category == 'scene':
            lastTag = self.control.scriptView.loadScene()
        elif category == 'page':
            lastTag = self.control.scriptView.loadPage()

        self.updateTitles()

        self.control.app.updateWindowTitle()

        # self.control.currentStory().updateStoryNames()

        # self.paned.set_position(self.control.scriptViewPanedPosition)

        self.control.category = category

        self.control.scriptView.addZeroWidthSpace(lastTag)

        if not self.control.screenplayModeSwitch.activating:
            if self.control.currentStory().isScreenplay:
                self.control.screenplayModeSwitch.set_state(True)
            else:
                self.control.screenplayModeSwitch.set_state(False)
            self.control.screenplayModeSwitch.callHandlerCode = False

        self.textView.tagIter.updateMode(self.control)

    def reset(self):
        self.textView.get_buffer().set_text("")

    def currentIssue(self):
        pass

    def currentStory(self):
        cl = self.currentLine()
        if cl.__class__.__name__ == "Heading":
            return cl.story
        else:
            return cl.heading.story

    def currentSequence(self):
        cl = self.currentLine()
        if cl.__class__.__name__ == "Heading":
            return cl.sequence
        else:
            return cl.heading.sequence

    def currentScene(self):
        cl = self.currentLine()
        if cl.__class__.__name__ == "Heading":
            return cl.scene
        else:
            return cl.heading.scene

    def currentPage(self):
        cl = self.currentLine()
        if cl.__class__.__name__ == "Heading":
            return cl.page
        else:
            return cl.heading.page

    def currentLine(self):
        insertIter = self.textView.insertIter()
        index = insertIter.get_line()
        line = self.lines[index]
        return line

    def previousLine(self):
        insertIter = self.textView.insertIter()
        insertIter.backward_chars(1)
        index = insertIter.get_line()
        line = self.lines[index]
        return line

    def updateCurrentStoryIndex(self):
        line, offset = self.textView.currentLocation()
        st = self.currentStory()
        ln = self.currentLine()
        pg = self.currentPage()
        sc = self.currentScene()
        sq = self.currentSequence()
        if ln.__class__.__name__ == 'Line':
            st.index.sequence = 0 #st.sequences.index(sq)
            st.index.scene = sq.scenes.index(sc)
            st.index.page = sc.pages.index(pg)
            st.index.line = pg.lines.index(ln)
            st.index.offset = offset
        else:
            st.index.sequence = 0 #st.sequences.index(sq)
            st.index.scene = sq.scenes.index(sc)
            st.index.page = sc.pages.index(pg)
            st.index.line = 0
            st.index.offset = 0

    def updateTitles(self, story=None):

        sqCount = 0
        pgCount = 0
        if story == None:
            story = self.control.currentStory()
        for sq in story.sequences:
            sqCount +=1

            scCount = 0
            for sc in sq.scenes:
                scCount +=1

                for pg in sc.pages:
                    pg.title = "Page " + str(pgCount +1)
                    pgCount +=1

    def removeScreenplayTags(self):
        st = self.control.currentStory()
        for sq in st.sequences:
            for sc in sq.scenes:
                for pg in sc.pages:
                    for ln in pg.lines:
                        if ln.tag == 'sceneHeading':
                            ln.tag = 'description'