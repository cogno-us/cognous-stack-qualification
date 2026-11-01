# EXPECT-RULE: ORIGIN_VIOLATION
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(host, request, proposal):
    return host.executor.execute(envelope=proposal, claim_id=request.claim_id, simulate=None)
