# EXPECT-RULE: NONLITERAL_KWARGS
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(host, body):
    run = lambda *a, **k: host.executor.execute(*a, **k)
    return run, run(**body)
