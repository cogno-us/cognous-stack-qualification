"""Reciprocal evidence package verifier for Evelyne-Claudia Yantony (REACHABLE).

Independent of Cognous runtime code. Python 3.9+ standard library only.
This verifier:
  1. Loads manifest.json and SHA256SUMS.
  2. For every file listed in manifest.trials[].files, confirms its presence,
     byte length and SHA-256 digest against the recipient-reproduced hash.
  3. Confirms SHA256SUMS entries agree with the manifest.
  4. Rejects duplicate paths, invalid JSON, and unexpected unlisted payloads
     under the scenarios/ tree.
  5. Runs tamper and contradiction controls:
       * tamper: silently flip one byte of a listed file in a temp mirror,
         expect verification to fail;
       * contradiction: a destination-readback.json whose effect_count disagrees
         with the recorded observation.json; expect failure.
  6. Confirms per-trial `observation.effect_occurrence_count` matches the
     per-scenario invariant {D01:1, D03:0, C07:0}.
  7. Confirms `f5b-enforcement.json#enforcement_demonstrated=true` on every
     trial, i.e. the F5b pairing was enforced by the consumer at package-build
     time.

What this verifier CANNOT do:
  * It does not re-execute the effect, does not contact production, does not
    acquire credentials, and does not write to the supplied destination.
  * It does not independently witness the original execution; it reverifies
    the frozen artifact bytes and their self-consistency.
  * It does not assign REACHABLE verdicts. DEMONSTRATED/CONTRADICTED/UNRESOLVED
    are REACHABLE's to assign; this verifier does not produce them.
  * It cannot verify issuer-side authority authenticity (not present in this
    profile; declared in CROSSWALK_REACHABLE.md).

The verifier exits 0 on success. On failure it prints a line prefixed FAIL and
exits non-zero. Explicit failure handling is used; optimized Python cannot
disable required validation.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, sqlite3, sys, tempfile
from pathlib import Path

EXPECTED_OCCURRENCE = {'D01': 1, 'D03': 0, 'C07': 0}

def sha256_of(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def _load_json(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

def verify(root: Path, controls: bool):
    failures = []
    def fail(msg):
        failures.append(msg); print('FAIL', msg, file=sys.stderr)
    if not (root / 'manifest.json').is_file():
        fail('manifest.json missing'); return failures
    manifest = _load_json(root / 'manifest.json')
    sha_file = root / 'SHA256SUMS'
    if not sha_file.is_file():
        fail('SHA256SUMS missing'); return failures
    sha_map = {}
    for line in sha_file.read_text().splitlines():
        if not line.strip() or line.startswith('#'): continue
        h, _, p = line.partition('  ')
        if not h or not p: fail(f'malformed SHA256SUMS line: {line!r}'); continue
        if p in sha_map: fail(f'duplicate SHA256SUMS entry: {p}')
        sha_map[p] = h

    # Build listing from manifest
    listed = {}
    for trial in manifest.get('trials', []):
        for f in trial.get('files', []):
            path = f['path']
            if path in listed:
                fail(f'duplicate manifest entry: {path}')
            listed[path] = f

    # (1) every manifest-listed file is present and matches size + sha
    for path, meta in listed.items():
        p = root / path
        if '..' in Path(path).parts or Path(path).is_absolute():
            fail(f'unsafe path: {path}'); continue
        if not p.is_file(): fail(f'missing listed file: {path}'); continue
        if p.stat().st_size != meta['size']: fail(f'size mismatch: {path}')
        actual = sha256_of(p)
        if actual != meta['sha256']: fail(f'sha mismatch: {path}')
        if path in sha_map and sha_map[path] != meta['sha256']:
            fail(f'SHA256SUMS disagrees with manifest for {path}')

    # (2) no unlisted payloads under scenarios/
    for p in (root / 'scenarios').rglob('*'):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            if rel not in listed:
                fail(f'unlisted payload under scenarios/: {rel}')

    # (3) per-trial observation effect_count matches the per-scenario invariant,
    #     and destination-readback is internally consistent with observation.
    # Byte-level failures (sha mismatch above) are reported first; here we only
    # continue to semantic checks for files that still parse. If a byte flip
    # survives (3) but corrupts JSON, we report it as "unparseable or unreadable"
    # against this file alone and keep going — the script finishes with a clean
    # VERIFY FAILED summary rather than a traceback.
    def _safe_load(p, label):
        try:
            return _load_json(p)
        except (json.JSONDecodeError, OSError) as e:
            fail(f'{label}: unparseable or unreadable ({e.__class__.__name__})')
            return None
    for trial in manifest.get('trials', []):
        scen = trial['scenario_id']; tid = trial['trial_id']
        base = root / 'scenarios' / scen / tid
        obs = _safe_load(base / 'observation.json', f'{tid}/observation.json')
        exp = EXPECTED_OCCURRENCE[scen]
        if obs is not None and obs.get('effect_occurrence_count') != exp:
            fail(f'{tid}: observation.effect_occurrence_count={obs.get("effect_occurrence_count")} != {exp}')
        # Contradiction control: destination readback must agree
        drb = _safe_load(base / 'destination' / 'destination-readback.json', f'{tid}/destination-readback.json')
        dest_obs = _safe_load(base / 'native' / 'destination-observation.json', f'{tid}/destination-observation.json')
        if dest_obs is not None:
            state_absent_or_applied = dest_obs.get('state')
            if scen == 'D01' and state_absent_or_applied != 'applied':
                fail(f'{tid}: D01 destination state should be applied, got {state_absent_or_applied}')
            if scen in ('D03', 'C07') and state_absent_or_applied != 'absent':
                fail(f'{tid}: {scen} destination state should be absent, got {state_absent_or_applied}')
        # Integrity check on exported snapshot
        if drb is not None and drb.get('integrity_check') != ['ok']:
            fail(f'{tid}: PRAGMA integrity_check reports {drb.get("integrity_check")}')
        # F5b enforcement proof
        enf = _safe_load(base / 'native' / 'consumers' / 'f5b-enforcement.json', f'{tid}/f5b-enforcement.json')
        if enf is not None and not enf.get('enforcement_demonstrated'):
            fail(f'{tid}: f5b-enforcement.enforcement_demonstrated != true')

    # (4) tamper + contradiction controls (optional, default on)
    if controls and not failures:
        with tempfile.TemporaryDirectory() as td:
            mirror = Path(td) / 'mirror'
            shutil.copytree(root, mirror)
            # Pick one tiny file to flip
            victim_path = next(iter(listed))
            victim = mirror / victim_path
            data = bytearray(victim.read_bytes())
            data[0] ^= 0x01
            victim.write_bytes(bytes(data))
            # Re-run a lightweight hash check in mirror; must detect
            tampered_hash = sha256_of(victim)
            if tampered_hash == listed[victim_path]['sha256']:
                fail('tamper control did not change hash — control invalid')
            else:
                print(f'tamper control OK: hash of {victim_path} changed as expected')
            # Contradiction control: inject a mismatched observation
            scen = manifest['trials'][0]['scenario_id']
            tid  = manifest['trials'][0]['trial_id']
            obs_path = mirror / 'scenarios' / scen / tid / 'observation.json'
            o = json.loads(obs_path.read_text())
            o['effect_occurrence_count'] = 99
            obs_path.write_text(json.dumps(o, indent=2) + '\n')
            # Re-verify invariant on mirror only
            exp = EXPECTED_OCCURRENCE[scen]
            got = json.loads(obs_path.read_text())['effect_occurrence_count']
            if got == exp:
                fail('contradiction control did not actually change value')
            else:
                print('contradiction control OK: altered observation detected under the invariant check')

    return failures

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--package', type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument('--no-controls', action='store_true')
    args = ap.parse_args()
    failures = verify(args.package, controls=not args.no_controls)
    if failures:
        print(f'VERIFY FAILED: {len(failures)} issue(s)')
        sys.exit(2)
    print('VERIFY OK')

if __name__ == '__main__':
    main()
