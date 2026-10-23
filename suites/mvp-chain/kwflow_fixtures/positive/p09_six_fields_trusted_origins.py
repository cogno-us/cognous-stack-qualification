# POSITIVE FIXTURE (source only, never executed): a statically proven fixed form or trusted origin; must be ACCEPTED.
class H:
    def envelope(self, d, p):
        from x import ExecutionOperation
        return ExecutionOperation(authority_context_id=p.authority_context_ref, grant_id=d.binding.grant_id, grant_revision=d.binding.grant_revision,
                                  effective_max_effects=d.binding.effective_max_effects, requested_permissions=tuple(p.requested_permissions))

    def run(self, fields):
        host = self._host
        proposal = host.build_proposal(fields)
        decision = host.workflow.decide(proposal, now=1)
        claim = host.executor.provision_claim(proposal=proposal, decision=decision, now=1)
        env = host.envelope(decision, proposal)
        return host.executor.execute(envelope=env, claim_id=claim.claim_id, simulate=None)
