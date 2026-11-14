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

def compress(raw):
    """store as $CL0 chunks with literal-only LZ (always valid)"""
    chunks = bytearray()
    for i in range(0, len(raw), 0x3c00):
        c = raw[i:i + 0x3c00]; lz = bytearray()
        for j in range(0, len(c), 0x7f):
            s = c[j:j + 0x7f]; lz.append(len(s) << 1); lz += s
        chunks += b'$CL0' + struct.pack('>III', len(c), len(lz) + 16, 0) + lz
    cl = len(chunks) + 0x10
    hdr = b'$CMP' + struct.pack('>III', cl, 0, 0) + struct.pack('>IIII', len(raw), cl, 0, 0x000f0000)
    out = hdr + bytes(chunks)
    return out + bytes((-len(out)) % 16)

if __name__ == '__main__':
    d = decompress(open(sys.argv[1], 'rb').read())
    open(sys.argv[2], 'wb').write(d); print(len(d))
