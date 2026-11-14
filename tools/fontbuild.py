"""Rebuild op_font_US_VITA.stx (SRD/$TXR/$RSI/SpFt) + .srdv with extra Korean glyphs.
build(stx, srdv, chars, ttf, size) -> (new_stx, new_srdv)"""
import struct, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
import dxt

BASE = 0x20  # first code point of bitfield

def parse(stx):
    sp = stx.index(b'SpFt'); f = stx[sp:]
    ver, rng, unk, name_off, n, tab_off, size = struct.unpack('<IIIIIII', f[4:32])
    bm_off, lh, bl = struct.unpack('<IHH', f[32:40])
    nb = (tab_off - 0x30 - 4) // 2
    bits = f[0x30:0x30 + nb]
    chars = [BASE + i for i in range(nb * 8) if bits[i >> 3] >> (i & 7) & 1]
    ents = [f[tab_off + 8 * i:tab_off + 8 * i + 8] for i in range(n)]
    assert len(chars) == n, (len(chars), n)
    return sp, dict(zip(chars, ents)), f

def entry(x, y, w, h, l, r, yo):
    return bytes([x & 255, (x >> 8) & 15 | (y & 15) << 4, y >> 4, w, h, l & 255, r & 255, yo & 255])

def build(stx, srdv, chars, ttf, size, W=2048, baseline=24, pad=2, start_y=88, fixed_h=None):
    sp, glyphs, f = parse(stx)
    bits = bytearray((struct.unpack('<I', f[0x18:0x1c])[0] - 0x34) // 2)
    ver, rng, unk, name_off, n, tab_off, fsize = struct.unpack('<IIIIIII', f[4:32])
    oh = struct.unpack('<H', stx[0x28:0x2a])[0]  # original texture height (logical)
    old = dxt.decode(srdv, 2048, 128)
    font = ImageFont.truetype(ttf, size)
    new = sorted(c for c in set(ord(c) for c in chars) - set(glyphs) if 0 <= c - BASE < len(bits) * 8)
    # pack
    placed = {}; x = 0; y = start_y; rowh = 0
    for cp in new:
        ch = chr(cp)
        x0, y0, x1, y1 = font.getbbox(ch, anchor='ls')
        adv = font.getlength(ch)
        if x1 <= x0: x0 = x1 = 0
        w = x1 - x0; h = y1 - y0
        if x + w + pad > W: x = 0; y += rowh + pad; rowh = 0
        placed[cp] = (x, y, w, h, x0, y0, adv)
        x += w + pad; rowh = max(rowh, h)
    used_h = y + rowh + pad
    H = 128
    while H < used_h: H *= 2
    if fixed_h: H = fixed_h
    img = np.zeros((H, W), np.uint8); img[:128, :] = old[:128, :]
    canvas = Image.fromarray(img); dr = ImageDraw.Draw(canvas)
    for cp, (x, y, w, h, x0, y0, adv) in placed.items():
        if w: dr.text((x - x0, y - y0), chr(cp), fill=255, font=font, anchor='ls')
        l = int(round(x0)); r = int(round(adv - x1_of(x0, w)))
        glyphs[cp] = entry(x, y, w, h, max(l, 0), max(r, 0), baseline + y0)
    img = np.array(canvas)
    # SpFt
    allc = sorted(glyphs); N = len(allc)
    bits = bytearray(len(bits))
    for c in allc: i = c - BASE; bits[i >> 3] |= 1 << (i & 7)
    words = struct.unpack('<%dI' % (len(bits) // 4), bits)
    pref = []; acc = 0
    for wv in words: pref.append(acc); acc += bin(wv).count('1')
    pref = [0] + pref
    prefb = struct.pack('<%dI' % len(pref), *pref)
    assert 0x30 + len(bits) + len(prefb) == tab_off, hex(0x30 + len(bits) + len(prefb))
    tab = b''.join(glyphs[c] for c in allc)
    new_bm = tab_off + 8 * N; new_name = new_bm + 16
    name = f[name_off:fsize] if False else f[name_off:name_off + f[name_off:].index(b'\0\0\0') + 3]
    name = name + b'\0' * ((len(name)) % 2)
    hdr = bytearray(f[:0x30])
    struct.pack_into('<I', hdr, 0x10, new_name); struct.pack_into('<I', hdr, 0x14, N)
    struct.pack_into('<I', hdr, 0x28, new_bm)
    spft = bytes(hdr) + bytes(bits) + prefb + tab + struct.pack('<IIII', new_name, new_name, new_name, new_name) + f[name_off:name_off + 24]
    # RSI
    rsi_start = stx.index(b'$RSI'); rsi = stx[rsi_start + 16:]
    r_hdr = bytearray(rsi[:0x30])
    old_len = struct.unpack('<I', rsi[0x28:0x2c])[0]
    strs = rsi[0x30 + old_len:struct.unpack('>I', stx[rsi_start + 4:rsi_start + 8])[0]]
    # name offsets: res name at 0x0c, subresource name at 0x20
    struct.pack_into('<I', r_hdr, 0x28, len(spft))
    struct.pack_into('<I', r_hdr, 0x0c, 0x30 + len(spft))
    struct.pack_into('<I', r_hdr, 0x20, 0x30 + len(spft) + 0x14)
    tex = dxt.encode(img)
    struct.pack_into('<I', r_hdr, 0x14, len(tex))
    rsi_data = bytes(r_hdr) + spft + strs
    def blk(tag, data, sub=b''):
        p = lambda b: b + b'\0' * ((-len(b)) % 16)
        return tag + struct.pack('>III', len(data), len(sub), 0) + p(data) + p(sub)
    ct0 = b'$CT0' + b'\0' * 12
    txr_data = bytearray(stx[0x20:0x30])
    struct.pack_into('<HH', txr_data, 6, W, H)  # width, height
    sub = blk(b'$RSI', rsi_data) + ct0
    out = stx[:0x10] + blk(b'$TXR', bytes(txr_data), sub) + ct0
    return out, tex, img

def x1_of(x0, w): return x0 + w

if __name__ == '__main__':
    stx = open(sys.argv[1], 'rb').read(); srdv = open(sys.argv[2], 'rb').read()
    chars = open(sys.argv[3], encoding='utf8').read()
    o, t, img = build(stx, srdv, chars, sys.argv[4], int(sys.argv[5]))
    open(sys.argv[6], 'wb').write(o); open(sys.argv[7], 'wb').write(t)
    Image.fromarray(img).save(sys.argv[7] + '.png'); print(len(o), len(t), img.shape)
