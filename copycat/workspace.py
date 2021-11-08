import logging

from .workspace_string import WorkspaceString

unknownAnswer = "?"


def __adjust_unhappiness(values):
    result = sum(values) / 2
    if result > 100.0:
        result = 100.0
    return result


class Workspace(object):
    def __init__(self):
        self.set_strings("", "", "")
        self.reset()
        self.total_unhappiness = 0.0
        self.intra_string_unhappiness = 0.0
        self.inter_string_unhappiness = 0.0

    def __repr__(self):
        return "<Workspace trying %s:%s::%s:?>" % (
            self.initial_string,
            self.modified_string,
            self.target_string,
        )

    def set_strings(self, initial, modified, target):
        self.target_string = target
        self.initial_string = initial
        self.modified_string = modified

    def reset(self):
        self.found_answer = False
        self.changed_object = None
        self.objects = []
        self.structures = []
        self.rule = None
        self.initial = WorkspaceString(self.initial_string)
        self.modified = WorkspaceString(self.modified_string)
        self.target = WorkspaceString(self.target_string)

    def assess_unhappiness(self):
        self.intra_string_unhappiness = __adjust_unhappiness(
            [o.relative_importance * o.intra_string_unhappiness for o in self.objects]
        )
        self.inter_string_unhappiness = __adjust_unhappiness(
            [o.relative_importance * o.inter_string_unhappiness for o in self.objects]
        )
        self.total_unhappiness = __adjust_unhappiness(
            [o.relative_importance * o.total_unhappiness for o in self.objects]
        )

    def assess_temperature(self):
        self.calculate_intra_string_unhappiness()
        self.calculate_inter_string_unhappiness()
        self.calculate_total_unhappiness()

    def calculate_intra_string_unhappiness(self):
        values = [o.relative_importance * o.intra_string_unhappiness for o in self.objects]
        value = sum(values) / 2.0
        self.intra_string_unhappiness = min(value, 100.0)

    def calculate_inter_string_unhappiness(self):
        values = [o.relative_importance * o.inter_string_unhappiness for o in self.objects]
        value = sum(values) / 2.0
        self.inter_string_unhappiness = min(value, 100.0)

    def calculate_total_unhappiness(self):
        for o in self.objects:
            logging.info(
                "%s, total_unhappiness: %d, relative_importance: %d",
                o,
                o.total_unhappiness,
                o.relative_importance * 1000,
            )
        values = [o.relative_importance * o.total_unhappiness for o in self.objects]
        value = sum(values) / 2.0
        self.total_unhappiness = min(value, 100.0)

    def update_everything(self):
        for structure in self.structures:
            structure.update_strength()
        for obj in self.objects:
            obj.update_value()
        self.initial.update_relative_importance()
        self.target.update_relative_importance()
        self.initial.update_intra_string_unhappiness()
        self.target.update_intra_string_unhappiness()

    def other_objects(self, an_object):
        return [o for o in self.objects if o != an_object]

    def number_of_unrelated_objects(self):
        """A list of all objects in the workspace with >= 1 open bond slots"""
        objects = [
            o
            for o in self.objects
            if o.string == self.initial or o.string == self.target
        ]
        objects = [o for o in objects if not o.spans_string()]
        objects = [
            o
            for o in objects
            if (not o.left_bond and not o.leftmost)
            or (not o.right_bond and not o.rightmost)
        ]
        return len(objects)

    def number_of_ungrouped_objects(self):
        """A list of all objects in the workspace that have no group."""
        objects = [
            o
            for o in self.objects
            if o.string == self.initial or o.string == self.target
        ]
        objects = [o for o in objects if not o.spans_string()]
        objects = [o for o in objects if not o.group]
        return len(objects)

    def number_of_unreplaced_objects(self):
        """A list of all unreplaced objects in the inital string"""
        from .letter import Letter

        objects = [
            o
            for o in self.objects
            if o.string == self.initial and isinstance(o, Letter)
        ]
        objects = [o for o in objects if not o.replacement]
        return len(objects)

    def number_of_uncorresponding_objects(self):
        """A list of all uncorresponded objects in the inital string"""
        objects = [
            o
            for o in self.objects
            if o.string == self.initial or o.string == self.target
        ]
        objects = [o for o in objects if not o.correspondence]
        return len(objects)

    def number_of_bonds(self):
        """The number of bonds in the workspace"""
        from .bond import Bond

        return len([o for o in self.structures if isinstance(o, Bond)])

    def correspondences(self):
        from .correspondence import Correspondence

        return [s for s in self.structures if isinstance(s, Correspondence)]

    def slippages(self):
        result = []
        if self.changed_object and self.changed_object.correspondence:
            result = [m for m in self.changed_object.correspondence.concept_mappings]
        for objekt in workspace.initial.objects:
            if objekt.correspondence:
                for mapping in objekt.correspondence.slippages():
                    if not mapping.is_nearly_contained_by(result):
                        result += [mapping]
        return result

    def build_rule(self, rule):
        if self.rule:
            self.structures.remove(self.rule)
        self.rule = rule
        self.structures += [rule]
        rule.activate_rule_descriptions()

    def break_rule(self):
        self.rule = None

    def build_descriptions(self, objekt):
        for description in objekt.descriptions:
            description.description_type.buffer = 100.0
            description.descriptor.buffer = 100.0
            if description not in self.structures:
                self.structures += [description]


workspace = Workspace()
