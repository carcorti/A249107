#!/usr/bin/env python3
"""Independent A249107 arithmetic and sealed-record checker (no C imports).

Trial division/math.isqrt check membership. Record checks do not independently
repeat the global negative scan. --low/--high enumerate one bounded interval.
Project author: Carlo Corti.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAP = 40_000_000_000_000
LIMITS = (CAP, 900_000_000_000_000, 22_050_000_000_000_000,
          595_350_000_000_000_000, 17_562_825_000_000_000_000,
          553_228_987_500_000_000_000, 553_508_012_914_801_786_476)
PREFIX_SHA = '82e9a0924e33abbc7318a7cc6e8f6d8f30b16a7a4ddb8c00f243cfcd53c23dc2'
UPPER = (1058578125, 1719903125, 1719906250, 2961903125,
         2981259375, 3975021875, 6363828125)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def derivative(n):
    if n < 2:
        return 0
    remaining, total, p = n, 0, 2
    while p <= remaining // p:
        exponent = 0
        while remaining % p == 0:
            remaining //= p
            exponent += 1
        total += exponent * (n // p)
        p = 3 if p == 2 else p + 2
    if remaining > 1:
        total += n // remaining
    return total


def witness(n):
    values = [n]
    for _ in range(5):
        values.append(derivative(values[-1]))
    square = sum(v*v for v in values)
    r = math.isqrt(square)
    return tuple(values+[r]) if n >= 2 and r*r == square else None


def lines(raw):
    need(raw.endswith(b'\n') and b'\r' not in raw and b'\0' not in raw,
         'record framing')
    result = raw.decode('ascii').split('\n')[:-1]
    need(all(len(line) <= 255 for line in result), 'oversized record')
    return result


def number(text, bits=64):
    need(text.isascii() and text.isdecimal(), 'decimal integer grammar')
    value = int(text)
    need(value < 1 << bits, 'integer width')
    return value


def digest(text):
    need(len(text) == 64 and all(c in '0123456789abcdef' for c in text),
         'digest grammar')
    return text


def config(raw):
    rows = lines(raw)
    keys = ('start', 'end', 'block', 'group', 'threads',
            'source_sha', 'makefile_sha', 'binary_sha')
    need(len(rows) == 9 and rows[0] == 'A249107-CFG-1', 'config schema')
    result = {}
    for key, row in zip(keys, rows[1:]):
        pair = row.split('\t')
        need(len(pair) == 2 and pair[0] == key, 'config field')
        result[key] = number(pair[1]) if key in keys[:5] else digest(pair[1])
    a, b, block, group, threads = (result[k] for k in keys[:5])
    need(2 <= a <= b <= CAP and 16384 <= block <= 1048576 and
         block & (block-1) == 0 and 1 <= threads <= 8 and
         1 <= group <= (b-a)//block+1, 'config domain')
    need(segments(result) <= 2048, 'segment count')
    return result


def segments(c):
    blocks = (c['end']-c['start']+c['block'])//c['block']
    return (blocks+c['group']-1)//c['group']


def bounds(c, j):
    # Independent integer calculation of the documented balanced partition.
    blocks = (c['end']-c['start']+c['block'])//c['block']
    count = segments(c)
    need(0 <= j < count, 'segment index')
    first, after = j*blocks//count, (j+1)*blocks//count
    return (c['start']+first*c['block'],
            min(c['end'], c['start']+after*c['block']-1))


def rows(records):
    result = []
    for record in records:
        parts = record.split('\t')
        need(len(parts) == 7, 'hit width')
        row = tuple(number(p, 64 if j < 5 else 128)
                    for j, p in enumerate(parts))
        need(2 <= row[0] <= CAP and row[1] > 0 and row[-1] > 0 and
             all(v <= upper for v, upper in zip(row, LIMITS)), 'hit domain')
        need(not result or result[-1][0] < row[0], 'hit order')
        result.append(row)
    return result


def sealed_run(run, source_root=ROOT, positive=True):
    raw = (run/'run.cfg').read_bytes()
    c, cfg_sha = config(raw), sha(raw)
    for name, key in [('a249107.c', 'source_sha'), ('Makefile', 'makefile_sha')]:
        need(sha((source_root/'src'/name).read_bytes()) == c[key], 'source/build identity')
    records = lines((run/'manifest.tsv').read_bytes())
    count = segments(c)
    need(len(records) == count+2 and records[:2] == [
        'A249107-MANIFEST-1\tcfg_sha='+cfg_sha,
        'id\tlow\thigh\tstate_sha\telapsed_ns\thits'], 'complete manifest')
    found, previous = [], c['start']-1
    for j, record in enumerate(records[2:]):
        fields = record.split('\t')
        need(len(fields) == 6 and fields[0] == format(j, '010x'), 'manifest ID')
        lo, hi = bounds(c, j)
        need(number(fields[1]) == lo == previous+1 and number(fields[2]) == hi,
             'coverage gap/overlap')
        previous = hi
        state_sha, elapsed, hits = digest(fields[3]), number(fields[4]), number(fields[5])
        base = 's'+fields[0]
        raw_state = (run/(base+'.tsv')).read_bytes()
        need(sha(raw_state) == state_sha and
             (run/(base+'.sha256')).read_bytes() == (state_sha+'\n').encode(), 'seal')
        need(len(raw_state) >= 75 and raw_state[-75:-65] == b'state_sha\t' and
             raw_state[-1:] == b'\n', 'state footer shape')
        need(sha(raw_state[:-75]) == digest(raw_state[-65:-1].decode()), 'state digest')
        body = lines(raw_state[:-75])
        need(len(body) == 8+hits and body[0] == 'A249107-SEG-1', 'state schema/count')
        wanted = [('cfg_sha', cfg_sha), ('id', fields[0]), ('low', str(lo)),
                  ('high', str(hi)), ('frontier', str(hi)),
                  ('elapsed_ns', str(elapsed)), ('hits', str(hits))]
        need(body[1:8] == [k+'\t'+v for k, v in wanted], 'state metadata/completion')
        data = rows(body[8:])
        need(all(lo <= x[0] <= hi for x in data), 'hit outside coverage')
        found.extend(data)
    need(previous == c['end'], 'not complete to END')
    aggregate = lines((run/'hits.tsv').read_bytes())
    need(aggregate[:2] == ['A249107-HITS-1\tcfg_sha='+cfg_sha,
                          'n\tx1\tx2\tx3\tx4\tx5\troot'] and
         rows(aggregate[2:]) == found, 'aggregate mismatch')
    wanted = {'s'+format(j, '010x')+suffix for j in range(count)
              for suffix in ('.tsv', '.sha256')}
    actual = {p.name for p in run.iterdir() if p.name.startswith('s') and
              p.name.endswith(('.tsv', '.sha256'))}
    need(actual == wanted, 'orphan/missing state')
    if positive:
        for row in found:
            need(witness(row[0]) == row, 'independent positive arithmetic')
    return c, found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path)
    parser.add_argument('--low', type=int)
    parser.add_argument('--high', type=int)
    args = parser.parse_args()
    raw = (ROOT/'data/b249107.txt').read_bytes()
    need(sha(raw) == PREFIX_SHA and raw.endswith(b'\n\n') and
         not raw.endswith(b'\n\n\n'), 'accepted baseline identity/framing')
    baseline = [tuple(map(int, line.split())) for line in raw.splitlines() if line]
    need(len(baseline) == 10 and [i for i, _ in baseline] == list(range(1, 11)) and
         baseline[-1] == (10, 380264131), 'accepted baseline indices')
    for _, n in baseline:
        need(witness(n) is not None, 'accepted positive')
    need(witness(UPPER[0]) == UPPER, 'upper witness')
    for m, rate, root in [(338745, 1, 2036425), (2434337, 2, 165567453)]:
        a = [m]
        for _ in range(5):
            a.append(derivative(a[-1])+rate*a[-1])
        need(sum(x*x for x in a) == root*root, 'shifted seed')
    need((args.low is None) == (args.high is None), 'both window endpoints required')
    need(args.run is not None or args.low is None, 'window needs retained run')
    result = {'author': 'Carlo Corti', 'status': 'PASS', 'baseline_terms': 10,
              'method': 'trial division/math.isqrt; independent of C sieve/MR/rho/GMP',
              'scope': 'positive checks only; baseline indexing inherited'}
    if args.run:
        c, found = sealed_run(args.run)
        result.update(recorded_interval=[c['start'], c['end']], hits=len(found),
                      scope='complete sealed-record audit and independent positives; global negatives not repeated')
        if args.low is not None:
            need(2 <= args.low <= args.high <= CAP and args.high-args.low < 40000,
                 'independent interval budget')
            need(c['start'] <= args.low <= args.high <= c['end'], 'window outside run')
            expected = [w for n in range(args.low, args.high+1) if (w := witness(n))]
            need(expected == [w for w in found if args.low <= w[0] <= args.high],
                 'independent complete interval mismatch')
            result.update(independent_interval=[args.low, args.high],
                          independent_inputs=args.high-args.low+1,
                          independent_hits=len(expected))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as error:
        raise SystemExit('FAIL: '+str(error))
