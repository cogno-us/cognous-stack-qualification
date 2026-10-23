# EXPECT-RULE: OPAQUE_KWARGS_TO_PROTECTED
# NEGATIVE FIXTURE (source only, never executed): ** is assembled indirectly and carries client input into a protected API.
def handle(host, body):
    run = lambda *a, **k: host.executor.execute(*a, **k)
    return run(**body)
