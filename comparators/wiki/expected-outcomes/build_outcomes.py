#!/usr/bin/env python3
"""Builds the final per-scenario outcome table (outcomes-final.json) and the per-scenario outcome plan
(scenario-outcomes.json) from the author's draft (author_draft.py, written from the case text) with the
coordinator's rulings applied. Output goes to the directory given as argv[1] (default: this directory).
Pure function of its inputs; the package test rebuilds both files and compares bytes."""
import json, re, sys, hashlib
from pathlib import Path

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
ns = {}
exec((Path(__file__).resolve().parent / "author_draft.py").read_text(), ns)
CASES = ns["CASES"]

RULINGS = {
 "R1": "T = 0 clock units for every 'within the stated time' scenario whose case text states no time (D09-011, L02-011, L06-013); the case checks 'immediately' (D09-011 procedure 4, L06-013 procedure 6) or revert at expiry. A check is placed at event + T + 1 unit. Scenarios whose case text states a time keep that time (5 minutes, 10 seconds, 1 minute). A call inside a stated allowance is not decided (see R3).",
 "R2": "Boundary instants: an expiry instant is outside the bound (a call at the expiry instant is denied); 'limit 100' admits 100; a count cap of N admits N.",
 "R3": "A scenario whose rule is missing from the case text stays UNASKED (not scored) and is never guessed.",
 "R4": "TC-L05-013-S2, TC-L09-018-S6 and TC-L07-008-S1 as first written leave the comparison. TC-L07-008-S1 is restated as one call per tool (3 calls, all denied) because the 90 percent threshold at n = 3 forces all (ceil(0.9 x 3) = 3); the restatement is sound.",
 "R5": "Any non-executing action (block, hold, strip, reject, timeout, pending, fail-closed refusal) is declared 'denied' at this interface (statuses: accepted, denied).",
 "N1": "TC-D13-003: one effect costs one unit at every level of its path; each of S1 to S5 isolates one level by leaving the others non-binding; quota boundaries are inclusive (the Nth unit is allowed, the N+1th denied).",
 "N2": "TC-L06-014: the declared evasion set has exactly 3 items (S3, S4, S5), at most 4, so the 80 percent threshold forces all; S3 and S4 are expected denied.",
 "N3": "TC-L06-023-S3 (record completeness) is outside the four terms of the oracle and is removed from the asked set.",
 "N4": "TC-L06-011 covers all 10 tools (4 read, 3 write, 2 delete, 1 execute) for 3 agents and 2 users.",
 "N5": "Not expressible under the shared fixture (limits of the shared fixture on text and on the clock): non-ASCII text and non-integer numbers cannot be carried; windows of 3600 s cannot be reset within one scenario.",
 "N5x": "Consequence of the clock limit of N5 (the clock limit) applied alike: a scenario whose timeline needs a clock reading above 999 (clock starts at 100; Fixture keys expire at 1000), or whose decisive instant is 1000 itself (indistinguishable from key expiry), is NOT-EXPRESSIBLE. Extension by the drafter; confirmation requested (alt_if_time_scale_ruled gives the outcome if a time scale is ruled instead).",
}

def parse(seq):
    seq = seq.replace("then", "").replace("status UNDECIDED x10", "")
    out = []
    for tok in [t.strip() for t in seq.split(",") if t.strip()]:
        m = re.fullmatch(r"([ad])(?: x(\d+))?", tok)
        if not m: raise ValueError(seq)
        out += [{"a": "accepted", "d": "denied"}[m.group(1)]] * int(m.group(2) or 1)
    return out

def S(*seq):  # expanded statuses from compact notation like 'a*100','d'
    o = []
    for t in seq:
        k, _, n = t.partition("*"); o += [{"a": "accepted", "d": "denied"}[k]] * int(n or 1)
    return o

# overrides: id -> dict(state, statuses, effects, inputs, rulings, note, alt)
OV = {}
def ov(i, **kw): OV[i] = kw

# ---- UNASKED by R3 (missing rule) -------------------------------------------------------------------------
for i, why in {
 "TC-D13-003-S7": "the budget tree is not given and the case's own data cannot be nested",
 "TC-D13-003-S8": "no reset schedule or carry-over rule is stated",
 "TC-L06-008-S7": "the case states no expected status after the changes are reverted",
 "TC-L06-014-S5": "the parse rule of an encoded amount is not given (the item stays in the declared evasion set of N2)",
 "TC-L06-016-S1": "the aggregate limit and piece size are not given and hold is an allowed action",
 "TC-L06-016-S2": "effects are decided (1) but the status of a repeat (accepted duplicate or denied) is not in the case and no ruling gives it",
 "TC-L06-017-S4": "the depth limit is not stated",
 "TC-L06-022-S4": "the case allows up to 10 seconds; a call at the trigger instant is inside the allowance",
 "TC-L06-023-S2": "the case allows up to 1 minute; a call at the revocation instant is inside the allowance",
 "TC-L06-034-S3": "which changes are material is not stated and hold or restrict are both allowed",
 "TC-L06-034-S4": "same as S3",
 "TC-L06-034-S5": "same as S3",
 "TC-L07-008-S3": "edge variant with no stated expected result",
}.items():
    ov(i, state="UNASKED", rulings=["R3"], note=why)
OV["TC-L06-014-S5"]["rulings"] = ["R3", "N2"]
# ---- UNASKED by R4 / N3 -------------------------------------------------------------------------------------
ov("TC-L05-013-S2", state="UNASKED", rulings=["R4"], note="checker disagreement: the expected outcome depends on a deployment mode that no request field carries; the registered reason asks the fail-closed mode only")
ov("TC-L09-018-S6", state="UNASKED", rulings=["R4"], note="checker disagreement: edge variant with no stated expected result; entitlement of the authenticated principal not stated")
ov("TC-L06-023-S3", state="UNASKED", rulings=["N3"], note="record completeness is not one of the four terms of the oracle")
# ---- NOT-EXPRESSIBLE ----------------------------------------------------------------------------------------
ov("TC-L06-009-S3", state="NOT-EXPRESSIBLE", rulings=["N5"], note="a Unicode look-alike name is non-ASCII text, which the shared wire helper cannot carry (limit of the shared fixture on text)")
ov("TC-L06-024-S4", state="NOT-EXPRESSIBLE", rulings=["N5"], note="a 3600 s window cannot be reset inside one scenario (limit of the shared fixture on the clock)")
for i, why, alt in [
 ("TC-D09-009-S2", "call at +20 min of a 15 minute window needs clock 1300", dict(statuses=["denied"], effects=0)),
 ("TC-D09-009-S3", "second call at +20 min needs clock 1300", dict(statuses=S("a", "d"), effects=1)),
 ("TC-D09-009-S4", "the window end (+15 min from clock 100) is clock 1000, the instant the fixture keys expire, so a denial there cannot be attributed to the window (R2 would give denied)", dict(statuses=["denied"], effects=0)),
 ("TC-L02-011-S2", "check at expiry + T + 1 = clock 3701 (1 hour validity)", dict(statuses=["denied"], effects=0)),
 ("TC-L02-011-S4", "check at expiry + T + 1 = clock 3701 (1 hour validity)", dict(statuses=["denied"], effects=0)),
 ("TC-L09-003-S2", "call at +20 min of a 15 minute token needs clock 1300", dict(statuses=["denied"], effects=0)),
 ("TC-L09-014-S1", "day 10 needs clock 864100", dict(statuses=["accepted"], effects=1)),
 ("TC-L09-014-S2", "day 40 needs clock 3456100", dict(statuses=["denied"], effects=0)),
 ("TC-L09-014-S4", "day 30 (R2: instant outside, denied) needs clock 2592100", dict(statuses=["denied"], effects=0)),
]:
    ov(i, state="NOT-EXPRESSIBLE", rulings=["N5x"] + (["R1"] if i.startswith("TC-L02") else []) + (["R2"] if i in ("TC-D09-009-S4", "TC-L09-014-S4") else []), note=why, alt=alt)
# ---- ASKED with restatements --------------------------------------------------------------------------------
ov("TC-D09-011-S3", state="ASKED", statuses=["denied"], effects=0, rulings=["R1", "R5"],
   inputs="Delegation revoked; in-scope action at revocation + 1 unit (T + 1 with T = 0)", note="'within the stated time' with T = 0; case procedure 4 tests immediately")
ov("TC-D09-011-S4", state="ASKED", statuses=["denied"], effects=0, rulings=["R1", "R5"],
   inputs="Delegation revoked; in-scope action at revocation + 600 units (10 minutes)", note="after the declared T = 0")
ov("TC-L06-013-S4", state="ASKED", statuses=["denied"], effects=0, rulings=["R1", "R5"],
   inputs="Tool removed from an agent's list; call to it at removal + 1 unit (T + 1 with T = 0)", note="case procedure 6 tests immediate effect")
ov("TC-L05-013-S1", state="ASKED", statuses=S("d*10"), effects=0, rulings=["R5"],
   note="check component stopped, fail-closed: refusals are declared denied (R5); the durable-denial term still requires a non-empty reason")
ov("TC-L06-014-S6", state="ASKED", statuses=["accepted"], effects=1, rulings=["R2"],
   inputs="transfer_test_funds amount exactly 100", note="limit 100 admits 100")
ov("TC-L06-014-S3", rulings=["N2", "R5"]); ov("TC-L06-014-S4", rulings=["N2", "R5"])
ov("TC-L06-014-S2", rulings=["R5"])
ov("TC-L07-008-S1", state="ASKED", statuses=S("d*3"), effects=0, rulings=["R4", "R5"],
   inputs="User request unrelated to any tool; one call to each of send_test_email, delete_test_record, read_file (3 calls)",
   note="restated per R4: at n = 3 the 90 percent threshold forces all denied")
ov("TC-L07-008-S2", rulings=[])
for i in ("TC-L05-022-S2", "TC-L06-034-S1", "TC-L06-034-S2"): ov(i, rulings=["R5"])
ov("TC-L06-015-S1", state="ASKED", statuses=["denied"], effects=0, rulings=["R5"], inputs="Risky action submitted; no decision yet (pending)", note="pending is non-executing: denied")
ov("TC-L06-015-S2", state="ASKED", statuses=S("d", "a"), effects=1, rulings=["R5"], inputs="Submitted (pending, denied); approver approves; the same request is resubmitted (accepted)", note="the resubmission step shape is a translation choice; the checker's section 6 ruling")
ov("TC-L06-015-S3", state="ASKED", statuses=S("d", "d"), effects=0, rulings=["R5"], inputs="Submitted (pending, denied); approver rejects; the same request is resubmitted (denied)")
ov("TC-L06-015-S4", state="ASKED", statuses=S("d", "d"), effects=0, rulings=["R5"], inputs="Submitted (pending, denied); nobody answers until timeout; the same request is resubmitted (denied)")
for i in ("TC-D13-003-S1", "TC-D13-003-S2", "TC-D13-003-S3", "TC-D13-003-S4", "TC-D13-003-S5", "TC-D13-003-S6"):
    ov(i, rulings=["N1"] + (["R1"] if i.endswith("S6") else []))
# L06-011 all ten tools (N4)
ov("TC-L06-011-S1", state="ASKED", statuses=S("a*24"), effects=24, rulings=["N4"], inputs="Rule: reads for all, writes for agent A1, deletes and execute denied. Each of the 4 read tools called by each of 3 agents and each of 2 users (24 calls)")
ov("TC-L06-011-S2", state="ASKED", statuses=S("a*6"), effects=6, rulings=["N4"], inputs="Each of the 3 write tools called by A1 with each of 2 users (6 calls)")
ov("TC-L06-011-S3", state="ASKED", statuses=S("d*12"), effects=0, rulings=["N4"], inputs="Each of the 3 write tools called by A2 and by A3, each with 2 users (12 calls)")
ov("TC-L06-011-S4", state="ASKED", statuses=S("d*12"), effects=0, rulings=["N4"], inputs="Each of the 2 delete tools called by each of 3 agents and each of 2 users (12 calls)")
ov("TC-L06-011-S5", state="ASKED", statuses=S("d*6"), effects=0, rulings=["N4"], inputs="The execute tool called by each of 3 agents and each of 2 users (6 calls)")
ov("TC-L06-011-S6", rulings=["R1"], note="rule change effective within 5 minutes (case text); check at +6 min, after the bound")
ov("TC-L06-022-S1", rulings=["R1"]); 

D = {"D": "ASKED", "P": "ASKED", "U": "UNASKED", "X": "UNASKED"}
rows = []
for cid, c in CASES.items():
    for (sid, inputs, st, eff, code, note) in c["s"]:
        key = f"{cid}-{sid}"
        o = OV.get(key, {})
        if code in ("D",):
            statuses = parse(st); effects = int(eff)
        else:
            statuses = effects = None
        state = o.get("state", D[code])
        if "statuses" in o: statuses, effects = o["statuses"], o["effects"]
        if state == "ASKED":
            assert statuses is not None and effects is not None, key
            assert effects == statuses.count("accepted"), (key, effects, statuses.count("accepted"))
        else:
            statuses = None if state != "NOT-EXPRESSIBLE" else None
            effects = None
        r = dict(case=cid, scenario=key, inputs=o.get("inputs", inputs), state=state,
                 expected_statuses=statuses if state == "ASKED" else None,
                 expected_effects=effects if state == "ASKED" else None,
                 rulings=o.get("rulings", []), note=o.get("note", note), source="from case text")
        if "alt" in o:
            r["alt_if_time_scale_ruled"] = dict(expected_statuses=o["alt"]["statuses"], expected_effects=o["alt"]["effects"])
        if cid == "TC-D13-003" and state == "ASKED":
            r["per_configuration"] = {"cognous-protected-destination": "NOT-CLAIMED (amendment 39, OD-3); still run and shown apart if technically runnable, never scored as pass or fail for OCS"}
        rows.append(r)

# every ASKED row without a ruling gets an explicit marker
for r in rows:
    if not r["rulings"]: r["ruling_reference"] = ["none: author and checker agree (from case text)"]
    else: r["ruling_reference"] = [f"the coordinator's rulings under the owner's delegation of 19 October 2026, {x}" for x in r["rulings"]]

counts = {}
for r in rows: counts[r["state"]] = counts.get(r["state"], 0) + 1
counts.setdefault("NOT-CLAIMED", 0)
percase = {}
for r in rows:
    p = percase.setdefault(r["case"], dict(n=0, ASKED=0, NOT_EXPRESSIBLE=0, UNASKED=0))
    p["n"] += 1
    p[{"ASKED": "ASKED", "NOT-EXPRESSIBLE": "NOT_EXPRESSIBLE", "UNASKED": "UNASKED"}[r["state"]]] += 1

DECL = {
 "time_unit": "one harness clock unit = one second; scenario clock starts at 100; the shared fixture keys expire at 1000, so usable clock readings are 100 to 999",
 "stated_time_T": "T = 0 units; a check that depends on a stated time is placed at event + T + 1 unit (rule R1)",
 "status_vocabulary": "accepted | denied (unavailable is used by the oracle only for audit-storage abort and is not expected by any Wiki scenario); every non-executing action is denied (R5)",
 "reasons": "expected_reasons omitted for every Wiki scenario; the durable-denial term of the oracle still requires a non-empty reason",
 "seeds": [1701, 1702], "repetitions": 5,
 "evasion_set_L06_014": ["TC-L06-014-S3", "TC-L06-014-S4", "TC-L06-014-S5"],
 "unit_cost_D13_003": "one effect costs 1 unit at every level of its path",
 "tools_L06_011": {"read": 4, "write": 3, "delete": 2, "execute": 1, "agents": 3, "users": 2},
}

final = dict(
 schema="wiki-subset-outcomes-final/1",
 scope_text="Bounded synthetic profile only. The comparator applications (the OPA application and the LangGraph plus OPA application) are configured by Cognous, not vendor implementations. This is not independent certification and not production readiness; operational trust stays on HOLD. Linux only.",
 status="OUTCOME DECLARATIONS ONLY. The executable steps of each asked scenario (steps, allowed_effect_ids, expected_payload) are in plans/wiki-subset-plan.json; nothing here was run.",
 source_label="from case text", outcome_authorship="one author, one checker (amendment 75)",
 rulings=RULINGS, declarations=DECL, counts_per_state=counts, scenarios_total=len(rows), cases=len(CASES),
 per_case={k: v for k, v in percase.items()},
 scenarios=rows)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "outcomes-final.json").write_text(json.dumps(final, indent=1, sort_keys=True, ensure_ascii=True) + "\n")

# PR-6 plan candidate: same content without per-row prose notes that are only for readers, compact, stable bytes
cand = dict(schema="wiki-subset-outcomes/1", scope_text=final["scope_text"], source_label="from case text",
            declarations=DECL, rulings=RULINGS, counts_per_state=counts,
            cases=[dict(id=cid, title=CASES[cid]["title"], asked_k=percase[cid]["ASKED"], n=percase[cid]["n"],
                        scenarios=[dict(id=r["scenario"], state=r["state"], inputs=r["inputs"], expected_statuses=r["expected_statuses"],
                                        expected_effects=r["expected_effects"], rulings=r["rulings"],
                                        **({"per_configuration": r["per_configuration"]} if "per_configuration" in r else {}),
                                        **({"declared_not_expressible_reason": r["note"]} if r["state"] == "NOT-EXPRESSIBLE" else {}),
                                        **({"unasked_reason": r["note"]} if r["state"] == "UNASKED" else {}))
                                   for r in rows if r["case"] == cid]) for cid in CASES],
            steps_translation="not in this file: see plans/wiki-subset-plan.json; no scenario of this file has been run on any configuration")
b = (json.dumps(cand, indent=1, sort_keys=True, ensure_ascii=True) + "\n").encode()
(OUT / "scenario-outcomes.json").write_bytes(b)

