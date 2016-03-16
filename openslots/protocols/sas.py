"""Implement IGT's Slot Accounting System protocol"""


import os


___SAS_version___ = 602     # SAS version 6.02
"""int: current SAS version defined in this module"""


## Supported meters ##


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
    (0x22, 4, 'total_win', 'Sum of total coin out and total jackpot'),
    (0x23, 4, 'total_handpay', 'Sum of total hand paid canceled credits and '
     'total jackpot'),
    (0x24, 4, 'total_drop', 'Including but not limited to coins to drop, bills '
     'to drop, tickets to drop, and EFT in'),
    (0x25, 4, 'games_since_power_on', 'Games since last power reset'),
    (0x26, 4, 'games_since_door_close', 'Games since last slot door closure'),
    (0x27, 4, 'ext_coin_acc_in', 'Total credits from external coin acceptor'),
    (0x28, 4, 'cashable_tkt_in', 'Total cashable ticket in, including '
     'nonrestricted promo credits'),
    (0x29, 4, 'regular_tkt_in', 'Total regular cashable ticket in'),
    (0x2a, 4, 'restr_tkt_in', 'Total restricted promo ticket in'),
    (0x2b, 4, 'nrestr_tkt_in', 'Total nonrestricted promo ticket in'),
    (0x2c, 4, 'cashable_tkt_out', 'Total cashable ticket out, including debit'),
    (0x2d, 4, 'restr_tkt_out', 'Total restricted promo ticket out'),
    (0x2e, 4, 'cashable_eft_in', 'Electronic regular cashable transfers to '
     'gaming machine, not including external bonus awards'),
    (0x2f, 4, 'restr_eft_in', 'Electronic restricted promo transfers to gaming '
     'machine, not including external bonus awards'),
    (0x30, 4, 'nrestr_eft_in', 'Electronic nonrestricted promo transfers to '
     'gaming machine, not including external bonus awards'),
    (0x31, 4, 'debit_eft_in', 'Electronic debit transfers to gaming machine'),
    (0x32, 4, 'cashable_eft_out', 'Electronic regular cashable transfers to host'),
    (0x33, 4, 'restr_eft_out', 'Electronic restricted promo transfers to host'),
    (0x34, 4, 'nrestr_eft_out', 'Electronic nonrestricted promo transfers to host'),
    (0x35, 4, 'num_tkt_in', 'Quantity of regular cashable tickets in'),
    (0x36, 4, 'num_restr_in', 'Quantity of ')
]
"""list: Meters defined by version 6.02 of the SAS protocol.

This is a list of tuples (meter ID, BCD length, meter name, meter description,
and optional boolean whether this meter can be decremented). Used for generating
SASMeter objects during SASGame initialization.
"""


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

    def __init__(self, i, size=4, current=False, nvdir=None):
        self.id = int(i)
        self.__len__ = lambda: int(size)
        self._name = ''
        self.description = ''
        self._current = current

        if nvdir is not None:
            # set up non-volatile meter storage
            self._nv_fname = os.path.normpath(nvdir + os.path.sep + str(i))
            if os.path.isfile(self._nv_fname):
                with open(self._nv_fname, 'r') as nvfile:
                    self._value = int(nvfile.read())
            else:
                self._value = 0
                with open(self._nv_fname, 'x') as nvfile:
                    nvfile.write(str(self._value))
        else:
            self._nv_fname = None

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
        self._update_nvfile()

    def clear(self):
        del self.value

    def _update_nvfile(self):
        if self._nv_fname is not None:
            with open(self._nv_fname, 'w') as nvfile:
                nvfile.write(str(self._value))

    def __repr__(self):
        temp = "<SASMeter {:#06x} {}, value {}>"
        return temp.format(self.id, self.name, str(self))

    def __str__(self):
        return str(self.value).rjust(self.__len__() * 2, '0')

    def __bytes__(self):
        return int_to_bcd(self.value, self.__len__())

    def __iadd__(self, n):
        self._value += n if n > 0 else 0
        self._update_nvfile()
        return self

    def __isub__(self, n):
        if self._current:
            self._value -= n if n > 0 else 0
            if self._value < 0:
                self._value = 0
        self._update_nvfile()
        return self

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)


class SASGame(object):
    def __init__(self, meters=_602_meters, nvdir=None):
        self._v_id = 0
        self._v_seq = 0

        self._meters = meters
        self.nvdir = nvdir
        self.clear_meters()

    def clear_meters(self):
        """Initialize all meters to 0"""

        self.meters = dict()
        for m in self._meters:
            this_m = SASMeter(m[0], m[1], m[-1] if len(m) == 5 else False,
                              nvdir=self.nvdir)
            this_m.name = m[2]
            this_m.description = m[3]

            setattr(self, this_m.name, this_m)
            self.meters[this_m.id] = this_m

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
