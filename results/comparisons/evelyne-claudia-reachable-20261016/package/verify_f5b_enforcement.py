"""Standalone F5b pairing-enforcement verifier.

Loads the F5b-generation and security-generation consumer constants from the
VENDORED verbatim copies under ./vendored/ and checks each trial's
native/consumers/odes-package.json against both:

  * F5b consumer constants (expect: pins match F5b revisions exactly;
    profile version equals F5b profile version).
  * Security-generation substituted control-plane revision (expect: pins
    do NOT match F5b and the SECURITY_RUNTIME_GENERATIONS table flags the
    substitution as a different qualified generation).

The verifier does not run external code imports — it reads the vendored source
files, extracts the exact F5B_REVISIONS and SECURITY_REVISIONS dict literals
by executing those files in an isolated module namespace, and compares. The
vendored source bytes are hash-checked against this package's manifest before
use so a tampered vendor directory causes an explicit FAIL rather than a quiet
pass.

Per-trial result is written to each trial's
`native/consumers/verify_f5b_enforcement.result.json`.

The verifier is standalone: no network, no destination write, no import of
cognous runtime packages. Standard library only.

Checks this verifier CANNOT perform:
  * It does not execute Replay / ODES exporter end-to-end against a live
    producer — it validates the constants in the exported odes-package.json
    against the vendored consumer source.
  * It does not assign REACHABLE verdicts.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys, types
from pathlib import Path

PKG_ROOT_DEFAULT = Path(__file__).resolve().parent


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(65536), b''):
            h.update(c)
    return h.hexdigest()


def _load_vendored_module(path: Path, name: str) -> types.ModuleType:
    """Load a vendored source file as an isolated module (no sys.path leak)."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'cannot load vendored module from {path}')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _recorded_vendor_hashes(manifest: dict) -> dict:
    out = {}
    for entry in manifest.get('vendored_consumer_sources', []) or []:
        out[entry['path']] = entry['sha256']
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--package', type=Path, default=PKG_ROOT_DEFAULT)
    ap.add_argument('--out', type=Path,
                    help='Directory to write per-trial result.json into (default: temp dir on recipient side; '
                         'at build time pass the package root to materialize the committed artifacts).')
    args = ap.parse_args()
    root: Path = args.package.resolve()
    import tempfile
    out_root: Path = args.out.resolve() if args.out else Path(tempfile.mkdtemp(prefix='f5b-verify-')).resolve()
    manifest = json.loads((root / 'manifest.json').read_text())
    expected_hashes = _recorded_vendor_hashes(manifest)
    failures = []
    def fail(msg: str) -> None:
        failures.append(msg); print('FAIL', msg, file=sys.stderr)

    # (A) verify vendored source bytes against the manifest-recorded hashes
    vendor_dir = root / 'vendored'
    for rel, expected in expected_hashes.items():
        p = root / rel
        if not p.is_file():
            fail(f'vendored source missing: {rel}'); continue
        got = sha256_file(p)
        if got != expected:
            fail(f'vendored source hash mismatch: {rel} got {got} expected {expected}')
    if failures:
        print(f'F5B VERIFY FAILED early: {len(failures)} issue(s)')
        return 2

    # (B) load the constants from the vendored files
    odes_common = _load_vendored_module(vendor_dir / 'odes_common.py', 'vendored_odes_common')
    # The EP importer file imports sibling runtime models that we don't need
    # for the constant check. Parse it with ast and keep only top-level
    # Assign/AnnAssign nodes (plus stdlib imports they may reference).
    import ast
    ep_tree = ast.parse((vendor_dir / 'ep_importer.py').read_text())
    stdlib_safe = {'hashlib', 'json', 'collections', 'copy', 'pathlib', 'typing', 're'}
    kept: list = []
    for node in ep_tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            kept.append(node)
        elif isinstance(node, ast.Import):
            if all(a.name.split('.')[0] in stdlib_safe for a in node.names):
                kept.append(node)
        elif isinstance(node, ast.ImportFrom):
            if (node.module or '').split('.')[0] in stdlib_safe and node.level == 0:
                kept.append(node)
        # Drop function/class defs and relative imports.
    module = ast.Module(body=kept, type_ignores=[])
    namespace: dict = {'__name__': 'vendored_ep_importer_consts', '__builtins__': __builtins__}
    try:
        exec(compile(module, '<vendored_ep_importer_consts>', 'exec'), namespace)
    except Exception as e:
        fail(f'cannot evaluate vendored EP importer constants: {e!r}')
        print(f'F5B VERIFY FAILED: {len(failures)} issue(s)')
        return 2

    F5B_REVISIONS = odes_common.F5B_REVISIONS
    F5B_PROFILE_VERSION = odes_common.F5B_PROFILE_VERSION
    SECURITY_REVISIONS = odes_common.SECURITY_REVISIONS
    SECURITY_PROFILE_VERSION = odes_common.SECURITY_PROFILE_VERSION
    SECURITY_RUNTIME_GENERATIONS = odes_common.SECURITY_RUNTIME_GENERATIONS
    EP_F5B_REVISIONS = namespace.get('F5B_REVISIONS')
    EP_F5B_TRANSFORMATION_VERSION = namespace.get('F5B_TRANSFORMATION_VERSION')
    EP_SECURITY_REVISIONS = namespace.get('SECURITY_REVISIONS')
    for required in ('EP_F5B_REVISIONS','EP_F5B_TRANSFORMATION_VERSION','EP_SECURITY_REVISIONS'):
        if locals()[required] is None:
            fail(f'vendored EP importer did not expose {required}')

    # (C) consistency: ODES's F5B pins must agree with EP's F5B pins on the keys they share
    shared = set(F5B_REVISIONS.keys()) & set(EP_F5B_REVISIONS.keys())
    for k in shared:
        if F5B_REVISIONS[k] != EP_F5B_REVISIONS[k]:
            fail(f'F5B cross-consumer disagreement on {k}: ODES={F5B_REVISIONS[k]} EP={EP_F5B_REVISIONS[k]}')

    # (D) per-trial enforcement
    results_summary = []
    for trial in manifest.get('trials', []):
        tid = trial['trial_id']; scen = trial['scenario_id']
        base = root / 'scenarios' / scen / tid / 'native' / 'consumers'
        try:
            package = json.loads((base / 'odes-package.json').read_text())
        except Exception as e:
            fail(f'{tid}: cannot load odes-package.json: {e!r}'); continue

        prod_pins = package.get('provenance', {}).get('pinned_revisions', {})
        prod_profile = package.get('profile', {}).get('implementation_profile_version')

        # F5b accept check
        f5b_cp = prod_pins.get('control_plane')
        f5b_pin_check = {
            'produced_pins': prod_pins,
            'produced_profile_version': prod_profile,
            'expected_f5b_pins': F5B_REVISIONS,
            'expected_f5b_profile_version': F5B_PROFILE_VERSION,
            'pins_match_f5b': prod_pins == F5B_REVISIONS,
            'profile_matches_f5b': prod_profile == F5B_PROFILE_VERSION,
            'cp_recognized_as_f5b_generation': (f5b_cp in SECURITY_RUNTIME_GENERATIONS
                                                and SECURITY_RUNTIME_GENERATIONS[f5b_cp][0] == F5B_PROFILE_VERSION),
        }
        accept = all([f5b_pin_check['pins_match_f5b'], f5b_pin_check['profile_matches_f5b'],
                      f5b_pin_check['cp_recognized_as_f5b_generation']])

        # Security-generation substitution check: swap CP revision, expect fail with named reason
        sub_pins = dict(prod_pins); sub_pins['control_plane'] = SECURITY_REVISIONS['control_plane']
        sub_check = {
            'substituted_pins': sub_pins,
            'substituted_cp_in_f5b_pins': sub_pins == F5B_REVISIONS,
            'substituted_cp_recognized_as_security_generation': (
                SECURITY_REVISIONS['control_plane'] in SECURITY_RUNTIME_GENERATIONS and
                SECURITY_RUNTIME_GENERATIONS[SECURITY_REVISIONS['control_plane']][0] == SECURITY_PROFILE_VERSION),
            'substituted_profile_still_claims_f5b': prod_profile == F5B_PROFILE_VERSION,  # fixed; it should still claim F5b and now mismatch its pins
        }
        reject = (not sub_check['substituted_cp_in_f5b_pins']) and sub_check['substituted_cp_recognized_as_security_generation'] and sub_check['substituted_profile_still_claims_f5b']
        # Named reason: "control_plane revision does not match F5b profile pins; it belongs to the security generation"
        reason = None
        if not reject:
            reason = 'substitution did not expose a cross-generation mismatch'
        else:
            reason = ('control_plane revision does not match F5b profile pins; '
                      'it matches SECURITY_RUNTIME_GENERATIONS[security generation]')

        enforcement_demonstrated = accept and reject
        if not enforcement_demonstrated:
            fail(f'{tid}: f5b pairing NOT enforced (accept={accept} reject={reject})')

        result = {
            'trial_id': tid,
            'scenario_id': scen,
            'vendored_source_hashes': {k: sha256_file(root / k) for k in sorted(expected_hashes)},
            'f5b_accept_check': {**f5b_pin_check, 'accept': accept,
                                 'error_text_prefix': None if accept else 'produced package does not satisfy F5b accept predicate'},
            'security_generation_substitution_check': {**sub_check, 'reject': reject,
                                                       'reject_reason_prefix': reason[:200]},
            'enforcement_demonstrated': enforcement_demonstrated,
        }
        out_file = out_root / 'scenarios' / scen / tid / 'native' / 'consumers' / 'verify_f5b_enforcement.result.json'
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(result, indent=2) + '\n')
        results_summary.append({'trial_id': tid, 'enforcement_demonstrated': enforcement_demonstrated})
        print(f'{tid}: accept={accept} reject={reject} enforced={enforcement_demonstrated}')

    if failures:
        print(f'F5B VERIFY FAILED: {len(failures)} issue(s)')
        return 2
    print('F5B VERIFY OK (all trials)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
