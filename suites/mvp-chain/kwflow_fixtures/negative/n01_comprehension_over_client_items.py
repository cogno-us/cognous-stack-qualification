# EXPECT-RULE: NONLITERAL_KWARGS
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(host, body, envelope):
    kw = {k: v for k, v in body.items()}
    return host.executor.execute(envelope=envelope, **kw)
