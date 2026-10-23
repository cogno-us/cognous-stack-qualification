# EXPECT-RULE: NONLITERAL_KWARGS
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def poison(target, source):
    target.update(source)


def handle(host, body, envelope):
    kw = {"envelope": envelope}
    poison(kw, body)
    return host.executor.execute(**kw)
