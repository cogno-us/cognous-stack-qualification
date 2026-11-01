# EXPECT-RULE: PROHIBITED_KEY_IN_FIXED_FORM
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(host, body, envelope):
    return host.executor.execute_claim_atomic(envelope=envelope, **{"operation_id": body["op"]})
