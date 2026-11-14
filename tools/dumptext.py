"""Dump all UTF-16 .txt leaves in *US*_m.pak -> work/text_us.tsv (key \\t text)"""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(__file__))
from cpk import CPK
import scmp, stpk
A = os.path.join(os.path.dirname(__file__), '..', 'work/base')
rx = re.compile(r'US.*_m\.pak$')
rows = []
def walk(d, path):
    if d[:4] == b'$CMP': d = scmp.decompress(d)
    if d[:4] == b'KPTS':
        for i, e in enumerate(stpk.parse(d)): walk(e['data'], path + '/' + str(i) + ':' + e['name'])
    elif path.endswith('.txt') and d[:2] == b'\xff\xfe':
        t = d[2:].decode('utf-16le').rstrip('\0')
        if t: rows.append((path, t))
for c in ('game', 'battle', 'map', 'progress', 'character'):
    k = CPK(os.path.join(A, 'partition_op_%s_vita.cpk' % c) if c in ('game','progress','battle','character') else os.path.join(A,'..','..','emu/fs/ux0/app/PCSE00595/data/VITA','partition_op_%s_vita.cpk' % c))
    for e in k.files:
        if rx.search(e['name']): walk(k.read(e), c + ':' + e['name'])
json.dump(rows, open(sys.argv[1], 'w', encoding='utf8'), ensure_ascii=False, indent=0)
print(len(rows))
