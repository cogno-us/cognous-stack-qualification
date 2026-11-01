# EXPECT-RULE: PRODUCER_SHADOWED
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def provision_claim(x):
    return x


def handle(host, fields):
    claim = provision_claim(fields)
    return host.executor.execute(claim_id=claim.claim_id)
