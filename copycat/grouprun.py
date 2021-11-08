from .workspace import workspace


class GroupRun:
    def __init__(self):
        self.name = "xxx"
        self.maximum_number_of_runs = 1000
        self.run_strings = []
        self.answers = []
        self.scores = [0] * 100
        self.initial = workspace.initial
        self.modified = workspace.modified
        self.target = workspace.target


groupRun = GroupRun()
