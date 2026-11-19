#!/usr/bin/env python3
# Copyright 2026 James Barlow
# SPDX-License-Identifier: Apache-2.0
# AI-assisted (Claude, Anthropic), under the repository owner's direction.
"""Quantum Voodoo pass (card C48): replace the 20-Toffoli GF(2^6) clean-inverse leaf by R's 19-Toffoli leaf in a DQI
circuit WE generated (e.g. Syed Asad Ali's v12 builder run from source), at every site whose 16 output/helper wires are
statically clean at entry. Writes a `qhdl edit` script; the edit itself is `qhdl edit`.

    python3 scripts/qv_inverse19_pass.py TARGET.kmb OLD_TEMPLATE.kmb NEW_LEAF.kmb OUT_DIR [--all]

1. Find: every occurrence of the old template's exact op-type sequence (718 ops) in TARGET; the template's 22 wires and
   3 record bits map to the site's wires and bits by alignment (must be consistent and injective; op texts must then
   match exactly under the map).
2. Emit: the new leaf's ops (same 22 template wires, same 3 bit slots) rendered through each site's maps.
3. Clean entry (unless --all): keep a site only if each of template wires 6..21 was last touched before entry by an
   unconditional R/HMR on it, or never touched, and the site is at condition depth 0 (see c47_clean_entry.py).
Control: on e208d3507475 with --all this must reproduce R's `current-e208-preserve-records.qed` line for line.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qhdl_kmb as K  # noqa: E402

NEW_NAMES = None


def render(text, qmap, bmap):
    out = []
    for tok in text.split():
        if tok.startswith('q') and tok[1:].isdigit():
            out.append(f'q{qmap[int(tok[1:])]}')
        elif tok.startswith('b') and tok[1:].isdigit():
            out.append(f'b{bmap[int(tok[1:])]}')
        else:
            out.append(tok)
    return ' '.join(out)


def bits_of(text):
    return [int(t[1:]) for t in text.split() if t.startswith('b') and t[1:].isdigit()]


def main():
    tgt, old, new, out = sys.argv[1:5]
    all_sites = '--all' in sys.argv
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    k = K.read(tgt)
    d = K.Decoder(k)
    ko, kn = K.read(old), K.read(new)
    do, dn = K.Decoder(ko), K.Decoder(kn)
    no, nn = len(ko.op_types), len(kn.op_types)
    otext = [do.text(i) for i in range(no)]
    ntext = [dn.text(i) for i in range(nn)]
    pat = np.asarray(ko.op_types, np.uint8).tobytes()
    hay = np.asarray(k.op_types, np.uint8).tobytes()
    starts, p = [], hay.find(pat)
    while p >= 0:
        starts.append(p)
        p = hay.find(pat, p + 1)
    t = np.asarray(k.op_types, np.uint8)
    depth = K.condition_depth(t)
    # last-touch index for clean entry
    q = t & 0x30
    ops = np.arange(len(t), dtype=np.int64)
    occ_op, occ_q = [], []
    for code, names in ((0x30, ('qqq0', 'qqq1', 'qqq2')), (0x20, ('qq0', 'qq1')), (0x10, ('q0',))):
        idx = ops[q == code]
        for nm in names:
            occ_op.append(idx)
            occ_q.append(np.asarray(k.stream(nm), np.int64))
    occ_op, occ_q = np.concatenate(occ_op), np.concatenate(occ_q)
    order = np.lexsort((occ_op, occ_q))
    occ_op, occ_q = occ_op[order], occ_q[order]
    qstart = np.searchsorted(occ_q, np.arange(int(k.num_qubits) + 1))

    def last_touch(w, before):
        lo, hi = qstart[w], qstart[w + 1]
        j = np.searchsorted(occ_op[lo:hi], before) - 1
        return None if j < 0 else int(occ_op[lo + j])

    lines, rows = [], []
    for a in starts:
        b = a + no
        qmap, bmap, ok = {}, {}, True
        for i in range(no):
            tq, sq = do.qubits(i), d.qubits(a + i)
            tb, sb = bits_of(otext[i]), bits_of(d.text(a + i))
            if len(tq) != len(sq) or len(tb) != len(sb):
                ok = False
                break
            for x, y in list(zip(tq, sq)):
                if qmap.setdefault(x, y) != y:
                    ok = False
            for x, y in zip(tb, sb):
                if bmap.setdefault(x, y) != y:
                    ok = False
            if not ok:
                break
        row = dict(start=a, end=b)
        if ok:
            ok = (len(set(qmap.values())) == len(qmap) and len(set(bmap.values())) == len(bmap)
                  and all(render(otext[i], qmap, bmap) == d.text(a + i) for i in range(no)))
        if not ok:
            row['status'] = 'pattern match but not the template under one wire/bit map'
            rows.append(row)
            continue
        clean = int(depth[a]) == 0 and int(depth[b]) == 0
        why = []
        for tw in range(6, 22):
            w = qmap[tw]
            lt = last_touch(w, a)
            if lt is None:
                continue
            nm = d.text(lt).split()[0]
            if not (nm in ('R', 'HMR') and d.qubits(lt) == [w] and int(depth[lt]) == 0):
                clean = False
                why.append(f'template wire {tw} (q{w}) last {d.text(lt)} at {lt}')
        row.update(depth=int(depth[a]), clean=clean, unclean=why[:3])
        if clean or all_sites:
            body = '; '.join(render(x, qmap, bmap) for x in ntext)
            lines.append(f'replace {a}:{b} => {body}')
            row['status'] = 'replaced'
        else:
            row['status'] = 'kept (not clean at entry)'
        rows.append(row)
    (out / 'inverse19.qed').write_text('\n'.join(lines) + ('\n' if lines else ''))
    rep = dict(target=tgt, old_template=old, new_leaf=new, occurrences=len(starts),
               template_matches=sum(1 for r in rows if 'clean' in r), replaced=len(lines),
               kept_unclean=sum(1 for r in rows if r['status'].startswith('kept')), all_sites=all_sites, rows=rows)
    (out / 'inverse19.json').write_text(json.dumps(rep, indent=1))
    print(json.dumps({x: v for x, v in rep.items() if x != 'rows'}, indent=1))


if __name__ == '__main__':
    main()
