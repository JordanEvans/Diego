import os

import json

import _event
import _dialog
import _rtf

from _event import EventManager

class StoryIndex(object):

    def __init__(self, *args, **kwargs):
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

        if 'story' in kwargs.keys():
            self.story = kwargs['story']

        if 'sequence' in kwargs.keys():
            self.sequence = kwargs['sequence']

        if 'scene' in kwargs.keys():
            self.scene = kwargs['scene']

        if 'page' in kwargs.keys():
            self.page = kwargs['page']

        if 'line' in kwargs.keys():
            self.line = kwargs['line']

        if 'offset' in kwargs.keys():
            self.offset = kwargs['offset']

        # Note implemented.

        if 'issue' in kwargs.keys():
            self.issue = kwargs['issue']

        if 'chapter' in kwargs.keys():
            self.chapter = kwargs['chapter']

        if 'part' in kwargs.keys():
            self.part = kwargs['part']

    def data(self):
        return self.__dict__


class Line(object):
    def __init__(self, text='', tag='description'):
        self.text = text
        self.tag = tag

        self.findTags = [] # does not go in data.

    def data(self):
        data = {}
        data['text'] = self.text
        data['tag'] = self.tag
        return data


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
                s = Scene(pages=pages, info=scene['info'])
                s.title = scene['title']
                self.scenes.append(s)

    def data(self):
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

    def findAndReplace(self, find, replace):
        for scene in self.scenes:
            scene.findAndReplace(find, replace)

class Scene(object):

    def __init__(self, title='Scene', synopsis='', notes='', pages=[], info=''):
        self.title = title
        self.synopsis=synopsis
        self.notes=notes
        self.pages = []
        self.info = info

        if len(pages) == 0:
            self.pages = [Page()]
        else:
            for page in pages:
                self.pages.append(Page(lines=page['lines'], info=page['info']))

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

        return data

    def findAndReplace(self, find, replace):
        for page in self.pages:
            page.findAndReplace(find, replace)

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
            line.text = line.text.replace(find, replace)

    def panelCount(self):
        count = 0
        for line in self.lines:
            if line.tag == "description":
                count += 1
        return count

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
        self.eventManager = EventManager(self.control)
        # self.index = [0, 0, 0, 0, 0] # [sequence, scene, page, line, offset]
        self.index = StoryIndex()

        self.saved = True
        self.horizontalPanePosition = 150

        self.names = []

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
            self.control.currentStory().eventManager.addEvent(_event.NewSequenceEvent(sequence, self.control.currentStory().index))
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
            self.control.currentStory().eventManager.addEvent(_event.NewSceneEvent(scene, self.control.currentStory().index))
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
            self.control.currentStory().eventManager.addEvent(_event.NewPageEvent(page, self.control.currentStory().index))
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

        self.index = StoryIndex(None, data['index'])
        for sequence in data['sequences']:
            title=sequence['title']
            synopsis=sequence['synopsis']
            notes=sequence['notes']
            self.sequences.append(Sequence(title, synopsis, notes, scenes=sequence['scenes'], info=sequence['info']))

        self.control.historyEnabled = True

        self.horizontalPanePosition = data['horizontalPanePosition']

        self.updateCompletionNames()

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

    def save(self,):
        if self.path == None:
            _dialog.saveFile(self.control)
        else:
            self._save(self.path)

    def _save(self, path):
        self.control.saveDir = os.path.split(path)[0] + '/'
        self.path = path
        self.control.scriptView.textView.forceWordEvent()
        data = self.data()
        with open(path, 'w') as fp:
            json.dump(data, fp)
        self.control.app.updateWindowTitle()
        title = os.path.split(self.control.currentStory().path)[-1]
        self.control.currentStory().title = title
        self.control.storyItemBox.updateStoryLabelAtIndex(self.control.index)
        self.saved = True

        rtf = _rtf.RTF(self.control)
        rtf.exportScreenplay(path + ".rtf")
        rtfPath = path + ".rtf"

        cwd = os.getcwd()
        os.chdir(self.control.saveDir)
        os.system("soffice --headless --convert-to pdf " + "'" + rtfPath + "'")
        os.chdir(cwd)

        self.updateCompletionNames()
        # self.control.scriptView.textView.updateNameMenu()

    def default(self):
        self.control.historyEnabled = True
        self.sequences = [Sequence()]

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

    def data(self):
        data={}
        sequences=[]
        for sequence in self.sequences:
            sequences.append(sequence.data())
        data['sequences']=sequences
        data['index']=self.index.data()
        data["title"] = os.path.split(self.path)[-1]
        data["synopsis"] = self.synopsis
        data["notes"] = self.notes
        data['info'] = self.info
        data['horizontalPanePosition'] = self.control.scriptView.paned.get_position()
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

    def find(self, find):
        self.findLines = []
        for sq in self.sequences:
            for scene in sq.scenes:
                for page in scene.pages:
                    for line in page.lines:
                        if find in line.text:
                            self.findLines.append(line)
        return self.findLines

    def addFindTags(self, find):

        for sq in self.sequences:
            for scene in sq.scenes:
                for page in scene.pages:
                    for line in page.lines:
                        line.findTags = []

        if len(find) == 0:
            pass
