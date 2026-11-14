"""Rebuild {ctx: english} from the user's original CPKs (work/base). ctx = '<inner pak>/<txt name>'."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cpk import CPK
import scmp, stpk
def collect(base):
    out = {}
    def walk(d, names):
        if d[:4] == b'$CMP': d = scmp.decompress(d)
        if d[:4] == b'KPTS':
            for e in stpk.parse(d): walk(e['data'], names + [e['name']])
        elif names and names[-1].endswith('.txt') and d[:2] == b'\xff\xfe':
            t = d[2:].decode('utf-16le').rstrip('\0')
            if t: out.setdefault('/'.join(names[-2:]), t)
    for c in ('game', 'battle', 'progress', 'character'):
        k = CPK(os.path.join(base, 'partition_op_%s_vita.cpk' % c))
        for e in k.files:
            if re.search(r'US.*_m\.pak$', e['name']): walk(k.read(e), [os.path.basename(e['name'])])
    return out
