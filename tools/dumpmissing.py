"""dumpmissing.py unknown.json outdir : dump listed (pak,path,idx) textures to outdir with inventory (hash)"""
import sys, json, os, re, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import texget, srd, dxt, pakedit
from cpk import CPK
from PIL import Image
R = texget.R
u = [o for o in json.load(open(sys.argv[1])) if not re.search(r'_(FR|DE|IT|ES|EU)(_|\.|$)', o[0])]
out = sys.argv[2]; os.makedirs(out, exist_ok=True); inv = []; cpkof = {}
for c in ('game', 'battle', 'progress', 'character'):
    for e in CPK(os.path.join(R, 'work/base/partition_op_%s_vita.cpk' % c)).files: cpkof[e['name']] = c
for pak, path, idx, name, w, h, fmt in u:
    if 'op_ef_b' in path or path.endswith('.stx'): continue
    c = cpkof[pak]
    try:
        M, V = texget._pak(c, pak); VK = {pakedit.mvkey(k): k for k in V}
        if pakedit.mvkey(path) not in VK: continue
        t = srd.textures(M[path])[idx]; d = V[VK[pakedit.mvkey(path)]]; o, s, _ = t['res'][0]
        if t['fmt'] not in (0x0f, 0x11, 0x05, 0x01): continue
        a, _ = dxt.decode_tex(d[o:o + s], t)
    except Exception as ex: print('err', path, idx, ex); continue
    fn = os.path.join(out, '%04d.png' % len(inv)); Image.fromarray(a[:t['h'], :t['w']]).save(fn)
    inv.append(dict(cpk=c, pak=pak, path=path, idx=idx, name=name, w=t['w'], h=t['h'], fmt=t['fmt'], swz=t['swz'], png=fn, hash=hashlib.md5(open(fn, 'rb').read()).hexdigest()))
json.dump(inv, open(os.path.join(out, 'inventory.json'), 'w'), indent=0); print(len(inv))
seen = set(); sel = []
for i, x in enumerate(inv):
    if x['hash'] not in seen: seen.add(x['hash']); sel.append(i)
from PIL import ImageDraw
W = 1400; per = 40; n = 0
for s0 in range(0, len(sel), per):
    x = y = 0; rowh = 0; pos = []
    for i in sel[s0:s0 + per]:
        im = Image.open(inv[i]['png']).convert('RGBA'); sc = min(1, 330 / im.width, 130 / im.height); w, h = max(1, int(im.width * sc)), max(1, int(im.height * sc))
        if x + w + 8 > W: x = 0; y += rowh + 18; rowh = 0
        pos.append((i, im.resize((w, h)), x, y)); x += max(w, 60) + 8; rowh = max(rowh, h)
    sh = Image.new('RGB', (W, y + rowh + 20), (90, 90, 140)); dr = ImageDraw.Draw(sh)
    for i, im, x, y in pos: sh.paste(im, (x, y + 14), im); dr.text((x, y), str(i), fill=(255, 255, 0))
    sh.save(os.path.join(out, 's%02d.png' % n)); n += 1
print('uniq', len(sel), 'sheets', n)
