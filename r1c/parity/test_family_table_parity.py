"""CP/Replay effective-configuration parity (read-only). Each side is imported in its OWN subprocess from an exact-SHA checkout; nothing is shared at runtime.

Env: CP_SRC=<control-plane checkout>/src (b19c47dd...), REPLAY_SRC=<replay checkout>/src (6f45e288...). Fails (not skips) if unset or an import fails.
Compares: FAMILY_TABLE, SCHEMA_REVISIONS, composition order, field tuples, VERSION/DOMAIN/SCALAR_MAX, and the digest of one deterministic member built by the CP builders;
also that Replay's validator accepts the CP-built member and recomputes the same digest, and rejects it when a CP family row is altered.
"""
import json, os, subprocess, sys, textwrap

_CP = """
import sys, json; sys.path.insert(0, sys.argv[1])
from agent_control_plane import effective_configuration_binding as B, registry_effective_policy as E, registry_governed_policy as G
bound = {s: (None, "sha256:" + format(i + 1, "x") * 64) for i, s in enumerate(G.FAMILY_NAMES)}
scope = B.scope_identity("c\\u00e9-1", "t-1", "a-1", "i-1", "d-1")
rows = B.family_rows(bound, G.FAMILY_NAMES, E.FAMILY_TABLE, E.SCHEMA_REVISIONS)
m = B.build_members(scope=scope, host_profile_digest="sha256:" + "a" * 64, effective_profile_digest=None, f4_scalars=dict(zip(B.F4_FIELDS, (60, 120))),
                    other_scalars=dict(zip(B.OTHER_FIELDS, (1, 2, 3))), observation_policy=dict(zip(B.OBSERVATION_FIELDS, (5, 6))), families=rows)
print(json.dumps({"table": E.FAMILY_TABLE, "rev": E.SCHEMA_REVISIONS, "order": G.FAMILY_NAMES, "version": B.VERSION, "domain": B.DOMAIN, "smax": B.SCALAR_MAX,
  "fields": [B.RECORD_FIELDS, B.MEMBER_FIELDS, B.SCOPE_FIELDS, B.F4_FIELDS, B.OTHER_FIELDS, B.OBSERVATION_FIELDS, B.FAMILY_FIELDS], "record": B.mint(m)}))
"""
_REPLAY = """
import sys, json; sys.path.insert(0, sys.argv[1])
from agent_replay_bundle import effective_configuration as C
rec = json.loads(sys.argv[2])
print(json.dumps({"table": C.FAMILY_TABLE, "rev": C.SCHEMA_REVISIONS, "order": C.FAMILY_ORDER, "version": C.VERSION, "domain": C.DOMAIN, "smax": C.SCALAR_MAX,
  "fields": [C.RECORD_FIELDS, C.MEMBER_FIELDS, C.SCOPE_FIELDS, C.F4_FIELDS, C.OTHER_FIELDS, C.OBSERVATION_FIELDS, C.FAMILY_FIELDS],
  "defect": C.record_defect(rec), "digest": C.digest_of(rec["version"], rec["members"])}))
"""


def _run(code, *args):
    p = subprocess.run([sys.executable, "-I", "-c", textwrap.dedent(code), *args], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)


def _both():
    cp = _run(_CP, os.environ["CP_SRC"])
    return cp, _run(_REPLAY, os.environ["REPLAY_SRC"], json.dumps(cp["record"]))


def test_constants_and_tables_are_identical():
    cp, rp = _both()
    for k in ("table", "rev", "order", "version", "domain", "smax", "fields"):
        assert json.loads(json.dumps(cp[k])) == json.loads(json.dumps(rp[k])), k  # JSON-normalise tuple/list
    assert list(cp["table"]) == list(cp["order"])


def test_replay_accepts_cp_built_member_and_recomputes_the_same_digest():
    cp, rp = _both()
    assert rp["defect"] is None
    assert rp["digest"] == cp["record"]["digest"]


def test_replay_rejects_cp_member_with_altered_family_row():
    cp, _ = _both()
    bad = json.loads(json.dumps(cp["record"]))
    bad["members"]["families"][2]["contract_version"] = "r08-v99"
    assert _run(_REPLAY, os.environ["REPLAY_SRC"], json.dumps(bad))["defect"] == "invalid:families"
