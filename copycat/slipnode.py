import logging
import math
from random import random


def full_activation():
    return 100


def jump_threshold():
    return 55.0


def points_at(links, other):
    """Whether any of the links points at the other"""
    return any(_.points_at(other) for _ in links)


class Slipnode:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, name, depth, length=0.0):
        self.conceptual_depth = depth
        self.usual_conceptual_depth = depth
        self.name = name
        self.intrinsic_link_length = length
        self.shrunk_link_length = length * 0.4

        self.activation = 0.0
        self.buffer = 0.0
        self.clamped = False
        self.bond_facet_factor = 0.0
        self.category_links = []
        self.instance_links = []
        self.property_links = []
        self.lateral_slip_links = []
        self.lateral_non_slip_links = []
        self.incoming_links = []
        self.outgoing_links = []
        self.codelets = []
        self.clamp_bond_degree_of_association = False

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self}>"

    def reset(self):
        self.buffer = 0.0
        self.activation = 0.0

    def clamp_high(self):
        self.clamped = True
        self.activation = 100.0

    def unclamp(self):
        self.clamped = False

    def unclamped(self):
        return not self.clamped

    def set_conceptual_depth(self, depth):
        logging.info(f"set depth to {depth} for {self}")
        self.conceptual_depth = depth

    def category(self):
        if not len(self.category_links):
            return None
        link = self.category_links[0]
        return link.destination

    def fully_active(self):
        """Whether this node has full activation"""
        float_margin = 0.00001
        return self.activation > full_activation() - float_margin

    def activate_fully(self):
        """Make this node fully active"""
        self.activation = full_activation()

    def bond_degree_of_association(self):
        link_length = self.intrinsic_link_length
        if (not self.clamp_bond_degree_of_association) and self.fully_active():
            link_length = self.shrunk_link_length
        result = math.sqrt(100 - link_length) * 11.0
        return min(100.0, result)

    def degree_of_association(self):
        link_length = self.intrinsic_link_length
        if self.fully_active():
            link_length = self.shrunk_link_length
        return 100.0 - link_length

    def update(self):
        act = self.activation
        self.old_activation = act
        self.buffer -= self.activation * (100.0 - self.conceptual_depth) / 100.0

    def linked(self, other):
        """Whether the other is among the outgoing links"""
        return points_at(self.outgoing_links, other)

    def slip_linked(self, other):
        """Whether the other is among the lateral links"""
        return points_at(self.lateral_slip_links, other)

    def related(self, other):
        """Same or linked"""
        return self == other or self.linked(other)

    def apply_slippages(self, slippages):
        for slippage in slippages:
            if self == slippage.initial_descriptor:
                return slippage.target_descriptor
        return self

    def get_related_node(self, relation):
        """Return the node that is linked to this node via this relation.

        If no linked node is found, return None
        """
        from .slipnet import slipnet

        if relation == slipnet.identity:
            return self
        destinations = [
            _.destination for _ in self.outgoing_links if _.label == relation
        ]
        if destinations:
            return destinations[0]
        return None

    def get_bond_category(self, destination):
        """Return the label of the link between these nodes if it exists.

        If it does not exist return None
        """
        from .slipnet import slipnet

        result = None
        if self == destination:
            result = slipnet.identity
        else:
            for link in self.outgoing_links:
                if link.destination == destination:
                    result = link.label
                    break
        if result:
            logging.info(f"Got bond: {result.name}")
        else:
            logging.info("Got no bond")
        return result

    def spread_activation(self):
        if self.fully_active():
            _ = [link.spread_activation() for link in self.outgoing_links]

    def add_buffer(self):
        if self.unclamped():
            self.activation += self.buffer
        self.activation = max(min(self.activation, 100), 0)

    def can_jump(self):
        if self.activation <= jump_threshold():
            return False
        if self.clamped:
            return False
        value = (self.activation / 100.0) ** 3
        return random() < value

    def jump(self):
        if self.can_jump():
            self.activate_fully()

    def get_name(self):
        if len(self.name) == 1:
            return self.name.upper()
        return self.name
