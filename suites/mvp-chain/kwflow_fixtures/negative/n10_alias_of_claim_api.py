# EXPECT-RULE: OPAQUE_KWARGS_TO_PROTECTED
# NEGATIVE FIXTURE (source only, never executed): ** is assembled indirectly and carries client input into a protected API.
def handle(host, body):
    provision = host.executor.provision_claim
    return provision(**body)
