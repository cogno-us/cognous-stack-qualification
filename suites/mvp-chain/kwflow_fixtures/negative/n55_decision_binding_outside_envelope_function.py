# EXPECT-RULE: ORIGIN_VIOLATION
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def make(ExecutionOperation, d):
    return ExecutionOperation(grant_id=d.binding.grant_id)
