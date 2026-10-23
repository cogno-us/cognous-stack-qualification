# EXPECT-RULE: OPAQUE_KWARGS_TO_PROTECTED
# NEGATIVE FIXTURE (source only, never executed): ** is assembled indirectly and carries client input into a protected API.
def handle(host, body, envelope):
    kw = {"envelope": envelope}
    kw[body["name"]] = body["value"]
    return host.executor.execute(**kw)
