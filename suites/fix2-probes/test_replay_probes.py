"""Replay probes (PROBE2_REPLAY_DIR): merge chronology of operation folds and the cost of the nesting-depth scan.

The valid records are the captured real runs shipped with Replay (programme-2 profile fixtures); every damaged record is one
of them with merge records added. The scan-cost probe runs in a child process with a hard limit so that a slow head fails
quickly instead of holding the run for half a minute.
"""
import copy
import json
import subprocess
import sys
import textwrap

import pytest

from _support import pending, root

FIXTURE = "merge-folded-operation-dispatches-under-survivor"
O1, O2, O3 = "op-order-100/refund-1", "op-order-100/refund-2", "op-order-100/refund-3"
LATER = "2026-10-05T19:00:01+00:00"


def run_record(name=FIXTURE):
    path = root("PROBE2_REPLAY_DIR") / "tests" / "fixtures" / "programme2_profiles" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))["run"]


def imported(cp):
    """None when Replay accepts the record, else the stable refusal code."""
    from agent_replay_bundle import ImportContractError, import_bounded_workflow
    from agent_replay_bundle.importers import CONTROL_PLANE_P2_REVISION
    try:
        import_bounded_workflow(cp, control_plane_revision=CONTROL_PLANE_P2_REVISION)
    except ImportContractError as exc:
        return exc.code
    return None


def _admit(cp, operation_id):
    row = copy.deepcopy(cp["operations"][0])
    row["operation_id"] = operation_id
    cp["operations"].append(row)


def _merge(cp, merge_id, survivor, folded, recorded_at=None):
    row = copy.deepcopy(cp["merge_records"][0])
    row.update(merge_id=merge_id, survivor_operation_id=survivor, folded_operation_ids=folded)
    if recorded_at:
        row["recorded_at"] = recorded_at
    cp["merge_records"].append(row)


# ---------------------------------------------------------------------------------------------------- merge chronology
def test_control_the_captured_merge_record_is_accepted():
    assert imported(run_record()) is None


def test_control_a_transitive_fold_is_accepted():
    """refund-3 is folded into refund-2 first, then refund-2 into refund-1: every operation ends in one survivor."""
    cp = run_record()
    _admit(cp, O3)
    cp["merge_records"][0]["recorded_at"] = LATER  # refund-2 into refund-1 is the later record
    _merge(cp, "merge-earlier", O2, [O3])
    assert imported(cp) is None


@pending()
def test_probe_a_fold_cycle_is_refused():
    """refund-2 is folded into refund-1 and refund-1 into refund-2."""
    cp = run_record()
    _merge(cp, "merge-cycle", O2, [O1])
    assert imported(cp) is not None


@pending()
def test_probe_an_operation_folded_into_two_survivors_is_refused():
    """refund-2 is folded into refund-1 and also into refund-3."""
    cp = run_record()
    _admit(cp, O3)
    _merge(cp, "merge-second-fold", O3, [O2])
    assert imported(cp) is not None


# ----------------------------------------------------------------------------------------------------- scan cost
CHILD = textwrap.dedent("""
    import sys, time
    from agent_replay_bundle.ingress import check_depth
    text = '"' + '\\\\"' * 40000          # 80,001 characters: an unterminated string full of escaped quotes
    started = time.perf_counter()
    check_depth(text)
    print(round(time.perf_counter() - started, 3))
""")


def _scan_seconds(limit):
    try:
        done = subprocess.run([sys.executable, "-P", "-c", CHILD], capture_output=True, text=True, timeout=limit,
                              env={"PYTHONPATH": str(root("PROBE2_REPLAY_DIR") / "src"), "PYTHONDONTWRITEBYTECODE": "1"})
    except subprocess.TimeoutExpired:
        return None
    assert done.returncode == 0, done.stderr[-300:]
    return float(done.stdout.strip())


@pending()
def test_probe_an_80_kb_input_of_escaped_quotes_is_scanned_in_under_a_second():
    seconds = _scan_seconds(limit=3)
    assert seconds is not None and seconds < 1.0, f"depth scan took {'over 3' if seconds is None else seconds} s for 80 KB"


def test_control_a_large_well_formed_document_is_scanned_quickly_and_depth_is_still_limited():
    from agent_replay_bundle.ingress import InputBoundsError, check_depth
    big = json.dumps({"rows": [{"text": 'a "quoted" word \\ and more ' * 4} for _ in range(2000)]})
    check_depth(big)
    with pytest.raises(InputBoundsError):
        check_depth("[" * 200 + "]" * 200)
