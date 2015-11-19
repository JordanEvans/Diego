import string

from gi.repository import Gtk, Gdk, GLib, Pango

import _event
import _story

class TagIter(object):

    def __init__(self):
        self.tags = ['description', 'character', 'dialog']
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
        index = self.tags.index(tag)
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
        self.buffer = self.get_buffer()

        self.selectionMarkStart = None
        self.selectionMarkEnd = None

        self.word = []

        self.tagIter = TagIter()

        self.settingMargin = True

        self.fontSize = 10
        self.width = 749
        self.descriptionWidth = int(40.3125 * self.fontSize) #549
        self.characterWidth = self.descriptionWidth * 0.5
        self.dialogWidth = self.descriptionWidth * 0.7

        descriptionLeftMargin = self.descriptionWidth * 0.1
        characterLeftMargin = self.descriptionWidth * 0.55
        dialogLeftMargin = self.descriptionWidth * 0.3

        self.descriptionLeftMargin = descriptionLeftMargin
        self.characterLeftMargin = characterLeftMargin
        self.dialogLeftMargin = dialogLeftMargin

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

        self.forcingWordEvent = False
        self.newLineEvent = False
        self.deleteEvent = False
        self.backspaceEvent = False
        self.arrowPress = False
        self.cutPress = False
        self.formatingLine = False

    def resetTags(self, width=None):

        if width == None:
            width = self.get_allocated_width()
        self.width = width

        descriptionWidth = int(40.3125 * self.fontSize)
        characterWidth = self.descriptionWidth * 0.5
        dialogWidth = self.descriptionWidth * 0.70

        descriptionLeftMargin = descriptionWidth * 0.1
        characterLeftMargin = descriptionWidth * 0.55
        dialogLeftMargin = descriptionWidth * 0.3

        descriptionRightMargin = self.width - (descriptionLeftMargin + descriptionWidth)
        characterRightMargin = self.width - (characterLeftMargin + characterWidth)
        dialogRightMargin = self.width - (dialogLeftMargin + dialogWidth)

        if descriptionRightMargin < 50:
            return
        if characterLeftMargin < 0:
            return
        if dialogLeftMargin < 0:
            return

        self.descriptionWidth = descriptionWidth
        self.characterWidth = characterWidth
        self.dialogWidth = dialogWidth

        self.descriptionLeftMargin = descriptionLeftMargin
        self.characterLeftMargin = characterLeftMargin
        self.dialogLeftMargin = dialogLeftMargin

        self.descriptionRightMargin = descriptionRightMargin
        self.characterRightMargin = characterRightMargin
        self.dialogRightMargin = dialogRightMargin

        self.props.left_margin = self.descriptionLeftMargin
        self.props.right_margin = self.descriptionRightMargin

        self.descriptionTag.props.left_margin = self.descriptionLeftMargin
        self.characterTag.props.left_margin = self.characterLeftMargin
        self.dialogTag.props.left_margin = self.dialogLeftMargin

        self.descriptionTag.props.right_margin = self.descriptionRightMargin
        self.characterTag.props.right_margin = self.characterRightMargin
        self.dialogTag.props.right_margin = self.dialogRightMargin

        self.descriptionTag.props.font = "Sans " + str(self.fontSize)
        self.characterTag.props.font = "Sans " + str(self.fontSize)
        self.dialogTag.props.font = "Sans " + str(self.fontSize)

        self.control.scriptView.infoTextView.props.left_margin = self.control.scriptView.textView.descriptionLeftMargin
        self.control.scriptView.infoTextView.props.right_margin = self.control.scriptView.textView.descriptionRightMargin


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

        self.descriptionTag = self.buffer.create_tag("description",
                                                     background_rgba=descriptionBackground,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=10,
                                                     pixels_below_lines=10,
                                                     left_margin=self.descriptionLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Sans " + str(self.fontSize))

        self.characterTag = self.buffer.create_tag("character",
                                                   background_rgba=characterBackground,
                                                   left_margin=self.characterLeftMargin,
                                                   right_margin=self.characterRightMargin,
                                                   justification=Gtk.Justification.LEFT,
                                                   pixels_inside_wrap=pixelsInsideWrap,
                                                   pixels_above_lines=10,
                                                   pixels_below_lines=0,
                                                   font="Sans " + str(self.fontSize))

        self.dialogTag = self.buffer.create_tag("dialog",
                                                background_rgba=dialogBackground,
                                                left_margin=self.dialogLeftMargin,
                                                right_margin=self.dialogRightMargin,
                                                pixels_inside_wrap=pixelsInsideWrap,
                                                pixels_above_lines=2,
                                                pixels_below_lines=10,
                                                font="Sans " + str(self.fontSize))

    def do_size_allocate(self, allocation):

        if self.settingMargin:
            self.settingMargin = False
        else:
            Gtk.TextView.do_size_allocate(self, allocation)
            self.resetTags(allocation.width)
            self.settingMargin = True

        # if not self.control.startingUpApp:
        #     self.control.currentStory().horizontalPanePosition = self.control.scriptView.paned.get_position()

    def keyPress(self, widget, event):
        self.forcingWordEvent = False
        self.newLineEvent = False
        self.deleteEvent = False
        self.backspaceEvent = False
        self.arrowPress = False
        self.cutPress = False
        self.formatingLine = False

        insertIter = self.insertIter()

        if self.removeCrossPageSelection():
            return 1

        if event.state & Gdk.ModifierType.CONTROL_MASK:

            if event.keyval == 65507: # pasting
                return 1

            elif event.keyval == 45: # minus key
                if self.fontSize > 4:
                    self.fontSize -= 1
                    self.resetTags()
                    return 1

            elif event.keyval==61: # equal key
                self.fontSize += 1
                self.resetTags()
                return 1

        else:

            if event.keyval == 65307: # esc
                if self.control.scriptView.paned.get_position() == 0:
                    self.control.scriptView.paned.set_position(self.control.currentStory().horizontalPanePosition)
                else:
                    self.control.currentStory().horizontalPanePosition = self.control.scriptView.paned.get_position()
                    self.control.scriptView.paned.set_position(0)
                return

            if event.keyval == 65470: # F1 press
                self.printTags()
                return 1

            if self.insertingOnFirstIter(event):
                return 1

            if (event.keyval == 32) and insertIter.get_line_offset() == 0:
                self.tagIter.increment()
                self.control.currentLine().tag = self.tagIter.tag()
                self.updateLineTag(formatingEmptyLine=True)
                self.control.currentStory().saved = False
                self.formatingLine = True
                return 1

            if (event.keyval == 65293):
                return self.returnPress()

            elif (event.keyval == 65288):
                self.backspacePress()
                return 1

            elif (event.keyval == 65535):
                self.deletePress()
                return 1

            elif event.keyval in [65361,65362,65363,65364]:
                self.forceWordEvent()
                self.arrowPress = True
                self.tagIter.reset()
                return 0

            if self.pressOnHeading():
                return 1

            # if not self.deleteEvent and not self.backspaceEvent and not self.arrowPress and self.isPrintable(event.string):
            if self.isPrintable(event.string):

                self.setSelectionClipboard()
                cutEvent = self.chainDeleteSelectedTextEvent()
                insertIter = self.insertIter()

                self.buffer.insert(insertIter, event.string, 1)

                self.updateLineTag()

                self.addCharToWord(event, duringKeyPressEvent=True)
                if cutEvent:
                    self.forceWordEvent()

                self.control.currentStory().saved = False

            if event.keyval == 32:
                self.forcingWordEvent = True

            # print event.keyval
            return 1

    def keyRelease(self, widget, event):

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

    def updateLineTag(self, line=None, formatingEmptyLine=False):

        if line != None:
            cp = self.control.currentPage()
            updateLine = self.control.scriptView.lines[line]
            bufferIndex = self.control.scriptView.lines.index(updateLine)
        else:
            updateLine = self.control.currentLine()
            bufferIndex = self.control.scriptView.lines.index(updateLine)

        startIter = self.buffer.get_iter_at_line(bufferIndex)
        endIter = self.buffer.get_iter_at_line(bufferIndex +1)

        if formatingEmptyLine:
            # When true, this handles the last line of the editor.
            if endIter.get_line() == len(self.control.scriptView.lines) -1 :
                endIter.forward_to_end()

        text = self.buffer.get_text(startIter, endIter, True)

        self.buffer.remove_all_tags(startIter, endIter)

        startIter = self.buffer.get_iter_at_line(bufferIndex)
        endIter = self.buffer.get_iter_at_line(bufferIndex + 1)

        if formatingEmptyLine:
            # When true, this handles the last line of the editor.
            if endIter.get_line() == len(self.control.scriptView.lines) -1 :
                endIter.forward_to_end()

        self.buffer.apply_tag_by_name(updateLine.tag, startIter, endIter)

    def printTags(self):
        charIter = self.startIter()
        print
        print
        while 1:
            self.p(charIter.get_tags())
            try:
                charIter.forward_char()

            except:
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

        if canGoForward:
            forwardTags = forwardIter.get_tags()
            names = [name.props.name for name in forwardTags]
            if "heading" in names or backwardChar == '\xef\xbf\xbc':
                nextCharIsHeading = True

        if canGoBackward:
            backwardTags = backwardIter.get_tags()
            names = [name.props.name for name in backwardTags]
            if "heading" in names or backwardChar == '\xef\xbf\xbc':
                prevCharIsHeading = True

        if currentCharIsHeading:
            return

        self.forceWordEvent()

        cutEvent = self.chainDeleteSelectedTextEvent()
        if cutEvent != None :
            cutEvent.chained = False

        currentLine = self.control.currentLine()

        if currentCharIsNewLine:
            newLineEvent = _event.NewLineEvent(self.control, tag=currentLine.tag)
            self.control.currentStory().eventManager.addEvent(newLineEvent)
            insertIter = self.insertIter()
            lineIndex = insertIter.get_line()

            self.buffer.insert(insertIter, '\n', 1)

            startIter = self.buffer.get_iter_at_line(lineIndex)
            endIter = self.buffer.get_iter_at_line(lineIndex)
            endIter.forward_to_line_end()
            endIter.forward_char()
            sc,ec,text = startIter.get_char(), endIter.get_char(), self.buffer.get_text(startIter, endIter, True)
            self.buffer.remove_all_tags(startIter, endIter)
            self.buffer.apply_tag_by_name(currentLine.tag, startIter, endIter)

            startIter = self.buffer.get_iter_at_line(lineIndex + 1)
            endIter = self.buffer.get_iter_at_line(lineIndex + 1)
            endIter.forward_char()
            sc,ec,text = startIter.get_char(), endIter.get_char(), self.buffer.get_text(startIter, endIter, True)
            self.buffer.remove_all_tags(startIter, endIter)
            self.buffer.apply_tag_by_name(currentLine.tag, startIter, endIter)

        else:
            insertIter = self.insertIter()
            endLineIter = self.lineEndIter(insertIter.get_line())
            carryText = self.buffer.get_text(insertIter,endLineIter,False)
            if len(carryText):
                self.buffer.delete(insertIter, endLineIter)
            newLineEvent = _event.NewLineEvent(self.control, carryText, tag=currentLine.tag)
            self.control.currentStory().eventManager.addEvent(newLineEvent)
            insertIter = self.insertIter()

            lineIndex = insertIter.get_line()

            self.buffer.insert(insertIter, '\n' + carryText, len(carryText) + 1)

            startIter = self.buffer.get_iter_at_line(lineIndex)
            endIter = self.buffer.get_iter_at_line(lineIndex)
            endIter.forward_to_line_end()
            endIter.forward_char()

            sc,ec,text = startIter.get_char(), endIter.get_char(), self.buffer.get_text(startIter, endIter, True)
            self.buffer.remove_all_tags(startIter, endIter)
            self.buffer.apply_tag_by_name(currentLine.tag, startIter, endIter)

            startIter = self.buffer.get_iter_at_line(lineIndex + 1)
            endIter = self.buffer.get_iter_at_line(lineIndex + 1)
            endIter.forward_to_line_end()
            endIter.forward_char()

            sc,ec,text = startIter.get_char(), endIter.get_char(), self.buffer.get_text(startIter, endIter, True)
            self.buffer.remove_all_tags(startIter, endIter)
            self.buffer.apply_tag_by_name(currentLine.tag, startIter, endIter)

            insertIter = self.insertIter()
            insertIter.backward_chars(len(carryText))
            self.buffer.place_cursor(insertIter)

        self.newLineEvent = True
        self.control.currentStory().saved = False

        self.updateLineTag(previousLineIndex)
        self.updateLineTag()

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

        bounds = self.buffer.get_selection_bounds()
        if len(bounds):
            selectStart, selectEnd = bounds
            if selectEnd.get_char() == '\xef\xbf\xbc':
                return 1

            startCanGoBackward = selectStart.backward_char()
            if startCanGoBackward:
                if selectStart.get_char() == '\xef\xbf\xbc':
                    return 1

        if canGoForward:
            forwardTags = forwardIter.get_tags()
            names = [name.props.name for name in forwardTags]
            if "heading" in names or backwardChar == '\xef\xbf\xbc':
                nextCharIsHeading = True

        if canGoBackward:
            backwardTags = backwardIter.get_tags()
            names = [name.props.name for name in backwardTags]
            if "heading" in names or backwardChar == '\xef\xbf\xbc':
                prevCharIsHeading = True

        if not len(bounds) and currentCharIsNewLine and forwardChar == '\xef\xbf\xbc':
            if insertIter.get_chars_in_line() > 1:
                return 1

        if len(bounds) and nextCharIsHeading and prevCharIsHeading:
            return 1

        if currentChar and not nextCharIsHeading:

            self.forceWordEvent()
            self.setSelectionClipboard()
            cutEvent = self.chainDeleteSelectedTextEvent()
            if cutEvent:
                self.control.currentStory().saved = False
                self.updateLineTag()
                return 1

            self.deleteEvent = True
            nextIter = self.insertIter()
            nextIter.forward_char()
            delChar = self.buffer.get_text(insertIter, nextIter, True)
            self.buffer.delete(insertIter, nextIter)
            self.control.currentStory().saved = False

            self.control.currentStory().eventManager.addEvent(_event.DeleteEvent(self.control, delChar))

        else:
            return 1

    def backspacePress(self):
        insertIter = self.insertIter()
        currentChar = insertIter.get_char()
        currentCharIsNewLine = currentChar == '\n'

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
            if "heading" in names or backwardChar == '\xef\xbf\xbc':
                prevCharIsHeading = True

        forwardIter = self.insertIter()
        canGoForward = forwardIter.forward_char()
        forwardChar = forwardIter.get_char()

        nextCharIsHeading = False
        if canGoForward:
            forwardTags = forwardIter.get_tags()
            names = [name.props.name for name in forwardTags]
            if "heading" in names or backwardChar == '\xef\xbf\xbc':
                nextCharIsHeading = True

        self.control.scriptView.textView.markSet()
        self.setSelectionClipboard()

        # Will not backspace if a heading is there, but will use the backspace as cut event if there is a selection.
        if prevCharIsHeading and len(self.control.scriptView.textView.selectedClipboard) == 0:
            return 1

        if currentCharIsHeading:
            return 1

        if currentChar == '\xef\xbf\xbc' and not prevCharIsHeading:
            currentLine = insertIter.get_line()
            prevLineIter = self.get_buffer().get_iter_at_line(currentLine-1)
            if prevLineIter.get_chars_in_line() > 1:
                return 1

        self.forceWordEvent()
        #self.setSelectionClipboard()
        cutEvent = self.chainDeleteSelectedTextEvent()
        self.updateLineTag()
        if cutEvent:
            self.control.currentStory().saved = False
            return 1

        self.backspaceEvent = True

        insertIter = self.insertIter()
        backIter = self.insertIter()
        backIter.backward_char()

        if backIter.get_char() == '\n':
            removedNewLine = True
        else:
            removedNewLine = False

        self.control.currentStory().eventManager.addEvent(_event.BackspaceEvent(self.control, removedNewLine))

        self.buffer.delete(backIter, insertIter)

        self.control.currentStory().saved = False

        # if removedNewLine:
        #     self.updatePanel()

    def buttonPress(self, widget, event):
        self.forceWordEvent()

    def buttonRelease(self, widget, event):
        self.removeCrossPageSelection()
        self.control.scriptView.updateCurrentStoryIndex()
        self.tagIter.load(self.control.currentLine().tag)
        self.updateLineTag()
        self.selectedClipboard = []

        self.control.scriptView.updateCurrentStoryIndex()

        self.buttonReleaseIter = self.insertIter()

        self.updatePanel()

    def updatePanel(self):
        paneNumber = self.control.currentPanel()
        pad = " " * 30
        self.control.panelLabel.set_text(pad + "PANEL " + str(paneNumber))

    def do_cut_clipboard(self):

        self.setSelectionClipboard()

        if len(self.selectedClipboard):

            self.forceWordEvent()

            self.control.copyClipboard.lines = list(self.selectedClipboard)

            cutEvent = _event.CutEvent(self.control)
            self.control.currentStory().eventManager.addEvent(cutEvent)

            self.cutPress = True

            Gtk.TextView.do_cut_clipboard(self)

            self.control.currentStory().saved = False

            self.selectedClipboard = []

            self.formatLine(cutEvent.textViewLine, self.control.scriptView.lines[cutEvent.textViewLine].tag)

            self.control.scriptView.updateCurrentStoryIndex()

    def do_copy_clipboard(self):
        self.setSelectionClipboard()
        self.control.copyClipboard.lines = list(self.selectedClipboard)
        Gtk.TextView.do_copy_clipboard(self)

    def isPrintable(self, character):
        if len(character) and character in string.printable and ord(character) < 127:
            return True
        else:
            return False

    def chainDeleteSelectedTextEvent(self):

        if len(self.control.scriptView.textView.selectedClipboard):
            return self.control.scriptView.textView.deleteSelectedText()

    def deleteSelectedText(self):
        if len(self.selectedClipboard):
            self.forceWordEvent()

            self.cutClipboard = list(self.selectedClipboard)
            cutEvent = _event.CutEvent(self.control)
            cutEvent.chained = True

            self.buffer.delete(self.selectionIterStart, self.selectionIterEnd)

            self.control.currentStory().eventManager.addEvent(cutEvent)

            self.control.scriptView.updateCurrentStoryIndex()

            return cutEvent

    def removeCrossPageSelection(self):
        bounds = self.buffer.get_selection_bounds()
        if len(bounds):
            startLine = self.control.scriptView.lines[bounds[0].get_line()]
            endLine = self.control.scriptView.lines[bounds[1].get_line()]
            if startLine.__class__.__name__=='Line':
                startPage = startLine.heading.page
            else:
                self.buffer.select_range(bounds[0], bounds[0])
                return 1

            if endLine.__class__.__name__=="Line":
                endPage = endLine.heading.page
            else:
                self.buffer.select_range(bounds[0], bounds[0])
                return 1

            if startPage != endPage:
                self.buffer.select_range(bounds[0], bounds[0])
                return 1
        return 0

    def config(self, ):
        pass

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

        self.connect("focus-out-event",self.focusOut)
        self.connect("focus-in-event",self.focusIn)

        self.connect("leave-notify-event",self.leaveNotify)
        self.connect("enter-notify-event",self.enterNotify)

        self.connect_after("select-all", self.selectAll)

        self.buffer.connect("mark-set", self.markSet)

    def do_drag_drop(self, context, x, y, time):

        self.control.notImplemented()
        return

        self.forceWordEvent()

        self.setSelectionClipboard()
        self.control.copyClipboard.lines = list(self.selectedClipboard)

        cutEvent = _event.CutEvent(self.control)
        self.control.currentStory().eventManager.addEvent(cutEvent)

        self.cutPress = True

        Gtk.TextView.do_drag_drop(self, context, x, y, time)

        self.control.currentStory().saved = False

        self.selectedClipboard = []

        self.formatLine(cutEvent.textViewLine, self.control.scriptView.lines[cutEvent.textViewLine].tag)

        self.control.scriptView.updateCurrentStoryIndex()

        #GLib.timeout_add(1000, self.dragDropPaste)

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
            lineText = self.buffer.get_text(lineIter, lineEndIter, False)
            offset = len(lineText) - len(dragLines[0].text)

        cs = self.control.scriptView.currentStory()
        cs.index.line = line
        cs.index.offset = offset

        # pasteIter = self.iterAtLoation(line, offset)
        #
        # self.buffer.place_cursor(pasteIter)

        # self.control.scriptView.updateCurrentStoryIndex()

        pasteEvent = _event.PasteEvent(self.control)
        self.control.currentStory().eventManager.addEvent(pasteEvent)

    def markSet(self, buffer=None, anIter=None, mark=None):
        # This is being done so the index is immediately updated after a selection is deselected.
        try:
            self.control.scriptView.updateCurrentStoryIndex()
        except:
            pass

        return

    def formatLine(self, index, tag):
        startIter = self.buffer.get_iter_at_line(index)
        endIter = self.buffer.get_iter_at_line(index)
        endIter.forward_to_line_end()
        endIter.forward_char()

        sc,ec,text = startIter.get_char(), endIter.get_char(), self.buffer.get_text(startIter, endIter, True)

        self.buffer.remove_all_tags(startIter, endIter)
        self.buffer.apply_tag_by_name(tag, startIter, endIter)

    def do_paste_clipboard(self):
        self.pasteClipboard()

    def pasteClipboard(self, widget=None):

        if len(self.control.copyClipboard.lines) == 0:
            return

        insertIter = self.insertIter()
        lineOffset = insertIter.get_line_offset()
        currentLine = self.control.currentLine()
        bufferIndex = self.control.scriptView.lines.index(currentLine)
        startLineIter = self.lineIter(bufferIndex)
        endLineIter = self.lineIter(bufferIndex)
        endLineIter.forward_to_line_end()
        lineText = self.buffer.get_text(startLineIter, endLineIter, False)

        # self.control.p('text', self.buffer.get_text(startLineIter, endLineIter, False))

        self.setSelectionClipboard()
        cutEvent = self.chainDeleteSelectedTextEvent()
        if cutEvent:
            self.updateLineTag()

        self.pasteEvent = _event.PasteEvent(self.control)
        self.control.currentStory().eventManager.addEvent(self.pasteEvent)

        insertIter = self.insertIter()

        if len(self.control.copyClipboard.lines) == 1:
            self.buffer.insert(insertIter, self.control.copyClipboard.lines[0].text)

        else:
            for i in range(len(self.control.copyClipboard.lines) - 1):
                line = self.control.copyClipboard.lines[i]
                self.buffer.insert(insertIter, line.text + "\n")

            self.buffer.insert(insertIter, self.control.copyClipboard.lines[i+1].text)

        # If the line is empty that is being pasted on, then the copyClipboard determines tag.
        # If the line is not empty and the line offset is zero, the copyClipboard determines tag.
        if len(lineText) == 0 or lineOffset == 0:
            line = self.pasteEvent.clipboardLines[0]
            self.control.scriptView.lines[bufferIndex].tag = line.tag
            for i in range(len(self.pasteEvent.clipboardLines)):
                line = self.pasteEvent.clipboardLines[i]
                self.formatLine(bufferIndex + i, line.tag)

        # If the line is not empty and the line offset is non zero, the buffer line determines tag.
        else:

            line = self.control.scriptView.lines[bufferIndex]
            self.formatLine(bufferIndex, line.tag)

            for i in range(1, len(self.pasteEvent.clipboardLines)):
                line = self.pasteEvent.clipboardLines[i]
                self.formatLine(bufferIndex + i, line.tag)

        self.control.currentStory().saved = False

    def pressOnHeading(self):
        if 'heading' in [tag.props.name for tag in self.insertIter().get_tags()]:
            return 1

    def forceWordEvent(self):
        if len(self.word):
            word = ''.join(self.word)
            if len(word):
                self.control.scriptView.updateCurrentStoryIndex()
                self.control.currentStory().eventManager.addEvent(_event.WordEvent(self.control, word))
                self.word = []

    def addCharToWord(self, event, duringKeyPressEvent=False):
        self.word.append(event.string)
        if event.string == ' ':
            word = ''.join(self.word)
            self.control.scriptView.updateCurrentStoryIndex()
            self.control.currentStory().eventManager.addEvent(_event.WordEvent(self.control, word, duringKeyPressEvent))
            self.word = []

    def setSelectionClipboard(self):

        bounds = self.buffer.get_selection_bounds()

        self.selectedClipboard = []

        if len(bounds):
            startIter, endIter = bounds

            if startIter.get_offset() > endIter.get_offset():
                import os
                os.exit("iters switche around in setSelectionClipboar")
                holder = endIter
                endIter = startIter
                startIter = holder

            self.selectionIterStart = startIter
            self.selectionIterEnd = endIter

            startLine = startIter.get_line()
            endLine = endIter.get_line()

            for i in range(startLine, endLine + 1):
                tag = self.control.scriptView.lines[i].tag
                self.selectedClipboard.append(_story.Line(tag=tag))

            if len(self.selectedClipboard) == 1:
                self.selectedClipboard[0].text = self.buffer.get_text(startIter, endIter, True)


            elif len(self.selectedClipboard) == 2:
                end = self.lineEndIter(startIter.get_line())
                self.selectedClipboard[0].text = self.buffer.get_text(startIter, end, True)

                start = self.lineIter(endIter.get_line())
                self.selectedClipboard[1].text = self.buffer.get_text(start, endIter, True)

            else:
                lastLine = self.selectedClipboard.pop(-1)

                lineIndex = startIter.get_line()

                end = self.lineEndIter(startIter.get_line())
                self.selectedClipboard[0].text = self.buffer.get_text(startIter, end, True)

                lineIndex += 1

                for i in range(len(self.selectedClipboard) -1):
                    start = self.lineIter(lineIndex)
                    end = self.lineEndIter(lineIndex)
                    self.selectedClipboard[i+1].text = self.buffer.get_text(start, end, True)
                    lineIndex += 1

                self.selectedClipboard.append(lastLine)

                start = self.lineIter(lineIndex)
                self.selectedClipboard[-1].text = self.buffer.get_text(start, endIter, True)

            self.control.selectionClipboard.lines = list(self.selectedClipboard)

    def selectAll(self, widget, event):
        self.buffer.select_range(self.endIter(), self.endIter())

    def currentLocation(self):
        insertIter = self.insertIter()
        line = insertIter.get_line()
        offset = insertIter.get_line_offset()
        return line, offset

    def printTags(self):

        walkIter = self.get_buffer().get_iter_at_offset(0)

        names = walkIter.get_tags()
        if len(names):
            names = [name.props.name for name in names]
        print [walkIter.get_char(), ]

        while walkIter.forward_char():
            names = walkIter.get_tags()
            if len(names):
                names = [name.props.name for name in names]
            print [walkIter.get_char(), names]

    def insertingOnFirstIter(self, event):
        isStartIter = self.insertIter().is_start()
        if isStartIter:
            if event.keyval not in [65361, 65362, 65363, 65364, 65366, 65367]: # allow arrows, pageup/down,
                return 1
        return 0

    def insertIter(self):
        return self.get_buffer().get_iter_at_mark(self.get_buffer().get_insert())

    def insertMark(self, name=None):
        return self.get_buffer().create_mark(name, self.insertIter(), True )

    def lineIter(self, index):
        return self.buffer.get_iter_at_line(index)

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

    def leaveNotify(self, widget, event):
        self.forceWordEvent()
        self.tagIter.reset()

    def enterNotify(self, widget, event):
        pass

    def focusOut(self, widget, event):
        self.forceWordEvent()
        self.tagIter.reset()

    def focusIn(self, widget, event):
        pass


class ScriptView(Gtk.Box):

    def __init__(self, control):
        Gtk.Box.__init__(self)
        self.control = control
        self.off = True

        self.lines = []

        self.paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.paned.connect('map-event', self.acceptPosition)
        self.pack_start(self.paned, 1, 1, 0)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.infoTextView = Gtk.TextView()
        self.infoViewFontSize = 16
        self.infoTextView.connect('key-release-event', self.updateInfo)
        self.infoTextView.connect('key-press-event', self.infoTextViewKeyPress)

        self.scrolledWindow = Gtk.ScrolledWindow()
        self.scrolledWindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.scrolledWindow.add(self.infoTextView)

        props = self.infoTextView.props
        self.paned.add1(self.scrolledWindow)
        self.paned.add2(vbox)

        self.scrolledWindow = Gtk.ScrolledWindow()
        self.scrolledWindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        vbox.pack_start(self.scrolledWindow, 1, 1, 0)

        self.createTextView()
        self.scrolledWindow.add(self.textView)

        self.infoTextView.props.left_margin = 25
        self.infoTextView.props.right_margin = 100
        self.infoTextView.props.wrap_mode = Gtk.WrapMode.WORD
        self.infoTextView.props.pixels_below_lines = 10
        self.infoTextView.props.pixels_above_lines = 10
        self.infoTextView.props.left_margin = self.textView.descriptionLeftMargin
        self.infoTextView.props.right_margin = self.textView.descriptionRightMargin

    def infoTextViewKeyPress(self, widget, event):

        if event.state & Gdk.ModifierType.CONTROL_MASK:
            print event.keyval

            if event.keyval == 45: # minus key
                if self.control.scriptView.infoViewFontSize > 4:
                    self.infoViewFontSize -= 1
                    self.infoTextView.modify_font(Pango.FontDescription("Sans " + str(self.infoViewFontSize)))
                    self.infoTextView.props.left_margin = self.textView.descriptionLeftMargin
                    self.infoTextView.props.right_margin = self.textView.descriptionRightMargin

            elif event.keyval==61: # equal key
                self.infoViewFontSize += 1
                self.infoTextView.modify_font(Pango.FontDescription("Sans " + str(self.infoViewFontSize)))
                self.infoTextView.props.left_margin = self.textView.descriptionLeftMargin
                self.infoTextView.props.right_margin = self.textView.descriptionRightMargin

    def acceptPosition(self):
        print 'ap'

    def createTextView(self):

        self.textView = TextView(self.control)

        self.textBuffer = self.textView.get_buffer()

        self.textTagTable = self.textBuffer.get_tag_table()

        self.bt = self.textBuffer.create_tag("heading")
        self.bt.props.editable=False

        self.dt = self.textBuffer.create_tag("default", editable=True)

        #
        # self.textTagTable.add(headingTag)

    def postInit(self):
        pass

    def insertHeading(self, text):

        startMark = self.textView.insertMark()

        anchor = self.textBuffer.create_child_anchor(self.textView.insertIter())
        entry = Gtk.Label()
        entry.set_markup("""<span font_family='monospace' font='9.0' foreground='#99bbff' >""" + text + """</span>""")

        self.textView.add_child_at_anchor(entry, anchor)

        self.textBuffer.insert(self.textView.insertIter(), '\n', len('\n'))

        self.textBuffer.place_cursor(self.textView.insertIter())

        self.textBuffer.delete_mark(startMark)

    def insertPageText(self, pg):

        lineCount = len(pg.lines)
        line = pg.lines[0]
        text = ''.join(line.text)

        self.textView.buffer.insert(self.textView.insertIter(), text, len(text))

        for i in range(lineCount-1):
            line = pg.lines[i +1]
            text = '\n' + ''.join(line.text)
            self.textView.buffer.insert(self.textView.insertIter(), text, len(text))

    def loadStory(self):
        self.lines = []

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

        self.applyTags()
        self.textView.updatePanel()

        self.infoTextView.get_buffer().delete(self.infoTextView.get_buffer().get_start_iter(), self.infoTextView.get_buffer().get_end_iter())
        self.infoTextView.get_buffer().insert(self.infoTextView.get_buffer().get_start_iter(), st.info)

        # self.textView.printTags()

    def applyTags(self):

        for i in range(len(self.lines)):
            line = self.lines[i]

            if line.__class__.__name__ == "Line":

                startIter = self.textView.buffer.get_iter_at_line(i)
                #startIter.forward_to_line_end()
                endIter = self.textView.buffer.get_iter_at_line(i)
                endIter.forward_to_line_end()
                endIter.forward_char()

                self.textView.buffer.remove_all_tags(startIter, endIter)

                startIter = self.textView.buffer.get_iter_at_line(i)
                # startIter.forward_to_line_end()
                endIter = self.textView.buffer.get_iter_at_line(i)
                endIter.forward_to_line_end()
                endIter.forward_char()

                self.textView.buffer.apply_tag_by_name(line.tag, startIter, endIter)
            elif line.__class__.__name__ == "Heading":

                startIter = self.textView.buffer.get_iter_at_line(i)

                endIter = self.textView.buffer.get_iter_at_line(i)
                endIter.forward_to_line_end()
                endIter.forward_char()

                self.textView.buffer.remove_all_tags(startIter, endIter)

                startIter = self.textView.buffer.get_iter_at_line(i)

                endIter = self.textView.buffer.get_iter_at_line(i)
                endIter.forward_to_line_end()
                endIter.forward_char()

                self.textView.buffer.apply_tag_by_name('heading', startIter, endIter)

    def loadSequence(self):
        self.lines = []

        pages = []
        headings = []
        st = self.control.currentStory()
        currentSequence = self.control.currentSequence()
        for sq in self.control.currentStory().sequences:
            for sc in sq.scenes:
                for pg in sc.pages:
                    if currentSequence == sq:
                        pages.append(pg)
                        headings.append(Heading(st,sq,sc,pg))

        firstPage = pages.pop(0)
        firstHeading = headings.pop(0)

        self.insertHeading(firstHeading.sequence.title + " > " + firstHeading.scene.title + " > " + firstHeading.page.title)
        
        self.lines.append(firstHeading)
        self.insertPageText(firstPage)
        self.lines += firstPage.lines
        for ln in firstPage.lines:
            ln.heading = firstHeading

        for i in range(len(pages)):
            pg = pages[i]
            heading = headings[i]
            self.textBuffer.insert(self.textView.insertIter(), '\n', len('\n'))

            self.insertHeading(heading.sequence.title + " > " + heading.scene.title + " > " + heading.page.title)

            self.lines.append(heading)
            self.insertPageText(pg)
            self.lines += pg.lines
            for ln in pg.lines:
                ln.heading = heading

        self.applyTags()
        self.textView.updatePanel()
        self.infoTextView.get_buffer().delete(self.infoTextView.get_buffer().get_start_iter(), self.infoTextView.get_buffer().get_end_iter())
        self.infoTextView.get_buffer().insert(self.infoTextView.get_buffer().get_start_iter(), currentSequence.info)

    def updateInfo(self, textView, eventKey):

        if eventKey.keyval == 65307: # esc
            panePosition = self.control.scriptView.paned.get_position()

            if panePosition > self.get_allocated_height() -10:
                cs = self.control.currentStory()
                # if self.control.currentStory().horizontalPanePosition > self.get_allocated_height() -10:
                #     cs.horizontalPanePosition = 150
                self.control.scriptView.paned.set_position(cs.horizontalPanePosition)
            else:

                self.control.currentStory().horizontalPanePosition = self.control.scriptView.paned.get_position()
                self.control.scriptView.paned.set_position(self.get_allocated_height())
            return 1

        text = self.infoTextView.get_buffer().get_text(self.infoTextView.get_buffer().get_start_iter(), self.infoTextView.get_buffer().get_end_iter(), True)

        if self.control.category == 'story':
            self.currentStory().info = text
        elif self.control.category == 'sequence':
            self.currentSequence().info = text
        elif self.control.category == 'scene':
            self.currentScene().info = text
        elif self.control.category == 'page':
            self.currentPage().info = text

    def loadScene(self):
        self.lines = []

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

        self.applyTags()
        self.textView.updatePanel()
        self.infoTextView.get_buffer().delete(self.infoTextView.get_buffer().get_start_iter(), self.infoTextView.get_buffer().get_end_iter())
        self.infoTextView.get_buffer().insert(self.infoTextView.get_buffer().get_start_iter(), currentScene.info)

    def loadPage(self):
        self.lines = []

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

        self.applyTags()
        self.textView.updatePanel()
        self.infoTextView.get_buffer().delete(self.infoTextView.get_buffer().get_start_iter(), self.infoTextView.get_buffer().get_end_iter())
        self.infoTextView.get_buffer().insert(self.infoTextView.get_buffer().get_start_iter(), currentPage.info)

    def load(self):
        pass

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
        # self.control.p("usi", line, offset)
        st = self.currentStory()
        ln = self.currentLine()
        pg = self.currentPage()
        sc = self.currentScene()
        sq = self.currentSequence()
        if ln.__class__.__name__ == 'Line':
            st.index.sequence = st.sequences.index(sq)
            st.index.scene = sq.scenes.index(sc)
            st.index.page = sc.pages.index(pg)
            st.index.line = pg.lines.index(ln)
            st.index.offset = offset
        else:
            st.index.sequence = st.sequences.index(sq)
            st.index.scene = sq.scenes.index(sc)
            st.index.page = sc.pages.index(pg)
            st.index.line = 0
            st.index.offet = 0

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
