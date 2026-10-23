# POSITIVE FIXTURE (source only, never executed): a statically proven fixed form; must be ACCEPTED.
def handle(host, envelope):
    run = lambda *a, **k: host.executor.execute(*a, **k)
    return run(envelope=envelope, **{"simulate": None})
