"""Core OpenSlots module"""


from tabulate import tabulate
from .utils import RNG
from .protocols import sas


class Symbol(object):
    def __init__(self, name, wild=False, wild_excludes=[], image=None):
        self.name = name
        self.image = image
        self.wild = wild
        self.wild_excludes = wild_excludes

    def __eq__(self, other):
        if self.wild and other.name not in self.wild_excludes:
            return True
        elif other.wild and self.name not in other.wild_excludes:
            return True
        elif self.name == other.name:
            return True
        else:
            return False


class Reel(object):
    def __init__(self, symbols, window=3):
        self.window = window
        self.symbols = symbols


class Game(object):
    def __init__(self, reels, paytable, rng=RNG, meters=sas.SASGame):
        self.reels = reels
        self.paytable = paytable
        self.rng = rng()
        self.meters = meters()
        self.rng.cycle()
        self._debug = True

    def add_credits(self, n):
        self.meters.credits += n

    def cash_out(self):
        self.meters.credits.clear()

    def spin(self, lines, line_bet):
        self.meters.coin_in += lines * line_bet
        self.meters.credits -= lines * line_bet

        window = []
        for reel in self.reels:
            stop = self.rng.randint(0, len(reel.symbols))
            stopp = stop + reel.window
            if stopp > len(reel.symbols):
                stopp -= len(reel.symbols)
                this_r = reel.symbols[stop:]
                this_r += reel.symbols[:stopp]
            else:
                this_r = reel.symbols[stop:stopp]
            window.append(this_r)

        if self._debug:
            rows = []
            numrows = max([r.window for r in self.reels])
            for i in range(numrows):
                this_row = []
                for r in window:
                    if i < len(r):
                        this_row.append(r[i].name)
                    else:
                        this_row.append('')
                rows.append(this_row)
            print(tabulate(rows))

        win = 0
        for rule in self.paytable:
            win += rule(window, lines) * line_bet
        self.meters.coin_out += win
        self.meters.credits += win

        if self._debug:
            print('Won ', win, ' credits')
            print('Credits: ', self.meters.credits)


class GameRule(object):
    """Base class for evaluating win conditions and triggering events"""

    def __init__(self, symbol, pays):
        """
        Args:
            symbol (Symbol): The Symbol object this rule evaluates for
            pays (seq): How much times line bet to pay for `i` symbols
        """

        self.symbol = symbol
        self.pays = pays

    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class ScatterPay(GameRule):
    """Evaluate a win condition for a scatter pay rule"""

    def __call__(self, window, *args, **kwargs):
        """
        Determine how much to pay for a symbol appearing anywhere on any reel.

        Args:
            window (seq): A sequence containing slices from a number of reels

        Returns:
            win (int): The amount won (if any)
        """
        n = 0
        for reel in window:
            for sym in reel:
                if sym == self.symbol:
                    n += 1

        return self.pays[n-1] if n > 0 else 0

    def payback(self, freqs, reels, window):
        """
        Determine payback contribution by this rule

        Args:
            freqs (seq:int): Number of this symbol on each reel
            reels (seq:Symbol): The reelstrips for this paytable
            window (seq:int): Number of symbols visible in each reel
        """

        assert len(freqs) == len(reels) == len(window)
        n = len(reels)
        total_combos = 1

        from functools import reduce
        from operator import mul

        # calculate stops which result in scatter being shown
        winning_stops = []
        losing_stops = []
        for i, r in enumerate(reels):
            num_stops = len(r)
            winning_stops.append(freqs[i] * window[i])
            losing_stops.append(num_stops - winning_stops)

            # get total combinations (winning and losing) while we're at it
            total_combos *= num_stops

        # calculate combinations for each number of scatters
        combos = [[] for i in range(n)]
        for i in range(1<<n):
            this_combo = []
            mask = []
            for j in range(n):
                if i & 1<<j:
                    this_combo.append(winning_stops[j])
                    mask.append('a')
                else:
                    this_combo.append(losing_stops[j])
                    mask.append('b')
            combos[mask.count('a')] = this_combo

        # calculate odds for each number of scatters
        probs = []
        for c in combos:
            this_prob = 0
            for x in c:
                this_prob += reduce(mul, x, 1)
            probs.append(this_prob / total_combos)

        # and finally, calculate payback
        payback = 0.0
        for i, p in enumerate(probs):
            payback += p * self.pays[i]

        return payback


class LinePay(GameRule):
    """Evaluate a win condition for a line-pay rule"""

    def __init__(self, symbol, pays, paylines):
        """
        Args:
            symbol (Symbol): The Symbol object this rule evaluates for
            pays (seq): How much times line bet to pay for `i` symbols
            paylines (seq): Sequence of vertical indices on each reel

        Example:
            # For 3 reels, 5 paylines
            pays = [0, 2, 5]
            paylines = [(1, 1, 1),
                        (0, 0, 0),
                        (2, 2, 2),
                        (0, 1, 2),
                        (2, 1, 0)
                        ]
        """

        self.symbol = symbol
        self.pays = pays
        self.paylines = paylines

    def __call__(self, window, active):
        """Determine how much to pay for winners on this spin.

        Args:
            window (seq): A sequence containing slices from a number of reels
            active (int): Number of paylines played

        Returns:
            win (int): The amount won (if any)
        """

        win = 0
        for line in self.paylines[:active]:
            n = 0
            for i, j in enumerate(line):
                if window[i][j] == self.symbol:
                    n += 1
                else:
                    break
            if n:
                win += self.pays[n-1]

        return win


class WinWays(GameRule):
    """Evaluate a win condition for adjacent reels"""

    def __call__(self, window, *args, **kwargs):
        """Determine how much to pay for symbols on adjacent reels.

        Args:
            window (seq): A sequence containing slices from a number of reels

        Returns:
            win (int): The amount won (if any)

        Win will be multiplied by number of symbol appearing on reels.

        Example:
            If pays=[0, 1, 2, 5, 10], will pay total 8x bet for 2, 1, and 2
            symbols appearing on reels 1, 2, and 3 (2x bet, x2, x2)
        """

        mult = 1
        n = 0  # number of adjacent reels containing symbol
        for reel in window:
            in_reel = 0
            for sym in reel:
                if sym == self.symbol:
                    if not in_reel:
                        n += 1
                    in_reel += 1
            if not in_reel:
                break
            else:
                mult *= in_reel

        if n > 0:
            return self.pays[n-1] * mult
