# EXPECT-RULE: NONLITERAL_KWARGS
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(host, body, envelope):
    a = dict(body)
    b = {**a}
    return host.executor.execute(envelope=envelope, **b.copy())
