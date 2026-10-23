# EXPECT-RULE: SIMULATE_NOT_CONSTANT_NONE
# NEGATIVE FIXTURE (source only, never executed): ** is assembled indirectly and carries client input into a protected API.
def handle(host, body, envelope):
    return host.executor.execute(envelope=envelope, simulate=body["simulate"])
