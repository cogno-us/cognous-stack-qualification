# EXPECT-RULE: OPAQUE_KWARGS_TO_PROTECTED
# NEGATIVE FIXTURE (source only, never executed): ** is assembled indirectly and carries client input into a protected API.
def handle(host, body, envelope):
    base = {"envelope": envelope}
    kw = base | body
    return host.executor.execute(**kw)
