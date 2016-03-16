"""Core OpenSlots module"""


class Reel(object):
    def __init__(self, symbols, window=3):
        self.window = window
        self.symbols = symbols


class Game(object):
    def __init__(self, reels, paytable):
        self.reels = reels
        self.paytable = paytable


class Symbol(object):
    def __init__(self, name, image=None, wild=False, wild_excludes=None):
        self.name = name
        self.image = image
        self.wild = wild
        self.wild_excludes = wild_excludes

    def __eq__(self, other):
        return (self.name == other.name or
                self.wild and other.name not in self.wild_excludes
                )


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

    def __call__(self, window):
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

    def __call__(self, window):
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
