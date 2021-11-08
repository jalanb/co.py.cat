import logging
import random

from . import formulas
from .slipnet import slipnet
from .workspace import workspace
from .workspace_object import WorkspaceObject


class Group(WorkspaceObject):
    def __init__(
        self, string, group_category, direction_category, facet, object_list, bond_list
    ):
        WorkspaceObject.__init__(self, string)
        self.group_category = group_category
        self.direction_category = direction_category
        self.facet = facet
        self.object_list = object_list
        self.bond_list = bond_list
        self.bond_category = self.group_category.get_related_node(slipnet.bond_category)

        left_object = object_list[0]
        right_object = object_list[-1]
        self.left_index = left_object.left_index
        self.leftmost = self.left_index == 1
        self.right_index = right_object.right_index
        self.rightmost = self.right_index == len(self.string)

        self.descriptions = []
        self.bond_descriptions = []
        self.extrinsic_descriptions = []
        self.outgoing_bonds = []
        self.incoming_bonds = []
        self.bonds = []
        self.left_bond = None
        self.right_bond = None
        self.correspondence = None
        self.changed = False
        self.new_answer_letter = False
        self.clamp_salience = False
        self.name = ""

        from .description import Description

        if self.bond_list and len(self.bond_list):
            first_facet = self.bond_list[0].facet
            self.add_bond_description(
                Description(self, slipnet.bond_facet, first_facet)
            )
        self.add_bond_description(
            Description(self, slipnet.bond_category, self.bond_category)
        )

        self.add_description(slipnet.object_category, slipnet.group)
        self.add_description(slipnet.group_category, self.group_category)
        if not self.direction_category:
            # sameness group - find letter_category
            letter = self.object_list[0].get_descriptor(self.facet)
            self.add_description(self.facet, letter)
        if self.direction_category:
            self.add_description(slipnet.direction_category, self.direction_category)
        if self.spans_string():
            self.add_description(slipnet.string_position_category, slipnet.whole)
        elif self.left_index == 1:
            self.add_description(slipnet.string_position_category, slipnet.leftmost)
        elif self.right_index == self.string.length:
            self.add_description(slipnet.string_position_category, slipnet.rightmost)
        elif self.middle_object():
            self.add_description(slipnet.string_position_category, slipnet.middle)
        self.add_length_description_category()

    def add_length_description_category(self):
        # check whether or not to add length description category
        probability = self.length_description_probability()
        if random.random() < probability:
            length = len(self.object_list)
            if length < 6:
                self.add_description(slipnet.length, slipnet.numbers[length - 1])

    def __str__(self):
        string = self.string.__str__()
        left = self.left_index - 1
        right = self.right_index
        return f"group[{left}:{right - 1}] == {string[left:right]}"

    def get_incompatible_groups(self):
        result = []
        for objekt in self.object_list:
            while objekt.group:
                result += [objekt.group]
                objekt = objekt.group
        return result

    def add_bond_description(self, description):
        self.bond_descriptions += [description]

    def single_letter_group_probability(self):
        number_of_supporters = self.number_of_local_supporting_groups()
        if not number_of_supporters:
            return 0.0
        if number_of_supporters == 1:
            exp = 4.0
        elif number_of_supporters == 2:
            exp = 2.0
        else:
            exp = 1.0
        support = self.local_support() / 100.0
        activation = slipnet.length.activation / 100.0
        supported_activation = (support * activation) ** exp
        return formulas.temperature_adjusted_probability(supported_activation)

    def flipped_version(self):
        flipped_bonds = [b.flippedversion() for b in self.bond_list]
        flipped_group = self.group_category.get_related_node(slipnet.flipped)
        flipped_direction = self.direction_category.get_related_node(slipnet.flipped)
        return Group(
            self.string,
            flipped_group,
            flipped_direction,
            self.facet,
            self.object_list,
            flipped_bonds,
        )

    def build_group(self):
        workspace.objects += [self]
        workspace.structures += [self]
        self.string.objects += [self]
        for objekt in self.object_list:
            objekt.group = self
        workspace.build_descriptions(self)
        self.activate_descriptions()

    def activate_descriptions(self):
        for description in self.descriptions:
            logging.info(f"Activate: {description}")
            description.descriptor.buffer = 100.0

    def length_description_probability(self):
        length = len(self.object_list)
        if length > 5:
            return 0.0
        cubedlength = length ** 3
        fred = cubedlength * (100.0 - slipnet.length.activation) / 100.0
        probability = 0.5 ** fred
        value = formulas.temperature_adjusted_probability(probability)
        if value < 0.06:
            value = 0.0  # otherwise 1/20 chance always
        return value

    def break_the_structure(self):
        self.break_group()

    def break_group(self):
        while len(self.descriptions):
            description = self.descriptions[-1]
            description.break_description()
        for objekt in self.object_list:
            objekt.group = None
        if self.group:
            self.group.break_group()
        if self in workspace.structures:
            workspace.structures.remove(self)
        if self in workspace.objects:
            workspace.objects.remove(self)
        if self in self.string.objects:
            self.string.objects.remove(self)
        if self.correspondence:
            self.correspondence.break_correspondence()
        if self.left_bond:
            self.left_bond.break_bond()
        if self.right_bond:
            self.right_bond.break_bond()

    def update_internal_strength(self):
        related_bond_association = self.group_category.get_related_node(
            slipnet.bond_category
        ).degree_of_association()
        bond_weight = related_bond_association ** 0.98
        length = len(self.object_list)
        if length == 1:
            length_factor = 5.0
        elif length == 2:
            length_factor = 20.0
        elif length == 3:
            length_factor = 60.0
        else:
            length_factor = 90.0
        length_weight = 100.0 - bond_weight
        weight_list = (
            (related_bond_association, bond_weight),
            (length_factor, length_weight),
        )
        self.internal_strength = formulas.weighted_average(weight_list)

    def update_external_strength(self):
        if self.spans_string():
            self.external_strength = 100.0
        else:
            self.external_strength = self.local_support()

    def local_support(self):
        number_of_supporters = self.number_of_local_supporting_groups()
        if number_of_supporters == 0.0:
            return 0.0
        support_factor = min(1.0, 0.6 ** (1 / (number_of_supporters ** 3)))
        density_factor = 100.0 * ((self.local_density() / 100.0) ** 0.5)
        return density_factor * support_factor

    def number_of_local_supporting_groups(self):
        count = 0
        for objekt in self.string.objects:
            if isinstance(objekt, Group):
                if (
                    objekt.right_index < self.left_index
                    or objekt.left_index > self.right_index
                    and objekt.group_category == self.group_category
                    and objekt.direction_category == self.direction_category
                ):
                    count += 1
        return count

    def local_density(self):
        number_of_supporters = self.number_of_local_supporting_groups()
        half_length = len(self.string) / 2.0
        return 100.0 * number_of_supporters / half_length

    def same_group(self, other):
        if self.left_index != other.left_index:
            return False
        if self.right_index != other.right_index:
            return False
        if self.group_category != other.group_category:
            return False
        if self.direction_category != other.direction_category:
            return False
        if self.facet != other.facet:
            return False
        return True

    def more_possible_descriptions(self, node):
        result = []
        i = 1
        for number in slipnet.numbers:
            if node == number and len(self.objects) == i:
                result += [node]
            i += 1
        return result

    def distinguishing_descriptor(self, descriptor):
        """Whether no other object of the same type has the same descriptor"""
        if not WorkspaceObject.distinguishing_descriptor(descriptor):
            return False
        for objekt in self.string.objects:
            # check to see if they are of the same type
            if isinstance(objekt, Group) and objekt != self:
                # check all descriptions for the descriptor
                for description in objekt.descriptions:
                    if description.descriptor == descriptor:
                        return False
        return True
