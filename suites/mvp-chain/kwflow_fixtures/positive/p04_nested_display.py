# POSITIVE FIXTURE (source only, never executed): a statically proven fixed form; must be ACCEPTED.
def handle(host, envelope):
    return host.executor.execute(**{**{"envelope": envelope}, "simulate": None})
