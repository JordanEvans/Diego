

from _item import Item

class Data(object):

    def __init__(self, control):
        self.control = control
        
        self.name = ''
        self.intExt = ''
        self.location = ''
        self.time = ''
        self.notation = ''

    def load(self):
        pass

    def save(self,):
        pass

    def reset(self):
        pass
    
class View(Item):

    def __init__(self, control):
        Item.__init__(self, control)

    def entryLeaveNotifyEvent(self, entry, eventCrossing):
        pass