# EXPECT-RULE: ORIGIN_VIOLATION
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(host, fields):
    claim = host.executor.provision_claim(proposal=fields)
    return host.executor.execute(claim_id=claim.claim_id)
