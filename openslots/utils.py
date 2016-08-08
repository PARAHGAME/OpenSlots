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

    Details:
        This method will calculate theoretical average RTP for each mode and
        return them as a dict keyed by mode.

        Default win modes supported are `line` and `scatter`. Any win modes not
        supported must implement a `.payback(reels, rules)` method.

        Line wins:
    """

    def prod(s):
        """Return the cumulative product of a sequence, analogous to sum()"""

        from functools import reduce
        from operator import mul

        return reduce(mul, s, 1)

    import itertools
    from collections import namedtuple

    Payback = namedtuple('Payback', ['rules', 'total_combos'])

    absolute_total_combos = prod([len(r) for r in reels])

    # First get symbol counts on each reel, it'll make our lives easier
    # Also get symbols present on each reel
    symbols_per_reel = dict()
    num_reels = len(reels)
    unique_sym_reels = []
    for i, r in enumerate(reels):
        for s in r.symbols:
            if s not in symbols_per_reel:
                symbols_per_reel[s] = [0] * num_reels
            symbols_per_reel[s][i] += 1

        unique_sym_reels.append(list(set(r.symbols)))

    line_rules = []
    scatter_rules = []
    for rule in rules:
        if rule.mode == 'line':
            line_rules.append(rule)
        elif rule.mode == 'scatter':
            scatter_rules.append(rule)

    # Iterate through line pay combinations:
    possible_lines = itertools.product(*unique_sym_reels)
    line_rule_pays = dict()
    for line in possible_lines:
        highest_winner = 0
        paid_rule = None
        for i, rule in enumerate(line_rules):
            this_pay = rule(line)
            if this_pay > highest_winner:
                highest_winner = this_pay
                paid_rule = i
        if paid_rule is None:
            continue
        elif paid_rule in line_rule_pays:
            line_rule_pays[paid_rule] += prod([reels[i].count(s) for i, s in enumerate(line)])
        else:
            line_rule_pays[paid_rule] = prod([reels[i].count(s) for i, s in enumerate(line)])

    line_pays = [(line_rules[k], v) for k, v in line_rule_pays.items()]

    return Payback(line_pays, absolute_total_combos)


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
