import json, os

import _event

class ArchiveManager(object):

    def __init__(self, control, scene):
        self.control = control
        self.scene = scene
        self.paths = []
        self.pathIndex = -1
        self.events = {}

    def reset(self):
        for path in self.paths:
            os.remove(path)
        self.paths = []
        self.events = {}

        self.pathIndex = 0
        self.appendExistingPath()
        self.save()
        self.control.updateHistoryColor()

    def clear(self):
        if os.path.exists(self.control.currentStory().historyDir() + "/"):
            paths = os.listdir(self.control.currentStory().historyDir() + "/")

            scenePaths = []
            for path in paths:
                splitPath = path.split("-")
                if len(splitPath) > 1:
                    if splitPath[-2] == str(self.scene.id):
                        scenePaths.append(self.control.currentStory().historyDir() + "/" + path)

            for path in scenePaths:
                os.remove(path)

            timeStampPath = self.control.currentStory().historyDir() + "/timestamp-" + str(self.scene.id)
            if os.path.exists(timeStampPath):
                os.remove(timeStampPath)

        self.paths = []
        self.events = {}

        self.pathIndex = 0
        self.appendExistingPath()
        self.scene.eventIndex = -1

        try:
            self.save()
        except:
            print "archive manager could not save when clearing"

    def canForward(self):
        if len(self.paths) == 0:
            return False
        if self.pathIndex + 1 < len(self.paths):
            return True
        return False

    def canBackward(self):
        if self.pathIndex > 0:
            return True
        return False

    def forward(self):
        if self.canForward():
            self.pathIndex += 1
            self.load()
            self.scene.eventIndex = 0

    def backward(self):
        if self.canBackward():
            self.pathIndex -= 1
            self.load()
            self.scene.eventIndex = len(self.events) - 1

    def nextEvents(self):
        if self.canForward():
            return self.eventsFromArchivePath(self.paths[self.pathIndex + 1])
        return {}

    def previousEvents(self):
        if self.canBackward():
            return self.eventsFromArchivePath(self.paths[self.pathIndex - 1])
        return {}

    def load(self):
        self.events = self.eventsFromArchivePath(self.paths[self.pathIndex])

    def save(self):
        if len(self.paths):
            data = {}
            events = {}
            keys = self.events.keys()
            for key in keys:
                eventData = self.events[key].data(self.control)
                events[key] = eventData
            data['events'] = events

            with open(self.paths[self.pathIndex], 'w') as fp:
                json.dump(data, fp)
            fp.close()

    def removeEventsAfterIndex(self, index):
        keys = self.events.keys()
        slicedEvents = {}
        for key in keys:
            if key < index:
                slicedEvents[key] = self.events[key]
        self.events = slicedEvents

    def removePathsAfterIndex(self, index):
        removePaths = self.paths[index:]
        self.paths = self.paths[:index + 1]
        for path in removePaths:
            os.remove(path)

    def currentPathExists(self):
        cs = self.control.currentStory()
        path = cs.historyDir() + "/" + str(self.scene.id) + "-" + str(self.pathIndex)
        if os.path.exists(path):
            return True
        else:
            return False

    def appendExistingPath(self):
        cs = self.control.currentStory()
        path = cs.historyDir() + "/" + str(self.scene.id) + "-" + str(self.pathIndex)
        if path not in self.paths:
            self.paths.append(path)

    def eventsFromArchivePath(self, path):
        archiveEvents = {}
        with open(path, 'r') as fp:
            data = json.load(fp)
            keys = data['events'].keys()
            for key in keys:
                event = data['events'][key]
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
                elif event['name'] == "FormatLines":
                    evt = _event.FormatLines(scene, page, line, offset, text, tags)
                elif event['name'] == "Page":
                    evt = _event.Page(scene, page)
                if 'beforeTags' in event.keys():
                    evt.beforeTags = event['beforeTags']
                if 'pushedOffHeading' in event.keys():
                    evt.pushedOffHeading = event['pushedOffHeading']
                archiveEvents[int(key)] = evt
        fp.close()
        return archiveEvents