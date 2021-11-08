import logging

from .formulas import weighted_average
from .slipnet import slipnet
from .workspace import workspace
from .workspace_structure import WorkspaceStructure


class Rule(WorkspaceStructure):
    def __init__(self, facet, descriptor, category, relation):
        WorkspaceStructure.__init__(self)
        self.facet = facet
        self.descriptor = descriptor
        self.category = category
        self.relation = relation

    def __str__(self):
        if not self.facet:
            return "Empty rule"
        return (
            f"Replace {self.facet.name} of {self.descriptor.name} "
            f"{self.category.name} by {self.relation.name}"
        )

    def update_external_strength(self):
        self.external_strength = self.internal_strength

    def update_internal_strength(self):
        if not (self.descriptor and self.relation):
            self.internal_strength = 0.0
            return
        average_depth = (
            self.descriptor.conceptual_depth + self.relation.conceptual_depth
        ) / 2.0
        average_depth **= 1.1
        # see if the object corresponds to an object
        # if so, see if the descriptor is present (modulo slippages) in the
        # corresponding object
        changed_objects = [o for o in workspace.initial.objects if o.changed]
        changed = changed_objects[0]
        shared_descriptor_term = 0.0
        if changed and changed.correspondence:
            target_object = changed.correspondence.object_from_target
            slippages = workspace.slippages()
            slipnode = self.descriptor.apply_slippages(slippages)
            if not target_object.described(slipnode):
                self.internal_strength = 0.0
                return
            shared_descriptor_term = 100.0
        conceptual_height = (100.0 - self.descriptor.conceptual_depth) / 10.0
        shared_descriptor_weight = conceptual_height ** 1.4
        depth_difference = 100.0 - abs(
            self.descriptor.conceptual_depth - self.relation.conceptual_depth
        )
        weights = (
            (depth_difference, 12),
            (average_depth, 18),
            (shared_descriptor_term, shared_descriptor_weight),
        )
        self.internal_strength = weighted_average(weights)
        if self.internal_strength > 100.0:
            self.internal_strength = 100.0

    def rule_equal(self, other):
        if not other:
            return False
        if self.relation != other.relation:
            return False
        if self.facet != other.facet:
            return False
        if self.category != other.category:
            return False
        if self.descriptor != other.descriptor:
            return False
        return True

    def activate_rule_descriptions(self):
        if self.relation:
            self.relation.buffer = 100.0
        if self.facet:
            self.facet.buffer = 100.0
        if self.category:
            self.category.buffer = 100.0
        if self.descriptor:
            self.descriptor.buffer = 100.0

    def incompatible_rule_correspondence(self, correspondence):
        if not correspondence:
            return False
        # find changed object
        changeds = [o for o in workspace.initial.objects if o.changed]
        if not changeds:
            return False
        changed = changeds[0]
        if correspondence.object_from_initial != changed:
            return False
        # it is incompatible if the rule descriptor is not in the mapping list
        return bool(
            m
            for m in correspondence.concept_mappings
            if m.initial_descriptor == self.descriptor
        )

    def __change_string(self, string):
        # applies the changes to self string ie. successor
        if self.facet == slipnet.length:
            if self.relation == slipnet.predecessor:
                return string[0:-1]
            if self.relation == slipnet.successor:
                return string + string[0:1]
            return string
        # apply character changes
        if self.relation == slipnet.predecessor:
            if "a" in string:
                return None
            return "".join(chr(ord(c) - 1) for c in string)
        elif self.relation == slipnet.successor:
            if "z" in string:
                return None
            return "".join(chr(ord(c) + 1) for c in string)
        else:
            return self.relation.name.lower()

    def build_translated_rule(self):
        slippages = workspace.slippages()
        self.category = self.category.apply_slippages(slippages)
        self.facet = self.facet.apply_slippages(slippages)
        self.descriptor = self.descriptor.apply_slippages(slippages)
        self.relation = self.relation.apply_slippages(slippages)
        # generate the final string
        self.final_answer = workspace.target_string
        changeds = [
            o
            for o in workspace.target.objects
            if o.described(self.descriptor) and o.described(self.category)
        ]
        changed = changeds and changeds[0] or None
        logging.debug("changed object = %s", changed)
        if changed:
            left = changed.left_index
            start_string = ""
            if left > 1:
                start_string = self.final_answer[0 : left - 1]
            right = changed.right_index
            middle_string = self.__change_string(self.final_answer[left - 1 : right])
            if not middle_string:
                return False
            end_string = ""
            if right < len(self.final_answer):
                end_string = self.final_answer[right:]
            self.final_answer = start_string + middle_string + end_string
        return True
