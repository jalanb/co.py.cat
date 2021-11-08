import logging

from .letter import Letter
from .slipnet import slipnet


class WorkspaceString(object):
    def __init__(self, s):
        self.string = s
        self.bonds = []
        self.objects = []
        self.letters = []
        self.length = len(s)
        self.intra_string_unhappiness = 0.0
        if not self.length:
            return
        position = 0
        from .workspace import workspace

        for c in self.string.upper():
            value = ord(c) - ord("A")
            letter = Letter(self, position + 1, self.length)
            letter.workspace_string = self
            letter.add_description(slipnet.object_category, slipnet.letter)
            letter.add_description(slipnet.letter_category, slipnet.letters[value])
            letter.describe(position + 1, self.length)
            workspace.build_descriptions(letter)
            self.letters += [letter]
            position += 1

    def __repr__(self):
        return "<WorkspaceString: %s>" % self.string

    def __str__(self):
        return "%s with %d letters, %d objects, %d bonds" % (
            self.string,
            len(self.letters),
            len(self.objects),
            len(self.bonds),
        )

    def log(self, heading):
        s = "%s: %s - " % (heading, self)
        for letter in self.letters:
            s += " %s" % letter
        s += "; "
        for o in self.objects:
            s += " %s" % o
        s += "; "
        for b in self.bonds:
            s += " %s" % b
        s += "."
        logging.info(s)

    def __len__(self):
        return len(self.string)

    def __getitem__(self, i):
        return self.string[i]

    def update_relative_importance(self):
        """Update the normalised importance of all objects in the string"""
        total = sum(o.raw_importance for o in self.objects)
        if not total:
            for o in self.objects:
                o.relative_importance = 0.0
        else:
            for o in self.objects:
                logging.info(
                    "object: %s, relative: %d = raw: %d / total: %d",
                    o,
                    o.relative_importance * 1000,
                    o.raw_importance,
                    total,
                )
                o.relative_importance = o.raw_importance / total

    def update_intra_string_unhappiness(self):
        if not len(self.objects):
            self.intra_string_unhappiness = 0.0
            return
        total = sum(o.intra_string_unhappiness for o in self.objects)
        self.intra_string_unhappiness = total / len(self.objects)

    def equivalent_group(self, sought):
        from .group import Group

        for objekt in self.objects:
            if isinstance(objekt, Group):
                if objekt.same_group(sought):
                    return objekt
        return None
