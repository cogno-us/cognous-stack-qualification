# POSITIVE FIXTURE (source only, never executed): demonstrably fixed trusted forwarding; must be ACCEPTED.
def handle(host, envelope):
    kw = {"envelope": envelope}
    kw.update({"claim_id": "c-1"})
    kw.update(simulate=None)
    kw["extra_ok"] = 1
    return host.executor.execute(**kw)
