"""SRD block parser + texture list"""
import struct, sys

def blocks(d, off=0, end=None):
    end = len(d) if end is None else end; out = []
    while off + 16 <= end:
        tag = d[off:off + 4]; ds, ss, unk = struct.unpack('>III', d[off + 4:off + 16])
        dp = off + 16; sp = dp + ds + ((-ds) % 16)
        out.append(dict(tag=tag, off=off, data=(dp, ds), sub=(sp, ss), unk=unk))
        off = sp + ss + ((-ss) % 16)
    return out

def textures(d):
    res = []
    for b in blocks(d):
        if b['tag'] != b'$TXR': continue
        dp, ds = b['data']; sp, ss = b['sub']
        unk1, swz, w, h, scan, fmt, u2, pal, palid = struct.unpack('<IHHHHBBBB', d[dp:dp + 16])
        for sb in blocks(d, sp, sp + ss):
            if sb['tag'] != b'$RSI': continue
            rp, rs = sb['data']; r = d[rp:rp + rs]
            n = r[4] if False else struct.unpack('<I', r[4:8])[0]
            nres = r[5] if False else None
            # resources table starts at 0x10, each 16 bytes, count = r[2]? use (byte 2) heuristically
            cnt = r[2] if r[0] == 6 else 1
            ress = []
            for i in range(max(1, r[3] if False else 1)):
                a, s, x, y = struct.unpack('<IIII', r[0x10 + 16 * i:0x20 + 16 * i])
                ress.append((a & 0x0fffffff, s, a >> 28))
            nm_off = struct.unpack('<I', r[0x0c:0x10])[0]
            name = r[nm_off:r.index(b'\0', nm_off)].decode('latin1') if nm_off < len(r) else ''
            res.append(dict(off=b['off'], fmt=fmt, w=w, h=h, swz=swz, scan=scan, res=ress, name=name, rsi=r[:16].hex()))
    return res

if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    for b in blocks(d): print(b['tag'], b['data'], b['sub'])
    for t in textures(d): print(t)
