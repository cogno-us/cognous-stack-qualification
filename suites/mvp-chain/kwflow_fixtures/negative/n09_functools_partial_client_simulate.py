# EXPECT-RULE: SIMULATE_NOT_CONSTANT_NONE
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
from functools import partial


def handle(host, body, envelope):
    return partial(host.executor.execute, simulate=body.get("simulate"))
