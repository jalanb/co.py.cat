import logging

from workspaceString import WorkspaceString

unknownAnswer = '?'


def __adjustUnhappiness(values):
    result = sum(values) / 2
    if result > 100.0:
        result = 100.0
    return result


class Workspace(object):
    def __init__(self):
        self.setStrings('', '', '')
        self.reset()
        self.totalUnhappiness = 0.0
        self.intraStringUnhappiness = 0.0
        self.interStringUnhappiness = 0.0

    def __repr__(self):
        return '<Workspace trying %s:%s::%s:?>' % (
            self.initialString, self.modifiedString, self.targetString)

    def setStrings(self, initial, modified, target):
        self.targetString = target
        self.initialString = initial
        self.modifiedString = modified

    def reset(self):
        self.foundAnswer = False
        self.changedObject = None
        self.objects = []
        self.structures = []
        self.rule = None
        self.initial = WorkspaceString(self.initialString)
        self.modified = WorkspaceString(self.modifiedString)
        self.target = WorkspaceString(self.targetString)

    def assessUnhappiness(self):
        self.intraStringUnhappiness = __adjustUnhappiness([
            o.relativeImportance * o.intraStringUnhappiness
            for o in self.objects])
        self.interStringUnhappiness = __adjustUnhappiness([
            o.relativeImportance * o.interStringUnhappiness
            for o in self.objects])
        self.totalUnhappiness = __adjustUnhappiness([
            o.relativeImportance * o.totalUnhappiness for o in self.objects])

    def assessTemperature(self):
        self.calculateIntraStringUnhappiness()
        self.calculateInterStringUnhappiness()
        self.calculateTotalUnhappiness()

    def calculateIntraStringUnhappiness(self):
        values = [o.relativeImportance * o.intraStringUnhappiness
                  for o in self.objects]
        value = sum(values) / 2.0
        self.intraStringUnhappiness = min(value, 100.0)

    def calculateInterStringUnhappiness(self):
        values = [o.relativeImportance * o.interStringUnhappiness
                  for o in self.objects]
        value = sum(values) / 2.0
        self.interStringUnhappiness = min(value, 100.0)

    def calculateTotalUnhappiness(self):
        for o in self.objects:
            logging.info("%s, totalUnhappiness: %d, relativeImportance: %d",
                         o, o.totalUnhappiness, o.relativeImportance * 1000)
        values = [o.relativeImportance * o.totalUnhappiness
                  for o in self.objects]
        value = sum(values) / 2.0
        self.totalUnhappiness = min(value, 100.0)

    def updateEverything(self):
        for structure in self.structures:
            structure.updateStrength()
        for obj in self.objects:
            obj.updateValue()
        self.initial.updateRelativeImportance()
        self.target.updateRelativeImportance()
        self.initial.updateIntraStringUnhappiness()
        self.target.updateIntraStringUnhappiness()

    def otherObjects(self, anObject):
        return [o for o in self.objects if o != anObject]

    def numberOfUnrelatedObjects(self):
        """A list of all objects in the workspace with >= 1 open bond slots"""
        objects = [o for o in self.objects
                   if o.string == self.initial or o.string == self.target]
        objects = [o for o in objects if not o.spansString()]
        objects = [o for o in objects
                   if (not o.leftBond and not o.leftmost) or
                   (not o.rightBond and not o.rightmost)]
        return len(objects)

    def numberOfUngroupedObjects(self):
        """A list of all objects in the workspace that have no group."""
        objects = [o for o in self.objects if
                   o.string == self.initial or o.string == self.target]
        objects = [o for o in objects if not o.spansString()]
        objects = [o for o in objects if not o.group]
        return len(objects)

    def numberOfUnreplacedObjects(self):
        """A list of all unreplaced objects in the inital string"""
        from letter import Letter

        objects = [o for o in self.objects
                   if o.string == self.initial and isinstance(o, Letter)]
        objects = [o for o in objects if not o.replacement]
        return len(objects)

    def numberOfUncorrespondingObjects(self):
        """A list of all uncorresponded objects in the inital string"""
        objects = [o for o in self.objects
                   if o.string == self.initial or o.string == self.target]
        objects = [o for o in objects if not o.correspondence]
        return len(objects)

    def numberOfBonds(self):
        """The number of bonds in the workspace"""
        from bond import Bond

        return len([o for o in self.structures if isinstance(o, Bond)])

    def correspondences(self):
        from correspondence import Correspondence

        return [s for s in self.structures if isinstance(s, Correspondence)]

    def slippages(self):
        result = []
        if self.changedObject and self.changedObject.correspondence:
            result = [m for m in
                      self.changedObject.correspondence.conceptMappings]
        for objekt in workspace.initial.objects:
            if objekt.correspondence:
                for mapping in objekt.correspondence.slippages():
                    if not mapping.isNearlyContainedBy(result):
                        result += [mapping]
        return result

    def buildRule(self, rule):
        if self.rule:
            self.structures.remove(self.rule)
        self.rule = rule
        self.structures += [rule]
        rule.activateRuleDescriptions()

    def breakRule(self):
        self.rule = None

    def buildDescriptions(self, objekt):
        for description in objekt.descriptions:
            description.descriptionType.buffer = 100.0
            description.descriptor.buffer = 100.0
            if description not in self.structures:
                self.structures += [description]


workspace = Workspace()
