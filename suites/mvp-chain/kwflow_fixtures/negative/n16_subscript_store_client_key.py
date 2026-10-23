# EXPECT-RULE: NONLITERAL_KWARGS
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(host, body, envelope):
    kw = {"envelope": envelope}
    kw[body["name"]] = body["value"]
    return host.executor.execute(**kw)
