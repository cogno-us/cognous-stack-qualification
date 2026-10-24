# EXPECT-RULE: ORIGIN_VIOLATION
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(ExecutionOperation, fields):
    return ExecutionOperation(authority_context_id=fields["ctx"])
