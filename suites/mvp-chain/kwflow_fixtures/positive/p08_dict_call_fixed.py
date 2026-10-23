# POSITIVE FIXTURE (source only, never executed): demonstrably fixed trusted forwarding; must be ACCEPTED.
def handle(host, envelope):
    fixed = {"claim_id": "c-1"}
    return host.executor.execute(**dict(fixed, envelope=envelope, simulate=None))
