import logging

from .sliplink import Sliplink
from .slipnode import Slipnode


def distinguishing_descriptor(descriptor):
    """Whether no other object of the same type has the same descriptor"""
    if descriptor == slipnet.letter:
        return False
    if descriptor == slipnet.group:
        return False
    for number in slipnet.numbers:
        if number == descriptor:
            return False
    return True


class SlipNet:
    # pylint: disable=too-many-instance-attributes
    def __init__(self):
        logging.debug("SlipNet.__init__()")
        self.initially_clamped_slipnodes = []
        self.slipnodes = []
        self.sliplinks = []
        self.bond_facets = []
        self.time_step_ength = 15
        self.number_of_updates = 0
        self.__add_initial_nodes()
        self.__add_initial_links()
        self.predecessor = None

    def __repr__(self):
        return "<slipnet>"

    def set_conceptual_depths(self, depth):
        logging.debug(f"slipnet set all depths to {depth}")
        _ = [node.set_conceptual_depth(depth) for node in self.slipnodes]

    def reset(self):
        logging.debug("slipnet.reset()")
        self.number_of_updates = 0
        for node in self.slipnodes:
            node.reset()
            if node in self.initially_clamped_slipnodes:
                node.clamp_high()

    def update(self):
        def _update(node):
            node.add_buffer()
            node.jump()
            node.buffer = 0.0

        logging.debug("slipnet.update()")
        self.number_of_updates += 1
        if self.number_of_updates == 50:
            _ = [node.unclamp() for node in self.initially_clamped_slipnodes]
        _ = [node.update() for node in self.slipnodes]
        _ = [node.spread_activation() for node in self.slipnodes]
        _ = [_update(node) for node in self.slipnodes]

    def __add_initial_nodes(self):
        # pylint: disable=too-many-statements
        self.slipnodes = []
        self.letters = [self.__add_node(c, 10.0) for c in "abcdefghijklmnopqrstuvwxyz"]
        self.numbers = [self.__add_node(c, 30.0) for c in "12345"]

        # string positions
        self.leftmost = self.__add_node("leftmost", 40.0)
        self.rightmost = self.__add_node("rightmost", 40.0)
        self.middle = self.__add_node("middle", 40.0)
        self.single = self.__add_node("single", 40.0)
        self.whole = self.__add_node("whole", 40.0)

        # alphabetic positions
        self.first = self.__add_node("first", 60.0)
        self.last = self.__add_node("last", 60.0)

        # directions
        self.left = self.__add_node("left", 40.0)
        self.left.codelets += ["top-down-bond-scout--direction"]
        self.left.codelets += ["top-down-group-scout--direction"]
        self.right = self.__add_node("right", 40.0)
        self.right.codelets += ["top-down-bond-scout--direction"]
        self.right.codelets += ["top-down-group-scout--direction"]

        # bond types
        self.predecessor = self.__add_node("predecessor", 50.0, 60.0)
        self.predecessor.codelets += ["top-down-bond-scout--category"]
        self.successor = self.__add_node("successor", 50.0, 60.0)
        self.successor.codelets += ["top-down-bond-scout--category"]
        self.sameness = self.__add_node("sameness", 80.0)
        self.sameness.codelets += ["top-down-bond-scout--category"]

        # group types
        self.predecessor_group = self.__add_node("predecessorGroup", 50.0)
        self.predecessor_group.codelets += ["top-down-group-scout--category"]
        self.successor_group = self.__add_node("successorGroup", 50.0)
        self.successor_group.codelets += ["top-down-group-scout--category"]
        self.sameness_group = self.__add_node("samenessGroup", 80.0)
        self.sameness_group.codelets += ["top-down-group-scout--category"]

        # other relations
        self.identity = self.__add_node("identity", 90.0)
        self.opposite = self.__add_node("opposite", 90.0, 80.0)

        # objects
        self.letter = self.__add_node("letter", 20.0)
        self.group = self.__add_node("group", 80.0)

        # categories
        self.letter_category = self.__add_node("letter_category", 30.0)
        self.string_position_category = self.__add_node("stringPositionCategory", 70.0)
        self.string_position_category.codelets += ["top-down-description-scout"]
        self.alphabetic_position_category = self.__add_node(
            "alphabeticPositionCategory", 80.0
        )
        self.alphabetic_position_category.codelets += ["top-down-description-scout"]
        self.direction_category = self.__add_node("direction_category", 70.0)
        self.bond_category = self.__add_node("bond_category", 80.0)
        self.group_category = self.__add_node("groupCategory", 80.0)
        self.length = self.__add_node("length", 60.0)
        self.object_category = self.__add_node("objectCategory", 90.0)
        self.bond_facet = self.__add_node("bond_facet", 90.0)

        # specify the descriptor types that bonds can form between
        self.bond_facets += [self.letter_category]
        self.bond_facets += [self.length]

        #
        self.initially_clamped_slipnodes += [self.letter_category]
        self.letter_category.clamped = True
        self.initially_clamped_slipnodes += [self.string_position_category]
        self.string_position_category.clamped = True

    def __add_initial_links(self):
        self.sliplinks = []
        self.__link_items_to_their_neighbours(self.letters)
        self.__link_items_to_their_neighbours(self.numbers)
        # letter categories
        for letter in self.letters:
            self.__add_instance_link(self.letter_category, letter, 97.0)
        self.__add_category_link(self.sameness_group, self.letter_category, 50.0)
        # lengths
        for number in self.numbers:
            self.__add_instance_link(self.length, number)
        groups = [self.predecessor_group, self.successor_group, self.sameness_group]
        for group in groups:
            self.__add_non_slip_link(group, self.length, length=95.0)
        opposites = [
            (self.first, self.last),
            (self.leftmost, self.rightmost),
            (self.leftmost, self.rightmost),
            (self.left, self.right),
            (self.successor, self.predecessor),
            (self.successor_group, self.predecessor_group),
        ]
        for a, b in opposites:
            self.__add_opposite_link(a, b)
        # properties
        self.__add_property_link(self.letters[0], self.first, 75.0)
        self.__add_property_link(self.letters[-1], self.last, 75.0)
        links = [
            # object categories
            (self.object_category, self.letter),
            (self.object_category, self.group),
            # string positions,
            (self.string_position_category, self.leftmost),
            (self.string_position_category, self.rightmost),
            (self.string_position_category, self.middle),
            (self.string_position_category, self.single),
            (self.string_position_category, self.whole),
            # alphabetic positions,
            (self.alphabetic_position_category, self.first),
            (self.alphabetic_position_category, self.last),
            # direction categories,
            (self.direction_category, self.left),
            (self.direction_category, self.right),
            # bond categories,
            (self.bond_category, self.predecessor),
            (self.bond_category, self.successor),
            (self.bond_category, self.sameness),
            # group categories
            (self.group_category, self.predecessor_group),
            (self.group_category, self.successor_group),
            (self.group_category, self.sameness_group),
            # bond facets
            (self.bond_facet, self.letter_category),
            (self.bond_facet, self.length),
        ]
        for a, b in links:
            self.__add_instance_link(a, b)
        # link bonds to their groups
        self.__add_non_slip_link(
            self.sameness, self.sameness_group, label=self.group_category, length=30.0
        )
        self.__add_non_slip_link(
            self.successor, self.successor_group, label=self.group_category, length=60.0
        )
        self.__add_non_slip_link(
            self.predecessor,
            self.predecessor_group,
            label=self.group_category,
            length=60.0,
        )
        # link bond groups to their bonds
        self.__add_non_slip_link(
            self.sameness_group, self.sameness, label=self.bond_category, length=90.0
        )
        self.__add_non_slip_link(
            self.successor_group, self.successor, label=self.bond_category, length=90.0
        )
        self.__add_non_slip_link(
            self.predecessor_group,
            self.predecessor,
            label=self.bond_category,
            length=90.0,
        )
        # letter category to length
        self.__add_slip_link(self.letter_category, self.length, length=95.0)
        self.__add_slip_link(self.length, self.letter_category, length=95.0)
        # letter to group
        self.__add_slip_link(self.letter, self.group, length=90.0)
        self.__add_slip_link(self.group, self.letter, length=90.0)
        # direction-position, direction-neighbour, position-neighbour
        self.__add_bidirectional_link(self.left, self.leftmost, 90.0)
        self.__add_bidirectional_link(self.right, self.rightmost, 90.0)
        self.__add_bidirectional_link(self.right, self.leftmost, 100.0)
        self.__add_bidirectional_link(self.left, self.rightmost, 100.0)
        self.__add_bidirectional_link(self.leftmost, self.first, 100.0)
        self.__add_bidirectional_link(self.rightmost, self.first, 100.0)
        self.__add_bidirectional_link(self.leftmost, self.last, 100.0)
        self.__add_bidirectional_link(self.rightmost, self.last, 100.0)
        # other
        self.__add_slip_link(self.single, self.whole, length=90.0)
        self.__add_slip_link(self.whole, self.single, length=90.0)

    def __add_link(self, source, destination, label=None, length=0.0):
        link = Sliplink(source, destination, label=label, length=length)
        self.sliplinks += [link]
        return link

    def __add_slip_link(self, source, destination, label=None, length=0.0):
        link = self.__add_link(source, destination, label, length)
        source.lateral_slip_links += [link]

    def __add_non_slip_link(self, source, destination, label=None, length=0.0):
        link = self.__add_link(source, destination, label, length)
        source.lateral_non_slip_links += [link]

    def __add_bidirectional_link(self, source, destination, length):
        self.__add_non_slip_link(source, destination, length=length)
        self.__add_non_slip_link(destination, source, length=length)

    def __add_category_link(self, source, destination, length):
        # noinspection PyArgumentEqualDefault
        link = self.__add_link(source, destination, None, length)
        source.category_links += [link]

    def __add_instance_link(self, source, destination, length=100.0):
        category_length = source.conceptual_depth - destination.conceptual_depth
        self.__add_category_link(destination, source, category_length)
        # noinspection PyArgumentEqualDefault
        link = self.__add_link(source, destination, None, length)
        source.instance_links += [link]

    def __add_property_link(self, source, destination, length):
        # noinspection PyArgumentEqualDefault
        link = self.__add_link(source, destination, None, length)
        source.property_links += [link]

    def __add_opposite_link(self, source, destination):
        self.__add_slip_link(source, destination, label=self.opposite)
        self.__add_slip_link(destination, source, label=self.opposite)

    def __add_node(self, name, depth, length=0):
        slipnode = Slipnode(name, depth, length)
        self.slipnodes += [slipnode]
        return slipnode

    def __link_items_to_their_neighbours(self, items):
        previous = items[0]
        for item in items[1:]:
            self.__add_non_slip_link(previous, item, label=self.successor)
            self.__add_non_slip_link(item, previous, label=self.predecessor)
            previous = item


slipnet = SlipNet()
