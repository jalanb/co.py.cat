from .workspace_structure import WorkspaceStructure


class Replacement(WorkspaceStructure):
    def __init__(self, object_from_initial, object_from_modified, relation):
        WorkspaceStructure.__init__(self)
        self.object_from_initial = object_from_initial
        self.object_from_modified = object_from_modified
        self.relation = relation
