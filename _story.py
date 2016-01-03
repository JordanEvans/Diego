import os, re, time

import json

import _event
import _dialog
import _rtf
import _script
import _archive

from _event import EventManager

DEFAULT_TIMES = ["DAY", "NIGHT", "DUSK", "DAWN"]
RESTRICTED_CHARACTER_NAMES = ["POV", "LATER", "MONTAGE", 'ZOOM:', 'XLS', 'WIPE TO:', 'V.O.', 'TIME CUT', 'TIGHT ON', 'SUPER:', 'STOCK SHOT:', 'SPLIT SCREEN SHOT:', 'SMASH CUT TO:', 'SAME', 'ROLL', 'REVERSE ANGLE', 'PUSH IN:', 'PRELAP', 'O.S.', 'O.C.', 'MOS', 'MATCH DISSOLVE TO:', 'MATCH CUT TO:', 'LAP DISSOLVE:', 'JUMP CUT TO:', 'INTO VIEW:', 'INTO FRAME:', 'INSERT', 'FREEZE FRAME:', 'FLASHBACK:', 'FLASH CUT:', 'FAVOR ON', 'FADE TO:', 'EXTREME LONG SHOT', 'EXTREME CLOSE UP', 'ESTABLISHING SHOT:', 'ECU', 'EXTREME CLOSE UP', 'DISSOLVE TO:', 'CUT TO:', 'CROSSFADE:', 'CRAWL', 'CONTINUOUS', 'CLOSER ANGLE', 'CLOSE ON', 'ANGLE ON', 'AERIAL SHOT', ]

class StoryIndex(object):

    def __init__(self, indexDict=None):
        self.story = 0
        self.sequence = 0
        self.scene = 0
        self.page = 0
        self.line = 0
        self.offset = 0

        # Not implemented yet.
        self.issue = 1
        self.chapter = 1
        self.part = 1

        if indexDict:

            if u'story' in indexDict.keys():
                self.story = indexDict['story']

            if u'sequence' in indexDict.keys():
                self.sequence = indexDict['sequence']

            if u'scene' in indexDict.keys():
                self.scene = indexDict['scene']

            if u'page' in indexDict.keys():
                self.page = indexDict['page']

            if u'line' in indexDict.keys():
                self.line = indexDict['line']

            if u'offset' in indexDict.keys():
                self.offset = indexDict['offset']

            # Note implemented.

            if 'issue' in indexDict.keys():
                self.issue = indexDict['issue']

            if 'chapter' in indexDict.keys():
                self.chapter = indexDict['chapter']

            if 'part' in indexDict.keys():
                self.part = indexDict['part']

    def data(self):
        return self.__dict__


class Line(object):
    def __init__(self, text='', tag='description'):
        self.text = text
        self.tag = tag
        self.findTags = [] # does not go in data.
        self.mispelled = []

    def data(self):
        data = {}
        data['text'] = self.text
        data['tag'] = self.tag
        return data

    def before(self, control):
        index = control.scriptView.lines.index(self)
        if index == 0:
            return self
        else:
            return  control.scriptView.lines[index - 1]

    def after(self, control):
        index = control.scriptView.lines.index(self)
        if index == len(control.scriptView.lines) -1:
            return self
        else:
            return  control.scriptView.lines[index + 1]

    def updateMispelled(self, control):
        control.scriptView.textView.forceWordEvent()
        self.mispelled = []
        words = re.findall(r"[\w']+|[ .,!?;\-=:'\"@#$^&*(){}]", self.text)
        self.mispelled = []
        offset = 0
        for w in words:
            w = unicode(w)
            if control.wordMispelled(w):
                mw = MispelledWord(w, offset)
                self.mispelled.append(mw)
            offset += len(w)

    def applyMispelledTags(self, control, cursorWordOnly=False):

        if not cursorWordOnly:
            for word in self.mispelled:

                lineIndex = control.scriptView.lines.index(self)

                startIter = control.scriptView.textView.buffer.get_iter_at_line(lineIndex)
                startIter.forward_chars(word.offset)
                endIter = control.scriptView.textView.buffer.get_iter_at_line(lineIndex)
                endIter.forward_chars(word.offset + len(word.word))

                control.scriptView.textView.buffer.remove_all_tags(startIter, endIter)
                control.scriptView.textView.buffer.apply_tag_by_name(self.tag + "Mispelled", startIter, endIter)
        else:
            lineOffset = control.scriptView.textView.insertIter().get_line_offset()
            cursorWord = None
            for word in self.mispelled:
                if word.offset + len(word.word) + 1 == lineOffset:
                    cursorWord = word
                    break

            if cursorWord:
                word = cursorWord
                lineIndex = control.scriptView.lines.index(self)

                startIter = control.scriptView.textView.buffer.get_iter_at_line(lineIndex)
                startIter.forward_chars(word.offset)
                endIter = control.scriptView.textView.buffer.get_iter_at_line(lineIndex)
                endIter.forward_chars(word.offset + len(word.word))

                control.scriptView.textView.buffer.remove_all_tags(startIter, endIter)
                control.scriptView.textView.buffer.apply_tag_by_name(self.tag + "Mispelled", startIter, endIter)

    def addUppercasNamesToStoryNames(self, control):
        names = []

        if self.tag == 'character':
            if self.text not in names:
                names.append(self.text)
        else:
            if self.tag == 'description':

                if not self.text.isupper(): # the whole line may not be upper

                    upper = ""

                    words = re.findall(r"[\w']+|[ .,!?;\-=:'\"@#$^&*(){}]", self.text)

                    for w in words:

                        # Current Word is upper.
                        if w.isupper():

                            # When upper is started already, add the word.
                            if len(upper):
                                if w != " ":
                                    upper += w

                            # This start the upper.
                            else:
                                upper = w

                        else:
                            # Upper is started, and will try to add another upper, add space if a space found.
                            if len(upper) and w == ' ':
                                upper += " "

                            # If upper was started and upper not in names.
                            else:
                                n = upper.rstrip()
                                if len(n):
                                    if n not in names:
                                        names.append(n)
                                upper = ""

                    if len(upper) and upper not in names:
                        names.append(upper.rstrip())

        for n in names:
            control.currentStory().addName(n)


class Sequence(object):

    def __init__(self, control, story, title='Sequence', synopsis='', notes='', scenes=[], info=''):
        self.title = title
        self.synopsis = synopsis
        self.notes = notes
        self.scenes = []
        self.info = info

        if len(scenes) == 0:
            self.scenes.append(Scene(control))
        else:
            for scene in scenes:
                pages = scene['pages']

                id = None
                if 'id' in scene.keys():
                    id = scene['id']

                s = Scene(control, pages=pages, info=scene['info'], id=id)
                s.title = scene['title']
                self.scenes.append(s)

                s.undoIndex = scene['undoIndex']
                if s.undoIndex < 0:
                    s.undoIndex = 0

                s.eventIndex = scene['eventIndex']
                s.createArchiveManager(control)
                s.archiveManager.pathIndex = scene['pathIndex']
                s.archiveManager.paths = scene['archivePaths']
                s.timeStamp = scene['timeStamp']

                try:
                    s.archiveManager.load()
                except:
                    print "archive manager could not load"
                    try:
                        s.archiveManager.clear()
                    except:
                        print "archive manager could not clear"

                try:
                    timeStampPath = story.historyDir() + "/timestamp-" + str(id) #scene['timeStampPath']
                    with open(timeStampPath, 'r') as fp:
                        timeStamp = json.load(fp)
                except:
                    s.archiveManager.clear()
                    print "timestamp could not load"

                try:
                    if timeStamp['timeStamp'] != scene['timeStamp']:
                        s.archiveManager.clear()

                except:
                    s.archiveManager.clear()
                    print "timestamp could not be verified"

    def data(self, currentStory):
        scenes = []
        for scene in self.scenes:
            scenes.append(scene.data())
        data = {}
        data["title"] = self.title
        data["synopsis"] = self.synopsis
        data["notes"] = self.notes
        data["scenes"] = scenes
        data['info'] = self.info
        return data

    def findAndReplace(self, find, replace, control):
        for scene in self.scenes:
            scene.findAndReplace(find, replace, control)


class Scene(object):

    def __init__(self, control, title='Scene', synopsis='', notes='', pages=[], info='', events={}, id=None):

        self.id = id

        self.title = title
        self.synopsis=synopsis
        self.notes=notes
        self.pages = []
        self.info = info

        self.eventIndex = -1
        self.archiveManager = None
        self.hasUndone = False

        self.undoIndex = 0
        self.eventCount = 0
        self.saveIndex = 0

        self.timeStamp = None

        if len(pages) == 0:
            self.pages = [Page()]
        else:
            for page in pages:
                self.pages.append(Page(lines=page['lines'], info=page['info']))

    def currentEvent(self):
        if self.eventIndex == -1:
            return None
        elif self.eventIndex == len(self.archiveManager.events):
            return None
        else:
            return self.archiveManager.events[self.eventIndex]

    def nextEvent(self):
        ei = self.eventIndex + 1

        if ei < 0:
            return None
        elif ei == len(self.archiveManager.events):
            return None
        else:
            return self.archiveManager.events[ei]

    def canForward(self):
        if self.eventIndex + 1 < len(self.archiveManager.events):
            return True
        return False

    def canBackward(self):
        if self.eventIndex > 0:
            return True
        return False

    def canUndo(self):
        if self.eventIndex >= 0:
            return True
        return False

    def canRedo(self):
        if self.eventIndex + 1 < len(self.archiveManager.events):
            return True
        return False

    def redo(self, control):

        if self.canRedo():
            nextEvent = self.nextEvent()

            nextEvent.redo(control)
            self.undoIndex -= 1
            self.saveIndex += 1

            if self.canForward():
                self.eventIndex += 1

            elif self.archiveManager.canForward():
                self.archiveManager.forward(control)

            else:
                self.eventIndex += 1

        elif self.archiveManager.canForward():
            self.archiveManager.forward()
            self.currentEvent().redo(control)
            self.undoIndex -= 1
            self.saveIndex += 1

    def undo(self, control):

        if self.canUndo():

            ce = self.currentEvent()
            if ce is None:
                return

            if not self.archiveManager.currentPathExists():
                if self.archiveManager.pathIndex == -1:
                    self.archiveManager.pathIndex += 1
                self.archiveManager.appendExistingPath()
                self.archiveManager.save()

            elif self.eventIndex == 0:
                self.archiveManager.save()

            ce.undo(control)
            self.hasUndone = True
            self.undoIndex += 1
            self.saveIndex -= 1

            if self.canBackward():
                self.eventIndex -= 1

            elif self.archiveManager.canBackward():
                self.archiveManager.backward()

            else:
                self.eventIndex -= 1

        elif self.archiveManager.canBackward():
            self.archiveManager.backward()
            self.undo(control)
            self.hasUndone = True
            self.undoIndex += 1
            self.saveIndex -= 1

    def createArchiveManager(self, control):
        self.archiveManager = _archive.ArchiveManager(control, self)

    def createId(self, story):
        if self.id is None:
            story.scenesCreated += 1
            self.id = story.scenesCreated

    def archivePath(self, currentStory):
        path = currentStory.historyDir() + "/" + str(self.id) + "-" + str(self.archiveFileNumber)
        return path

    def archivePaths(self, control):
        historyDir = control.currentStory().historyDir()
        return os.listdir(historyDir)

    def newArchivePath(self, control):
        currentStory = control.currentStory()
        count = len(self.archivePaths(control))
        return currentStory.historyDir() + "/" + str(self.id) + "-" + str(count)

    def nextArchivePath(self, control, number):
        currentStory = control.currentStory()
        return currentStory.historyDir() + "/" + str(self.id) + "-" + str(number)

    def previousArchivePath(self, control, number):
        currentStory = control.currentStory()
        return currentStory.historyDir() + "/" + str(self.id) + "-" + str(number)

    def clearHistory(self, control):
        self.eventIndex = -1

        self.archiveManager.reset()

    def data(self):

        pages = []
        for page in self.pages:
            pages.append(page.data())
        data = {}
        data["title"] = self.title
        data["synopsis"] = self.synopsis
        data["notes"] = self.notes
        data["pages"] = pages
        data['info'] = self.info
        data['id'] = self.id
        data['eventIndex'] = self.eventIndex
        data['pathIndex'] = self.archiveManager.pathIndex
        data['archivePaths'] = self.archiveManager.paths
        data['undoIndex'] = self.undoIndex
        data['timeStamp'] = self.timeStamp

        return data

    def createTimeStamp(self):
        self.timeStamp = time.time()

    def findAndReplace(self, find, replace, control):
        for page in self.pages:
            page.findAndReplace(find, replace)
        self.clearHistory(control)

    def names(self, control):
        names = []
        storyNames = list(control.currentStory().names)
        for p in self.pages:
            for l in p.lines:

                if l.tag == 'character':
                    if l.text not in names:
                        names.append(l.text)

                elif l.tag != 'sceneHeading':
                    for sn in storyNames:
                        words = re.findall(r"[\w']+|[ .,!?;\-=:'\"@#$^&*(){}]", l.text)
                        if sn in words:
                            names.append(sn)

        for n in names:
            if n in storyNames:
                storyNames.remove(n)

        return names + storyNames

    def addUppercasNamesToStoryNames(self, control):
        for page in self.pages:
            page.addUppercasNamesToStoryNames(control)

    def correspond(self, control, verbose=False):
        for page in self.pages:
            page.correspond(control, verbose=verbose)

    def updateLocations(self, sceneHeading, story):
        for page in self.pages:
            if page.lines[0].tag == 'sceneHeading':
                loc = sceneHeading.location(page.lines[0].text)
                story.addLocation(loc)
        story.locations.sort()

    def updateTimes(self, sceneHeading, story):
        for page in self.pages:
            if page.lines[0].tag == 'sceneHeading':
                tm = sceneHeading.time(page.lines[0].text)
                story.addTime(tm)
        story.locations.sort()

    def printTags(self):
        for page in self.pages:
            page.printTags()


class Page(object):

    def __init__(self, lines=[], info=''):
        self.title = ''
        self.lines = []
        self.info = info
        if len(lines) == 0:
            self.lines.append(Line())
        else:
            for line in lines:
                self.lines.append(Line(line['text'], line['tag']))

    def data(self):
        data = {}
        lines = []
        for line in self.lines:
            lines.append(line.data())
        data['lines'] = lines
        data['info'] = self.info
        return data

    def findAndReplace(self, find, replace):
        find = unicode(find)
        replace = unicode(replace)
        for line in self.lines:
            words = re.findall(r"[\w']+|[ .,!?;-]", line.text)
            newLine = []
            for word in words:
                if word == find:
                    newLine.append(replace)
                else:
                    newLine.append(word)

            line.text = "".join(newLine)

    def panelCount(self):
        count = 0
        for line in self.lines:
            if line.tag == "description":
                count += 1
        return count

    def correspond(self, control, verbose=False):
        index = 0
        lastLine = control.scriptView.lines[-1]

        printLines = []
        col1 = 0
        col2 = 0
        for line in self.lines:
            modelInfo = [line.text, line.tag]
            bufferInfo = None
            check = []
            inBuffer = line in control.scriptView.lines

            if inBuffer:
                index = control.scriptView.lines.index(line)
                lineText = control.scriptView.textView.lineText(index)
                if line == lastLine:
                    lineText = lineText.rstrip(_script.ZERO_WIDTH_SPACE)
                lineTags = control.scriptView.textView.lineTags(index)
                bufferInfo = [lineText, lineTags]
                checkText = modelInfo[0] == lineText
                if len(lineTags) == 1:
                    checkTags = modelInfo[1] == lineTags[0]
                else:
                    checkTags = False
                check = [checkText, checkTags]

            else:

                print "Model Line Not Found In Buffer"

            if bufferInfo:

                if verbose:
                    x = index, check, modelInfo, bufferInfo
                    if len(str(modelInfo)) > col1:
                        col1 = len(str(modelInfo))
                    if len(str(bufferInfo)) > col2:
                        col2 = len(str(bufferInfo))
                    printLines.append(x)

                if (not check[0] or not check[1]) and not verbose:
                    t1 = ""
                    t2 = ""
                    if not check[0]:
                        t1 = u"Text on line " + unicode(str(index), 'utf-8') + u" in model does not match buffer text: " + u"\nbuffer: " + unicode(str(list(bufferInfo[0])), 'utf-8') + u"\nmodel: " + unicode(str(list(modelInfo[0])), 'utf-8')
                    if not check[0]:
                        t2 = u"Tags in model does not match buffer tags: " + u"\nbuffer: " + unicode(str(bufferInfo[1]), 'utf-8') + u"\nmodel: " + unicode(str(modelInfo[1]), 'utf-8')

                    verboseText = u"\n\n" + t1 + u'\n' + t2
                    #raise Exception(verboseText)

                    print verboseText

            index += 1

        if verbose:
            for l in printLines:
                space = (col1 - len(str(l[2])) + 1) * " "
                col1Text = str(l[2]) + space
                col2Text = str(l[3])
                s = str(l[0]) + " " + str(l[1]) + " " + col1Text + col2Text
                print s

    def addUppercasNamesToStoryNames(self, control):
        for line in self.lines:
            line.addUppercasNamesToStoryNames(control)

    def printTags(self):
        count = 0
        for line in self.lines:
            print count, line.tag


class Story(object):

    def __init__(self, control, path=None, info=''):

        self.id = None
        self.scenesCreated = 0

        self.control = control
        self.path = path
        self.title = self.uniqueTitle()
        if path:
            try:
                self.title = os.path.split(path)[-1]
            except:
                self.title = ""
        self.synopsis=''
        self.notes=''
        self.sequences = []
        self.info = info

        # self.index = [0, 0, 0, 0, 0] # [sequence, scene, page, line, offset]
        self.index = StoryIndex()

        self.saved = True

        self.names = []
        self.intExt = ['INT', 'EXT']
        self.locations = []
        self.times = DEFAULT_TIMES
        self.times.sort()
        self.isScreenplay = False

        self.firstAppearances = []

    def createId(self):
        if self.id == None:
            self.id = self.control.uniqueStoryId()

    def historyDir(self):
        return self.control.historyDir + "/" + self.title + "-" + self.id

    def makeHistoryDir(self):

        if not os.path.exists(self.historyDir()):
            os.mkdir(self.historyDir())

    def removeHistoryDir(self):
        if os.path.exists(self.historyDir()):
            os.removedirs(self.historyDir())
            os.remove(self.historyDir())

    def newSequence(self, prepend=False):
        sequence = Sequence(self.control)

        self.sequences.insert(0, sequence)

        self.control.currentStory().index.sequence = 0
        self.control.currentStory().index.scene = 0
        self.control.currentStory().index.page = 0
        self.control.currentStory().index.line = 0

    def newScene(self, prepend=False):
        scene = Scene(self.control)
        scene.createId(self)
        scene.archiveManager = _archive.ArchiveManager(self.control, scene)

        if prepend:
            position = self.control.currentStory().index.scene

        else:
            position = self.control.currentStory().index.scene +1

        self.control.currentSequence().scenes.insert(position, scene)

        self.control.currentStory().index.scene = position
        self.control.currentStory().index.page = 0
        self.control.currentStory().index.line = 0

        self.saved = False

    def newPage(self, prepend=False):
        page = Page()
        cs = self.control.currentScene()

        if prepend:
            pageIndex = self.control.currentStory().index.page

        else:
            pageIndex = self.control.currentStory().index.page +1

        self.control.currentStory().index.page = pageIndex

        self.control.currentStory().index.line = 0
        self.control.currentStory().index.offset = 0
        cs.pages.insert(pageIndex, page)

        sceneIndex = self.control.currentSequence().scenes.index(cs)
        if self.control.historyEnabled:
            self.control.eventManager.addEvent(_event.Page(sceneIndex, pageIndex))

    def deletePage(self, index):
        pass

    def load(self):
        if self.path != None and os.path.exists(self.path):
            self._load()
            return

        print 'data load: path unset/does not exist: ' + str(self.path)
        self.path = None
        self.default()

    def _load(self):

        # wrap this in try when app is done
        try:
            with open(self.path, 'r') as fp:
                data = json.load(fp)
        except:
            print "data _load: unable to load json file"
            self.control.reset()
            self.default()
            return

        self.control.historyEnabled = False

        self.id = data['id']

        self.makeHistoryDir()

        if 'scenesCreated' in data.keys():
            self.scenesCreated = data['scenesCreated']

        self.title=data['title']
        self.synopsis=data['synopsis']
        self.notes=data['notes']
        self.info = data['info']

        self.index = StoryIndex(data['index'])

        self.sequences = []
        for sequence in data['sequences']:
            title=sequence['title']
            synopsis=sequence['synopsis']
            notes=sequence['notes']
            self.sequences.append(Sequence(self.control, self, title, synopsis, notes, scenes=sequence['scenes'], info=sequence['info']))

        self.control.historyEnabled = True

        self.updateStoryNames()

        if 'isScreenplay' in data.keys():
            self.isScreenplay = data['isScreenplay']
            self.updateLocations()
            self.updateTimes()

        self.makeHistoryDir()
        self.updateEventCount()

        self.crashDetect()

        # self.hanselGretalImport()

    def loadId(self):

        try:
            with open(self.path, 'r') as fp:
                data = json.load(fp)
        except:
            print "data _load: unable to load json file"
            return

        if 'id' in data.keys():
            self.id = data['id']
        else:
            self.createId()

    def writeTimeStampFiles(self):


        historyDir = self.historyDir()
        if not os.path.exists(historyDir):
            self.makeHistoryDir()
        for scene in self.sequences[0].scenes:
            timeStampPath = historyDir + "/" + "timestamp-" + str(scene.id)

            timestamp = scene.timeStamp

            timeStampData = {}
            timeStampData['timeStamp'] = timestamp

            with open(timeStampPath, 'w') as fp:
                json.dump(timeStampData, fp)
            fp.close()

    def crashDetect(self):
        if os.path.exists(self.historyDir() + "/start"):
            print "story did not close properly"
            for scene in self.sequences[0].scenes:
                scene.archiveManager.clear()
        f = open(self.historyDir() + "/start", "w")
        f.close()

    def close(self):
        if os.path.exists(self.historyDir() + "/start"):
            os.remove(self.historyDir() + "/start")

    def updateEventCount(self):
        for sc in self.sequences[0].scenes:
            if len(sc.archiveManager.events):
                sc.eventCount = 0
                # sc.undoIndex = 0

    def uniqueTitle(self):
        count = 1

        title = "Untitled"

        split = title.split("-")
        if split[0] == "Untitled":
            title = "Untitled"

        if not os.path.exists(self.control.saveDir + title):
            return title

        while os.path.exists(self.control.saveDir + title + "-" + str(count)):
            count += 1

        return title + "-" + str(count)

    def uniquePath(self):
        count = 1

        try:
            title = self.control.currentStory().title
        except:
            title = self.uniqueTitle()

        split = title.split("-")
        if split[0] == "Untitled":
            title = "Untitled"

        if not os.path.exists(self.control.saveDir + title):
            return self.control.saveDir + title

        while os.path.exists(self.control.saveDir + title + "-" + str(count)):
            count += 1
        return self.control.saveDir + title + "-" + str(count)

    def save(self, pdf=True, rtf=True):

        if self.path == None:
            self.path = self.uniquePath()

        try:
            os.path.split(self.path)

        except:
            _dialog.saveFile(self.control)
            return

        else:
            # self.control.saveDir = os.path.split(self.path)[0] + '/'
            self._save(self.path, pdf=pdf, rtf=rtf)
            return

        # _dialog.saveFile(self.control)

    def _save(self, path, pdf=True, rtf=True):
        self.control.saveDir = os.path.split(path)[0] + '/'
        self.path = path
        self.control.scriptView.textView.forceWordEvent()
        self.saveArchiveManagerArchives()
        self.createSceneTimeStamps()
        data = self.data(self)

        with open(path, 'w') as fp:
            json.dump(data, fp)

        if self.control.state.backupDir and os.path.exists(self.control.state.backupDir) and os.path.isdir(self.control.state.backupDir):

            count = 0
            backupPath = self.control.state.backupDir + "/" + str(count) + "-" + self.title
            while os.path.exists(backupPath):
                backupPath = self.control.state.backupDir + "/" + str(count) + "-" + self.title
                count += 1
            with open(backupPath, 'w') as fp:
                json.dump(data, fp)

        self.control.app.updateWindowTitle()

        if path == None:
            title = self.title
        else:
            title = os.path.split(self.path)[-1]

        self.title = title
        self.control.storyItemBox.updateStoryLabelAtIndex(self.control.index)
        self.saved = True

        if rtf:
            rtff = _rtf.RTF(self.control)
            rtff.exportScript(path + ".rtf", self.isScreenplay)
            rtfPath = path + ".rtf"

        if pdf:
            cwd = os.getcwd()
            os.chdir(self.control.saveDir)
            os.system("soffice --headless --convert-to pdf " + "'" + rtfPath + "'")
            os.chdir(cwd)

        self.updateStoryNames()
        self.updateLocations()
        self.updateTimes()

        self.updateEventCount()

        self.updateSceneSessionPoints()

        self.saveEvent = self.control.currentScene().currentEvent()

        self.writeTimeStampFiles()

    def createSceneTimeStamps(self):
        for scene in self.sequences[0].scenes:
            scene.createTimeStamp()

    def saveArchiveManagerArchives(self):
        for scene in self.sequences[0].scenes:
            scene.archiveManager.save()

    def updateSceneSessionPoints(self):
        for sc in self.currentSequence().scenes:
            sc.sessionEventIndex = sc.eventIndex
            sc.saveIndex = 0
            sc.undoIndex = 0

    def default(self):
        self.createId()
        self.control.historyEnabled = True
        self.sequences = [Sequence(self.control, self)]
        self.sequences[0].scenes[0].createArchiveManager(self.control)
        for sc in self.sequences[0].scenes:
            sc.createId(self)
        self.defaultSave()

    def defaultSave(self):
        if self.path == None:
            self.path = self.uniquePath()

        # self.control.saveDir = os.path.split(self.path)[0] + '/'
        self.control.scriptView.textView.forceWordEvent()
        data = self.data(self)
        with open(self.path, 'w') as fp:
            json.dump(data, fp)

    def hanselGretalImport(self):
        import json
        path = 'HanselAndGretel'
        with open(path, 'r') as fp:
                data = json.load(fp)

        doc = data['document']

        seq = self.sequences[0]

        scenes = doc['scenes']

        for i in range(len(scenes) - 1):
            newScene = Scene(self.control)
            newScene.createId(self)
            newScene.createArchiveManager(self.control)
            seq.scenes.append(newScene)

        for i in range(len(scenes)):
            s = scenes[i]
            seq.scenes[i].title = scenes[i]['title']
            page = seq.scenes[i].pages[0]
            text = s['infos'][0]['text']

            cs = seq.scenes[i]
            cs.info = text

            for beat in scenes[i]['beats']:
                if len(beat['text']):
                 page.lines.append(Line(beat['text'], beat['tag']))

            if len(page.lines) > 1:
                page.lines.pop(0)

    def reset(self):
        self.path = None
        self.sequences = []
        self.eventManager = None

    def data(self, currentStory):
        data={}
        sequences=[]
        for sequence in self.sequences:
            sequences.append(sequence.data(currentStory))
        data['sequences']=sequences
        data['index']=self.index.data()
        data["title"] = os.path.split(self.path)[-1]
        data["synopsis"] = self.synopsis
        data["notes"] = self.notes
        data['info'] = self.info
        # data['scriptViewPanedPosition'] = self.control.scriptView.paned.get_position()
        data['isScreenplay'] = self.isScreenplay
        data['scenesCreated'] = self.scenesCreated
        data['id'] = self.id
        return data

    def currentIssue(self):
        pass

    def currentSequence(self):
        return self.sequences[self.index.sequence]

    def currentScene(self):
        currentSequence = self.currentSequence()
        return currentSequence.scenes[self.index.scene]

    def currentPage(self):
        currentScene = self.currentScene()
        return currentScene.pages[self.index.page]

    def currentLine(self):
        currentPage = self.currentPage()
        return currentPage.lines[self.index.line]

    def findAndReplace(self, find, replace):
        for seq in self.sequences:
            seq.findAndReplace(find, replace, self.control)

    def addName(self, name):
        name = name.upper()
        if name in RESTRICTED_CHARACTER_NAMES:
            return

        if len(name) and name not in self.names:
            self.names.append(name)
            self.names.sort()

    def addLocation(self, location):
        if location == '':
            return
        if location not in self.locations:
            self.locations.append(location)
        self.locations.sort()

    def addTime(self, time):
        if time == '':
            return
        if time not in self.times:
            self.times.append(time)
        self.times.sort()

    def updateStoryNames(self):
        self.names = []
        for sequence in self.sequences:
            for scene in sequence.scenes:
                for page in scene.pages:
                    for line in page.lines:
                        if line.tag == 'character':
                            if len(line.text.lstrip().rstrip()) and line.text not in self.names:
                                self.names.append(line.text)

        self.names.sort()

        for sequence in self.sequences:
            for scene in sequence.scenes:
                scene.addUppercasNamesToStoryNames(self.control)

        self.upperCaseFirstOccurenceOfCharactersInDescription()

    def upperCaseFirstOccurenceOfCharactersInDescription(self):
        applied = []
        storyNames = list(self.names)
        for sequence in self.sequences:
            for scene in sequence.scenes:
                for page in scene.pages:
                    for line in page.lines:
                        if line.tag == 'description':
                            words = re.findall(r"[\w']+|[ .,!?;\-=:'\"@#$^&*(){}]", line.text)
                            upwords = [w.upper() for w in words]
                            for name in storyNames:
                                if name in upwords and name not in applied:
                                    for i in range(len(upwords)):
                                        if name == upwords[i].upper():
                                            words[i] = upwords[i].upper()
                                            line.text = "".join(words)
                                            applied.append(words[i])
                                            break

    def updateLocations(self):
        self.locations = []
        sh = _script.SceneHeading()
        for sequence in self.sequences:
            for scene in sequence.scenes:
                scene.updateLocations(sh, self)
        self.locations.sort()

    def updateTimes(self):
        self.times = DEFAULT_TIMES
        sh = _script.SceneHeading()
        for sequence in self.sequences:
            for scene in sequence.scenes:
                scene.updateTimes(sh, self)

        self.times.sort()

    def updateFirstAppearancesAtLine(self, line):
        splitText = re.findall(r"[\w']+|[ .,!?;-]", line.text)
        for name in self.names:
            if name in splitText and name not in self.firstAppearances:
                self.firstAppearances.append(name)
                line.text = "".join(splitText)

    def updateFirstAppearances(self):
        for sequence in self.sequences:
            for scene in sequence.scenes:
                for page in scene.pages:
                    for line in page.lines:
                        self.updateFirstAppearancesAtLine(line)

    def updateMispelled(self):
        if self.control.trie:
            for sequence in self.sequences:
                for scene in sequence.scenes:
                    for page in scene.pages:
                        for line in page.lines:
                            line.updateMispelled(self.control)
                            # if len(line.mispelled):
                            #     print [o.word for o in line.mispelled]

    def correspond(self, control, verbose=False):
        if verbose:
            print
            print "Buffer Line Number - [strings match, tags match] - Model Contents - Buffer Contents"
        index = 0
        for sq in self.sequences:
            for sc in sq.scenes:
                if verbose:
                    print "SCENE", index, sc.title
                sc.correspond(control, verbose=verbose)
                index += 1

    def printTags(self):
        for scene in self.sequences[0].scenes:
            scene.printTags()


class MispelledWord(object):
    def __init__(self, word, offset):
        self.word = word
        self.offset = offset