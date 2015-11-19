import os

import json

import _event
import _dialog
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

    def data(self):
        data = {}
        data['text'] = self.text
        data['tag'] = self.tag
        return data

class Sequence(object):

    def __init__(self, title='', synopsis='', notes='', scenes=[]):
        self.title = title
        self.synopsis = synopsis
        self.notes = notes
        self.scenes = []

        if len(scenes) == 0:
            self.scenes.append(Scene())
        else:
            for scene in scenes:
                pages = scene['pages']
                s = Scene(pages=pages)
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
        return data


class Scene(object):

    def __init__(self, title='', synopsis='', notes='', pages=[]):
        self.title = title
        self.synopsis=synopsis
        self.notes=notes
        self.pages = []

        if len(pages) == 0:
            self.pages = [Page()]
        else:
            for page in pages:
                self.pages.append(Page(lines=page['lines']))

    def data(self):
        pages = []
        for page in self.pages:
            pages.append(page.data())
        data = {}
        data["title"] = self.title
        data["synopsis"] = self.synopsis
        data["notes"] = self.notes
        data["pages"] = pages

        return data


class Page(object):

    def __init__(self, lines=[]):
        self.title = ''
        self.lines = []
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
        return data

class Data(object):

    def __init__(self, control, path=None):
        self.control = control
        self.path = path
        self.title = ""
        if path:
            try:
                self.title = os.path.split(path)[-1]
            except:
                self.title = ""
        self.synopsis=''
        self.notes=''
        self.sequences = []
        self.eventManager = EventManager(self.control)
        self.index = StoryIndex()

        self.saved = True

    def newSequence(self):
        sequence = Sequence()

        position = self.control.currentStory().index.sequence +1
        self.sequences.insert(position, sequence)

        self.control.currentStory().index.sequence += 1
        self.control.currentStory().index.scene = 0
        self.control.currentStory().index.page = 0
        self.control.currentStory().index.line = 0

        if self.control.historyEnabled:
            self.control.currentStory().eventManager.addEvent(_event.NewSequenceEvent(sequence, self.control.currentStory().index))
        self.saved = False

    def newScene(self):
        scene = Scene()

        position = self.control.currentStory().index.scene +1
        self.control.currentSequence().scenes.insert(position, scene)

        self.control.currentStory().index.scene += 1
        self.control.currentStory().index.page = 0
        self.control.currentStory().index.line = 0

        if self.control.historyEnabled:
            self.control.currentStory().eventManager.addEvent(_event.NewSceneEvent(scene, self.control.currentStory().index))
        self.saved = False

    def newPage(self):
        page = Page()

        self.control.currentStory().index.page += 1
        self.control.currentStory().index.line = 0
        position = self.control.currentStory().index.page
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

        self.index = StoryIndex(None, data['index'])
        for sequence in data['sequences']:
            title=sequence['title']
            synopsis=sequence['synopsis']
            notes=sequence['notes']
            self.sequences.append(Sequence(title, synopsis, notes, scenes=sequence['scenes']))

        self.control.historyEnabled = True

    def save(self,):
        if self.path == None:
            _dialog.saveFile(self.control)
        else:
            self._save(self.path)

    def _save(self, path):
        self.path = path

        data = self.data()

        with open(path, 'w') as fp:
            json.dump(data, fp)

        self.control.app.updateWindowTitle()

        self.saved = True

    def default(self):
        self.control.historyEnabled = True
        self.sequences = [Sequence()]

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
