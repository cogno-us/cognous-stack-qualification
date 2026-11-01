"""Child process for C08 route B: executes one atomic claim and is killed (os._exit(77)) at a named seam.

SPDX-License-Identifier: Apache-2.0

argv: <workdir with an already provisioned atomic-claim destination> <seam> <simulate|->
seams: before_begin | after_begin | after_effect_insert_before_commit | after_commit | before_failure_record
"""
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import _c_2a_helpers as C  # noqa: E402


def main():
    work, seam, simulate = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    simulate = None if simulate == '-' else simulate
    flow = C.reopen_b(work)
    part = flow.parts[0]

    def hook(stage):
        if stage == seam:
            os._exit(77)
    flow.dest.stage_hook = hook
    if seam == 'before_failure_record':
        original = flow.dest.record_failure

        def dying(*args, **kwargs):
            os._exit(77)
        flow.dest.record_failure = dying
    res = flow.executor.execute(envelope=part.env, claim_id=part.claim.claim_id, simulate=simulate)
    print('SEAM-NOT-REACHED', res.status)


main()
