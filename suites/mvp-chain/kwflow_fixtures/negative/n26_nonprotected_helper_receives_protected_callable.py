# EXPECT-RULE: NONLITERAL_KWARGS
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def run(fn, **kw):
    return fn(**kw)


def handle(host, body):
    return run(host.executor.execute, **body)
