# Frozen security review evidence

Read [the addendum](../../docs/security-coverage-addendum.md) before interpreting these receipts. `summary.json` is the index; `sha256.json` commits all other files in this directory. Git history binds the manifest and tooling. Checksums show retained-byte consistency, not reviewer independence or security assurance.

Reproduce a path screen without executing target code:

```sh
python tools/security_coverage.py --repository /path/to/checkout --revision EXACT_40_CHARACTER_SHA --label selected-component --out /tmp/new-screen.json
python -m unittest discover -s tests -p 'test_security_coverage.py' -v
python -m unittest discover -s tests -p 'test_public_link_checker.py' -v
```

Use the exact revision in each component receipt. Screening reads Git objects and ignores dirty working files; candidate revisions require a new scope. Python 3.12.14, Bandit 1.9.4 and Git were used. Manual traces require source inspection and cannot be reproduced by replaying a parser. Public network observations can change. Existing failed attempts remain historical evidence, not the latest status. Embedding assessment remains false because actual environment/configuration evidence is unavailable.
