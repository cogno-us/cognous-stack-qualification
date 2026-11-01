# EXPECT-RULE: SIMULATE_NOT_CONSTANT_NONE
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(host, body, envelope):
    return host.executor.execute(envelope=envelope, simulate=body["simulate"])
