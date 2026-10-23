# EXPECT-RULE: OPAQUE_KWARGS_TO_UNRESOLVED
# NEGATIVE FIXTURE (source only, never executed): ** is assembled indirectly and carries client input into a protected API.
def handle(host, body):
    return getattr(host.executor, body["method"])(**body)
