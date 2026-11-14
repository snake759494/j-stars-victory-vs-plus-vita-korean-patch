"""texget.get(idx) -> (orig_sub rgba, t)  from work/base using inventory"""
import os, json, re, functools
from cpk import CPK
import pakedit, srd, dxt
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
INV = json.load(open(os.path.join(R, 'work/img/inventory.json')))
INV2 = json.load(open(os.path.join(R, 'work/img2/inventory.json')))
@functools.lru_cache(8)
def _pak(c, name):
    k = CPK(os.path.join(R, 'work/base/partition_op_%s_vita.cpk' % c)); by = {e['name']: e for e in k.files}
    m = k.read(by[name]); v = k.read(by[name[:-6] + '_v.pak']); k.f.close()
    M, V = {}, {}
    pakedit.rebuild(m, lambda p, d: M.__setitem__(p, d) if p.endswith('.srd') else None)
    pakedit.rebuild(v, lambda p, d: V.__setitem__(p, d) if p.endswith('.srdv') else None)
    return M, V
def get(i, inv=None):
    it = (inv or INV)[i]; M, V = _pak(it['cpk'], it['pak'])
    t = srd.textures(M[it['path']])[it['idx']]
    VK = {pakedit.mvkey(k): k for k in V}
    d = V[VK[pakedit.mvkey(it['path'])]]; o, s, _ = t['res'][0]
    a, sw = dxt.decode_tex(d[o:o + s], t)
    return a[:t['h'], :t['w']].copy(), t
