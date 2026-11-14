"""Dump all textures of *US* m/v pak pairs to PNG. texdump.py outdir [regex]"""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(__file__))
from cpk import CPK
import scmp, stpk, srd, dxt
import numpy as np
from PIL import Image
B = os.path.join(os.path.dirname(__file__), '..', 'work', 'base')
out = sys.argv[1]; rx = re.compile(sys.argv[2] if len(sys.argv) > 2 else r'US.*_m\.pak$')
def leaves(d, path, acc):
    if d[:4] == b'$CMP': d = scmp.decompress(d)
    if d[:4] == b'KPTS':
        for e in stpk.parse(d): leaves(e['data'], path + '/' + e['name'], acc)
    else: acc[path] = d
inv = []
for c in (sys.argv[3].split(',') if len(sys.argv) > 3 else ('game', 'battle', 'progress', 'character')):
    k = CPK(os.path.join(B, 'partition_op_%s_vita.cpk' % c)); byname = {e['name']: e for e in k.files}
    for e in k.files:
        if not rx.search(e['name']): continue
        vn = e['name'][:-6] + '_v.pak'
        if vn not in byname: continue
        M = {}; V = {}
        leaves(k.read(e), '', M); leaves(k.read(byname[vn]), '', V)
        import pakedit
        vmap = {pakedit.mvkey(p): d for p, d in V.items()}
        for p, d in M.items():
            if not p.endswith('.srd'): continue
            vd = vmap.get(pakedit.mvkey(p))
            if vd is None: continue
            try: ts = srd.textures(d)
            except Exception as ex: print('ERR', p, ex); continue
            for i, t in enumerate(ts):
                o, s, _ = t['res'][0]
                try: a = dxt.decode_rgba(vd[o:o + s], t['w'], t['h'], t['fmt'], t['swz'] != 0 or t['fmt'] == 0x0f)
                except Exception as ex: print('ERRT', p, t['fmt'], ex); continue
                fn = os.path.join(out, c, e['name'].split('/')[-1][:-6], p.strip('/').replace('/', '__') + '__%d_%s.png' % (i, t['name'].replace('/', '_')))
                os.makedirs(os.path.dirname(fn), exist_ok=True)
                Image.fromarray(a[:t['h'], :t['w']]).save(fn)
                inv.append(dict(cpk=c, pak=e['name'], path=p, idx=i, name=t['name'], w=t['w'], h=t['h'], fmt=t['fmt'], swz=t['swz'], png=fn))
json.dump(inv, open(os.path.join(out, 'inventory.json'), 'w'), indent=0)
print(len(inv))
