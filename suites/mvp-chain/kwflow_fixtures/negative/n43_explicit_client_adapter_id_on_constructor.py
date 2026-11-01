# EXPECT-RULE: PROHIBITED_KEYWORD_NON_LITERAL
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(ExecutionOperation, body):
    return ExecutionOperation(adapter_id=body["adapter"], amount=1)
