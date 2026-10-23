# EXPECT-RULE: OPAQUE_POSITIONAL_UNPACK
# NEGATIVE FIXTURE (source only, never executed): ** is assembled indirectly and carries client input into a protected API.
def handle(host, body):
    return host.executor.execute(*body["args"])
