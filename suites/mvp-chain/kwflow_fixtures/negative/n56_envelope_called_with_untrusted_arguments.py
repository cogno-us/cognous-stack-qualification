# EXPECT-RULE: ORIGIN_CALLER_UNTRUSTED
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
class H:
    def envelope(self, d, p):
        return d, p


def handle(host, body):
    return host.envelope(body["d"], body["p"])
