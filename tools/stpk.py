import struct, sys

def parse(d):
    assert d[:4] == b'KPTS', d[:4]
    ver, n, al = struct.unpack('<III', d[4:16])
    ents = []
    for i in range(n):
        o = 16 + i * 0x30
        off, sz, a, b = struct.unpack('<IIII', d[o:o + 16])
        name = d[o + 16:o + 0x30].split(b'\0')[0].decode()
        ents.append(dict(name=name, off=off, size=sz, a=a, b=b, data=d[off:off + sz], align=al))
    return ents

def build(ents, align=None):
    """rebuild keeping the original alignment (0x40 for _m paks, 0x1000 for texture _v paks)"""
    if align is None: align = ents[0].get('align', 0x40) if ents else 0x40
    n = len(ents); hdr = bytearray(b'KPTS' + struct.pack('<III', 1, n, align))
    pos = 16 + n * 0x30; pos = (pos + align - 1) // align * align
    body = bytearray(); offs = []
    for e in ents:
        offs.append(pos + len(body)); body += e['data']
        while len(body) % align: body += b'\0'
    for e, o in zip(ents, offs):
        hdr += struct.pack('<IIII', o, len(e['data']), e['a'], e['b']) + e['name'].encode().ljust(0x20, b'\0')
    while len(hdr) % align: hdr += b'\0'
    return bytes(hdr + body)

if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    for e in parse(d): print(hex(e['off']), hex(e['size']), e['a'], e['b'], e['name'], e['data'][:8])
