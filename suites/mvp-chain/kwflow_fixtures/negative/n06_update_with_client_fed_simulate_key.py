# EXPECT-RULE: PROHIBITED_KEY_IN_FIXED_MAPPING
# NEGATIVE FIXTURE (source only, never executed): ** is assembled indirectly and carries client input into a protected API.
def handle(host, body, envelope):
    kw = {"envelope": envelope}
    kw.update({"simulate": body["s"]})
    return host.executor.execute(**kw)
