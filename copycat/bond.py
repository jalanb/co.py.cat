from .slipnet import slipnet
from .workspace import workspace
from .workspace_structure import WorkspaceStructure


class Bond(WorkspaceStructure):
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        source,
        destination,
        bond_category,
        bond_facet,
        source_descriptor,
        destination_descriptor,
    ):
        WorkspaceStructure.__init__(self)
        self.source = source
        self.string = self.source.string
        self.destination = destination
        self.left_object = self.source
        self.right_object = self.destination
        self.direction_category = slipnet.right
        if self.source.left_index > self.destination.right_index:
            self.left_object = self.destination
            self.right_object = self.source
            self.direction_category = slipnet.left
        self.facet = bond_facet
        self.source_descriptor = source_descriptor
        self.destination_descriptor = destination_descriptor
        self.category = bond_category

        self.destination_is_on_right = self.destination == self.right_object
        self.bidirectional = self.source_descriptor == self.destination_descriptor
        if self.bidirectional:
            self.direction_category = None

    def flipped_version(self):
        return Bond(
            self.destination,
            self.source,
            self.category.get_related_node(slipnet.opposite),
            self.facet,
            self.destination_descriptor,
            self.source_descriptor,
        )

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self}>"

    def __str__(self):
        return f"{self.category.name} bond between {self.left_object} and {self.right_object}"

    def build_bond(self):
        workspace.structures += [self]
        self.string.bonds += [self]
        self.category.buffer = 100.0
        if self.direction_category:
            self.direction_category.buffer = 100.0
        self.left_object.right_bond = self
        self.right_object.left_bond = self
        self.left_object.bonds += [self]
        self.right_object.bonds += [self]

    def break_the_structure(self):
        self.break_bond()

    def break_bond(self):
        if self in workspace.structures:
            workspace.structures.remove(self)
        if self in self.string.bonds:
            self.string.bonds.remove(self)
        self.left_object.right_bond = None
        self.right_object.left_bond = None
        if self in self.left_object.bonds:
            self.left_object.bonds.remove(self)
        if self in self.right_object.bonds:
            self.right_object.bonds.remove(self)

    def get_incompatible_correspondences(self):
        # returns a list of correspondences that are incompatible with
        # self bond
        incompatibles = []
        if self.left_object.leftmost and self.left_object.correspondence:
            correspondence = self.left_object.correspondence
            if self.string == workspace.initial:
                objekt = self.left_object.correspondence.object_from_target
            else:
                objekt = self.left_object.correspondence.object_from_initial
            if objekt.leftmost and objekt.right_bond:
                if (
                    objekt.right_bond.direction_category
                    and objekt.right_bond.direction_category != self.direction_category
                ):
                    incompatibles += [correspondence]
        if self.right_object.rightmost and self.right_object.correspondence:
            correspondence = self.right_object.correspondence
            if self.string == workspace.initial:
                objekt = self.right_object.correspondence.object_from_target
            else:
                objekt = self.right_object.correspondence.object_from_initial
            if objekt.rightmost and objekt.left_bond:
                if (
                    objekt.left_bond.direction_category
                    and objekt.left_bond.direction_category != self.direction_category
                ):
                    incompatibles += [correspondence]
        return incompatibles

    def update_internal_strength(self):
        # bonds between objects of same type(ie. letter or group) are
        # stronger than bonds between different types
        source_gap = self.source.left_index != self.source.right_index
        destination_gap = self.destination.left_index != self.destination.right_index
        if source_gap == destination_gap:
            member_compatibility = 1.0
        else:
            member_compatibility = 0.7
        # letter category bonds are stronger
        if self.facet == slipnet.letter_category:
            facet_factor = 1.0
        else:
            facet_factor = 0.7
        strength = min(
            100.0,
            member_compatibility * facet_factor * self.category.bond_degree_of_association(),
        )
        self.internal_strength = strength

    def update_external_strength(self):
        self.external_strength = 0.0
        supporters = self.number_of_local_supporting_bonds()
        if supporters > 0.0:
            density = self.local_density() / 100.0
            density = density ** 0.5 * 100.0
            support_factor = 0.6 ** (1.0 / supporters ** 3)
            support_factor = max(1.0, support_factor)
            strength = support_factor * density
            self.external_strength = strength

    def number_of_local_supporting_bonds(self):
        return len(
            [
                b
                for b in self.string.bonds
                if b.string == self.source.string
                and self.left_object.letter_distance(b.left_object) != 0
                and self.right_object.letter_distance(b.right_object) != 0
                and self.category == b.category
                and self.direction_category == b.direction_category
            ]
        )

    def same_categories(self, other):
        return (
            self.category == other.category
            and self.direction_category == other.direction_category
        )

    def my_ends(self, object1, object2):
        if self.source == object1 and self.destination == object2:
            return True
        return self.source == object2 and self.destination == object1

    def local_density(self):
        # returns a rough measure of the density in the string
        # of the same bond-category and the direction-category of
        # the given bond
        slot_sum = support_sum = 0.0
        for object1 in workspace.objects:
            if object1.string == self.string:
                for object2 in workspace.objects:
                    if object1.beside(object2):
                        slot_sum += 1.0
                        for bond in self.string.bonds:
                            if (
                                bond != self
                                and self.same_categories(bond)
                                and self.my_ends(object1, object2)
                            ):
                                support_sum += 1.0
        try:
            return 100.0 * support_sum / slot_sum
        except ZeroDivisionError:
            return 0.0

    def same_neighbours(self, other):
        if self.left_object == other.left_object:
            return True
        return self.right_object == other.right_object

    def get_incompatible_bonds(self):
        return [b for b in self.string.bonds if self.same_neighbours(b)]


def possible_group_bonds(bond_category, direction_category, bond_facet, bonds):
    result = []
    for bond in bonds:
        if (
            bond.category == bond_category
            and bond.direction_category == direction_category
        ):
            result += [bond]
        else:
            # a modified bond might be made
            if bond_category == slipnet.sameness:
                return None  # a different bond cannot be made here
            if (
                bond.category == bond_category
                or bond.direction_category == direction_category
            ):
                return None  # a different bond cannot be made here
            if bond.category == slipnet.sameness:
                return None
            bond = Bond(
                bond.destination,
                bond.source,
                bond_category,
                bond_facet,
                bond.destination_descriptor,
                bond.source_descriptor,
            )
            result += [bond]
    return result
