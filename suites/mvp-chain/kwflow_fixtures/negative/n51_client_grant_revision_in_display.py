# EXPECT-RULE: ORIGIN_VIOLATION
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(host, fields, envelope):
    return host.executor.execute(envelope=envelope, **{"grant_revision": fields["r"]})
