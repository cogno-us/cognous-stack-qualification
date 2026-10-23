# POSITIVE FIXTURE (source only, never executed): a statically proven fixed form; must be ACCEPTED.
def handle(host, decision, proposal):
    claim = host.executor.provision_claim(proposal=proposal, decision=decision, now=1)
    return host.executor.execute(envelope=proposal, claim_id=claim.claim_id, simulate=None)
