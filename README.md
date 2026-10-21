# OEIS A249107

Carlo Corti · Independent researcher · carlo.corti@outlook.com

Release **v1.0.1**. Public repository:
[carcorti/A249107](https://github.com/carcorti/A249107).
The persistent [Zenodo concept DOI](https://doi.org/10.5281/zenodo.23534992)
identifies the release series. Each deposited release has a separate
version-specific DOI; the initial v1.0 deposit is
[10.5281/zenodo.23534993](https://doi.org/10.5281/zenodo.23534993).
Cite the article and software using `CITATION.cff`, including the software
version when referring to this exact package. The complete package, including
the manuscript and PDF, is distributed under the [MIT license](LICENSE).

The [monolithic English manuscript](paper/A249107.tex) and
[corresponding PDF](paper/A249107.pdf) present the homothetic
classification and describe the exact computational extension of the integers
`n >= 2` for which `n^2 + D(n)^2 + ... + D^5(n)^2` is a square.
`D` is the arithmetic derivative, iterated by composition, with `D(0)=D(1)=0`.
Later zero coordinates are allowed. There is no primitivity or family filter.

There are **16 consecutive terms**, ending at `a(16)=30429212500`. The first
ten terms and their negative coverage are inherited. Four completed stages
cover 380264132..30429212500: 30048948369 inputs, six new positives and 50
sealed segments. Completeness depends on the executed C code and its external
deterministic primality premise; record audits and positive checks do not
independently repeat the production negative census.

The sample contains eleven primitive ordered forms: two infinite homothetic
classes and nine singletons. Three trajectories terminate; thirteen diverge
by the proved divisibility criterion. The next term is unresolved:
`30429212500 < a(17) <= 205397184375`. This upper witness is unindexed.
The supported input cap `40000000000000` is a representation bound, not coverage.

## Essential contents

Every retained file serves a build, claim, verification or attribution need:

| File | Purpose |
| --- | --- |
| `paper/A249107.tex`, `paper/A249107.pdf` | Complete proofs, tables and inline bibliography, as source and matching PDF; no external figures or bibliography files |
| `src/a249107.c`, `src/Makefile` | Production algorithm and public build/check entry points |
| `data/b249107.txt` | Canonical 16 index/value pairs |
| `data/a249107.txt` | Canonical documentary witnesses: `i n D(n) D^2(n) D^3(n) D^4(n) D^5(n) root` |
| `data/math.json` | Frozen exact arithmetic output against which regeneration is compared |
| `check/verify.py` | Portable inventory, archive, record, data and bounded native checks |
| `check/check.py` | Exact original trial-division checker, independent of C sieve/MR/rho/GMP |
| `check/finite_audit.py` | Exact original finite manuscript arithmetic; driver adapts locations only |
| `evid/run.tgz` | Complete production records, receipts, historical build/binary/baseline and environments |
| `evid/dev.tgz` | Original development harness/fixtures and final raw reports supporting the paper's bounded validation claims |
| `CITATION.cff`, `LICENSE`, `.gitignore`, `checks.sha256`, `README.md` | Attribution, existing MIT grant, generated-file exclusions, integrity inventory and reproduction instructions |

The a-file is a documentary witness table, not a sparse list of later indexed
terms. Both canonical text files end with exactly one empty final line.
Derived telemetry is regenerated rather than duplicated. Superseded tests,
intermediate fixtures, duplicate sources/binaries, review conversations and
obsolete drafts are omitted. Third-party articles are cited in the paper.

The eight-character basename limit applies to ordinary payload files and
directory components, including archive members. **TeX manuscripts and C/Python
program files are exceptions:** they retain their conventional meaningful names.
The author-requested repository control file `.gitignore` is also an explicit
exception. The manuscript is `A249107.tex`; original programs include `finite_audit.py`,
`tsan_controls.c` and `io_faults.c`. Archive indexes record original paths,
sizes, hashes, modes and roles. Historical layouts are restored in scratch
storage outside this payload.

## Reproduce the checks

Python 3.8 or later, standard library only; tested with Python 3.12.3.
From any extraction or clone root:

```sh
python3 -B check/verify.py
python3 -B check/verify.py windows
python3 -B check/verify.py native
```

The default checks inventory and all archive members, reconstructs the
historical reference in temporary storage, audits four complete sealed runs,
regenerates both canonical tables byte-for-byte and compares all finite
arithmetic output. Only interpreter-version metadata is excluded from that
comparison. Nothing is written into the payload. `.git/` provider metadata
and an optional built `src/a249107` are accepted; other unexpected files fail.

`windows` also independently enumerates eight disjoint boundary windows of
4096 inputs (32768 inputs, three hits), then the four original development
windows (5098 distinct inputs, four hits). These two groups overlap and must
not be added as disjoint coverage. Their exact definitions are in the driver.

`native` builds in scratch storage, compares one/four/eight workers on
2..65538 against trial division, replays the sixteen isolated positives,
the unindexed upper witness and an actual wide negative, and separately
verifies the archived runs with their exact historical executable.
`all` combines the modes. These are bounded diagnostics, not a new campaign.

Export fresh data to a new directory outside the payload:

```sh
python3 -B check/verify.py data --write /tmp/a249107-data
```

This writes regenerated a/b files, telemetry and math JSON. To inspect or
rerun the original development harness with its historical ten-term baseline:

```sh
python3 -B check/verify.py restore --write /tmp/a249107-old
```

The destination must not exist. It receives original paths restored from
both archives, the common exact C source and the original checker. For example,
from that scratch directory `python3 -B validation/check.py --run campaign_T4`
audits the fourth stage. The checker's old `UPPER` is a(11), not the present
upper bound on a(17). The original Makefile and its ten-row smoke target are
historical inputs; the public Makefile routes `check` to the current driver.
Development harness commands and their qualified results remain in the raw
reports. Optional reruns require their recorded tools (including SymPy,
Clang/libomp/Archer and sanitizer tooling); the default checker installs none.
Retained sanitizer/static reports substantiate only their recorded scopes.

## Build and identity

Requirements: Linux LP64, GCC with C17/unsigned 128-bit support, OpenMP,
GMP and OpenSSL libcrypto development libraries, GNU make and sha256sum.
The historical environment used GCC 13.3.0, GMP 6.3.0, OpenSSL 3.0.13,
Python 3.12.3 and a Ryzen 7940HS with eight workers. Exact captures are in
`run.tgz`. The original per-invocation receipts total approximately 36953 active wall
seconds; CPU seconds were not retained. Recorded precision is retained in the
archived receipts. Do not infer installed RAM from RSS.

```sh
make -C src
make -C src check
```

The C source is byte-identical to the executed source. Only the Makefile's
two `check` recipes changed, from the old checker/smoke paths to the public
driver's `data` and `native` modes. Compiler flags, linkage and binding logic
are unchanged. The original Makefile and executable remain in `run.tgz`.
This routing change gives the public Makefile and rebuilt executable new
identities; neither is represented as the historical executed binary.

Historical SHA-256 identities:

```text
C source  6b7cce67e6311cc664d674c2e9f51bca245449669230c24be6783e036e107c2b
Makefile  a6ec2b3a2fc82f00c279ff26d85131fc4d59f2b4579d0be754673f54fd517067
Binary    d98336668ed0298aa248c99dd58f33d7067ae1ece5456d1ef6944717c6b4a9e1
```

Current public bytes, including the TeX source, PDF and `.gitignore`, are
identified by `checks.sha256`. It covers every payload file except itself;
from the package root, run `sha256sum -c checks.sha256` to verify them. Archive indexes retain
all historical member identities. Source and Makefile must remain beside the
executable because its runtime identity checks require both. A different
toolchain can produce a different executable hash.

CLI: `a249107 init DIR START END BLOCK GROUP THREADS`, `next DIR`,
`status DIR`, `verify DIR`. `init` requires a new directory; `next` commits
only completed blocks and recomputes an interrupted block. There is no
intra-input resumability. The archived campaigns are complete read-only evidence.

## Manuscript and compressed evidence

The delivered PDF is built from `paper/A249107.tex`. With TeX Live and the
packages listed in that source, rebuild outside the package to keep auxiliary
files out of the strict integrity inventory:

```sh
texout=$(mktemp -d /tmp/a249107-tex.XXXXXXXX)
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory="$texout" paper/A249107.tex
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory="$texout" paper/A249107.tex
```

The result is `$texout/A249107.pdf`. Repeat if LaTeX requests another pass;
the settled log should contain no errors or warnings. Creation timestamps and
PDF identifiers can differ across rebuilds, so the delivered PDF has its own
SHA-256 in `checks.sha256`. `.gitignore` excludes TeX auxiliaries, Python
caches and the locally compiled C executable; it does not exclude the PDF.

`run.tgz` contains 121 indexed evidence members (108575 uncompressed content
bytes), plus its index. `dev.tgz` contains 18 indexed members (1043240 content
bytes), plus its index. Their compressed sizes are about 50 kB and 264 kB.
Each includes `index.json`; inspect it with `tar -xOf evid/run.tgz index.json`
or the corresponding development archive. Original reports retain execution-time absolute paths as historical provenance;
the portable checks do not require those paths to exist. The driver checks member
identities and restores paths safely; do not extract blindly over a working project.
A complete package SHA inventory protects both archives and their indexes.
