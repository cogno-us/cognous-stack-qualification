# POSITIVE FIXTURE (source only, never executed): demonstrably fixed trusted forwarding; must be ACCEPTED.
import functools


def handle(host, envelope):
    bound = functools.partial(host.executor.execute, simulate=None, claim_id="c-1")
    return bound(envelope=envelope)
