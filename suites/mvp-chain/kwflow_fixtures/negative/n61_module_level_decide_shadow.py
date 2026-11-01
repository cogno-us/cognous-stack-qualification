# EXPECT-RULE: PRODUCER_SHADOWED
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def decide(x):
    return x


def handle(ExecutionOperation, fields):
    d = decide(fields)
    return ExecutionOperation(grant_id=d.binding.grant_id)
