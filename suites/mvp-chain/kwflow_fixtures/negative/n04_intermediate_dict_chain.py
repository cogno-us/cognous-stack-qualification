# EXPECT-RULE: OPAQUE_KWARGS_TO_PROTECTED
# NEGATIVE FIXTURE (source only, never executed): ** is assembled indirectly and carries client input into a protected API.
def handle(host, body, envelope):
    a = dict(body)
    b = {**a}
    c = b.copy()
    return host.executor.execute(envelope=envelope, **c)
