# EXPECT-RULE: PROHIBITED_KEY_IN_FIXED_MAPPING
# NEGATIVE FIXTURE (source only, never executed): ** is assembled indirectly and carries client input into a protected API.
def handle(host, body, envelope):
    kw = {"operation_id": body["op"]}
    return host.executor.execute_claim_atomic(envelope=envelope, **kw)
