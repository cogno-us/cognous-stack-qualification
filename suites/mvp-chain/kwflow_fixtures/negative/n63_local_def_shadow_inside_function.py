# EXPECT-RULE: PRODUCER_SHADOWED
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(host, fields):
    def decide(x):
        return x

    d = decide(fields)
    return host.executor.execute(grant_id=d.binding.grant_id)
