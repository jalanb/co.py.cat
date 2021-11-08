from .slipnet import slipnet
from .workspace_object import WorkspaceObject


class Letter(WorkspaceObject):
    def __init__(self, string, position, length):
        WorkspaceObject.__init__(self, string)
        from .workspace import workspace

        workspace.objects += [self]
        string.objects += [self]
        self.left_index = position
        self.leftmost = self.left_index == 1
        self.right_index = position
        self.rightmost = self.right_index == length

    def describe(self, position, length):
        if length == 1:
            self.add_description(slipnet.string_position_category, slipnet.single)
        if self.leftmost and length > 1:  # ? why check length ?
            self.add_description(slipnet.string_position_category, slipnet.leftmost)
        if self.rightmost and length > 1:  # ? why check length ?
            self.add_description(slipnet.string_position_category, slipnet.rightmost)
        if length > 2 and position * 2 == length + 1:
            self.add_description(slipnet.string_position_category, slipnet.middle)

    def __repr__(self):
        return f"<Letter: {self}>"

    def __str__(self):
        if not self.string:
            return ""
        index = self.left_index - 1
        if len(self.string) <= index:
            raise ValueError(
                "len(self.string) <= self.left_index ::"
                f" {len(self.string)} <= {self.left_index}"
            )
        return self.string[index]

    def distinguishing_descriptor(self, descriptor):
        """Whether no other object of the same type has the same descriptor"""
        if not WorkspaceObject.distinguishing_descriptor(descriptor):
            return False
        for object_ in self.string.objects:
            # check to see if they are of the same type
            if isinstance(object_, Letter) and object_ != self:
                # check all descriptions for the descriptor
                for description in object_.descriptions:
                    if description.descriptor == descriptor:
                        return False
        return True
