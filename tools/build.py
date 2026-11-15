"""Full build.  python build.py [--out DIR] [--notex]
- merges work/tr/out/*.json (+glossary) -> en->ko
- builds Korean font, replaces text leaves & textures, patches CPKs into DIR (default emu app dir)"""
import sys, os, json, re, glob, struct, collections
sys.path.insert(0, os.path.dirname(__file__))
from cpk import CPK, patch_cpk
import pakedit, fontbuild, srd, dxt, scmp, stpk, layers
import numpy as np
from PIL import Image
R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
W = os.path.join(R, 'work'); B = os.path.join(W, 'base')
OUT = os.path.join(R, 'out')
args = sys.argv[1:]
if '--out' in args: OUT = args[args.index('--out') + 1]
NOTEX = '--notex' in args
FONT_TTF = os.path.join(R, 'NanumSquareNeo-bRg.ttf')
TEX_TTF = os.path.join(R, 'NanumSquareNeo-eHv.ttf')
TEX_TTF_BODY = os.path.join(R, 'NanumSquareNeo-cBd.ttf')

# ---------- translations ----------
src = json.load(open(os.path.join(W, 'tr/all_src.json'), encoding='utf8'))
ko = {}
gl = json.load(open(os.path.join(W, 'tr/glossary.json'), encoding='utf8'))
for k, v in gl.items(): ko[int(k)] = v
for f in sorted(glob.glob(os.path.join(W, 'tr/out/*.json'))):
    for k, v in json.load(open(f, encoding='utf8')).items(): ko[int(k)] = v
for fx in ('fix.json', 'fix2.json', 'fix3.json'):
    fix = os.path.join(W, 'tr', fx)
    if os.path.exists(fix):
        for k, v in json.load(open(fix, encoding='utf8')).items(): ko[int(k)] = v
NORM = {'～': '~', '！': '!', '？': '?', '，': ',', '：': ':', '“': '"', '”': '"', '‘': "'", '’': "'", '…': '...', '·': '·', '〜': '~', '—': '-', '–': '-', '「': '"', '」': '"', '『': '"', '』': '"'}
def norm(s):
    for a, b in NORM.items(): s = s.replace(a, b)
    return s
en2ko = {}
for x in src:
    t = ko.get(x['id'])
    if t:
        if chr(92) not in x['en']: t = t.replace(chr(92) + 'n', chr(10)).replace(chr(92) + 'r', chr(13))
        en2ko[x['en']] = norm(t)
en2ko.setdefault('OFF', '끔')
print('translations', len(en2ko), '/', len(src))

# ---------- font ----------
def grab_font():
    k = CPK(os.path.join(B, 'partition_op_game_vita.cpk'))
    rd = lambda n: [k.read(e) for e in k.files if e['name'] == n][0]
    gm, gv = rd('game/resident/game_resident_US_m.pak'), rd('game/resident/game_resident_US_v.pak')
    got = {}
    def g(p, d):
        if p.endswith('op_font_US_VITA.stx') or p.endswith('op_font_US_VITA.srdv'): got[p.split('.')[-1]] = d
    pakedit.rebuild(gm, g); pakedit.rebuild(gv, g)
    return got['stx'], got['srdv']
stx, srdv = grab_font()
_, oglyphs, _ = fontbuild.parse(stx)
chars = set(re.sub(r'<[^>]*>', '', ''.join(en2ko.values())))
hangul = sorted(c for c in chars if '가' <= c <= '힣')
from fontTools.ttLib import TTFont
_cmap = TTFont(FONT_TTF).getBestCmap()
missing = sorted(c for c in chars if ord(c) not in oglyphs and not (0xac00 <= ord(c) <= 0xd7a3) and ord(c) > 0x1f and ord(c) in _cmap and ord(c) < 0x3000)
print('hangul', len(hangul), 'other new chars', ''.join(missing))
nstx, ntex, fimg = fontbuild.build(stx, srdv, ''.join(hangul) + ''.join(missing), FONT_TTF, 22)
Image.fromarray(fimg).save(os.path.join(W, 'font_built.png'))
_, nglyphs, _ = fontbuild.parse(nstx)
def adv(c):
    e = nglyphs.get(ord(c)) or nglyphs.get(0x20)
    return e[3] + e[5] + e[6]
def width(line):
    return sum(adv(c) for c in re.sub(r'<[^>]*>', '', line))

# ---------- line-width check / reflow ----------
LIMIT = {'MainModeScript': 600}
overflow = []
def fit(en, k, ctx):
    el = en.split('\n'); kl = k.split('\n')
    lim = max(width(l) for l in el) * 1.06 + 4
    cap = None
    for key, v in LIMIT.items():
        if key in ctx: cap = v
    if cap: lim = max(lim, cap)
    if all(width(l) <= lim for l in kl): return k
    if '<' in k or (chr(10) not in en and len(en) < 45):  # tags / short single-line UI: do not reflow, just report
        overflow.append((ctx, en, k)); return k
    words = ' '.join(x.strip() for x in kl).split(' ')
    lines = ['']
    for w_ in words:
        t = (lines[-1] + ' ' + w_).strip()
        if width(t) <= lim or not lines[-1]: lines[-1] = t
        else: lines.append(w_)
    if len(lines) > max(len(el), len(kl)): overflow.append((ctx, en, '\n'.join(lines)))
    return '\n'.join(lines)
ctx_of = {x['en']: x['ctx'] for x in src}
for en in list(en2ko): en2ko[en] = fit(en, en2ko[en], ctx_of.get(en,''))
with open(os.path.join(W, 'overflow.txt'), 'w', encoding='utf8') as f:
    for c, e, k in overflow: f.write('%s\n  EN: %r\n  KO: %r\n' % (c, e, k))
print('overflow', len(overflow))

# ---------- text replacement fn ----------
cnt = collections.Counter()
def tfn(path, d):
    if path.endswith('.txt') and d[:2] == b'\xff\xfe' and 'StaffRoll' not in path:
        t = d[2:].decode('utf-16le')
        core = t.rstrip('\0'); tail = t[len(core):]
        k = en2ko.get(core)
        if k is None: return None
        cnt['txt'] += 1
        return b'\xff\xfe' + (k + (tail or '\0')).encode('utf-16le')
    return None

# ---------- textures ----------
TEX = {}
if not NOTEX:
    inv = json.load(open(os.path.join(W, 'img/inventory.json')))
    import retext
    for f in sorted(glob.glob(os.path.join(W, 'img/texts_*.json'))):
        for k, v in json.load(open(f, encoding='utf8')).items():
            if not v.get('ko') or v.get('skip'): continue
            it = inv[int(k)]; v['_id'] = int(k)
            TEX[(it['cpk'], it['pak'], it['path'], it['idx'])] = v
    for sub in ('img2', 'img4', 'img5', 'img6'):
      inv2p = os.path.join(W, sub, 'inventory.json')
      if os.path.exists(inv2p):
        inv2 = json.load(open(inv2p)); byh = collections.defaultdict(list)
        for x in inv2: byh[x['hash']].append(x)
        for f in sorted(glob.glob(os.path.join(W, sub, 'texts_*.json'))):
            for k, v in json.load(open(f, encoding='utf8')).items():
                if k.startswith('_') or not v.get('ko') or v.get('skip'): continue
                for it in byh[inv2[int(k)]['hash']]:
                    TEX[(it['cpk'], it['pak'], it['path'], it['idx'])] = v
    print('textures to replace', len(TEX))
    texfix = os.path.join(W, 'img/style.json')
    STY = json.load(open(texfix, encoding='utf8')) if os.path.exists(texfix) else {}
def tex_new(key, orig, v):
    style = v.get('style', '') or ''
    if v.get('kind') == 'logo' or v['ko'].strip() == v.get('en', '').strip(): return None
    if orig.shape[1] >= 1000 and orig.shape[0] >= 600 and v.get('kind') == 'body':
        import tips, tipcaps
        i = v.get('_id')
        out = orig if i in tipcaps.NOAUTO else tips.retip(orig, norm(v['ko']), TEX_TTF, os.path.join(R, 'NanumSquareNeo-dEb.ttf'))
        return tipcaps.apply(out, i, TEX_TTF) if i in tipcaps.CAPS else out
    if v.get('box'):
        return retext.boxed(orig, norm(v['ko']), os.path.join(R, v.get('font', 'NanumSquareNeo-cBd.ttf')), v['box'])
    it = '이탤릭' in style or 'italic' in style.lower() or '기울' in style
    body = v.get('kind') == 'body' and orig.shape[0] > 60
    font = TEX_TTF_BODY if body else TEX_TTF
    return retext.smart(orig, norm(v['ko']), font, italic=0.2 if it else 0.0, kind=v.get('kind'), mode=v.get('mode'))

def process_pair(c, mname, mdata, vdata):
    """returns (new_m or None, new_v or None)"""
    nm, chm = pakedit.rebuild(mdata, tfn)
    if NOTEX or vdata is None: return (nm if chm else None), None
    keys = {k: v for k, v in TEX.items() if k[0] == c and k[1] == mname}
    if not keys: return (nm if chm else None), None
    # need srd info from m leaves
    M = {}
    def grab(p, d):
        if p.endswith('.srd') or p.endswith('.s'): M[p] = d
    pakedit.rebuild(mdata, grab)
    MK = {pakedit.mvkey(k): k for k in M}
    def vfn(p, d):
        mp = MK.get(pakedit.mvkey(p))
        if mp is None: return None
        ts = srd.textures(M[mp]); out = None
        items = []
        for (cc, pk, pp, idx), v in keys.items():
            if pp != mp: continue
            t = ts[idx]
            if t['fmt'] not in (0x11, 0x0f, 0x05, 0x01): continue
            o, s, _ = t['res'][0]
            orig, sw = dxt.decode_tex(d[o:o + s], t)
            items.append(dict(key=(cc, pk, pp, idx), v=v, t=t, sw=sw, o=o, s=s, orig=orig, sub=orig[:t['h'], :t['w']].copy()))
        grp = {}
        for it in items:
            g = (it['v'].get('group') or layers.stem(it['t']['name']), it['t']['w'], it['t']['h'], it['v']['ko'])
            grp.setdefault(g, []).append(it)
        for g, its in grp.items():
            isef = lambda x: layers.is_ef(x['t']['name']) or x['v'].get('layer') == 'glow'
            its.sort(key=lambda x: (isef(x), x['key'][3]))
            m = its[0]; m['new'] = tex_new(m['key'], m['sub'], m['v'])
            for it in its[1:]:
                if m['new'] is None or isef(m): it['new'] = tex_new(it['key'], it['sub'], it['v']); continue
                if isef(it):
                    st = it['v'].get('style', '') or ''
                    ital = 0.2 if ('이탤릭' in st or '기울' in st or 'italic' in st.lower()) else 0.0
                    it['new'] = layers.layer_from(m['sub'], m['new'], it['sub'], norm(it['v']['ko']), TEX_TTF, ital)
                else:
                    st = it['v'].get('style', '') or ''
                    ital = 0.2 if ('이탤릭' in st or '기울' in st or 'italic' in st.lower()) else 0.0
                    it['new'] = layers.variant_from(m['sub'], it['sub'], norm(it['v']['ko']), TEX_TTF, ital)
                    if it['new'] is None: it['new'] = tex_new(it['key'], it['sub'], it['v'])
        for it in items:
            new = it.get('new'); t = it['t']
            if new is None: continue
            full = it['orig'].copy(); full[:t['h'], :t['w']] = new
            enc = dxt.encode_tex(full, t, it['sw'])
            if len(enc) > it['s']: continue
            out = bytearray(out or d); out[it['o']:it['o'] + len(enc)] = enc; cnt['tex'] += 1
        return bytes(out) if out else None
    nv, chv = pakedit.rebuild(vdata, vfn)
    return (nm if chm else None), (nv if chv else None)

# ---------- per cpk ----------
os.makedirs(OUT, exist_ok=True)
TEXPAKS = set(k[1] for k in TEX)
for c in ('game', 'battle', 'progress', 'character'):
    k = CPK(os.path.join(B, 'partition_op_%s_vita.cpk' % c)); byname = {e['name']: e for e in k.files}
    repl = {}
    for e in k.files:
        if not (re.search(r'US.*_m\.pak$', e['name']) or e['name'] in TEXPAKS): continue
        vn = e['name'][:-6] + '_v.pak'
        md = k.read(e); vd = k.read(byname[vn]) if vn in byname else None
        nm, nv = process_pair(c, e['name'], md, vd)
        if e['name'] == 'game/resident/game_resident_US_m.pak':
            nm, _ = pakedit.rebuild(nm or md, lambda p, d: nstx if p.endswith('op_font_US_VITA.stx') else None)
            nv, _ = pakedit.rebuild(nv or vd, lambda p, d: ntex if p.endswith('op_font_US_VITA.srdv') else None)
        if nm: repl[e['name']] = nm
        if nv: repl[vn] = nv
    k.f.close()
    print(c, 'files replaced', len(repl), dict(cnt))
    if repl: patch_cpk(os.path.join(B, 'partition_op_%s_vita.cpk' % c), os.path.join(OUT, 'partition_op_%s_vita.cpk' % c), repl)
print('done', dict(cnt))
