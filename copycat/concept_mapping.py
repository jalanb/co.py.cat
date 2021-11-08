import logging

from .slipnet import slipnet


class ConceptMapping:
    def __init__(
        self,
        initial_description_type,
        target_description_type,
        initial_descriptor,
        target_descriptor,
        initial_object,
        target_object,
    ):
        # pylint: disable=too-many-arguments
        logging.info(
            f"make a map: {initial_description_type.get_name()}-"
            f"{target_description_type.get_name()}"
        )
        self.initial_description_type = initial_description_type
        self.target_description_type = target_description_type
        self.initial_descriptor = initial_descriptor
        self.target_descriptor = target_descriptor
        self.initial_object = initial_object
        self.target_object = target_object
        self.label = initial_descriptor.get_bond_category(target_descriptor)

    def __repr__(self):
        return (
            f"<ConceptMapping: {self} from {self.initial_descriptor} "
            f"to {self.target_descriptor}>"
        )

    def __str__(self):
        return self.label and self.label.name or "anonymous"

    def slippability(self):
        association = self.__degree_of_association()
        if association == 100.0:
            return 100.0
        depth = self.__conceptual_depth() / 100.0
        return association * (1 - depth * depth)

    def __degree_of_association(self):
        # Assumes the 2 descriptors are connected in the slipnet by <= 1 link
        if self.initial_descriptor == self.target_descriptor:
            return 100.0
        for link in self.initial_descriptor.lateral_slip_links:
            if link.destination == self.target_descriptor:
                return link.degree_of_association()
        return 0.0

    def strength(self):
        association = self.__degree_of_association()
        if association == 100.0:
            return 100.0
        depth = self.__conceptual_depth() / 100.0
        return association * (1 + depth * depth)

    def __conceptual_depth(self):
        return (
            self.initial_descriptor.conceptual_depth
            + self.target_descriptor.conceptual_depth
        ) / 2.0

    def distinguishing(self):
        if self.initial_descriptor == slipnet.whole:
            if self.target_descriptor == slipnet.whole:
                return False
        if not self.initial_object.distinguishing_descriptor(self.initial_descriptor):
            return False
        return self.target_object.distinguishing_descriptor(self.target_descriptor)

    def same_initial_type(self, other):
        return self.initial_description_type == other.initial_description_type

    def same_target_type(self, other):
        return self.target_description_type == other.target_description_type

    def same_types(self, other):
        return self.same_initial_type(other) and self.same_target_type(other)

    def same_initial_descriptor(self, other):
        return self.initial_descriptor == other.initial_descriptor

    def same_target_descriptor(self, other):
        return self.target_descriptor == other.target_descriptor

    def same_descriptors(self, other):
        if self.same_initial_descriptor(other):
            return self.same_target_descriptor(other)

    def same_kind(self, other):
        return self.same_types(other) and self.same_descriptors(other)

    def nearly_same_kind(self, other):
        return self.same_types(other) and self.same_initial_descriptor(other)

    def is_contained_by(self, mappings):
        return any(self.same_kind(mapping) for mapping in mappings)

    def is_nearly_contained_by(self, mappings):
        return any(self.nearly_same_kind(mapping) for mapping in mappings)

    def related(self, other):
        if self.initial_descriptor.related(other.initial_descriptor):
            return True
        return self.target_descriptor.related(other.target_descriptor)

    def incompatible(self, other):
        # Concept-mappings (a -> b) and (c -> d) are incompatible if a is
        # related to c or if b is related to d, and the a -> b relationship is
        # different from the c -> d relationship. E.g., rightmost -> leftmost
        # is incompatible with right -> right, since rightmost is linked
        # to right, but the relationships (opposite and identity) are different
        # Notice that slipnet distances are not looked at, only slipnet links.
        # This should be changed eventually.
        if not self.related(other):
            return False
        if not self.label or not other.label:
            return False
        return self.label != other.label

    def supports(self, other):
        # Concept-mappings (a -> b) and (c -> d) support each other if a is
        # related to c and if b is related to d and the a -> b relationship is
        # the same as the c -> d relationship.  E.g., rightmost -> rightmost
        # supports right -> right and leftmost -> leftmost.
        # Notice that slipnet distances are not looked at, only slipnet links.
        # This should be changed eventually.

        # If the two concept-mappings are the same, then return t.  This
        # means that letter->group supports letter->group, even though these
        # concept-mappings have no label.

        if self.initial_descriptor == other.initial_descriptor:
            if self.target_descriptor == other.target_descriptor:
                return True
        # if the descriptors are not related return false
        if not self.related(other):
            return False
        if not self.label or not other.label:
            return False
        return self.label == other.label

    def relevant(self):
        if self.initial_description_type.fully_active():
            return self.target_description_type.fully_active()

    def slippage(self):
        if self.label != slipnet.sameness:
            return self.label != slipnet.identity

    def symmetric_version(self):
        if not self.slippage():
            return self
        bond = self.target_descriptor.get_bond_category(self.initial_descriptor)
        if bond == self.label:
            return self
        return ConceptMapping(
            self.target_description_type,
            self.initial_description_type,
            self.target_descriptor,
            self.initial_descriptor1,
            self.initial_object,
            self.target_object,
        )
