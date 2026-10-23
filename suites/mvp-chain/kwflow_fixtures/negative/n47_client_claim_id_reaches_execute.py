# EXPECT-RULE: ORIGIN_VIOLATION
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(host, fields, decision, proposal):
    claim = host.executor.provision_claim(proposal=proposal, decision=decision, now=1)
    return host.executor.execute(envelope=proposal, claim_id=fields["claim_id"], simulate=None)
