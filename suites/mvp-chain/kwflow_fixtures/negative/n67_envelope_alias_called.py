# EXPECT-RULE: PROTECTED_CALLABLE_ESCAPES
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(host, f):
    e = host.envelope
    return e(f, f)
