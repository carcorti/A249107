#!/usr/bin/env python3
"""Package-relative checks; all generated files and native probes use scratch roots.

Data/record checks do not independently enumerate the production negatives.
The retained checker and finite manuscript arithmetic are unmodified modules.
"""
import argparse
from decimal import Decimal
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
STAGES = ('O2', 'T2', 'T3', 'T4')
HIST = None
ARCHIVES = {}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def short_path(name, directory=False):
    p = Path(name)
    need(name and not p.is_absolute() and '..' not in p.parts and '\\' not in name,
         'unsafe path: '+name)
    for i, part in enumerate(p.parts):
        file_part = i == len(p.parts)-1 and not directory
        stem = (Path(part).stem if file_part else part).lstrip('.')
        # The author explicitly requires this repository control file.
        control = name == '.gitignore' and file_part
        exception = control or (file_part and Path(part).suffix.lower() in ('.tex', '.c', '.py'))
        need(stem and (exception or len(stem) <= 8), 'long ordinary basename: '+name)


def read_archive(path):
    with tarfile.open(path, 'r:gz') as tar:
        members = tar.getmembers()
        names = [t.name for t in members]
        need(len(names) == len(set(names)) and 'index.json' in names, 'archive inventory')
        for t in members:
            short_path(t.name)
            need(t.isfile() and t.size <= 2000000, 'invalid archive member')
        index = json.loads(tar.extractfile('index.json').read())
        rows = index['members']
        need(set(names) == {'index.json'} | {r['path'] for r in rows}
             and len(rows)+1 == len(names), 'indexed archive inventory')
        result = {}
        for row in rows:
            target = Path(row['restore'])
            need(not target.is_absolute() and '..' not in target.parts and str(target) != '.',
                 'unsafe historical restore path')
            raw = tar.extractfile(row['path']).read()
            need(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'archive member identity')
            need(row['restore'] not in result and row['mode'] in (0o644, 0o755), 'duplicate/mode')
            result[row['restore']] = (raw, row['mode'])
        return result


def restore(destination, development=False):
    destination.mkdir(parents=True, exist_ok=False)
    for archive in ('run', 'dev') if development else ('run',):
        for name, (raw, mode) in ARCHIVES[archive].items():
            target = destination/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw); target.chmod(mode)
    # One exact source copy and one exact independent checker serve all stages.
    for source, target in [('src/a249107.c','src/a249107.c'),
                           ('check/check.py','validation/check.py')]:
        p = destination/target; p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/source, p)


def inventory():
    expected = {}
    for line in (ROOT/'checks.sha256').read_text().splitlines():
        digest, name = line.split('  ', 1)
        short_path(name)
        need(len(digest) == 64 and name not in expected, 'invalid checksum manifest')
        expected[name] = digest
    need(expected and 'check/verify.py' in expected, 'empty/incomplete manifest')
    actual = set()
    for p in ROOT.rglob('*'):
        rel = p.relative_to(ROOT)
        if rel.parts[0] == '.git':
            continue
        need(not p.is_symlink(), 'symlink in payload: '+str(rel))
        short_path(str(rel), directory=p.is_dir())
        if p.is_file() and str(rel) not in ('checks.sha256', 'src/a249107'):
            actual.add(str(rel))
    need(actual == set(expected), 'missing/unexpected payload: '+repr(sorted(actual ^ set(expected))))
    for name, digest in expected.items():
        need(sha((ROOT/name).read_bytes()) == digest, 'changed file: '+name)
    for name in ('run', 'dev'):
        ARCHIVES[name] = read_archive(ROOT/'evid'/(name+'.tgz'))
    return len(expected)


def oracle():
    return module(ROOT/'check/check.py', 'historical_checker')


def regenerate(o):
    """Derive the canonical data from the accepted reference and sealed hits."""
    base = (HIST/'data/b249107.txt').read_bytes()
    need(sha(base) == o.PREFIX_SHA, 'historical ten-row reference identity')
    prior = [tuple(map(int, line.split())) for line in base.splitlines() if line]
    need(len(prior) == 10 and [i for i, _ in prior] == list(range(1, 11)), 'baseline indices')
    witnesses = []
    for _, n in prior:
        w = o.witness(n)
        need(w is not None, 'baseline positive')
        witnesses.append(w)
    manifest = ['# stage\tsegment\tlow\thigh\tinputs\tthreads\tblock\twall_s\tcpu_s\tpeak_rss_kib\thits\tcommand']
    previous = prior[-1][1]
    total_segments = 0
    for label in STAGES:
        directory = HIST/('campaign_'+label)
        cfg, hits = o.sealed_run(directory, source_root=HIST)
        need(cfg['start'] == previous+1, 'cross-stage gap')
        previous = cfg['end']
        for name, key in [('a249107.c', 'source_sha'), ('Makefile', 'makefile_sha')]:
            need(sha((HIST/'src'/name).read_bytes()) == cfg[key], 'public source drift')
        need(sha((HIST/'src/a249107').read_bytes()) == cfg['binary_sha'],
             'historical binary not campaign binary')
        receipts = (HIST/('campaign_'+label+'_logs/resources.txt')).read_text().splitlines()
        segments = (directory/'manifest.tsv').read_text().splitlines()[2:]
        need(len(receipts) == len(segments), 'receipt/segment count')
        total_segments += len(segments)
        for line, resource in zip(segments, receipts):
            sid, lo, hi, _, elapsed, count = line.split('\t')
            fields = dict(item.split('=', 1) for item in resource.split())
            need(fields['exit'] == '0' and Decimal(fields['elapsed_s']) >= 0,
                 'failed resource receipt')
            values = [label, sid, lo, hi, str(int(hi)-int(lo)+1),
                      str(cfg['threads']), str(cfg['block']), fields['elapsed_s'],
                      'unknown', fields['peak_rss_kib'], count,
                      'a249107 next campaign_'+label]
            manifest.append('\t'.join(values))
        witnesses.extend(hits)
    need(total_segments == 50 and len(witnesses) == 16
         and previous == 30429212500, 'selected consolidated frontier')
    need(all(a[0] < b[0] for a, b in zip(witnesses, witnesses[1:])), 'hit ordering')
    braw = ''.join(str(i)+' '+str(w[0])+'\n' for i, w in enumerate(witnesses, 1)).encode()+b'\n'
    # Preserve the exact documentary table's original header and row grammar.
    header = ('# A249107: indexed Pythagorean 7-tuples.\n'
              '# i n D(n) D^2(n) D^3(n) D^4(n) D^5(n) root\n'
              '# n = a(i); D is the arithmetic derivative; root^2 = n^2 + D(n)^2 + D^2(n)^2 + D^3(n)^2 + D^4(n)^2 + D^5(n)^2.\n'
              '# Prepared by Carlo Corti, 2026-10-20.\n')
    wraw = header.encode()+''.join(' '.join(map(str, (i,)+w))+'\n'
                                  for i, w in enumerate(witnesses, 1)).encode()+b'\n'
    return braw, wraw, ('\n'.join(manifest)+'\n').encode(), witnesses


def data_checks(o, export=None):
    braw, wraw, telemetry, witnesses = regenerate(o)
    for name, raw in [('data/b249107.txt', braw), ('data/a249107.txt', wraw)]:
        need((ROOT/name).read_bytes() == raw, 'regenerated data mismatch: '+name)
    for raw in (braw, wraw):
        need(raw.endswith(b'\n\n') and not raw.endswith(b'\n\n\n') and b'\r' not in raw,
             'canonical final blank line')
    with tempfile.TemporaryDirectory(prefix='a249107-math-') as directory:
        work = Path(directory)
        (work/'data').mkdir()
        (work/'data/b249107.txt').write_bytes(braw)
        (work/'data/a249107.txt').write_bytes(wraw)
        finite = module(ROOT/'check/finite_audit.py', 'finite_math')
        # Adapt original file locations only; its arithmetic code is byte-identical.
        finite.ROOT = work
        finite.OUT = work
        finite.main()
        actual = json.loads((work/'finite_audit.json').read_text())
        retained = json.loads((ROOT/'data/math.json').read_text())
        # Python version is execution metadata, not a mathematical comparison.
        actual.pop('python'); retained.pop('python')
        need(actual == retained and actual['status'] == 'PASS', 'finite arithmetic output drift')
        if export is not None:
            export.mkdir(parents=True, exist_ok=False)
            (export/'b249107.txt').write_bytes(braw)
            (export/'a249107.txt').write_bytes(wraw)
            (export/'runs.tsv').write_bytes(telemetry)
            shutil.copyfile(work/'finite_audit.json', export/'math.json')
    print('DATA PASS: 16 witnesses; 11 forms; 50 sealed segments; exact regeneration.')
    return witnesses


def window_checks(o):
    cases = {'postrun': [{'stage': 'campaign_O2', 'author': 'Carlo Corti', 'status': 'PASS', 'baseline_terms': 10, 'method': 'trial division/math.isqrt; independent of C sieve/MR/rho/GMP', 'scope': 'complete sealed-record audit and independent positives; global negatives not repeated', 'recorded_interval': [380264132, 1058578125], 'hits': 1, 'independent_interval': [380264132, 380268227], 'independent_inputs': 4096, 'independent_hits': 0}, {'stage': 'campaign_O2', 'author': 'Carlo Corti', 'status': 'PASS', 'baseline_terms': 10, 'method': 'trial division/math.isqrt; independent of C sieve/MR/rho/GMP', 'scope': 'complete sealed-record audit and independent positives; global negatives not repeated', 'recorded_interval': [380264132, 1058578125], 'hits': 1, 'independent_interval': [1058574030, 1058578125], 'independent_inputs': 4096, 'independent_hits': 1}, {'stage': 'campaign_T2', 'author': 'Carlo Corti', 'status': 'PASS', 'baseline_terms': 10, 'method': 'trial division/math.isqrt; independent of C sieve/MR/rho/GMP', 'scope': 'complete sealed-record audit and independent positives; global negatives not repeated', 'recorded_interval': [1058578126, 1774631673], 'hits': 2, 'independent_interval': [1058578126, 1058582221], 'independent_inputs': 4096, 'independent_hits': 0}, {'stage': 'campaign_T2', 'author': 'Carlo Corti', 'status': 'PASS', 'baseline_terms': 10, 'method': 'trial division/math.isqrt; independent of C sieve/MR/rho/GMP', 'scope': 'complete sealed-record audit and independent positives; global negatives not repeated', 'recorded_interval': [1058578126, 1774631673], 'hits': 2, 'independent_interval': [1774627578, 1774631673], 'independent_inputs': 4096, 'independent_hits': 1}, {'stage': 'campaign_T3', 'author': 'Carlo Corti', 'status': 'PASS', 'baseline_terms': 10, 'method': 'trial division/math.isqrt; independent of C sieve/MR/rho/GMP', 'scope': 'complete sealed-record audit and independent positives; global negatives not repeated', 'recorded_interval': [1774631674, 10000000000], 'hits': 2, 'independent_interval': [1774631674, 1774635769], 'independent_inputs': 4096, 'independent_hits': 0}, {'stage': 'campaign_T3', 'author': 'Carlo Corti', 'status': 'PASS', 'baseline_terms': 10, 'method': 'trial division/math.isqrt; independent of C sieve/MR/rho/GMP', 'scope': 'complete sealed-record audit and independent positives; global negatives not repeated', 'recorded_interval': [1774631674, 10000000000], 'hits': 2, 'independent_interval': [9999995905, 10000000000], 'independent_inputs': 4096, 'independent_hits': 0}, {'stage': 'campaign_T4', 'author': 'Carlo Corti', 'status': 'PASS', 'baseline_terms': 10, 'method': 'trial division/math.isqrt; independent of C sieve/MR/rho/GMP', 'scope': 'complete sealed-record audit and independent positives; global negatives not repeated', 'recorded_interval': [10000000001, 30429212500], 'hits': 1, 'independent_interval': [10000000001, 10000004096], 'independent_inputs': 4096, 'independent_hits': 0}, {'stage': 'campaign_T4', 'author': 'Carlo Corti', 'status': 'PASS', 'baseline_terms': 10, 'method': 'trial division/math.isqrt; independent of C sieve/MR/rho/GMP', 'scope': 'complete sealed-record audit and independent positives; global negatives not repeated', 'recorded_interval': [10000000001, 30429212500], 'hits': 1, 'independent_interval': [30429208405, 30429212500], 'independent_inputs': 4096, 'independent_hits': 1}], 'development': [{'run': 'smoke', 'low': 2, 'high': 5000, 'hits': 1}, {'run': 'window0', 'low': 10807, 'high': 10839, 'hits': 1}, {'run': 'window1', 'low': 380264115, 'high': 380264147, 'hits': 1}, {'run': 'window2', 'low': 1058578109, 'high': 1058578141, 'hits': 1}], 'development_scope': '5098 distinct inputs, 4 hits; overlaps postrun windows; never add counts as disjoint sets'}
    totals = []
    for group in ('postrun', 'development'):
        seen = set(); hit_count = 0
        for c in cases[group]:
            lo, hi = c['independent_interval'] if group == 'postrun' else (c['low'], c['high'])
            expected = c['independent_hits'] if group == 'postrun' else c['hits']
            need(2 <= lo <= hi and hi-lo < 40000, 'window budget')
            inputs = set(range(lo, hi+1))
            need(not (seen & inputs), 'within-group overlapping windows')
            seen.update(inputs)
            found = [w for n in range(lo, hi+1) if (w := o.witness(n))]
            need(len(found) == expected, 'finite window hit count')
            # Validate values, not merely the number of positives.
            canonical = [tuple(map(int, s.split()[1:]))
                         for s in (ROOT/'data/a249107.txt').read_text().splitlines()
                         if s and not s.startswith('#')]
            need(found == [w for w in canonical if lo <= w[0] <= hi], 'window witness mismatch')
            hit_count += len(found)
            print('WINDOW PASS:', group, lo, hi, 'hits', len(found), flush=True)
        totals.append((len(seen), hit_count))
    need(totals == [(32768, 3), (5098, 4)], 'scoped window totals')
    print('WINDOWS PASS: groups remain separate; overlaps are not added.')


def command(args, expected=0):
    result = subprocess.run([str(a) for a in args], capture_output=True, text=True, timeout=120)
    need(result.returncode == expected, 'command failed: '+repr(args)+'\n'+result.stderr)
    return result


def native_checks(o, witnesses):
    with tempfile.TemporaryDirectory(prefix='a249107-native-') as directory:
        work = Path(directory)
        for name in ('public', 'historical'):
            dest = work/name/'src'; dest.mkdir(parents=True)
            for f in ('a249107.c', 'Makefile'):
                shutil.copyfile((ROOT if name == 'public' else HIST)/'src'/f, dest/f)
        command(['make', '-C', work/'public/src'])
        rebuilt = work/'public/src/a249107'
        historical = work/'historical/src/a249107'
        historical.write_bytes((HIST/'src/a249107').read_bytes())
        historical.chmod(0o755)
        for label in STAGES:
            r = command([historical, 'verify', HIST/('campaign_'+label)])
            need('COMPLETE' in r.stdout, 'original binary incomplete run')
        expected = [w for n in range(2, 65539) if (w := o.witness(n))]
        for threads in (1, 4, 8):
            run = work/('threads'+str(threads))
            command([rebuilt, 'init', run, 2, 65538, 16384, 2, threads])
            cfg = o.config((run/'run.cfg').read_bytes())
            for _ in range(o.segments(cfg)):
                command([rebuilt, 'next', run])
            command([rebuilt, 'verify', run])
            _, found = o.sealed_run(run, source_root=work/'public')
            need(found == expected, 'thread/partition arithmetic disagreement')
        # Exact isolated positives and actual wide negative; no intermediate census.
        for i, n in enumerate([w[0] for w in witnesses]+[205397184375, 2**45]):
            run = work/('point'+str(i))
            command([rebuilt, 'init', run, n, n, 16384, 1, 8])
            command([rebuilt, 'next', run])
            _, found = o.sealed_run(run, source_root=work/'public')
            w = o.witness(n)
            need(found == ([w] if w else []), 'isolated native witness mismatch')
        print('NATIVE PASS: historical binary audits four runs; public build', sha(rebuilt.read_bytes()))
        print('NATIVE PASS: 1/4/8 workers, 2..65538, 18 isolated operands; scratch only.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', nargs='?', choices=('data', 'windows', 'native', 'all', 'restore'), default='data')
    parser.add_argument('--write', type=Path, help='new directory outside the package for data export or historical restore')
    args = parser.parse_args()
    if args.write is not None:
        args.write = args.write.resolve()
        need(args.mode in ('data', 'restore') and ROOT not in (args.write, *args.write.parents),
             'export must be outside package and mode data')
    global HIST
    count = inventory()
    if args.mode == 'restore':
        need(args.write is not None, 'restore requires --write NEW_DIRECTORY outside package')
        restore(args.write, development=True)
        print('RESTORE PASS: original paths reconstructed outside the publication payload.')
        return
    with tempfile.TemporaryDirectory(prefix='a249107-records-') as directory:
        HIST = Path(directory)/'historical'
        restore(HIST)
        o = oracle()
        witnesses = data_checks(o, args.write)
        if args.mode in ('windows', 'all'):
            window_checks(o)
        if args.mode in ('native', 'all'):
            native_checks(o, witnesses)
    print('PACKAGE CHECK PASS:', args.mode, count, 'manifested files; no global negative rescan.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        raise SystemExit('FAIL: '+str(error))
