"""OpenSlots utilities, including RNG"""


import math
import time
import threading

from random import SystemRandom


def calc_rtp(reels, rules):
    """
    Calculate theoretical average RTP

    Args:
        reels (seq:Reel): Reelstrips used in this game
        rules (seq:GameRule): Win conditions
    """

    # calculate base symbol frequency
    symbols = []
    sym_freq = []
    for i, r in enumerate(reels):
        for s in r.symbols:
            if s not in symbols:
                symbols.append(s)
        sym_freq.append([r.symbols.count(s) for s in symbols])

    # add for wilds
    for i, r in enumerate(reels):
        for s in symbols:
            if s.wild and s in r:
                n = r.symbols.count(s)
                for j, t in enumerate(symbols):
                    if t not in s.wild_excludes:
                        sym_freq[i][j] += n

    # get frequencies of symbol on each reel
    freqs = []
    for i, s in enumerate(symbols):
        freqs.append([x[i] for x in sym_freq])

    payback = 0.0
    for r in rules:
        sym_idx = symbols.index(r.symbol)
        payback += r.payback(freqs[sym_idx], reels)

    return payback


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

    def choice(self, seq):
        """Return a random item from a given sequence"""

        r = math.floor(self._rng.random() * len(seq))
        return seq[r]

    def randint(self, a, b):
        """Return a random integer between a and b"""

        return math.floor((self._rng.random() * (b-a)) + a)

    def chi_square(self, n=1000000, k=1000):
        """Perform a chi-square goodness of fit test on the RNG.

        Args:
            k: Number of evenly-spaced ranges to categorize samples into.
            n: Number of samples.

        Returns:
            Pearson's cumulative test statistic, X^2, calculated as the sum of:
            observations in a category minus expected observations in that
            category, squared, divided by the expected observations in that
            category, for every category.

            You'll want to compare the resulting number against a chi-squared
            distribution table for the required p-value and k-1 degrees of
            freedom. The critical value for 95% confidence (p=0.05) at the
            default k=1000 is approximately 1074.
        """

        if self.is_cycling:
            self.stop_cycle()
            self.is_cycling = True

        U = [(i/k, (i+1)/k) for i in range(k)]
        N = [self._rng.random() for i in range(n)]
        x = 0
        for i in U:
            u = 0
            for j in N:
                if i[0] < j <=i[1]:
                    u += 1
            x += (u - (n/k))**2 / (n/k)

        if self.is_cycling:
            self.cycle()

        return x
