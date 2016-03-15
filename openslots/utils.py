"""OpenSlots utilities, including RNG"""


import time
import threading

from random import SystemRandom


def rng_cycle(rng):
    while rng.is_cycling:
        rng._cur = rng._rng.random()
        time.sleep(1/rng.hz)


class RNG(object):
    """Provide a random number generator which can constantly generate random
    numbers as required by various gaming jurisdictions.
    """

    def __init__(self, hz=100):
        self._rng = SystemRandom()
        self._cur = self._rng.random()
        self.is_cycling = False
        self.hz = hz

    def cycle(self):
        self.rng_thread = threading.Thread(target=rng_cycle, args=(self,))
        self.is_cycling = True
        self.rng_thread.start()

    def stop_cycle(self):
        self.is_cycling = False
        self.rng_thread.join()