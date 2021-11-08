

class Sliplink:
    def __init__(self, source, destination, label=None, length=0.0):
        self.source = source
        self.destination = destination
        self.label = label
        self.fixed_length = length
        source.outgoing_links += [self]
        destination.incoming_links += [self]

    def degree_of_association(self):
        if self.fixed_length > 0 or not self.label:
            return 100.0 - self.fixed_length
        return self.label.degree_of_association()

    def intrinsic_degree_of_association(self):
        if self.fixed_length > 1:
            return 100.0 - self.fixed_length
        if self.label:
            return 100.0 - self.label.intrinsic_link_length
        return 0.0

    def spread_activation(self):
        self.destination.buffer += self.intrinsic_degree_of_association()

    def points_at(self, other):
        return self.destination == other
