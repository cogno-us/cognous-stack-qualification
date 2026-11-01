# EXPECT-RULE: OPAQUE_POSITIONAL_UNPACK
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(host, body):
    return host.executor.execute(*body["args"])
