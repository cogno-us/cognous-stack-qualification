# EXPECT-RULE: SIMULATE_NOT_CONSTANT_NONE
# NEGATIVE FIXTURE (source only, never executed): ** is assembled indirectly and carries client input into a protected API.
from functools import partial


def handle(host, body, envelope):
    bound = partial(host.executor.execute, simulate=body.get("simulate"))
    return bound(envelope=envelope)
