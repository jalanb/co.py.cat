import logging


class Temperature(object):
    def __init__(self):
        self.value = 100.0
        self.clamped = True
        self.clamp_time = 30

    def update(self, value):
        logging.debug("update to %s", value)
        self.value = value

    def try_unclamp(self):
        from .coderack import coderack

        if self.clamped and coderack.codelets_run >= self.clamp_time:
            logging.info("unclamp temperature at %d", coderack.codelets_run)
            self.clamped = False

    def log(self):
        logging.debug("temperature.value: %f", self.value)


temperature = Temperature()
