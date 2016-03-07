"""Implement IGT's Slot Accounting System protocol"""


from collections import namedtuple, Counter


___SAS_version___ = 602     # SAS version 6.02


## Supported meters ##


# List of tuples: (id, size, name, description, current)
# Used to initialize SASGame instance

_602_meters = [
    (0x00, 4, 'coin_in', 'Total coin in credits'),
    (0x01, 4, 'coin_out', 'Total coin out credits'),
    (0x02, 4, 'jackpot_out', 'Total jackpot credits'),
    (0x03, 4, 'handpay_out', 'Total hand paid canceled credits'),
    (0x04, 4, 'total_cxld', 'Total canceled credits'),
    (0x05, 4, 'games_played', 'Games played'),
    (0x06, 4, 'games_won', 'Games won'),
    (0x07, 4, 'games_lost', 'Games lost'),
    (0x08, 4, 'coin_acc_in', 'Total credits from coin acceptor'),
    (0x09, 4, 'hopper_out', 'Total credits paid from hopper'),
    (0x0a, 4, 'coins_to_drop', 'Total credits from coins to drop'),
    (0x0b, 4, 'bills_in', 'Total credits from bills accepted'),
    (0x0c, 4, 'credits', 'Current credits', True),

    # 0x0d thru 0x14 deprecated in SAS 6.02, implemented in comm logic for
    # backwards compatibility using 0x80 thru 0x8b

    (0x15, 4, 'ticket_in', 'Total ticket in (credits cashable, nonrestricted '
     'and restricted)'),
    (0x16, 4, 'ticket_out', 'Total ticket out (credits cashable, nonrestricted '
     'and restricted)'),
    (0x17, 4, 'eft_in', 'Total electronic transfers in (credits cashable, '
     'nonrestricted, and restricted) not including host bonusing'),
    (0x18, 4, 'eft_out', 'Total electronic transfers out'),
    (0x19, 4, 'restricted_play', 'Total restricted credits played'),
    (0x1a, 4, 'nonrestricted_play', 'Total nonrestricted credits played'),
    (0x1b, 4, 'current_restricted', 'Current restricted credits', True),
    (0x1c, 4, 'paytable_win', 'Total machine-paid paytable win, not including '
     'progressive or external bonus credits'),
    (0x1d, 4, 'progressive_win', 'Total machine-paid progressive win'),
    (0x1e, 4, 'ext_bonus_win', 'Total machine-paid external bonus win'),
    (0x1f, 4, 'att_paytable_win', 'Total attendant-paid paytable win'),
    (0x20, 4, 'att_progressive_win', 'Total attendant-paid progressive win'),
    (0x21, 4, 'att_ext_bonus_win', 'Total attendant-paid external bonus win'),
]


## Useful functions ##


def crc(b, seed=0):
    """Compute 16-bit CRC from bytes or sequence of ints, returns bytes"""
    for x in b:
        q = (seed ^ x) & 0o17
        seed = (seed >> 4) ^ (q * 0o10201)
        q = (seed ^ (x >> 4)) & 0o17
        seed = (seed >> 4) ^ (q * 0o10201)
    return seed.to_bytes(2, byteorder='little')


def int_to_bcd(i, length=0):
    if i < 0 or not isinstance(i, int):
        raise ValueError("`i` must be a positive integer or 0")

    if length < 0 or not isinstance(length, int):
        raise ValueError("`length` must be a positive integer or 0")

    return int(str(i), 16).to_bytes(length, 'big')


def bcd_to_int(x):
    if not isinstance(x, bytes):
        raise ValueError("`x` must be bytes object")

    s = ''
    for i in x:
        s += format(i, 'x')

    return int(s, 16)


## Class definitions ##


class SASMeter(object):
    """An SASMeter stores a value and contains methods useful for SAS clients.
    The value can only either be incremented by some value or cleared (reset to
    zero). It also stores the digit length that will be used when converting to
    BCD in response to SAS polls. Lastly, it can easily be converted to BCD for
    responding to SAS polls by simply calling bytes() on it.

    If initialized with `current=True`, this meter tracks some "current" amount
    and can be added to or subtracted from. Otherwise the meter is treated as a
    "total" meter which can only be added to.
    """

    def __init__(self, i, size=4, current=False):
        self.id = int(i)
        self.__len__ = lambda: int(size)
        self._value = 0
        self._name = ''
        self.description = ''

        def isub(self, n):
            self._value -= n if n < 0 else 0
            return self

        if current:
            self.__isub__ = isub

    @property
    def name(self):
        """Short description of this meter, truncated to 50 chars"""
        return self._name

    @name.setter
    def name(self, s):
        self._name = s[:50]

    @property
    def value(self):
        return self._value

    @value.deleter
    def value(self):
        self._value = 0

    def clear(self):
        del self.value

    def __repr__(self):
        temp = "<SASMeter {:#06x} {}, value {}>"
        return temp.format(self.id, self.name, str(self))

    def __str__(self):
        return str(self.value).rjust(self.__len__() * 2, '0')

    def __bytes__(self):
        return int_to_bcd(self.value, self.__len__())

    def __iadd__(self, n):
        self._value += n if n > 0 else 0
        return self

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)


class SASGame(object):
    def __init__(self, meters=_602_meters):
        self._v_id = 0
        self._v_seq = 0

        self._meters = meters
        self.clear_meters()

    def clear_meters(self):
        """Initialize all meters to 0"""

        self.meters = dict()
        for m in self._meters:
            this_m = SASMeter(m[0], m[1], m[-1] if len(m) == 5 else False)
            this_m.name = m[2].lstrip('_')
            this_m.description = m[3]

            setattr(self, this_m.name, this_m)
            self.meters[this_m.name] = this_m

    def SE_validation_number(self):
        """Generate secure-enhanced ticket validation number from seed
        values. Returns string representing the 18-digit validation
        number.
        """
        
        # TODO move to v_id and v_seq assignment from host
        # if 0 > self._v_id >= 2**24:
        #    raise ValueError("Validation ID too large, %i" % self._v_id)
        # if 0 > self._v_seq >= 2**24:
        #    raise ValueError("Validation sequence too large, %i" % self._v_seq)
        
        a = [x for x in self._v_seq.to_bytes(3, byteorder='little')]
        a += [x for x in self._v_id.to_bytes(3, byteorder='little')]
        
        b = [0] * 6
        b[5] = a[5] ^ a[1]
        b[4] = a[4] ^ a[0]
        b[3] = a[3] ^ a[1]
        b[2] = a[2] ^ a[0]
        b[1] = a[1]
        b[0] = a[0]
        
        c = crc(b[:2])
        c += crc(b[2:4])
        c += crc(b[4:])
        
        n = [0, 0]
        
        for i, v in enumerate(c[3:]):
            n[0] += v << (i * 8)
            
        for i, v in enumerate(c[:3]):
            n[1] += v << (i * 8)
            
        v = [int(x) for x in '%08i%08i' % tuple(n)]
        v.reverse()
        v[7] |= (sum(v[:8]) % 5) << 1
        v[15] |= (sum(v[8:]) % 5) << 1
        v.reverse()
        
        return '00' + ''.join([str(x) for x in v])


class SASHost(object):
    pass
