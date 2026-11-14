import sys, os, re, json
sys.path.insert(0, os.path.dirname(__file__))
from cpk import CPK
import scmp, stpk, srd
R = os.path.join(os.path.dirname(__file__), '..')
known = set()
for p in ('work/img/inventory.json', 'work/img2/inventory.json'):
    for x in json.load(open(os.path.join(R, p))): known.add((x['pak'], x['path'], x['idx']))
out = []
def walk(d, path, pak):
    if d[:4] == b'$CMP':
        try: d = scmp.decompress(d)
        except Exception: return
    if d[:4] == b'KPTS':
        for e in stpk.parse(d): walk(e['data'], path + '/' + e['name'], pak)
    elif d[:4] == b'$CFH' or path.endswith(('.srd', '.stx', '.spr')):
        try: ts = srd.textures(d)
        except Exception: return
        for i, t in enumerate(ts):
            if (pak, path, i) not in known: out.append((pak, path, i, t['name'], t['w'], t['h'], t['fmt']))
for c in (sys.argv[1].split(',') if len(sys.argv) > 1 else ('game', 'battle', 'progress')):
    k = CPK(os.path.join(R, 'work/base/partition_op_%s_vita.cpk' % c))
    for e in k.files:
        if not re.search(r'_US', e['name']) and c == 'character' or re.search(r'_(JP|NS|CN|AS|TW|KR)(_|\.|$)', e['name']) or 'ultimate_blast' in e['name'] or 'worldmap/' in e['name']: continue
        if not e['name'].endswith('_m.pak') and not e['name'].endswith('.pak'): continue
        if e['name'].endswith('_v.pak'): continue
        walk(k.read(e), '', e['name'])
json.dump(out, open(os.path.join(R, 'work/unknown_tex_%s.json' % (sys.argv[1] if len(sys.argv) > 1 else 'all')), 'w'), indent=0)
print(len(out))
import collections
print(collections.Counter(o[0] for o in out).most_common(30))
