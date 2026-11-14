"""ext.py <cpkname> <pattern> <outdir> : extract files whose name contains pattern"""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
from cpk import CPK
A = os.path.join(os.path.dirname(__file__), '..', 'work/base')
c = CPK(os.path.join(A, 'partition_op_%s_vita.cpk' % sys.argv[1]))
rx = re.compile(sys.argv[2]); out = sys.argv[3]
n = 0
for e in c.files:
    if rx.search(e['name']):
        p = os.path.join(out, e['name']); os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'wb').write(c.read(e)); n += 1
print(n, 'files')
