from . import formulas


def abstract_call(object_, name):
    raise NotImplementedError(
        f"call of abstract method: {object_.__class__.__name__}.{name}()"
    )


class WorkspaceStructure:
    def __init__(self):
        self.string = None
        self.internal_strength = 0.0
        self.external_strength = 0.0
        self.total_strength = 0.0

    def update_strength(self):
        self.update_internal_strength()
        self.update_external_strength()
        self.update_total_strength()

    def update_total_strength(self):
        """Recalculate the strength from internal and external strengths"""
        weights = (
            (self.internal_strength, self.internal_strength),
            (self.external_strength, 100 - self.internal_strength),
        )
        strength = formulas.weighted_average(weights)
        self.total_strength = strength

    def total_weakness(self):
        """The total weakness is derived from total strength"""
        return 100 - self.total_strength ** 0.95

    def update_internal_strength(self):
        """How internally cohesive the structure is"""
        abstract_call(self, "update_internal_strength")

    def update_external_strength(self):
        abstract_call(self, "update_external_strength")

    def break_the_structure(self):
        """Break this workspace structure

        Exactly what is broken depends on sub-class
        """
        abstract_call(self, "break_the_structure")
