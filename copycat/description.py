import logging
from workspaceStructure import WorkspaceStructure


class Description(WorkspaceStructure):
    def __init__(self, workspaceObject, descriptionType, descriptor):
        WorkspaceStructure.__init__(self)
        self.object = workspaceObject
        self.string = workspaceObject.string
        self.descriptionType = descriptionType
        self.descriptor = descriptor

    def __repr__(self):
        return '<Description: %s>' % self.__str__()

    def __str__(self):
        s = 'description(%s) of %s' % (self.descriptor.get_name(), self.object)
        from workspace import workspace
        if self.object.string == workspace.initial:
            s += ' in initial string'
        else:
            s += ' in target string'
        return s

    def updateInternalStrength(self):
        self.internalStrength = self.descriptor.conceptualDepth

    def updateExternalStrength(self):
        self.externalStrength = (self.localSupport() + self.descriptionType.activation) / 2

    def localSupport(self):
        from workspace import workspace
        supporters = 0  # number of objects in the string with a descriptionType like self
        for other in workspace.otherObjects(self.object):
            if not (self.object.isWithin(other) or other.isWithin(self.object)):
                for description in other.descriptions:
                    if description.descriptionType == self.descriptionType:
                        supporters += 1
        results = {0: 0.0, 1: 20.0, 2: 60.0, 3: 90.0}
        if supporters in results:
            return results[supporters]
        return 100.0

    def build(self):
        self.descriptionType.buffer = 100.0
        self.descriptor.buffer = 100.0
        if not self.object.hasDescription(self.descriptor):
            logging.info('Add %s to descriptions' % self)
            self.object.descriptions += [self]

    def breakDescription(self):
        from workspace import workspace
        if self in workspace.structures:
            workspace.structures.remove(self)
        self.object.descriptions.remove(self)
