import logging

from .workspace_string import WorkspaceString

unknownAnswer = "?"


def __adjust_unhappiness(values):
    result = sum(values) / 2
    if result > 100.0:
        result = 100.0
    return result


class Workspace:
    def __init__(self):
        self.set_strings("", "", "")
        self.reset()
        self.total_unhappiness = 0.0
        self.intra_string_unhappiness = 0.0
        self.inter_string_unhappiness = 0.0

    def __repr__(self):
        return (
            f"<Workspace trying {self.initial_string}:{self.modified_string}"
            f"::{self.target_string}:?>"
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
            [_.relative_importance * _.intra_string_unhappiness for _ in self.objects]
        )
        self.inter_string_unhappiness = __adjust_unhappiness(
            [_.relative_importance * _.inter_string_unhappiness for _ in self.objects]
        )
        self.total_unhappiness = __adjust_unhappiness(
            [_.relative_importance * _.total_unhappiness for _ in self.objects]
        )

    def assess_temperature(self):
        self.calculate_intra_string_unhappiness()
        self.calculate_inter_string_unhappiness()
        self.calculate_total_unhappiness()

    def calculate_intra_string_unhappiness(self):
        values = [
            _.relative_importance * _.intra_string_unhappiness for _ in self.objects
        ]
        value = sum(values) / 2.0
        self.intra_string_unhappiness = min(value, 100.0)

    def calculate_inter_string_unhappiness(self):
        values = [
            _.relative_importance * _.inter_string_unhappiness for _ in self.objects
        ]
        value = sum(values) / 2.0
        self.inter_string_unhappiness = min(value, 100.0)

    def calculate_total_unhappiness(self):
        for object_ in self.objects:
            logging.info(
                f"{object_}, total_unhappiness: {object_.total_unhappiness}, "
                f"relative_importance: {object_.relative_importance * 1000}"
            )
        values = [_.relative_importance * _.total_unhappiness for _ in self.objects]
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
        return [_ for _ in self.objects if _ != an_object]

    def number_of_unrelated_objects(self):
        """A list of all objects in the workspace with >= 1 open bond slots"""
        objects = [
            _
            for _ in self.objects
            if _.string == self.initial or _.string == self.target
        ]
        objects = [_ for _ in objects if not _.spans_string()]
        objects = [
            _
            for _ in objects
            if (not _.left_bond and not _.leftmost)
            or (not _.right_bond and not _.rightmost)
        ]
        return len(objects)

    def number_of_ungrouped_objects(self):
        """A list of all objects in the workspace that have no group."""
        objects = [
            _
            for _ in self.objects
            if _.string == self.initial or _.string == self.target
        ]
        objects = [_ for _ in objects if not _.spans_string()]
        objects = [_ for _ in objects if not _.group]
        return len(objects)

    def number_of_unreplaced_objects(self):
        """A list of all unreplaced objects in the inital string"""
        from .letter import Letter

        objects = [
            _
            for _ in self.objects
            if _.string == self.initial and isinstance(_, Letter)
        ]
        objects = [_ for _ in objects if not _.replacement]
        return len(objects)

    def number_of_uncorresponding_objects(self):
        """A list of all uncorresponded objects in the inital string"""
        objects = [
            _
            for _ in self.objects
            if _.string == self.initial or _.string == self.target
        ]
        objects = [_ for _ in objects if not _.correspondence]
        return len(objects)

    def number_of_bonds(self):
        """The number of bonds in the workspace"""
        from .bond import Bond

        return len([_ for _ in self.structures if isinstance(_, Bond)])

    def correspondences(self):
        from .correspondence import Correspondence

        return [_ for _ in self.structures if isinstance(_, Correspondence)]

    def slippages(self):
        result = []
        if self.changed_object and self.changed_object.correspondence:
            result = [_ for _ in self.changed_object.correspondence.concept_mappings]
        for object_ in workspace.initial.objects:
            if object_.correspondence:
                for mapping in object_.correspondence.slippages():
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

    def build_descriptions(self, object_):
        for description in object_.descriptions:
            description.description_type.buffer = 100.0
            description.descriptor.buffer = 100.0
            if description not in self.structures:
                self.structures += [description]


workspace = Workspace()
