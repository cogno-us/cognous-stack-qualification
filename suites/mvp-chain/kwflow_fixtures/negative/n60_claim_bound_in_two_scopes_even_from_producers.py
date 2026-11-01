# EXPECT-RULE: ORIGIN_VIOLATION
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def a(host):
    claim = host.executor.provision_claim(1)
    return host.executor.execute(claim_id=claim.claim_id)


def b(host):
    claim = host.executor.provision_claim(2)
    return claim
