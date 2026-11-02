"""Subprocess probe: run the Control Plane F4 flow at ANY Control Plane checkout and print the raw run.json texts (byte-comparison across base/head, N25).

usage: probe_cp.py <cp-root> <registry-root> <carry: omit|false|true>
Same flow as the Control Plane's own legacy-golden generator (construct -> decide(authorized) -> execute -> decide(hold, aged status)); deterministic uuids.
"""
import base64
import itertools
import json
import sys
import tempfile
import uuid
from datetime import timedelta
from pathlib import Path

cp_root, reg_root, carry = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
for entry in reversed([cp_root, cp_root / "src", reg_root, reg_root / "baseline" / "execution-runtime", reg_root / "tests"]):
    sys.path.insert(0, str(entry))
import nacl.bindings as nb  # noqa: E402
import r08_support as r  # noqa: E402
import s01_support as s  # noqa: E402
from registry_adapters import ed25519_verifier as ev  # noqa: E402
from registry_successor import common as c, v2_age_bounds as f4, verify as v  # noqa: E402
import agent_control_plane.bounded as bm  # noqa: E402
import agent_control_plane.registry_f4_age_governance as gov  # noqa: E402
from agent_control_plane.bounded import BoundedRecordStore, LocalRefundDestination, ObservationPolicy  # noqa: E402
from agent_control_plane.registry_f4_age_governance import GovernedAgeWorkflow, GovernedScope, SelectionMaterial  # noqa: E402
from tests.test_bounded_authorization import NOW, PROFILE, manifest, tenant_proposal, tenant_resolver_for, TENANT  # noqa: E402

bm._now = lambda: NOW
gov._now = lambda: NOW
counter = itertools.count(1)
uuid.uuid4 = lambda: uuid.UUID(int=next(counter))
PK, SK = nb.crypto_sign_seed_keypair(bytes(range(32)))
act = manifest()["actions"][0]
ACTION, INST, DOM = act["action_id"], act["authority_context"]["institution_id"], act["authority_context"]["authority_domain"]
OP = "refund-issue-routine"
trust = v.TrustSnapshot("snap-test-1", 1, "2026-10-07T00:00:00Z", (v.IssuerEntry(s.KEY_ID, "issuer-test-1", "ed25519", PK, (v.AuthorityGrant("consumer-test", TENANT, INST, DOM, OP),)),))


def material(n):
    rec = r.seal_record(dict(r.make_record(), contract_version="r08-v2", family=f4.FAMILY_F4, record_id="f4-age-record", payload={"status_max_age_seconds": n, "approval_max_age_seconds": n}))
    stmt = r.make_statement_v2(rec, family=f4.FAMILY_F4, consumer_id="consumer-test", scope={"tenant": TENANT.lower(), "institution": INST, "authority_domain": DOM}, operation=OP,
                               effective={"valid_from": "2026-10-01T00:00:00Z", "valid_until": "2026-10-06T00:00:00Z"}, issued_at="2026-10-01T00:00:00Z")
    sig = base64.b64encode(nb.crypto_sign(s.V2_DOMAIN + c.canonical_bytes(stmt), SK)[:64]).decode()
    return SelectionMaterial(r.dumps(rec), r.dumps(s.envelope(stmt, signature=sig, pub=PK)), trust)


MAIN = material(60)


def build(tmp, resolver=None, mat=None):
    p = tenant_proposal()
    kw = {} if carry == "omit" else {"carry_selection_evidence": carry == "true"}
    return p, GovernedAgeWorkflow(scope=GovernedScope("consumer-test", TENANT.lower(), ACTION, OP), selection_source=lambda: (mat or MAIN), verifier=ev.Ed25519Verifier(), allow_test_time=True,
                                  construction_time=NOW, manifest=manifest(), resolver=resolver or tenant_resolver_for(p), destination=LocalRefundDestination(tmp / "destination.json"),
                                  records=BoundedRecordStore(tmp / "run.json", "run-1"), observation_policy=ObservationPolicy(max_age_seconds=300, clock_tolerance_seconds=5), **kw)


tmp = Path(tempfile.mkdtemp(dir="/dev/shm"))
p, flow = build(tmp)
d = flow.decide(p, now=NOW)
flow.execute(p, d, adapter_id=p.adapter_id, now=NOW)
(tmp / "hold").mkdir()
rr = tenant_resolver_for(p)
ctx = rr.contexts[PROFILE]
rr.statuses[ctx["grant"]["grant_id"]].observed_at = (NOW - timedelta(seconds=30)).isoformat()
_, hold = build(tmp / "hold", resolver=rr, mat=material(10))
hold.decide(p, now=NOW)
print(json.dumps({"main": (tmp / "run.json").read_bytes().decode(), "hold": (tmp / "hold" / "run.json").read_bytes().decode()}, sort_keys=True))
