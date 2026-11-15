"""Spike Chunsoft $CMP container (J-Stars Vita) decoder / encoder"""
import struct, sys

def lz_dec(data, shift=6):
    res = bytearray(); p = 0; mask = (1 << shift) - 1
    while p < len(data):
        b = data[p]; p += 1
        if b & 1:
            cnt = (b & mask) >> 1; off = ((b >> shift) << 8) | data[p]; p += 1
            for _ in range(cnt): res.append(res[-off])
        else:
            cnt = b >> 1; res += data[p:p + cnt]; p += cnt
    return bytes(res)

def huff_dec(blk):
    # blk starts with $CH0
    assert blk[:4] == b'$CH0'
    dsz, csz, n = struct.unpack('>III', blk[4:16])
    tab = {}
    for i in range(n):
        b0, b1, b2, sym = blk[16 + 4 * i:20 + 4 * i]
        ln = b2 >> 3; code = b0 | (b1 << 8) | ((b2 & 7) << 16)
        tab[(ln, code)] = sym
    if n == 1: return bytes([blk[19]]) * dsz
    data = blk[16 + 4 * n:csz]
    out = bytearray(); code = 0; ln = 0
    for byte in data:
        for k in range(7, -1, -1):
            code = (code << 1) | ((byte >> k) & 1); ln += 1
            s = tab.get((ln, code))
            if s is not None:
                out.append(s); code = 0; ln = 0
                if len(out) == dsz: return bytes(out)
    return bytes(out)

def decompress(b):
    assert b[:4] == b'$CMP', b[:4]
    total = struct.unpack('>I', b[0x10:0x14])[0]
    p = 0x20; out = bytearray()
    while len(out) < total and p < len(b):
        tag = b[p:p + 4]; dsz, csz, extra = struct.unpack('>III', b[p + 4:p + 16])
        if tag == b'$CL0':
            out += lz_dec(b[p + 16:p + csz]); p += csz
        elif tag == b'$CLH':
            c = huff_dec(b[p + 16:p + csz]); assert c[:4] == b'$CL0'
            out += lz_dec(c[16:]); p += csz
        elif tag == b'$CH0':
            out += huff_dec(b[p:p + csz]); p += csz
        elif tag == b'$CR0':
            out += b[p + 16:p + 16 + dsz]; p += 16 + dsz
        else:
            raise ValueError('tag %r at %x' % (tag, p))
    return bytes(out)

import numpy as _np
try:
    from numba import njit as _njit
except ImportError:  # pure-python fallback (slow)
    def _njit(*a, **k):
        return (lambda f: f) if not (a and callable(a[0])) else a[0]

@_njit(cache=True)
def _find(src, i, n, head, prev, HB):
    best = 0; boff = 0
    if i + 2 >= n: return 0, 0
    h = ((int(src[i]) << 8) ^ (int(src[i + 1]) << 4) ^ int(src[i + 2])) & (HB - 1)
    j = head[h]; tries = 0
    while j >= 0 and i - j <= 1023 and tries < 256:
        l = 0
        while l < 31 and i + l < n and src[j + l] == src[i + l]:
            l += 1
        if l > best:
            best = l; boff = i - j
            if l == 31: break
        j = prev[j]; tries += 1
    return best, boff

@_njit(cache=True)
def _ins(src, p, n, head, prev, HB):
    if p + 2 < n:
        hh = ((int(src[p]) << 8) ^ (int(src[p + 1]) << 4) ^ int(src[p + 2])) & (HB - 1)
        prev[p] = head[hh]; head[hh] = p

@_njit(cache=True)
def _lz_enc(src, out):
    """$CL0 LZ: literal run b=cnt<<1 (cnt<=127); copy b=((off>>8)<<6)|(cnt<<1)|1, next=off&255 (off<=1023, 3<=cnt<=31)"""
    n = src.shape[0]; HB = 8192
    head = _np.full(HB, -1, _np.int64); prev = _np.full(n, -1, _np.int64); ins = _np.zeros(n, _np.uint8)
    o = 0; lit0 = 0; i = 0
    while i < n:
        best, boff = _find(src, i, n, head, prev, HB)
        if best >= 3 and best < 31 and i + 1 < n:
            if not ins[i]:
                _ins(src, i, n, head, prev, HB); ins[i] = 1
            b2, o2 = _find(src, i + 1, n, head, prev, HB)
            if b2 > best:
                i += 1; best = b2; boff = o2
        if best >= 3:
            k = lit0
            while k < i:
                c = min(127, i - k); out[o] = c << 1; o += 1
                for t in range(c):
                    out[o] = src[k + t]; o += 1
                k += c
            out[o] = ((boff >> 8) << 6) | (best << 1) | 1; out[o + 1] = boff & 255; o += 2
            for t in range(best):
                if not ins[i + t]:
                    _ins(src, i + t, n, head, prev, HB); ins[i + t] = 1
            i += best; lit0 = i
        else:
            if not ins[i]:
                _ins(src, i, n, head, prev, HB); ins[i] = 1
            i += 1
    k = lit0
    while k < n:
        c = min(127, n - k); out[o] = c << 1; o += 1
        for t in range(c):
            out[o] = src[k + t]; o += 1
        k += c
    return o

def lz_enc(c):
    a = _np.frombuffer(bytes(c), _np.uint8)
    out = _np.zeros(len(a) + len(a) // 64 + 16, _np.uint8)
    return out[:_lz_enc(a, out)].tobytes()

@_njit(cache=True)
def _hpack(data, codes, lens, out):
    o = 0; acc = 0; nb = 0
    for i in range(data.shape[0]):
        s = data[i]; acc = (acc << lens[s]) | codes[s]; nb += lens[s]
        while nb >= 8:
            nb -= 8; out[o] = (acc >> nb) & 255; o += 1
        acc &= (1 << nb) - 1
    if nb:
        out[o] = (acc << (8 - nb)) & 255; o += 1
    return o

def _hlens(freq, maxlen=15):
    import heapq
    syms = [i for i in range(256) if freq[i]]
    if len(syms) == 1: return {syms[0]: 1}
    hp = [(freq[s], k, (s,)) for k, s in enumerate(syms)]; heapq.heapify(hp); L = {s: 0 for s in syms}; k = 256
    while len(hp) > 1:
        a = heapq.heappop(hp); b = heapq.heappop(hp)
        for s in a[2] + b[2]: L[s] += 1
        heapq.heappush(hp, (a[0] + b[0], k, a[2] + b[2])); k += 1
    while max(L.values()) > maxlen:  # simple length limiting via Kraft repair
        for s in L:
            if L[s] > maxlen: L[s] = maxlen
        while sum(2.0 ** -l for l in L.values()) > 1:
            s = max((x for x in L if L[x] < maxlen), key=lambda x: (L[x], -freq[x])); L[s] += 1
    return L

def huff_enc(blk):
    """$CH0 block encoding blk (canonical Huffman, entries in descending length)"""
    a = _np.frombuffer(bytes(blk), _np.uint8)
    freq = _np.bincount(a, minlength=256)
    L = _hlens(freq)
    order = sorted(L, key=lambda s: (L[s], s)); code = 0; prev = L[order[0]]; C = {}
    for s in order:
        code <<= (L[s] - prev); prev = L[s]; C[s] = code; code += 1
    codes = _np.zeros(256, _np.int64); lens = _np.zeros(256, _np.int64)
    for s in L: codes[s] = C[s]; lens[s] = L[s]
    out = _np.zeros(len(a) * 2 + 16, _np.uint8); n = _hpack(a, codes, lens, out)
    ents = bytearray()
    for s in sorted(L, key=lambda s: (-L[s], -C[s])):
        c = C[s]; ents += bytes([c & 255, (c >> 8) & 255, (L[s] << 3) | ((c >> 16) & 7), s])
    body = bytes(ents) + out[:n].tobytes()
    return b'$CH0' + struct.pack('>III', len(blk), 16 + len(body), len(L)) + body

def compress(raw):
    """$CL0 chunks (0x3c00 each) with real LZ, wrapped in $CLH (Huffman) when smaller"""
    chunks = bytearray()
    for i in range(0, len(raw), 0x3c00):
        c = raw[i:i + 0x3c00]; lz = lz_enc(c)
        cl0 = b'$CL0' + struct.pack('>III', len(c), len(lz) + 16, 0) + lz
        ch = huff_enc(cl0)
        if 16 + len(ch) < len(cl0):
            chunks += b'$CLH' + struct.pack('>III', len(c), 16 + len(ch), len(cl0)) + ch
        else:
            chunks += cl0
    cl = len(chunks) + 0x10
    hdr = b'$CMP' + struct.pack('>III', cl, 0, 0) + struct.pack('>IIII', len(raw), cl, 0, 0x000f0000)
    out = hdr + bytes(chunks)
    return out + bytes((-len(out)) % 16)

if __name__ == '__main__':
    d = decompress(open(sys.argv[1], 'rb').read())
    open(sys.argv[2], 'wb').write(d); print(len(d))
