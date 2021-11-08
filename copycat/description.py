import logging

from .workspace_structure import WorkspaceStructure


class Description(WorkspaceStructure):
    def __init__(self, workspace_object, description_type, descriptor):
        WorkspaceStructure.__init__(self)
        self.object = workspace_object
        self.string = workspace_object.string
        self.description_type = description_type
        self.descriptor = descriptor

    def __repr__(self):
        return f"<Description: {self}>"

    def __str__(self):
        from .workspace import workspace
        descriptor = self.descriptor.get_name()
        container = "initial" if self.object.string == workspace.initial else "target"
        return f"description({descriptor}) of {self.object} in {container} string"

    def update_internal_strength(self):
        self.internal_strength = self.descriptor.conceptual_depth

    def update_external_strength(self):
        self.external_strength = (
            self.local_support() + self.description_type.activation
        ) / 2

    def local_support(self):
        from .workspace import workspace

        described_like_self = 0
        for other in workspace.other_objects(self.object):
            if self.object.is_within(other) or other.is_within(self.object):
                continue
            for description in other.descriptions:
                if description.description_type == self.description_type:
                    described_like_self += 1
        results = {0: 0.0, 1: 20.0, 2: 60.0, 3: 90.0}
        if described_like_self in results:
            return results[described_like_self]
        return 100.0

    def build(self):
        self.description_type.buffer = 100.0
        self.descriptor.buffer = 100.0
        if not self.object.described(self.descriptor):
            logging.info(f"Add {self} to descriptions")
            self.object.descriptions += [self]

    def break_description(self):
        from .workspace import workspace

        if self in workspace.structures:
            workspace.structures.remove(self)
        self.object.descriptions.remove(self)
