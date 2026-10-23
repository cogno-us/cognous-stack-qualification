# EXPECT-RULE: PROHIBITED_KEY_IN_FIXED_FORM
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(host, body, envelope):
    return host.executor.execute(envelope=envelope, **{k: getattr(body, k) for k in ("amount", "requirement_id")})
