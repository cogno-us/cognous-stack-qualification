# POSITIVE FIXTURE (source only, never executed): demonstrably fixed trusted forwarding; must be ACCEPTED.
def handle(host, body, envelope):
    return host.executor.execute(**{"envelope": envelope, "claim_id": "c-1", "simulate": None})
