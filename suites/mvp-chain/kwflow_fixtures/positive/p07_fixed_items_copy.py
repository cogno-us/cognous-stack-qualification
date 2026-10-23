# POSITIVE FIXTURE (source only, never executed): demonstrably fixed trusted forwarding; must be ACCEPTED.
def handle(host, envelope):
    base = {"envelope": envelope, "claim_id": "c-1"}
    kw = {k: v for k, v in base.items()}
    return host.executor.execute(**kw)
