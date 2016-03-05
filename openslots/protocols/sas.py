"""Implement IGT's Slot Accounting System protocol"""


from collections import namedtuple, Counter


___SAS_version___ = 602     # SAS version 6.02


def crc(b, seed=0):
    """Compute 16-bit CRC from bytes or sequence of ints, returns bytes"""
    for x in b:
        q = (seed ^ x) & 0o17
        seed = (seed >> 4) ^ (q * 0o10201)
        q = (seed ^ (x >> 4)) & 0o17
        seed = (seed >> 4) ^ (q * 0o10201)
    return (seed).to_bytes(2, byteorder='little')


SASByte = namedtuple('SASByte', ['x', 'addr'])


class SASGame(object):
    def __init__(self):
        self._meters = Counter()
        self._v_id = 0
        self._v_seq = 0

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
