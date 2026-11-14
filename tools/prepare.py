"""Prepare work/ for tools/build.py from the repository data and the user's original CPKs.

usage: python tools/prepare.py   (original CPKs must be in work/base/)
- text/ko.json ({'<inner pak>/<txt>': Korean}) + original text read from work/base -> work/tr/all_src.json, work/tr/out/ko.json
- text/images/<set>/* -> work/<set>/
"""
import os, sys, json, shutil, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcmap
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); W = os.path.join(R, 'work')
base = os.path.join(W, 'base')
for c in ('game', 'battle', 'progress', 'character'):
    if not os.path.exists(os.path.join(base, 'partition_op_%s_vita.cpk' % c)): sys.exit('work/base/partition_op_%s_vita.cpk 가 없습니다.' % c)
ko = json.load(open(os.path.join(R, 'text/ko.json'), encoding='utf8'))
m = srcmap.collect(base)
src, out = [], {}
for i, (ctx, k) in enumerate(ko.items()):
    if ctx not in m: print('원문 없음:', ctx); continue
    src.append(dict(id=i, ctx=ctx, en=m[ctx])); out[str(i)] = k
os.makedirs(os.path.join(W, 'tr/out'), exist_ok=True)
json.dump(src, open(os.path.join(W, 'tr/all_src.json'), 'w', encoding='utf8'), ensure_ascii=False)
json.dump(out, open(os.path.join(W, 'tr/out/ko.json'), 'w', encoding='utf8'), ensure_ascii=False)
json.dump({}, open(os.path.join(W, 'tr/glossary.json'), 'w'))
for d in glob.glob(os.path.join(R, 'text/images/*')):
    t = os.path.join(W, os.path.basename(d)); os.makedirs(t, exist_ok=True)
    for f in glob.glob(os.path.join(d, '*.json')): shutil.copy(f, t)
print('텍스트', len(src), '준비 완료')
