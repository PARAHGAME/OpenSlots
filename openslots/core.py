"""Core OpenSlots module"""


from tabulate import tabulate
from .utils import RNG
from .protocols import sas


class Symbol(object):
    def __init__(self, name, wild=False, wild_excludes=[], image=None):
        self._name = name
        self.image = image
        self.wild = wild
        self.wild_excludes = wild_excludes

    @property
    def name(self):
        return self._name

    def __hash__(self):
        temp = self.name, self.wild, self.wild_excludes
        return hash(temp)

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

    def __len__(self):
        """Number of reelstops on this virtual reel"""
        return len(self.symbols)

    def slice(self, stop):
        """Get the symbols to display at the given reelstop.

        Args:
            stop (int): reelstop position at the top of the window

        Returns:
            slice (list:Symbol): list of Symbols displayed in the window at the
                given reelstop
        """

        n = len(self.symbols)
        assert n > stop >= 0

        if stop + self.window > n:
            # wrap reel around around
            return self.symbols[stop:] + self.symbols[:stop + self.window - n]
        else:
            return self.symbols[stop:stop + self.window]


class Payline(object):
    def __init__(self, payline):
        """
        Args:
            payline (seq:int): indices of displayed reel positions from the top

        Example:
            Payline([1, 1, 1, 1, 1])  # center of reels
        """
        self._payline = payline
        self.active = False

    def evaluate(self, window):
        """Evaluate the state of this payline from the current position of the
        reels.

        Args:
            window (seq:seq:Symbol): The currently displayed symbols on each reel

        Returns:
            lineSymbol): The symbols on this payline
        """

        assert len(window) == len(self._payline)

        if self.active:
            return [r[i] for r, i in zip(window, self._payline)]
        else:
            return [None] * len(window)


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

    def __init__(self, symbol, n, pays):
        """
        Args:
            symbol (Symbol): The Symbol object this rule evaluates for
            n (int): Number of symbols to evaluate condition for
            pays (int): How much times line bet to pay for `n` symbols
        """

        self.symbol = symbol
        self.n = n
        self.pays = pays
        self._mode = None

    @property
    def mode(self):
        """Used by game engine to determine whether to pass a Payline
        object or a sequence of reel slices when calling this rule.
        """

        return self._mode

    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class LeftPay(GameRule):
    """Evaluate a left-to-right line pay"""

    def __init__(self, *args, **kwargs):
        super(self.__class__).__init__(*args, **kwargs)

        self._mode = 'line'

    def __call__(self, line):
        """
        Args:
            line (seq:Symbol): the payline to evaluate for

        Returns either self.pays if win condition evaluates True, otherwise 0
        """

        n = 0
        all_wilds = True
        for symbol in line:
            if symbol == self.symbol:
                n += 1
                if not symbol.wild:
                    all_wilds = False
            else:
                break

        if n == self.n and not all_wilds:
            return self.pays
        else:
            return 0

    def payback(self, reels):
        """
        Args:
            reels (seq:Reel): Reelstrips in use

        Returns (float, float): probability and percentage return contributed by
            this rule.

        Details:
            Probability of having exactly `n` symbols `S` in a row is equal to
            the probability of having at least `n` symbols `S` in a row, minus
            the probability of having exactly `n` wild symbols in a row, minus
            the probability of having more than `n` symbols in a row, where the
            probability of having more than `n` symbols in a row is equal to the
            sum of the probabilities of having at least `n+x` symbols in a row
            up to where `n+x` equals the number of reels.
        """

        num_reels = len(reels)

        # first determine which wilds apply to our symbol:

        wilds = dict()
        for i, r in enumerate(reels):
            for s in r.symbols:
                if s in wilds:
                    wilds[s][i] += 1
                elif s.wild and self.symbol not in s.wild_excludes:
                    wilds[s] = [0] * num_reels
                    wilds[s][i] += 1

        num_wilds = [0] * num_reels
        for v in wilds.values():
            for i, n in enumerate(v):
                num_wilds[i] += n

        # now that we have the number of wilds on each reel, we should be able
        # to calculate the probabilities of having at least `x` number of wilds
        # in a row:

        wild_probs = [0.0] * num_reels
        for i, r in enumerate(reels):
            if not i:
                wild_probs[i] = num_wilds[i] / len(r)
            else:
                wild_probs[i] = wild_probs[i-1] * (num_wilds[i] / len(r))

        # now get probability of having exactly `self.n` wilds in a row:

        prob_all_wild = wild_probs[self.n] - sum(wild_probs[self.n+1:])

        # and basically repeat the process for our own symbol:

        our_probs = [0.0] * num_reels
        for i, r in enumerate(reels):
            if not i:
                our_probs[i] = r.count(self.symbol) / len(r)
            else:
                our_probs[i] = our_probs[i-1] * (r.count(self.symbol) / len(r))

        final_prob = our_probs[self.n]
        final_prob -= sum(our_probs[self.n+1:]) - prob_all_wild

        final_return = final_prob * self.pays

        return final_prob, final_return


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

    def payback(self, freqs, reels):
        """
        Determine payback contribution by this rule

        Args:
            freqs (seq:int): Number of this symbol on each reel
            reels (seq:Reel): The reelstrips for this paytable
        """

        assert len(freqs) == len(reels)
        window = [r.window for r in reels]
        reels = [r.symbols for r in reels]
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
            losing_stops.append(num_stops - winning_stops[i])

            # get total combinations (winning and losing) while we're at it
            total_combos *= num_stops

        # calculate combinations for each number of scatters
        combos = [[] for i in range(n)]
        for i in range(1, 1<<n):
            this_combo = []
            mask = []
            for j in range(n):
                if i & 1<<j:
                    this_combo.append(winning_stops[j])
                    mask.append('a')
                else:
                    this_combo.append(losing_stops[j])
                    mask.append('b')
            combos[mask.count('a')-1].append(this_combo)

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
    """Evaluate a win condition for a line-pay rule. Pays only left to right."""

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

        super(self.__class__).__init__(symbol, pays)

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

    def payback(self, freqs, reels):
        """
        Determine payback contribution by this rule

        Args:
            freqs (seq:int): Number of this symbol on each reel
            reels (seq:Reel): The reelstrips for this paytable
        """

        assert len(freqs) == len(reels)
        reels = [r.symbols for r in reels]
        n = len(reels)
        total_combos = 1

        for r in reels:
            total_combos *= len(r)

        payback = 0.0
        higher_wins = 0.0
        for i, p in zip(range(n, 0, -1), self.pays[::-1]):
            win_odds = 1.0
            for j, r in enumerate(reels):
                win_odds *= freqs[j] if j < i else (len(reels[j]) - freqs[j])
            win_odds /= total_combos
            print(win_odds)
            payback += win_odds * p
            higher_wins += win_odds

        return payback


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
