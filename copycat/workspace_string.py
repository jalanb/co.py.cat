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
        return f"<WorkspaceString: {self.string}>"

    def __str__(self):
        return (
            f"{self.string} with {len(self.letters)} letters, "
            f"{len(self.objects)} objects, {len(self.bonds)} bonds"
        )

    def log(self, heading):
        letters = " ".join(str(_) for _ in self.letters)
        objects = " ".join(str(_) for _ in self.objects)
        bonds = " ".join(str(_) for _ in self.bonds)
        logging.info(f"{heading}: {self} - {letters}, {objects}, {bonds}.")

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
                    f"object: {o}, relative: {o.relative_importance * 1000} = "
                    f"raw: {o.raw_importance} / total: {total}"
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
