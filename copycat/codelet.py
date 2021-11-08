class Codelet:
    def __init__(self, name: str, urgency, timestamp):
        self.name = name
        self.urgency = urgency
        self.arguments: list = []
        self.pressure = None
        self.timestamp = timestamp

    def __str__(self) -> str:
        return str(self.name)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self}>"
