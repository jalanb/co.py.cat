import logging

from .description import Description
from .slipnet import distinguishing_descriptor
from .slipnet import slipnet
from .workspace_structure import WorkspaceStructure


class WorkspaceObject(WorkspaceStructure):
    def __init__(self, workspace_string):
        WorkspaceStructure.__init__(self)
        self.string = workspace_string
        self.descriptions = []
        self.extrinsic_descriptions = []
        self.incoming_bonds = []
        self.outgoing_bonds = []
        self.bonds = []
        self.group = None
        self.changed = None
        self.correspondence = None
        self.clamp_salience = False
        self.raw_importance = 0.0
        self.relative_importance = 0.0
        self.left_bond = None
        self.right_bond = None
        self.new_answer_letter = False
        self.name = ""
        self.replacement = None
        self.right_index = 0
        self.left_index = 0
        self.leftmost = False
        self.rightmost = False
        self.intra_string_salience = 0.0
        self.inter_string_salience = 0.0
        self.total_salience = 0.0
        self.intra_string_unhappiness = 0.0
        self.inter_string_unhappiness = 0.0
        self.total_unhappiness = 0.0

    def __str__(self):
        return "object"

    def spans_string(self):
        return self.leftmost and self.rightmost

    def add_description(self, description_type, descriptor):
        description = Description(self, description_type, descriptor)
        logging.info(f"Adding description: {description} to {self}")
        self.descriptions += [description]

    def add_descriptions(self, descriptions):
        copy = descriptions[:]  # in case we add to our own descriptions
        for description in copy:
            logging.info(f"might add: {description}")
            if not self.contains_description(description):
                self.add_description(
                    description.description_type, description.descriptor
                )
            else:
                logging.info("Won't add it")
        from .workspace import workspace

        workspace.build_descriptions(self)

    def __calculate_intra_string_happiness(self):
        if self.spans_string():
            return 100.0
        if self.group:
            return self.group.total_strength
        bond_strength = 0.0
        for bond in self.bonds:
            bond_strength += bond.total_strength
        divisor = 6.0
        if self.spans_string():  # then we have already returned
            divisor = 3.0
        return bond_strength / divisor

    def __calculate_raw_importance(self):
        """Calculate the raw importance of this object.

        Which is the sum of all relevant descriptions"""
        result = 0.0
        for description in self.descriptions:
            if description.description_type.fully_active():
                result += description.descriptor.activation
            else:
                result += description.descriptor.activation / 20.0
        if self.group:
            result *= 2.0 / 3.0
        if self.changed:
            result *= 2.0
        return result

    def update_value(self):
        self.raw_importance = self.__calculate_raw_importance()
        intra_string_happiness = self.__calculate_intra_string_happiness()
        self.intra_string_unhappiness = 100.0 - intra_string_happiness

        inter_string_happiness = 0.0
        if self.correspondence:
            inter_string_happiness = self.correspondence.total_strength
        self.inter_string_unhappiness = 100.0 - inter_string_happiness

        average_happiness = (intra_string_happiness + inter_string_happiness) / 2
        self.total_unhappiness = 100.0 - average_happiness

        if self.clamp_salience:
            self.intra_string_salience = 100.0
            self.inter_string_salience = 100.0
        else:
            from .formulas import weighted_average

            self.intra_string_salience = weighted_average(
                ((self.relative_importance, 0.2), (self.intra_string_unhappiness, 0.8))
            )
            self.inter_string_salience = weighted_average(
                ((self.relative_importance, 0.8), (self.inter_string_unhappiness, 0.2))
            )
        self.total_salience = (
            self.intra_string_salience + self.inter_string_salience
        ) / 2.0
        logging.info(
            f"Set salience of {self} to {self.total_salience}"
            f" = ({self.intra_string_salience} + {self.inter_string_salience}) / 2"
        )

    def is_within(self, other):
        return (
            self.left_index >= other.left_index
            and self.right_index <= other.right_index
        )

    def relevant_descriptions(self):
        return [_ for _ in self.descriptions if _.description_type.fully_active()]

    def get_possible_descriptions(self, description_type):
        logging.info(f"getting possible descriptions for {self}")
        descriptions = []
        from .group import Group

        for link in description_type.instance_links:
            node = link.destination
            if node == slipnet.first and self.described(slipnet.letters[0]):
                descriptions += [node]
            if node == slipnet.last and self.described(slipnet.letters[-1]):
                descriptions += [node]
            index = 1
            for number in slipnet.numbers:
                if node == number and isinstance(self, Group):
                    if len(self.object_list) == index:
                        descriptions += [node]
                index += 1
            if node == slipnet.middle and self.middle_object():
                descriptions += [node]
        logging.info(", ".join(_.get_name() for _ in descriptions))
        return descriptions

    def contains_description(self, sought):
        sought_type = sought.description_type
        sought_descriptor = sought.descriptor
        for description in self.descriptions:
            if sought_type == description.description_type:
                if sought_descriptor == description.descriptor:
                    return True
        return False

    def described(self, slipnode):
        return any(_.descriptor == slipnode for _ in self.descriptions)

    def middle_object(self):
        # only works if string is 3 chars long
        # as we have access to the string, why not just " == len / 2" ?
        object_on_my_right_is_rightmost = object_on_my_left_is_leftmost = False
        for object_ in self.string.objects:
            if object_.leftmost and object_.right_index == self.left_index - 1:
                object_on_my_left_is_leftmost = True
            if object_.rightmost and object_.left_index == self.right_index + 1:
                object_on_my_right_is_rightmost = True
        return object_on_my_right_is_rightmost and object_on_my_left_is_leftmost

    @staticmethod
    def distinguishing_descriptor(descriptor):
        return distinguishing_descriptor(descriptor)

    def relevant_distinguishing_descriptors(self):
        return [
            _.descriptor
            for _ in self.relevant_descriptions()
            if distinguishing_descriptor(_.descriptor)
        ]

    def get_descriptor(self, description_type):
        """The description attached to this object of the description type."""
        descriptor = None
        logging.info(f"\nIn {self}, trying for type: {description_type.get_name()}")
        for description in self.descriptions:
            logging.info(f"Trying description: {description}")
            if description.description_type == description_type:
                return description.descriptor
        return descriptor

    def get_description_type(self, sought_description):
        """The description_type attached to this object of that description"""
        for description in self.descriptions:
            if description.descriptor == sought_description:
                return description.description_type
        description = None
        return description

    def get_common_groups(self, other):
        return [
            _ for _ in self.string.objects if self.is_within(_) and other.is_within(_)
        ]

    def letter_distance(self, other):
        if other.left_index > self.right_index:
            return other.left_index - self.right_index
        if self.left_index > other.right_index:
            return self.left_index - other.right_index
        return 0

    def letter_span(self):
        return self.right_index - self.left_index + 1

    def beside(self, other):
        if self.string != other.string:
            return False
        if self.left_index == other.right_index + 1:
            return True
        return other.left_index == self.right_index + 1
