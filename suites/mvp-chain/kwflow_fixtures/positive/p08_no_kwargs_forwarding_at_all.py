# POSITIVE FIXTURE (source only, never executed): a statically proven fixed form or trusted origin; must be ACCEPTED.
class H:
    def go(self, decision, proposal):
        host = self._host
        claim = host.executor.provision_claim(proposal=proposal, decision=decision, now=1)
        return host.executor.execute(envelope=proposal, claim_id=claim.claim_id, simulate=None)
