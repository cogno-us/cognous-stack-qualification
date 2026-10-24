# EXPECT-RULE: COMPREHENSION_NOT_FIXED
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(host, body, envelope):
    names = ("amount",)
    other = names
    return host.executor.execute(envelope=envelope, **{k: getattr(body, k) for k in names})
