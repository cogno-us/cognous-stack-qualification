# EXPECT-RULE: NONLITERAL_KWARGS
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def forward(executor, **kw):
    return executor.execute(**kw)


def handle(host, body):
    return forward(host.executor, **body)
