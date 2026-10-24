# EXPECT-RULE: ORIGIN_VIOLATION
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(host, other, fields):
    claim = other.provision_claim(fields)
    return host.executor.execute(claim_id=claim.claim_id)
