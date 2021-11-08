"""Handle workplace strings for copycat"""

import logging

from .group import Group
from .letter import Letter
from .slipnet import slipnet


class WorkspaceString:
    """A string in a workplace"""
    def __init__(self, string):
        self.string = string
        self.bonds = []
        self.objects = []
        self.letters = []
        self.length = len(string)
        self.intra_string_unhappiness = 0.0
        if not self.length:
            return
        position = 0

        from .workspace import workspace
        for char in self.string.upper():
            value = ord(char) - ord("A")
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
        """Log the string's pertinent attributes"""
        letters = " ".join(str(_) for _ in self.letters)
        objects = " ".join(str(_) for _ in self.objects)
        bonds = " ".join(str(_) for _ in self.bonds)
        logging.info(f"{heading}: {self} - {letters}, {objects}, {bonds}.")

    def __len__(self):
        return len(self.string)

    def __getitem__(self, index):
        return self.string[index]

    def update_relative_importance(self):
        """Update the normalised importance of all objects in the string"""
        total = sum(_.raw_importance for _ in self.objects)
        if not total:
            for object_ in self.objects:
                object_.relative_importance = 0.0
        else:
            for object_ in self.objects:
                logging.info(
                    f"object: {object_}, relative: {object_.relative_importance * 1000} = "
                    f"raw: {object_.raw_importance} / total: {total}"
                )
                object_.relative_importance = object_.raw_importance / total

    def update_intra_string_unhappiness(self):
        """Update the unhappiness between objects of the string"""
        if not self.objects:
            self.intra_string_unhappiness = 0.0
            return
        total = sum(_.intra_string_unhappiness for _ in self.objects)
        self.intra_string_unhappiness = total / len(self.objects)

    def equivalent_group(self, sought):
        """The first object from the same group as sought"""

        for objekt in self.objects:
            if isinstance(objekt, Group):
                if objekt.same_group(sought):
                    return objekt
        return None
