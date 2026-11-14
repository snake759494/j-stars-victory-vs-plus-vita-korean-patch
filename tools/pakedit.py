"""Recursive pak rebuild. rebuild(data, fn, path) ; fn(path, leaf_bytes) -> new bytes or None"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import scmp, stpk

def rebuild(d, fn, path=''):
    """returns (new_bytes, changed)"""
    comp = d[:4] == b'$CMP'
    raw = scmp.decompress(d) if comp else d
    if raw[:4] == b'KPTS':
        ents = stpk.parse(raw); ch = False
        for i, e in enumerate(ents):
            nd, c = rebuild(e['data'], fn, path + '/' + e['name'])
            if c: e['data'] = nd; ch = True
        if not ch: return d, False
        raw = stpk.build(ents)
    else:
        nd = fn(path, raw)
        if nd is None: return d, False
        raw = nd
    return (scmp.compress(raw) if comp else raw), True

import re as _re
def mvkey(p):
    """normalise an m-pak or v-pak leaf path so that pairs (incl. 32-char truncated names) compare equal"""
    segs = []
    for s in p.split('/'):
        if s.endswith('.srdv'): s = s[:-1]
        s = _re.sub(r'_[mv](?=\.(p(a(k)?)?)?$)', '_X', s)
        segs.append(s)
    return '/'.join(segs)
