# CP/Replay FAMILY_TABLE parity (prototype, not pushed)
File: test_family_table_parity.py (58 lines, stdlib + pytest). Lives in cogno-us/cognous-stack-qualification, r1c/ (the only place that can see both sides; Replay cannot import CP).
Setup: shallow-fetch exactly CP b19c47ddd020409d24e52e70b11359c46265edbb (tree 039219b5...) and Replay 6f45e288ae37ec7e7712f9296760927d2d843bba (tree b2932497...) into separate dirs; verify `git rev-parse HEAD` and tree.
Run: CP_SRC=<cp>/src REPLAY_SRC=<replay>/src python3 -m pytest -q test_family_table_parity.py
Expected: 3 passed. Each side imported in its own `python -I` subprocess (no shared runtime). Fails if env unset or import fails.
Mutation (verified): editing a CP FAMILY_TABLE entry, a Replay FAMILY_TABLE entry, or Replay DOMAIN -> 2 failed (tables test + digest test).
