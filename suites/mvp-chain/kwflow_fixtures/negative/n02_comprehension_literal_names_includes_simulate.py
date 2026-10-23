# EXPECT-RULE: PROHIBITED_KEY_IN_FIXED_MAPPING
# NEGATIVE FIXTURE (source only, never executed): ** is assembled indirectly and carries client input into a protected API.
def handle(host, body, envelope):
    names = ("claim_id", "simulate")
    kw = {k: body[k] for k in names}
    return host.executor.execute(envelope=envelope, **kw)
