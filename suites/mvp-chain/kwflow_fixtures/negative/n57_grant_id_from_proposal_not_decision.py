# EXPECT-RULE: ORIGIN_VIOLATION
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
class H:
    def envelope(self, d, p):
        from x import ExecutionOperation
        return ExecutionOperation(grant_id=p.binding.grant_id)
