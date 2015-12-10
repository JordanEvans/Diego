import string, os

from gi.repository import Gtk, Gdk, GLib, Pango, GObject

import _event
import _story

ZERO_WIDTH_SPACE = u'\u200B'.encode('utf-8')
HEADING = '\xef\xbf\xbc'
NON_WORD_CHARACTERS = [' ', '\n', ',', ':', ';', '!', '"', "'", HEADING]

DESCRIPTION_WIDTH = 52.0 #40.3125
DIALOG_LEFT_FACTOR = 0.34
CHARACTER_LEFT_FACTOR = 0.536
PARENTHETIC_LEFT_FACTOR = 0.45
CHARACTER_WIDTH_FACTOR = 0.35
DIALOG_WIDTH_FACTOR = 0.5
PARENTHETIC_WIDTH_FACTOR = 0.50

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

        components = intExt, location, time, notation
        stripped = []
        for component in components:
            stripped.append(component.lstrip().rstrip())
        components = stripped

        return components

    def cursorComponent(self, text, offset):

        component = 'intExt'
        hitLocation = False
        hitTime = False

        for i in range(len(text)):
            if offset == i:
                return component
            c = text[i]
            if c == '.' and not hitLocation:
                component = 'location'
            if c == '-' and not hitTime:
                component = 'time'

            if c == '-' and hitTime:
                component = 'notation'

        return component

    def completeLine(self, line, offset):
        #components = self.componentsFromString(line.text)
        print self.cursorComponent(line, offset)

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
        self.buffer = self.get_buffer()

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

        self.intExts = ["INT.", "EXT."]

    def buttonPress(self, widget, event):

        self.forceWordEvent()

        # # Update names in the scene where the cursor is moving from a character line.
        # self.buttonPressScene = self.control.currentScene()
        # if self.tagIter.tag() == 'character':
        #     self.buttonPressScene.updateCompletionNames()

        if self.tagIter.tag() == "character":
            self.control.currentStory().addName(self.control.currentLine().text)

    def buttonRelease(self, widget, event):

        buttonReleaseScene = self.control.currentScene()

        self.removeCrossPageSelection()

        self.control.scriptView.updateCurrentStoryIndex()
        self.tagIter.load(self.control.currentLine().tag)

        tag = self.updateLineTag()
        self.selectedClipboard = []

        self.updatePanel()

        tag = self.tagIter.tag()
        self.resetGlobalMargin(tag)

        # This forces the cursor before the ZERO_WIDTH_SPACE
        insertIter = self.insertIter()
        if insertIter.get_offset() == self.endIter().get_offset():
            insertIter.backward_char()
            bounds = self.buffer.get_selection_bounds()
            if bounds:
                startMark = self.iterMark(bounds[0])
                bounds[1].backward_char()
                endMark = self.iterMark(bounds[1])
            self.buffer.place_cursor(insertIter)
            if bounds:
                self.buffer.select_range(self.markIter(startMark), self.markIter(endMark))

        # # If changing to another scene, update the completion names so they are relevant to that scene.
        # if buttonReleaseScene != self.buttonPressScene:
        #     buttonReleaseScene.updateCompletionNames()

        # sh = SceneHeading()
        # sh.completeLine(self.control.currentLine().text, self.control.currentStory().index.offset)

        # self.printTags()

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

        if event.state & Gdk.ModifierType.SHIFT_MASK:

            if event.keyval >= 65 and event.keyval <= 90:

                if self.control.currentLine().tag == 'sceneHeading':
                    returnValue = self.completeSceneHeading(event)
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
                return 1

            elif event.keyval == 99: #copy
                self.do_copy_clipboard()
                return 1

            elif event.keyval == 120: #cut
                self.do_cut_clipboard()
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
                return 1

        self.nameIter = None
        self.sceneHeadingIter = None

        if event.keyval == 65289: # doing formating for the tab character now.
            currentLine = self.control.currentLine()
            if currentLine.tag not in ['heading', 'sceneHeading']:

                self.tagIter.increment()

                currentLine.tag = self.tagIter.tag()
                index = self.control.scriptView.lines.index(currentLine)

                tag = self.updateLineTag(line=index, formatingLastLineWhenEmpty=True, autoSceneHeading=False)
                self.control.currentStory().saved = False
                self.formatingLine = True
                self.resetGlobalMargin(tag)

            return 1

        if event.keyval == 65307: # esc
            if self.control.scriptView.paned.get_position() == 0:
                self.control.scriptView.paned.set_position(self.control.currentStory().horizontalPanePosition)
            else:
                self.control.currentStory().horizontalPanePosition = self.control.scriptView.paned.get_position()
                self.control.scriptView.paned.set_position(0)
            return

        if event.keyval == 65470: # F1 press
            return 1

        if self.insertingOnFirstIter(event):
            return 1

        if event.keyval == 32 and insertIter.get_line_offset() == 0: # format line

            # Do not format a Scene Heading, the first line of a scene.
            currentLine = self.control.currentLine()
            if currentLine.tag in ['heading', 'sceneHeading']:
                return 1

            self.tagIter.increment()
            currentLine.tag = self.tagIter.tag()

            tag = self.updateLineTag(formatingLastLineWhenEmpty=True)
            self.control.currentStory().saved = False
            self.formatingLine = True
            self.resetGlobalMargin(tag)

            return 1

        if (event.keyval == 65293): # new line
            return self.returnPress()

        elif (event.keyval == 65288): # backspace
            self.backspacePress()
            # if self.tagIter.tag() == 'character':
            #     self.control.currentScene().updateCompletionNames()
            return 1

        elif (event.keyval == 65535): # delete
            self.deletePress()
            return 1

        elif event.keyval in [65361,65362,65363,65364]: # arrow key
            self.forceWordEvent()
            self.arrowPress = True

            if self.tagIter.tag() == 'character':
                self.control.currentScene().updateCompletionNames()

            return 0

        if self.pressOnHeading():
            return 1

        # if not self.deleteEvent and not self.backspaceEvent and not self.arrowPress and self.isPrintable(event.string):
        if self.isPrintable(event.string):

            character = event.string
            if self.control.currentLine().tag == 'sceneHeading':
                character = event.string.upper()

            self.setSelectionClipboard()
            cutEvent = self.chainDeleteSelectedTextEvent()
            insertIter = self.insertIter()

            self.buffer.insert(insertIter, character, 1)

            self.updateLineTag()

            self.addCharToWord(character, duringKeyPressEvent=True)

            if cutEvent:
                self.forceWordEvent()

            self.control.currentStory().saved = False

        if event.keyval == 32:
            self.forcingWordEvent = True

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

        if self.arrowPress:
            # In case the line has changed, TagIter needs current line tag.
            self.tagIter.load(self.control.currentLine().tag)

        # self.printTags()

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

                        # get rid of first upper case that in in self.word
                        self.word.pop(-1)
                        wordHasLength = len(self.word)

                        # write the word to the model.
                        self.forceWordEvent()

                        # remove the first upper from the buffer, corresponding with model
                        startIter = self.insertIter()
                        endIter = self.insertIter()
                        startIter.backward_chars(1)
                        self.buffer.delete(startIter,endIter)

                        # complete the current iters name
                        self.completeCharacterName(self.sceneHeadingIter.name(), wordHasLength)

                        return 1

                    elif self.sceneHeadingIter == None:
                        pass

                    # Here means we atleast autocompleted once and continue to do so.
                    elif self.sceneHeadingIter.initChar == character:

                        # Delete the last completed name in the buffer.
                        startIter = self.insertIter()
                        endIter = self.insertIter()
                        startIter.backward_chars(len(self.sceneHeadingIter.name()))
                        self.buffer.delete(startIter,endIter)

                        # Delete the last completed name in the model.
                        offset = self.control.currentStory().index.offset
                        text = self.control.currentLine().text
                        x = text[:offset - len(self.sceneHeadingIter.name())]
                        y = text[offset:]
                        currentLine = self.control.currentLine()
                        currentLine.text = text[:offset - len(self.sceneHeadingIter.name())] + text[offset:]

                        # The index must be updated where the deletion began.
                        self.control.currentStory().index.offset -= (len(self.sceneHeadingIter.name()) - 1)

                        # Bring the next name forward and complete it.
                        self.sceneHeadingIter.increment()
                        self.completeCharacterName(self.sceneHeadingIter.name(), 0)

                        return 1

                    # Here we have been completing, but changed the start letter of the character name.
                    else:
                        # Delete the last completed name in the buffer.
                        startIter = self.insertIter()
                        endIter = self.insertIter()
                        startIter.backward_chars(len(self.sceneHeadingIter.name()))
                        self.buffer.delete(startIter,endIter)

                        # Delete the last completed name in the model.
                        offset = self.control.currentStory().index.offset
                        text = self.control.currentLine().text
                        x = text[:offset - len(self.sceneHeadingIter.name())]
                        y = text[offset:]
                        currentLine = self.control.currentLine()
                        currentLine.text = text[:offset - len(self.sceneHeadingIter.name())] + text[offset:]

                        # The index must be updated where the deletion began.
                        self.control.currentStory().index.offset -= (len(self.sceneHeadingIter.name()) - 1)

                        # Reset the NameIter and complete
                        self.sceneHeadingIter = NameIter(prefixes, character)
                        self.completeCharacterName(self.sceneHeadingIter.name(), 0)

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

                for name in self.control.currentStory().names:
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

                        # get rid of first upper case that in in self.word
                        self.word.pop(-1)
                        wordHasLength = len(self.word)

                        # write the word to the model.
                        self.forceWordEvent()

                        # remove the first upper from the buffer, corresponding with model
                        startIter = self.insertIter()
                        endIter = self.insertIter()
                        startIter.backward_chars(1)
                        self.buffer.delete(startIter,endIter)

                        # complete the current iters name
                        self.completeCharacterName(self.nameIter.name(), wordHasLength)

                        return 1

                    elif self.nameIter == None:
                        pass

                    # Here means we atleast autocompleted once and continue to do so.
                    elif self.nameIter.initChar == character:

                        # Delete the last completed name in the buffer.
                        startIter = self.insertIter()
                        endIter = self.insertIter()
                        startIter.backward_chars(len(self.nameIter.name()))
                        self.buffer.delete(startIter,endIter)

                        # Delete the last completed name in the model.
                        offset = self.control.currentStory().index.offset
                        text = self.control.currentLine().text
                        x = text[:offset - len(self.nameIter.name())]
                        y = text[offset:]
                        currentLine = self.control.currentLine()
                        currentLine.text = text[:offset - len(self.nameIter.name())] + text[offset:]

                        # The index must be updated where the deletion began.
                        self.control.currentStory().index.offset -= (len(self.nameIter.name()) - 1)

                        # Bring the next name forward and complete it.
                        self.nameIter.increment()
                        self.completeCharacterName(self.nameIter.name(), 0)

                        return 1

                    # Here we have been completing, but changed the start letter of the character name.
                    else:
                        # Delete the last completed name in the buffer.
                        startIter = self.insertIter()
                        endIter = self.insertIter()
                        startIter.backward_chars(len(self.nameIter.name()))
                        self.buffer.delete(startIter,endIter)

                        # Delete the last completed name in the model.
                        offset = self.control.currentStory().index.offset
                        text = self.control.currentLine().text
                        x = text[:offset - len(self.nameIter.name())]
                        y = text[offset:]
                        currentLine = self.control.currentLine()
                        currentLine.text = text[:offset - len(self.nameIter.name())] + text[offset:]

                        # The index must be updated where the deletion began.
                        self.control.currentStory().index.offset -= (len(self.nameIter.name()) - 1)

                        # Reset the NameIter and complete
                        self.nameIter = NameIter(prefixes, character)
                        self.completeCharacterName(self.nameIter.name(), 0)

                        return 1

    def resetTags(self, width=None):

        if width == None:
            width = self.get_allocated_width()
        self.width = width

        descriptionWidth = int(DESCRIPTION_WIDTH * self.fontSize)
        characterWidth = self.descriptionWidth * CHARACTER_WIDTH_FACTOR
        dialogWidth = self.descriptionWidth * DIALOG_WIDTH_FACTOR
        parentheticWidth = self.descriptionWidth * PARENTHETIC_WIDTH_FACTOR

        descriptionLeftMargin = descriptionWidth * 0.1
        characterLeftMargin = descriptionWidth * CHARACTER_LEFT_FACTOR
        dialogLeftMargin = descriptionWidth * DIALOG_LEFT_FACTOR
        parentheticLeftMargin = descriptionWidth * PARENTHETIC_LEFT_FACTOR

        descriptionRightMargin = self.width - (descriptionLeftMargin + descriptionWidth)
        characterRightMargin = self.width - (characterLeftMargin + characterWidth)
        dialogRightMargin = self.width - (dialogLeftMargin + dialogWidth)
        parentheticRightMargin = self.width - (dialogLeftMargin + parentheticWidth)

        self.descriptionLeftMargin = descriptionLeftMargin
        self.characterLeftMargin = characterLeftMargin
        self.dialogLeftMargin = dialogLeftMargin
        self.parentheticLeftMargin = parentheticLeftMargin

        if descriptionRightMargin < 50:
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
        self.sceneHeadingTag.props.left_margin = self.descriptionLeftMargin

        self.descriptionTag.props.right_margin = self.descriptionRightMargin
        self.characterTag.props.right_margin = self.characterRightMargin
        self.dialogTag.props.right_margin = self.dialogRightMargin
        self.parentheticTag.props.right_margin = self.parentheticRightMargin
        self.sceneHeadingTag.props.right_margin = self.descriptionRightMargin

        self.descriptionFindTag.props.right_margin = self.descriptionRightMargin
        self.characterFindTag.props.right_margin = self.characterRightMargin
        self.dialogFindTag.props.right_margin = self.dialogRightMargin
        self.parentheticFindTag.props.right_margin = self.parentheticRightMargin
        self.sceneHeadingTag.props.right_margin = self.descriptionRightMargin

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

        self.control.scriptView.infoTextView.props.left_margin = self.control.scriptView.textView.descriptionLeftMargin
        self.control.scriptView.infoTextView.props.right_margin = self.control.scriptView.textView.descriptionRightMargin

        # Fixing last line tag issue.
        self.modify_font(Pango.FontDescription("Courier Prime " + str(self.fontSize)))
        self.props.left_margin = self.descriptionLeftMargin

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

        self.descriptionTag = self.buffer.create_tag("description",
                                                     background_rgba=descriptionBackground,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=10,
                                                     pixels_below_lines=10,
                                                     left_margin=self.descriptionLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize))

        self.characterTag = self.buffer.create_tag("character",
                                                   background_rgba=characterBackground,
                                                   left_margin=self.characterLeftMargin,
                                                   right_margin=self.characterRightMargin,
                                                   justification=Gtk.Justification.LEFT,
                                                   pixels_inside_wrap=pixelsInsideWrap,
                                                   pixels_above_lines=10,
                                                   pixels_below_lines=0,
                                                   font="Courier Prime " + str(self.fontSize))

        self.dialogTag = self.buffer.create_tag("dialog",
                                                background_rgba=dialogBackground,
                                                left_margin=self.dialogLeftMargin,
                                                right_margin=self.dialogRightMargin,
                                                pixels_inside_wrap=pixelsInsideWrap,
                                                pixels_above_lines=0,
                                                pixels_below_lines=10,
                                                font="Courier Prime " + str(self.fontSize))

        self.parentheticTag = self.buffer.create_tag("parenthetic",
                                                     background_rgba=descriptionBackground,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=0,
                                                     pixels_below_lines=0,
                                                     left_margin=self.parentheticLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize))

        self.headingTag = self.buffer.create_tag("heading",
                                                     background_rgba=descriptionBackground,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=10,
                                                     pixels_below_lines=10,
                                                     left_margin=self.descriptionLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize),
                                                     editable=False)

        self.sceneHeadingTag = self.buffer.create_tag("sceneHeading",
                                                     background_rgba=descriptionBackground, #Gdk.RGBA(0.0, 0.0, 1.0, 0.1), #descriptionBackground,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=10,
                                                     pixels_below_lines=10,
                                                     left_margin=self.descriptionLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize))


        ## Find Tags

        self.descriptionFindTag = self.buffer.create_tag("descriptionFind",
                                                     background_rgba=findColor,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=10,
                                                     pixels_below_lines=10,
                                                     left_margin=self.descriptionLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize))

        self.characterFindTag = self.buffer.create_tag("characterFind",
                                                   background_rgba=findColor,
                                                   left_margin=self.characterLeftMargin,
                                                   right_margin=self.characterRightMargin,
                                                   justification=Gtk.Justification.LEFT,
                                                   pixels_inside_wrap=pixelsInsideWrap,
                                                   pixels_above_lines=10,
                                                   pixels_below_lines=0,
                                                   font="Courier Prime " + str(self.fontSize))

        self.dialogFindTag = self.buffer.create_tag("dialogFind",
                                                background_rgba=findColor,
                                                left_margin=self.dialogLeftMargin,
                                                right_margin=self.dialogRightMargin,
                                                pixels_inside_wrap=pixelsInsideWrap,
                                                pixels_above_lines=0,
                                                pixels_below_lines=10,
                                                font="Courier Prime " + str(self.fontSize))

        self.parentheticFindTag = self.buffer.create_tag("parentheticFind",
                                                     background_rgba=findColor,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=0,
                                                     pixels_below_lines=0,
                                                     left_margin=self.parentheticLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize))


        self.sceneHeadingFindTag = self.buffer.create_tag("sceneHeadingFind",
                                                     background_rgba=Gdk.RGBA(0.0, 0.0, 1.0, 0.1), #descriptionBackground,
                                                     pixels_inside_wrap=pixelsInsideWrap,
                                                     pixels_above_lines=10,
                                                     pixels_below_lines=10,
                                                     left_margin=self.descriptionLeftMargin,
                                                     right_margin=self.descriptionRightMargin,
                                                     font="Courier Prime " + str(self.fontSize))

    def do_size_allocate(self, allocation):

        if self.settingMargin:
            self.settingMargin = False
        else:
            Gtk.TextView.do_size_allocate(self, allocation)
            self.resetTags(allocation.width)
            self.settingMargin = True

    def completeCharacterName(self, name, wordHasLength):

        currentLine = self.control.currentLine()

        # Lower case letters in words that are not the first character of a word and not upper case.
        if currentLine.tag not in ["character", "sceneHeading"]:
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

        ace = _event.AutocompleteCharacterEvent(self.control, name)
        self.control.currentStory().eventManager.addEvent(ace)

        insertIter = self.insertIter()
        self.buffer.insert(insertIter, name, len(name))

        offset = self.control.currentStory().index.offset
        text = self.control.currentLine().text

        if wordHasLength:
            currentLine.text = text[:offset - 0] + name + text[offset - 0:]
        else:
            currentLine.text = text[:offset - 1] + name + text[offset - 1:]

        index = self.control.scriptView.lines.index(currentLine)

        if len(name):
            self.formatLine(index, self.tagIter.tag())

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
            #self.updateLineTag(True)

    def updateLineTag(self, line=None, formatingLastLineWhenEmpty=False, autoSceneHeading=True):

        if line != None:
            cp = self.control.currentPage()
            updateLine = self.control.scriptView.lines[line]
            bufferIndex = self.control.scriptView.lines.index(updateLine)
        else:
            updateLine = self.control.currentLine()
            bufferIndex = self.control.scriptView.lines.index(updateLine)

        onLastLine = False
        if bufferIndex == len(self.control.scriptView.lines) - 1:
            onLastLine = True

        startIter = self.buffer.get_iter_at_line(bufferIndex)
        endIter = self.buffer.get_iter_at_line(bufferIndex +1)

        if endIter.get_char() == ZERO_WIDTH_SPACE:
            endIter.forward_char()

        if onLastLine:
            endIter.forward_to_line_end()

        text = self.buffer.get_text(startIter, endIter, True)

        self.buffer.remove_all_tags(startIter, endIter)

        startIter = self.buffer.get_iter_at_line(bufferIndex)
        endIter = self.buffer.get_iter_at_line(bufferIndex +1)

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
                if self.control.currentLine().before(self.control).tag == 'heading':
                    tag = "sceneHeading"
                    self.control.currentLine().tag = 'sceneHeading'

        self.buffer.apply_tag_by_name(tag, startIter, endIter)

        return updateLine.tag

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

    def iterInfo(self, iter):
        info = iter.get_line(), iter.get_offset(), iter.get_char(), [name.props.name for name in iter.get_tags()]
        print "insert", info
        return info

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
            if "heading" in names or backwardChar == HEADING:
                nextCharIsHeading = True

        if canGoBackward:
            backwardTags = backwardIter.get_tags()
            names = [name.props.name for name in backwardTags]
            if "heading" in names or backwardChar == HEADING:
                prevCharIsHeading = True

        self.forceWordEvent()

        if self.tagIter.tag() == "character":
            self.control.currentStory().addName(self.control.currentLine().text)

        if self.control.currentLine().tag == "sceneHeading":
            sh = SceneHeading()
            location = sh.location(self.control.currentLine().text)
            self.control.currentStory().addLocation(location)
            time = sh.time(self.control.currentLine().text)
            self.control.currentStory().addTime(time)


        # In case the cursor is at the end of a heading line, allow a new line to be created.
        if currentCharIsHeading:
            # return

            # Push the cursor to the next line.
            insertIter = self.insertIter()
            insertIter.forward_char()
            self.buffer.place_cursor(insertIter)

            # Update the model so the current line is next line.
            currentLine = self.control.currentLine()
            lineIndex = self.control.currentPage().lines.index(currentLine)
            #self.control.currentStory().index.line = lineIndex + 1
            self.control.currentStory().index.offset = 0
            tag = self.control.currentLine().tag
            self.tagIter.load(tag)

        # if self.tagIter.tag() == 'character':
        #     self.control.currentScene().updateCompletionNames()

        cutEvent = self.chainDeleteSelectedTextEvent()
        if cutEvent != None :
            cutEvent.chained = False

        currentLine = self.control.currentLine()

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

        if currentLine.tag == 'sceneHeading':
            newLineTag = 'description'
            components = SceneHeading().componentsFromString(currentLine.text)
            if len(components) > 1:
                self.control.currentStory().addLocation(components[1])
                # if components[1] not in self.locations:
                #     self.locations.append(components[1])
                #     self.locations.sort()

        self.tagIter.load(newLineTag)

        if currentCharIsNewLine:

            if currentCharIsHeading:

                nextLineTag = newLineTag
                newLineTag = 'description'

                insertIter = self.insertIter()
                lineIndex = insertIter.get_line()

                newLineEvent = _event.NewLineEvent(self.control, tag=newLineTag, fromHeading=True)
                self.control.currentStory().eventManager.addEvent(newLineEvent)

                self.buffer.insert(insertIter, '\n', 1)

                insertIter = self.insertIter()
                insertIter.backward_char()
                self.buffer.place_cursor(insertIter)

                # self.control.currentStory().index.line = lineIndex - 1

            else:
                newLineEvent = _event.NewLineEvent(self.control, tag=newLineTag)
                self.control.currentStory().eventManager.addEvent(newLineEvent)
                insertIter = self.insertIter()
                lineIndex = insertIter.get_line()

                self.buffer.insert(insertIter, '\n', 1)

                startIter = self.buffer.get_iter_at_line(lineIndex + 1)
                endIter = self.buffer.get_iter_at_line(lineIndex + 1)
                endIter.forward_char()
                sc,ec,text = startIter.get_char(), endIter.get_char(), self.buffer.get_text(startIter, endIter, True)
                self.buffer.remove_all_tags(startIter, endIter)
                self.buffer.apply_tag_by_name(newLineTag, startIter, endIter)

        else:

            # Get the carry text (if any), delete it in the buffer and send it to the NewLineEvent
            insertIter = self.insertIter()
            of = insertIter.get_offset()
            endLineIter = self.lineEndIter(insertIter.get_line())
            of2 = endLineIter.get_offset()

            onLastLine = False
            if endLineIter.get_offset() == self.endIter().get_offset():
                onLastLine = True
                endLineIter.backward_char()

            carryText = self.buffer.get_text(insertIter, endLineIter, False)

            #Fixes the last line problem.
            if carryText == ZERO_WIDTH_SPACE:
                carryText = ''

            if len(carryText):
                self.buffer.delete(insertIter, endLineIter)
            newLineEvent = _event.NewLineEvent(self.control, carryText, tag=newLineTag)
            self.control.currentStory().eventManager.addEvent(newLineEvent)

            # Insert the new line in the buffer and append the carry text.
            insertIter = self.insertIter()
            lineIndex = insertIter.get_line()
            self.buffer.insert(insertIter, '\n' + carryText, len(carryText) + 1)

            # Remove all tags, starts with the new line text (if any) and stops 'after' next newLine character.

            startIter = self.buffer.get_iter_at_line(lineIndex + 1)
            endIter = self.buffer.get_iter_at_line(lineIndex + 1)
            endIter.forward_to_line_end()
            endIter.forward_char()

            self.buffer.remove_all_tags(startIter, endIter)
            self.buffer.apply_tag_by_name(newLineTag, startIter, endIter)

            # Places the cursor on zero offset of newline.
            insertIter = self.insertIter()
            insertIter.backward_chars(len(carryText))
            self.buffer.place_cursor(insertIter)

        self.newLineEvent = True
        self.control.currentStory().saved = False

        self.updateLineTag(previousLineIndex)
        tag = self.updateLineTag()

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
            if selectEnd.get_char() == HEADING:
                return 1

            startCanGoBackward = selectStart.backward_char()
            if startCanGoBackward:
                if selectStart.get_char() == HEADING:
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

        if not len(bounds) and currentCharIsNewLine and forwardChar == HEADING:
            if insertIter.get_chars_in_line() > 1:
                return 1

        if len(bounds) and nextCharIsHeading and prevCharIsHeading:
            return 1

        if currentChar == ZERO_WIDTH_SPACE:
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

        # Will not backspace if a heading is there, but will use the backspace as cut event if there is a selection.
        if prevCharIsHeading and len(self.control.scriptView.textView.selectedClipboard) == 0:
            return 1

        if currentCharIsHeading:
            return 1

        if currentChar == HEADING and not prevCharIsHeading:
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

    def updatePanel(self):
        paneNumber = self.control.currentPanel()
        pad = " " * 30
        panelCount = str(self.control.currentPage().panelCount())
        self.control.panelLabel.set_text(pad + "PANEL " + str(paneNumber) + " / " + panelCount)

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

            # Stop the deletion of the ZERO_WIDTH_SPACE
            endOffset = self.endIter().get_offset()
            if self.selectionIterEnd.get_offset() == endOffset:
                self.selectionIterEnd.backward_char()

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

        if self.control.doMarkSetIndexUpdate:
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

    def addCharToWord(self, character, duringKeyPressEvent=False):

        self.word.append(character)

        if character == ' ':
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
        #self.tagIter.reset()

    def enterNotify(self, widget, event):
        pass

    def focusOut(self, widget, event):
        self.forceWordEvent()
        #self.tagIter.reset()

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

        self.scrolledWindow2 = Gtk.ScrolledWindow()
        self.scrolledWindow2.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        vbox.pack_start(self.scrolledWindow2, 1, 1, 0)

        self.createTextView()
        self.scrolledWindow2.add(self.textView)

        self.infoTextView.props.left_margin = 25
        self.infoTextView.props.right_margin = 100
        self.infoTextView.props.wrap_mode = Gtk.WrapMode.WORD
        self.infoTextView.props.pixels_below_lines = 10
        self.infoTextView.props.pixels_above_lines = 10
        self.infoTextView.props.left_margin = self.textView.descriptionLeftMargin
        self.infoTextView.props.right_margin = self.textView.descriptionRightMargin

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

        self.infoTextView.get_buffer().delete(self.infoTextView.get_buffer().get_start_iter(), self.infoTextView.get_buffer().get_end_iter())
        self.infoTextView.get_buffer().insert(self.infoTextView.get_buffer().get_start_iter(), st.info)

        # if not self.control.screenplayModeSwitch.activating:
        #     if self.control.currentStory().isScreenplay:
        #         self.control.screenplayModeSwitch.set_state(True)
        #     else:
        #         self.control.screenplayModeSwitch.set_state(False)
        #     self.control.screenplayModeSwitch.callHandlerCode = False
        #
        # self.textView.tagIter.updateMode(self.control)

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
        self.infoTextView.get_buffer().delete(self.infoTextView.get_buffer().get_start_iter(), self.infoTextView.get_buffer().get_end_iter())
        self.infoTextView.get_buffer().insert(self.infoTextView.get_buffer().get_start_iter(), currentScene.info)

        self.control.doMarkSetIndexUpdate = False
        # self.addZeroWidthSpace(lastTag)
        self.control.doMarkSetIndexUpdate = True
        return lastTag

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

        lastTag = self.applyTags()
        self.textView.updatePanel()
        self.infoTextView.get_buffer().delete(self.infoTextView.get_buffer().get_start_iter(), self.infoTextView.get_buffer().get_end_iter())
        self.infoTextView.get_buffer().insert(self.infoTextView.get_buffer().get_start_iter(), currentPage.info)

        self.control.doMarkSetIndexUpdate = False
        # self.addZeroWidthSpace(lastTag)
        self.control.doMarkSetIndexUpdate = True
        return lastTag

    def infoTextViewKeyPress(self, widget, event):

        if event.state & Gdk.ModifierType.CONTROL_MASK:

            if event.keyval == 45: # minus key
                if self.control.scriptView.infoViewFontSize > 4:
                    self.infoViewFontSize -= 1
                    self.infoTextView.modify_font(Pango.FontDescription("Courier Prime " + str(self.infoViewFontSize)))
                    self.infoTextView.props.left_margin = self.textView.descriptionLeftMargin
                    self.infoTextView.props.right_margin = self.textView.descriptionRightMargin

            elif event.keyval==61: # equal key
                self.infoViewFontSize += 1
                self.infoTextView.modify_font(Pango.FontDescription("Courier Prime " + str(self.infoViewFontSize)))
                self.infoTextView.props.left_margin = self.textView.descriptionLeftMargin
                self.infoTextView.props.right_margin = self.textView.descriptionRightMargin

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
        entry.set_markup("""<span font_family='monospace' font='9.0' foreground='#99bbff' >""" + text + """</span>""")

        self.textView.add_child_at_anchor(entry, anchor)

        self.textBuffer.insert(self.textView.insertIter(), '\n', len('\n'))

        startIter = self.textView.insertIter()
        startIter.backward_chars(2)
        endIter = self.textView.insertIter()
        endIter.forward_char()

        self.textView.buffer.apply_tag_by_name('heading', startIter, endIter)

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

    def applyTags(self):

        for i in range(len(self.lines)):
            line = self.lines[i]

            if line.__class__.__name__ == "Line":

                startIter = self.textView.buffer.get_iter_at_line(i)
                endIter = self.textView.buffer.get_iter_at_line(i)
                endIter.forward_to_line_end()
                endIter.forward_char()

                self.textView.buffer.remove_all_tags(startIter, endIter)

                startIter = self.textView.buffer.get_iter_at_line(i)
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

        return line.tag

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

        self.control.currentStory().updateCompletionNames()

        self.paned.set_position(self.control.currentStory().horizontalPanePosition)

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

    def removeScreenplayTags(self):
        st = self.control.currentStory()
        for sq in st.sequences:
            for sc in sq.scenes:
                for pg in sc.pages:
                    for ln in pg.lines:
                        if ln.tag == 'sceneHeading':
                            ln.tag = 'description'