import os, re

import json

import _event
import _dialog
import _rtf
import _script

from _event import EventManager

DEFAULT_TIMES = ["DAY", "NIGHT", "DUSK", "DAWN"]

HISTORY_RECORD_LIMIT = 3

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

                startIter = control.scriptView.textView.get_buffer().get_iter_at_line(lineIndex)
                startIter.forward_chars(word.offset)
                endIter = control.scriptView.textView.get_buffer().get_iter_at_line(lineIndex)
                endIter.forward_chars(word.offset + len(word.word))

                control.scriptView.textView.get_buffer().remove_all_tags(startIter, endIter)
                control.scriptView.textView.get_buffer().apply_tag_by_name(self.tag + "Mispelled", startIter, endIter)
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

                startIter = control.scriptView.textView.get_buffer().get_iter_at_line(lineIndex)
                startIter.forward_chars(word.offset)
                endIter = control.scriptView.textView.get_buffer().get_iter_at_line(lineIndex)
                endIter.forward_chars(word.offset + len(word.word))

                control.scriptView.textView.get_buffer().remove_all_tags(startIter, endIter)
                control.scriptView.textView.get_buffer().apply_tag_by_name(self.tag + "Mispelled", startIter, endIter)


class Sequence(object):

    def __init__(self, title='Sequence', synopsis='', notes='', scenes=[], info=''):
        self.title = title
        self.synopsis = synopsis
        self.notes = notes
        self.scenes = []
        self.info = info

        if len(scenes) == 0:
            self.scenes.append(Scene())
        else:
            for scene in scenes:
                pages = scene['pages']
                if 'events' in scene.keys():
                    s = Scene(pages=pages, info=scene['info'], events=scene['events'])
                else:
                    s = Scene(pages=pages, info=scene['info'])
                s.title = scene['title']
                self.scenes.append(s)

    def data(self, currentStory):
        scenes = []
        for scene in self.scenes:
            scenes.append(scene.data(currentStory))
        data = {}
        data["title"] = self.title
        data["synopsis"] = self.synopsis
        data["notes"] = self.notes
        data["scenes"] = scenes
        data['info'] = self.info
        return data

    def findAndReplace(self, find, replace):
        for scene in self.scenes:
            scene.findAndReplace(find, replace)


class Scene(object):

    def __init__(self, title='Scene', synopsis='', notes='', pages=[], info='', events=[]):
        self.title = title
        self.synopsis=synopsis
        self.notes=notes
        self.pages = []
        self.info = info

        self.events = events
        self.eventIndex = -1

        if len(pages) == 0:
            self.pages = [Page()]
        else:
            for page in pages:
                self.pages.append(Page(lines=page['lines'], info=page['info']))

    def data(self, currentStory):
        pages = []
        for page in self.pages:
            pages.append(page.data())
        data = {}
        data["title"] = self.title
        data["synopsis"] = self.synopsis
        data["notes"] = self.notes
        data["pages"] = pages
        data['info'] = self.info
        data['eventIndex'] = self.eventIndex
        events = []

        for record in self.events:
            events.append(record.data(currentStory))

        if self.eventIndex >= HISTORY_RECORD_LIMIT:
            data['eventIndex'] = self.eventIndex - (len(self.events) - HISTORY_RECORD_LIMIT)

        while len(events) > HISTORY_RECORD_LIMIT:
            events.pop(0)

        events.pop(0) # remove start event

        data['events'] = events

        return data

    def findAndReplace(self, find, replace):
        for page in self.pages:
            page.findAndReplace(find, replace)

    def names(self, control):
        names = []
        for p in self.pages:
            for l in p.lines:
                if l.tag == 'character' and l.text not in names:
                    names.append(l.text)

        snames = control.currentStory().names
        for n in names:
            if n in snames:
                snames.remove(n)

        return names + snames

    def correspond(self, control, verbose=False):
        for page in self.pages:
            page.correspond(control, verbose=verbose)

    def undo(self, control):
        if self.eventIndex > 0:
            self.events[self.eventIndex].undo(control)
            self.eventIndex -=1

    def redo(self, control):
        if self.eventIndex < len(self.events) -1:
            self.eventIndex +=1
            self.events[self.eventIndex].redo(control)


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
            splitText = re.findall(r"[\w']+|[ .,!?;-]", line.text)
            newLine = []
            for split in splitText:
                if split == find:
                    newLine.append(replace)
                else:
                    newLine.append(split)

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


class Story(object):

    def __init__(self, control, path=None, info=''):
        self.control = control
        self.path = path
        self.title = "Untitled"
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
        self.horizontalPanePosition = 150

        self.names = []
        self.intExt = ['INT', 'EXT']
        self.locations = []
        self.times = DEFAULT_TIMES
        self.times.sort()
        self.isScreenplay = False

        self.firstAppearances = []

    def newSequence(self, prepend=False):
        sequence = Sequence()

        if prepend:
            position = self.control.currentStory().index.sequence

        else:
            position = self.control.currentStory().index.sequence +1

        self.sequences.insert(position, sequence)

        self.control.currentStory().index.sequence = position
        self.control.currentStory().index.scene = 0
        self.control.currentStory().index.page = 0
        self.control.currentStory().index.line = 0

        if self.control.historyEnabled:
            self.control.eventManager.addEvent(_event.NewSequenceEvent(sequence, self.control.currentStory().index))
        self.saved = False

    def newScene(self, prepend=False):
        scene = Scene()

        if prepend:
            position = self.control.currentStory().index.scene

        else:
            position = self.control.currentStory().index.scene +1

        self.control.currentSequence().scenes.insert(position, scene)

        self.control.currentStory().index.scene = position
        self.control.currentStory().index.page = 0
        self.control.currentStory().index.line = 0

        if self.control.historyEnabled:
            self.control.eventManager.addEvent(_event.Event())
        self.saved = False

    def newPage(self, prepend=False):
        page = Page()

        if prepend:
            position = self.control.currentStory().index.page

        else:
            position = self.control.currentStory().index.page +1

        self.control.currentStory().index.page = position

        self.control.currentStory().index.line = 0
        self.control.currentScene().pages.insert(position, page)

        if self.control.historyEnabled:
            self.control.eventManager.addEvent(_event.Event())
        self.saved = False

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

        self.title=data['title']
        self.synopsis=data['synopsis']
        self.notes=data['notes']
        self.info = data['info']

        self.index = StoryIndex(data['index'])

        for sequence in data['sequences']:
            title=sequence['title']
            synopsis=sequence['synopsis']
            notes=sequence['notes']
            self.sequences.append(Sequence(title, synopsis, notes, scenes=sequence['scenes'], info=sequence['info']))

        self.control.historyEnabled = True

        events = []
        for sq in self.sequences:
            for sc in sq.scenes:
                self.control.eventManager.initSceneHistory(sc, events)

        self.horizontalPanePosition = data['horizontalPanePosition']

        self.updateCompletionNames()

        if 'isScreenplay' in data.keys():
            self.isScreenplay = data['isScreenplay']
            self.updateLocations()
            self.updateTimes()

        self.loadSceneHistories(data['sequences'][0])

    def loadSceneHistories(self, sequence):

        for dataScene in sequence['scenes']:
            if 'events' in dataScene.keys():
                for event in dataScene['events']:

                    scene = event['scene']
                    page = event['page']
                    line = event['line']
                    offset = event['offset']
                    text = event['text']
                    tags = event['tags']

                    if event['name'] == 'Insertion':
                        evt = _event.Insertion(scene, page, line, offset, text, tags)
                    elif event['name'] == 'Deletion':
                        evt = _event.Deletion(scene, page, line, offset, text, tags)
                    elif event['name'] == "Backspace":
                        evt = _event.Backspace(scene, page, line, offset, text, tags)
                        evt.carryText = event['carryText']

                    self.sequences[0].scenes[event['scene']].events.append(evt)
                    self.sequences[0].scenes[event['scene']].eventIndex = dataScene['eventIndex']

    def uniquePath(self):
        count = 1

        if not os.path.exists(self.control.saveDir + self.control.currentStory().title):
            return self.control.saveDir + self.control.currentStory().title

        while os.path.exists(self.control.saveDir + self.control.currentStory().title + "-" + str(count)):
            count += 1
        return self.control.saveDir + self.control.currentStory().title + "-" + str(count)

    def save(self,):
        if self.path == None:
            self.path = self.uniquePath()
        #     _dialog.saveFile(self.control)
        # else:
        self._save(self.path)

    def _save(self, path):
        self.control.saveDir = os.path.split(path)[0] + '/'
        self.path = path
        self.control.scriptView.textView.forceWordEvent()
        data = self.data(self)
        with open(path, 'w') as fp:
            json.dump(data, fp)
        self.control.app.updateWindowTitle()

        if path == None:
            title = self.title
        else:
            title = os.path.split(self.path)[-1]

        self.title = title
        self.control.storyItemBox.updateStoryLabelAtIndex(self.control.index)
        self.saved = True

        rtf = _rtf.RTF(self.control)
        rtf.exportScript(path + ".rtf", self.isScreenplay)
        rtfPath = path + ".rtf"

        cwd = os.getcwd()
        os.chdir(self.control.saveDir)
        os.system("soffice --headless --convert-to pdf " + "'" + rtfPath + "'")
        os.chdir(cwd)

        self.updateCompletionNames()
        self.updateLocations()
        self.updateTimes()

    def default(self):
        self.control.historyEnabled = True
        self.sequences = [Sequence()]
        self.control.eventManager.initSceneHistory(self.sequences[0].scenes[0], events=[])

    def hanselGretalImport(self):
        import json
        path = 'HanselAndGretel'
        with open(path, 'r') as fp:
                data = json.load(fp)

        doc = data['document']

        seq = self.sequences[0]

        scenes = doc['scenes']

        for i in range(len(scenes) - 1):
            newScene = Scene()
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
        self.saved = True

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
        data['horizontalPanePosition'] = self.control.scriptView.paned.get_position()
        data['isScreenplay'] = self.isScreenplay
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
            seq.findAndReplace(find, replace)

    def addName(self, name):
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

    def updateCompletionNames(self):
        self.names = []
        for sequence in self.sequences:
            for scene in sequence.scenes:
                for page in scene.pages:
                    for line in page.lines:
                        if line.tag == 'character':
                            if len(line.text.lstrip().rstrip()) and line.text not in self.names:
                                self.names.append(line.text)

        self.names.sort()

    def updateLocations(self):
        self.locations = []
        sh = _script.SceneHeading()
        for sequence in self.sequences:
            for scene in sequence.scenes:
                for page in scene.pages:
                    for line in page.lines:
                        if line.tag == 'sceneHeading':
                            loc = sh.location(line.text)
                            self.addLocation(loc)

        self.locations.sort()

    def updateTimes(self):
        self.times = DEFAULT_TIMES
        sh = _script.SceneHeading()
        for sequence in self.sequences:
            for scene in sequence.scenes:
                for page in scene.pages:
                    for line in page.lines:
                        if line.tag == 'sceneHeading':
                            tim = sh.time(line.text)
                            self.addTime(tim)

        self.locations.sort()

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


class MispelledWord(object):
    def __init__(self, word, offset):
        self.word = word
        self.offset = offset