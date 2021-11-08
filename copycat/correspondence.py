from .formulas import get_mappings
from .workspace import workspace
from .workspace_structure import WorkspaceStructure


class Correspondence(WorkspaceStructure):
    def __init__(
        self, object_from_initial, object_from_target, concept_mappings, flip_target_object
    ):
        WorkspaceStructure.__init__(self)
        self.object_from_initial = object_from_initial
        self.object_from_target = object_from_target
        self.concept_mappings = concept_mappings
        self.flip_target_object = flip_target_object
        self.accessory_concept_mappings = []

    def __repr__(self):
        return f"<{self.__class__.__name__} {self}>"

    def __str__(self):
        return (
            f"Correspondence between {self.object_from_initial} "
            f "and {self.object_from_target}"
        )

    def distinguishing_concept_mappings(self):
        return [m for m in self.concept_mappings if m.distinguishing()]

    def relevant_distinguishing_concept_mappings(self):
        return [m for m in self.concept_mappings if m.distinguishing() and m.relevant()]

    def extract_target_bond(self):
        target_bond = False
        if self.object_from_target.leftmost:
            target_bond = self.object_from_target.right_bond
        elif self.object_from_target.rightmost:
            target_bond = self.object_from_target.left_bond
        return target_bond

    def extract_initial_bond(self):
        initial_bond = False
        if self.object_from_initial.leftmost:
            initial_bond = self.object_from_initial.right_bond
        elif self.object_from_initial.rightmost:
            initial_bond = self.object_from_initial.left_bond
        return initial_bond

    def get_incompatible_bond(self):
        initial_bond = self.extract_initial_bond()
        if not initial_bond:
            return None
        target_bond = self.extract_target_bond()
        if not target_bond:
            return None
        from .concept_mapping import ConceptMapping
        from .slipnet import slipnet

        if initial_bond.direction_category and target_bond.direction_category:
            mapping = ConceptMapping(
                slipnet.direction_category,
                slipnet.direction_category,
                initial_bond.direction_category,
                target_bond.direction_category,
                None,
                None,
            )
            for m in self.concept_mappings:
                if m.incompatible(mapping):
                    return target_bond
        return None

    def get_incompatible_correspondences(self):
        return [
            o.correspondence
            for o in workspace.initial.objects
            if o and self.incompatible(o.correspondence)
        ]

    def incompatible(self, other):
        if not other:
            return False
        if self.object_from_initial == other.object_from_initial:
            return True
        if self.object_from_target == other.object_from_target:
            return True
        for mapping in self.concept_mappings:
            for other_mapping in other.concept_mappings:
                if mapping.incompatible(other_mapping):
                    return True
        return False

    def supporting(self, other):
        if self == other:
            return False
        if self.object_from_initial == other.object_from_initial:
            return False
        if self.object_from_target == other.object_from_target:
            return False
        if self.incompatible(other):
            return False
        for mapping in self.distinguishing_concept_mappings():
            for other_mapping in other.distinguishing_concept_mappings():
                if mapping.supports(other_mapping):
                    return True
        return False

    def support(self):
        from .letter import Letter

        if isinstance(self.object_from_initial, Letter):
            if self.object_from_initial.spans_string():
                return 100.0
        if isinstance(self.object_from_target, Letter):
            if self.object_from_target.spans_string():
                return 100.0
        total = sum(
            c.total_strength for c in workspace.correspondences() if self.supporting(c)
        )
        total = min(total, 100.0)
        return total

    def update_internal_strength(self):
        """A function of how many concept mappings there are

        Also considered: their strength and how well they cohere"""
        distinguishing_mappings = self.relevant_distinguishing_concept_mappings()
        number_of_concept_mappings = len(distinguishing_mappings)
        if number_of_concept_mappings < 1:
            self.internal_strength = 0.0
            return
        total_strength = sum(m.strength() for m in distinguishing_mappings)
        average_strength = total_strength / number_of_concept_mappings
        if number_of_concept_mappings == 1.0:
            number_of_concept_mappings_factor = 0.8
        elif number_of_concept_mappings == 2.0:
            number_of_concept_mappings_factor = 1.2
        else:
            number_of_concept_mappings_factor = 1.6
        if self.internally_coherent():
            internal_coherence_factor = 2.5
        else:
            internal_coherence_factor = 1.0
        internal_strength = (
            average_strength * internal_coherence_factor * number_of_concept_mappings_factor
        )
        self.internal_strength = min(internal_strength, 100.0)

    def update_external_strength(self):
        self.external_strength = self.support()

    def internally_coherent(self):
        """Whether any pair of distinguishing mappings support each other"""
        mappings = self.relevant_distinguishing_concept_mappings()
        for i in range(0, len(mappings)):
            for j in range(0, len(mappings)):
                if i != j:
                    if mappings[i].supports(mappings[j]):
                        return True
        return False

    def slippages(self):
        mappings = [m for m in self.concept_mappings if m.slippage()]
        mappings += [m for m in self.accessory_concept_mappings if m.slippage()]
        return mappings

    def reflexive(self):
        initial = self.object_from_initial
        if not initial.correspondence:
            return False
        if initial.correspondence.object_from_target == self.object_from_target:
            return True
        return False

    def build_correspondence(self):
        workspace.structures += [self]
        if self.object_from_initial.correspondence:
            self.object_from_initial.correspondence.break_correspondence()
        if self.object_from_target.correspondence:
            self.object_from_target.correspondence.break_correspondence()
        self.object_from_initial.correspondence = self
        self.object_from_target.correspondence = self
        # add mappings to accessory-concept-mapping-list
        relevant_mappings = self.relevant_distinguishing_concept_mappings()
        for mapping in relevant_mappings:
            if mapping.slippage():
                self.accessory_concept_mappings += [mapping.symmetric_version()]
        from .group import Group

        if isinstance(self.object_from_initial, Group):
            if isinstance(self.object_from_target, Group):
                bond_mappings = get_mappings(
                    self.object_from_initial,
                    self.object_from_target,
                    self.object_from_initial.bond_descriptions,
                    self.object_from_target.bond_descriptions,
                )
                for mapping in bond_mappings:
                    self.accessory_concept_mappings += [mapping]
                    if mapping.slippage():
                        self.accessory_concept_mappings += [mapping.symmetric_version()]
        for mapping in self.concept_mappings:
            if mapping.label:
                mapping.label.activation = 100.0

    def break_the_structure(self):
        self.break_correspondence()

    def break_correspondence(self):
        workspace.structures.remove(self)
        self.object_from_initial.correspondence = None
        self.object_from_target.correspondence = None
