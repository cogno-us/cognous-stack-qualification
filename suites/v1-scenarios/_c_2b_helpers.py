"""Shared bootstrap and harness for catalog scenarios C03, C04, C10, C11, C12, C13 and C14 (batch 2b).

SPDX-License-Identifier: Apache-2.0

Everything here runs against the FROZEN F5b-repaired seven-component bounded synthetic reference (verified pristine at
the exact pinned commits by the batch-1 helpers this module imports and never modifies) and, for C03/C04, against two
additional exactly pinned external checkouts:

    SCN_INDEX_DIR        cogno-us/cognous-evidence-registry @ d5e45d275cb301d9684b543e93b05997991d1cf2  (The Index)
    SCN_BITREP_DIR       cogno-us/cognous-evidence-attestation @ 5b5077dafde232a7801cb425c4efddcffb468723 (BitRep)
    SCN_INDEX_CHAIN_DIR  a runner-owned COPY of ``$SCN_INDEX_DIR/chain`` with ``npm ci --ignore-scripts`` already run
                         (node_modules would make the pin itself non-pristine, so the chain driver runs from a copy whose
                         tracked files are verified byte-identical to the pin; see ``verify_chain_copy``)

When a variable is unset the tests that need it are SKIPPED with the reason (never silently passed); the CI ``scenarios``
job must provide them (see the batch report). No product code, pin, profile or default is changed. No network, payment,
model or production effect is used (the only socket is the loopback JSON-RPC of a disposable Ganache chain in a child
process for the Index chain driver). Linux only (owner decision D2).

Determinism (owner decision D3): every case executes TWICE from fresh work directories and the two normalised
observations are compared (MATCH/MISMATCH is recorded and asserted). Hard gate (D5): zero unauthorized effects and zero
excess duplicate effects in every run of every case that can mutate a destination.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import platform
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True  # a bytecode file inside a pinned checkout would make it non-pristine

import _d02_d05_d09_helpers as H1  # noqa: E402  (batch-1 helpers, imported, never modified)
import _d06_d07_d08_helpers as H2  # noqa: E402
from _d02_d05_d09_helpers import Checks, canonical, digest, no_network  # noqa: E402,F401  (fixtures/utilities re-exported)
from pristine_checkout import require_pristine  # noqa: E402  (tools/ is on sys.path via the batch-1 helpers)

HERE = Path(__file__).resolve().parent
import _pins  # noqa: E402  (suites/ is on sys.path via the batch-1 helpers)
FROZEN_INDEX = _pins.FROZEN_INDEX
FROZEN_BITREP = _pins.FROZEN_BITREP
SCENARIO_VERSION = '1.0.0'
H = H1  # convenience alias for the route helpers (flow_a, flow_b, execute_a, db_summary, ...)


# ----------------------------------------------------------------------------------------------
# reference + pins
# ----------------------------------------------------------------------------------------------

def reference():
    """Verify the seven pins (both batch-1 loaders) and return the batch-1 reference object."""
    H2.reference()
    return H1.reference()


@pytest.fixture(scope='module')
def pinned_reference():
    """Module fixture: the seven pins verified pristine before use and again after the module's tests."""
    ref = reference()
    yield ref
    H1.assert_pins_still_pristine()
    H2.assert_pins_still_pristine()


def external_pin(var, sha, label):
    """Path of an external pinned checkout, verified pristine, or SKIP with the exact reason."""
    value = os.environ.get(var)
    if not value:
        pytest.skip(f'{var} is not set: the {label} pin ({sha}) was not provided to this run; CI must fetch it '
                    f'(see the batch report). Not a pass.')
    path = Path(value).resolve()
    require_pristine(path, sha, label)
    return path


def verify_chain_copy(index_pin, chain_copy):
    """The chain copy must hold exactly the pinned tracked files, byte-identical (blob hash), plus node_modules only."""
    tree = subprocess.check_output(['git', '-C', str(index_pin), 'ls-tree', '-r', 'HEAD', 'chain/'], text=True)
    expected = {}
    for row in tree.splitlines():
        meta, name = row.split('\t', 1)
        expected[name[len('chain/'):]] = meta.split()[2]
    actual = {}
    for path in sorted(Path(chain_copy).rglob('*')):
        rel = path.relative_to(chain_copy)
        if rel.parts and rel.parts[0] == 'node_modules':
            continue
        if path.is_file() or path.is_symlink():
            actual[str(rel)] = subprocess.check_output(['git', 'hash-object', '--no-filters', str(path)], text=True).strip()
    if actual != expected:
        raise ValueError('index chain copy differs from the pinned chain/ tree: '
                         f'missing={sorted(set(expected) - set(actual))} extra={sorted(set(actual) - set(expected))} '
                         f'changed={sorted(k for k in expected if k in actual and actual[k] != expected[k])}')
    if not (Path(chain_copy) / 'node_modules' / 'ethers').is_dir():
        raise ValueError('index chain copy has no node_modules (run npm ci --ignore-scripts in the copy)')


def external_identity():
    """Identity of the optional external pins for the evidence record (only those actually provided)."""
    out = {}
    for var, sha, repo in (('SCN_INDEX_DIR', FROZEN_INDEX, 'cogno-us/cognous-evidence-registry'),
                           ('SCN_BITREP_DIR', FROZEN_BITREP, 'cogno-us/cognous-evidence-attestation')):
        if os.environ.get(var):
            out[var] = {'repository': repo, 'commit': sha, 'verified_pristine_in_this_run': True}
    if os.environ.get('SCN_INDEX_CHAIN_DIR'):
        out['SCN_INDEX_CHAIN_DIR'] = {'derived_from': FROZEN_INDEX, 'tracked_files_verified_identical_to_pin': True}
    return out


# ----------------------------------------------------------------------------------------------
# evidence harness: run twice, compare, record
# ----------------------------------------------------------------------------------------------

def run_c_case(request, record_property, tmp_path, scenario, trial, *, gate=True, extra=None):
    """Execute ``trial(workdir, monkeypatch, checks)`` twice from fresh work directories, compare, record, assert.

    ``gate`` applies the D5 hard gate (a trial must return ``unauthorized_effects`` and ``excess_duplicate_effects``
    and both must be 0). Scenarios that cannot mutate a destination pass ``gate=False``; their JSON says so.
    A harness exception is recorded as a violation (INCONCLUSIVE, never a pass).
    """
    ref = reference()
    runs = []
    for n in (1, 2):
        work = tmp_path / f'run-{n}'
        work.mkdir()
        checks = Checks()
        mp = pytest.MonkeyPatch()
        try:
            observed = trial(work, mp, checks)
        except pytest.skip.Exception:
            raise
        except Exception as exc:
            observed = {'harness_exception': f'{type(exc).__name__}: {exc}'}
            checks.violations.append(f'harness exception (INCONCLUSIVE, not a pass): {type(exc).__name__}: {exc}')
        finally:
            mp.undo()
        if gate and 'harness_exception' not in observed:
            checks.equal(observed.get('unauthorized_effects'), 0, 'hard gate: unauthorized effects')
            checks.equal(observed.get('excess_duplicate_effects'), 0, 'hard gate: excess duplicate effects')
        runs.append({'run': n, 'observed': observed, 'violations': list(checks.violations)})
    d1, d2 = digest(runs[0]['observed']), digest(runs[1]['observed'])
    comparison = {'assertion': 'normalised observation of run 1 equals run 2 under unchanged conditions',
                  'run1_digest': d1, 'run2_digest': d2, 'verdict': 'MATCH' if d1 == d2 else 'MISMATCH'}
    failed = bool(runs[0]['violations'] or runs[1]['violations'])
    environment = H1.environment_identity()
    environment['external_pins'] = external_identity()
    payload = {'test': request.node.name, 'scenario': scenario, 'environment': environment,
               'hard_gate_applied': gate, 'run1': runs[0], 'run2': runs[1], 'determinism': comparison,
               'verdict': 'FAIL' if failed or comparison['verdict'] == 'MISMATCH' else 'PASS',
               'extra': extra or {},
               'assertion_scope': 'named synthetic assertion against the frozen bounded reference; not whole-scenario acceptance'}
    text = json.dumps(payload, indent=2, sort_keys=True, default=str)
    record_property('scenario_evidence', text)
    target = os.environ.get('SCN_EVIDENCE_DIR')
    if target:
        Path(target).mkdir(parents=True, exist_ok=True)
        (Path(target) / (request.node.name.replace('/', '_') + '.json')).write_text(text + '\n')
    assert not runs[0]['violations'], f'run 1 violations: {runs[0]["violations"]}'
    assert not runs[1]['violations'], f'run 2 violations: {runs[1]["violations"]}'
    assert comparison['verdict'] == 'MATCH', f'determinism mismatch between run 1 and run 2: {comparison}'
    return payload


# ----------------------------------------------------------------------------------------------
# BitRep (pinned 5b5077da): synthetic keys, trust snapshots, signed statements
# ----------------------------------------------------------------------------------------------

NOW = 1800000000  # fixed evaluation time of the synthetic cases (not a production current-time result)
SEED_A = bytes(range(32))         # public synthetic test seeds, never deploy
SEED_B = bytes(range(1, 33))
SEED_M = bytes(range(2, 34))      # "mallory": the attacker
_BITREP = None


def bitrep(pin):
    """Import the pinned BitRep modules (appended to sys.path so no reference-component module name is shadowed)."""
    global _BITREP
    if _BITREP is None:
        sys.path.append(str(pin))
        import models.verification as mv
        import utils.trust as ut
        import utils.verification as uv
        _BITREP = {'pin': pin, 'AttestationEnvelope': mv.AttestationEnvelope, 'SignedStatement': mv.SignedStatement,
                   'TrustRegistry': ut.TrustRegistry, 'TrustUnavailable': ut.TrustUnavailable,
                   'canonical_bytes': uv.canonical_bytes, 'statement_digest': uv.statement_digest,
                   'verify_attestation': uv.verify_attestation, 'strict_json': ut.strict_json}
        _BITREP = type('BitRepModules', (), _BITREP)
    return _BITREP


def _ed25519(seed):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    return Ed25519PrivateKey.from_private_bytes(seed)


def pub_b64(seed):
    from cryptography.hazmat.primitives import serialization
    return base64.b64encode(_ed25519(seed).public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()


def content_digest(data=b'synthetic evidence'):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def key_record(issuer='issuer:alice', key_id='key:1', seed=SEED_A, valid_from=NOW - 100, valid_until=NOW + 1000, revoked_at=None):
    return {'issuer': issuer, 'key_id': key_id, 'public_key': pub_b64(seed), 'valid_from': valid_from,
            'valid_until': valid_until, 'revoked_at': revoked_at}


def trust_doc(keys=None, *, audience='index:test', published_at=NOW - 100, valid_until=NOW + 1000):
    return {'registry_version': 'bitrep-trust/1', 'audience': audience, 'published_at': published_at, 'valid_until': valid_until,
            'keys': [key_record()] if keys is None else keys}


def statement_dict(**over):
    data = {'protocol_version': 'bitrep-attestation/1', 'algorithm': 'Ed25519', 'attestation_id': 'att-001',
            'issuer': 'issuer:alice', 'key_id': 'key:1', 'subject': 'claim:42', 'statement_type': 'asserts',
            'audience': 'index:test', 'content_digest': content_digest(), 'issued_at': NOW - 10, 'not_before': NOW - 10,
            'expires_at': NOW + 100}
    data.update(over)
    return data


def signed_envelope(br, seed=SEED_A, *, domain_separated=True, **over):
    """A well-formed envelope dict signed by ``seed`` over the canonical bytes of the (possibly overridden) statement."""
    data = statement_dict(**over)
    st = br.SignedStatement.model_validate(data)
    raw = br.canonical_bytes(st)
    if not domain_separated:
        raw = raw[len(b'BitRep attestation v1\n'):]
    return {'statement': data, 'signature': base64.b64encode(_ed25519(seed).sign(raw)).decode()}


def verify_dict(br, envelope, doc, now=NOW):
    """Library-level verification of an envelope dict; a pre-verification wire rejection is reported as such."""
    try:
        att = br.AttestationEnvelope.model_validate(copy.deepcopy(envelope))
    except Exception as exc:
        return {'outcome': 'rejected', 'reason': 'wire_rejected:' + type(exc).__name__, 'assurance': 'none'}
    try:
        res = br.verify_attestation(att, br.TrustRegistry.model_validate(copy.deepcopy(doc)), now)
    except br.TrustUnavailable:
        return {'outcome': 'unavailable', 'reason': 'trust_unavailable', 'assurance': 'none'}
    return {'outcome': res.outcome, 'reason': res.reason, 'assurance': res.assurance}


def flip_bit(b64_signature):
    raw = bytearray(base64.b64decode(b64_signature))
    raw[0] ^= 0x01
    return base64.b64encode(bytes(raw)).decode()


class BitRepHttp:
    """The pinned BitRep admission router on a private in-memory database; time and trust are test-supplied dependencies
    (the same dependency seams the pinned BitRep tests use), no network, no application storage."""

    def __init__(self, br, doc, now=NOW):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from db.connection import Base
        import api.attestations as attestations
        from models.attestation import AcceptedAttestationModel
        self.model = AcceptedAttestationModel
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.state = {'now': now, 'doc': doc}

        def get_db():
            db = self.session_factory()
            try:
                yield db
            finally:
                db.close()

        def get_now():
            return self.state['now']

        def get_trust():
            try:
                return br.TrustRegistry.model_validate(copy.deepcopy(self.state['doc']))
            except Exception as exc:  # pragma: no cover
                raise attestations.HTTPException(503, detail={'reason': 'trust_unavailable'}) from exc
        app = FastAPI()
        app.include_router(attestations.router)
        app.dependency_overrides[attestations.get_db] = get_db
        app.dependency_overrides[attestations.get_now] = get_now
        app.dependency_overrides[attestations.get_trust] = get_trust
        self.client = TestClient(app)

    def post(self, path, body):
        raw = body if isinstance(body, (bytes, bytearray)) else json.dumps(body).encode()
        return self.client.post(path, content=raw, headers={'content-type': 'application/json'})

    def stored(self):
        db = self.session_factory()
        try:
            return sorted((r.issuer, r.attestation_id, r.statement_digest) for r in db.query(self.model).all())
        finally:
            db.close()


def http_view(resp):
    body = resp.json()
    detail = body.get('detail') if isinstance(body, dict) else None
    reason = (detail or {}).get('reason') if isinstance(detail, dict) else None
    return {'status': resp.status_code, 'reason': reason or (body.get('reason') if isinstance(body, dict) else None),
            'admission': body.get('admission') if isinstance(body, dict) else None}


# ----------------------------------------------------------------------------------------------
# The Index (pinned d5e45d27): the Python API under test
# ----------------------------------------------------------------------------------------------
_INDEX_READY = False


def index_client(pin):
    """A fresh Index API client with fresh in-memory services (same wiring as the pinned probes' ``index_client``)."""
    global _INDEX_READY
    if not _INDEX_READY:
        sys.path.append(str(pin))
        _INDEX_READY = True
    from fastapi.testclient import TestClient
    from app.claims import service as cs
    from app.evidence import service as es
    from app.governance import service as gs
    from app.api import claims, evidence, governance
    cs.claims_service = cs.ClaimsService()
    es.evidence_service = es.EvidenceService()
    gs.governance_service = gs.GovernanceService()
    claims.claims_service = cs.claims_service
    evidence.evidence_service = es.evidence_service
    governance.governance_service = gs.governance_service
    from app.main import app
    return TestClient(app)


def index_adapter(index_pin, bitrep_pin):
    """The pinned Index-side BitRep binding verifier (chain/python/bitrep_adapter.py)."""
    os.environ['BITREP_ROOT'] = str(bitrep_pin)
    sys.path.append(str(Path(index_pin) / 'chain' / 'python'))
    import bitrep_adapter
    return bitrep_adapter


def run_node_driver(driver, chain_dir, work, **env):
    """Run a node driver from the verified chain copy; returns the parsed JSON observation."""
    proc = subprocess.run(['node', str(driver)], capture_output=True, text=True, timeout=300, cwd=str(work),
                          env={**os.environ, 'SCN_INDEX_CHAIN_DIR': str(chain_dir), 'NODE_NO_WARNINGS': '1', **env})
    if proc.returncode != 0:
        raise RuntimeError(f'node driver failed: {proc.stderr[-1500:]}')
    return json.loads(proc.stdout)


# ----------------------------------------------------------------------------------------------
# independent confinement observer (C10): audit hook, active only inside a window
# ----------------------------------------------------------------------------------------------
WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
WATCHED = {'subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn', 'os.fork', 'os.forkpty', 'socket.connect', 'socket.bind',
           'socket.getaddrinfo', 'socket.gethostbyname', 'os.rename', 'os.replace', 'os.remove', 'os.rmdir', 'os.mkdir',
           'os.symlink', 'os.link', 'os.truncate', 'os.chmod', 'shutil.copyfile', 'shutil.move', 'sqlite3.connect', 'ctypes.dlopen',
           'os.putenv'}


class Observer:
    """Records process, network, filesystem-write and sqlite events issued by this process while the window is open.

    It observes (it cannot block): a prohibited event is a finding, not a prevented act. Reads are listed only by
    count; write-class events are classified against the declared boundary directory.
    """
    _installed = False
    _current = None

    def __init__(self, boundary):
        self.boundary = Path(boundary).resolve()
        self.events = []

    @classmethod
    def _hook(cls, event, args):
        obs = cls._current
        if obs is None:
            return
        if event == 'open':
            path, _mode, flags = args
            if isinstance(path, int):
                return
            write = bool(flags & WRITE_FLAGS) if isinstance(flags, int) else False
            if write:
                obs.events.append(('open-write', str(os.fsdecode(path))))
            else:
                obs.events.append(('open-read', str(os.fsdecode(path))))
        elif event in WATCHED:
            def render(v):
                return os.fsdecode(v) if isinstance(v, (bytes, os.PathLike)) else repr(v)[:120]
            obs.events.append((event, ' '.join(render(a) for a in args)[:240]))

    def __enter__(self):
        if not Observer._installed:
            sys.addaudithook(Observer._hook)
            Observer._installed = True
        Observer._current = self
        return self

    def __exit__(self, *exc):
        Observer._current = None
        return False

    def _inside(self, text):
        first = text.split(' ')[0]
        if not first.startswith('/'):
            return True  # not a path (e.g. ':memory:')
        try:
            return Path(first).resolve().is_relative_to(self.boundary)
        except OSError:
            return False

    def report(self):
        kinds = {}
        for kind, _ in self.events:
            kinds[kind] = kinds.get(kind, 0) + 1
        process = sorted({k for k, _ in self.events if k in ('subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn', 'os.fork', 'os.forkpty')})
        network = sorted({k for k, _ in self.events if k.startswith('socket.')})
        writes = [(k, p) for k, p in self.events if k not in ('open-read',) and k not in ('subprocess.Popen', 'os.system', 'os.exec',
                  'os.posix_spawn', 'os.fork', 'os.forkpty') and not k.startswith('socket.')]
        outside = sorted({f'{k} {p}' for k, p in writes if not self._inside(p) and p.split(' ')[0] not in ('/dev/null',)})
        return {'event_counts': dict(sorted(kinds.items())), 'process_events': process, 'network_events': network,
                'write_class_events': len(writes), 'write_class_outside_boundary': outside}


def tree_snapshot(path):
    """Deterministic content snapshot of a directory (relative path -> type/size/sha256), symlinks not followed."""
    out = {}
    root = Path(path)
    if not root.exists():
        return out
    for p in sorted(root.rglob('*')):
        rel = str(p.relative_to(root))
        if p.is_symlink():
            out[rel] = ['symlink', os.readlink(p)]
        elif p.is_file():
            out[rel] = ['file', p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest()]
        else:
            out[rel] = ['dir']
    return out


def exc_text(exc):
    return f'{type(exc).__name__}: {str(exc)[:200]}'
