import logging


class Temperature(object):
    def __init__(self):
        self.value = 100.0
        self.clamped = True
        self.clamp_time = 30

    def update(self, value):
        logging.debug(f"update to {value}")
        self.value = value

    def try_unclamp(self):
        from .coderack import coderack

        if self.clamped and coderack.codelets_run >= self.clamp_time:
            logging.info(f"unclamp temperature at {coderack.codelets_run}")
            self.clamped = False

    def log(self):
        logging.debug(f"temperature.value: {self.value}")


temperature = Temperature()
