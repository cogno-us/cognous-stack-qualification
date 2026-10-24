# EXPECT-RULE: NONLITERAL_KWARGS
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(host, body, envelope):
    kw = {"envelope": envelope}

    def later():
        kw.update(body)

    later()
    return host.executor.execute(**kw)
