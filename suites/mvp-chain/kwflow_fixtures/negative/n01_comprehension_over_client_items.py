# EXPECT-RULE: OPAQUE_KWARGS_TO_PROTECTED
# NEGATIVE FIXTURE (source only, never executed): ** is assembled indirectly and carries client input into a protected API.
def handle(host, body, envelope):
    kw = {k: v for k, v in body.items()}
    return host.executor.execute(envelope=envelope, **kw)
