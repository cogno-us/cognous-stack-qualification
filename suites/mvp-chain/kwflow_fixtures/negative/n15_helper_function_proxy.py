# EXPECT-RULE: OPAQUE_KWARGS_TO_PROTECTED
# NEGATIVE FIXTURE (source only, never executed): ** is assembled indirectly and carries client input into a protected API.
def forward(executor, **kw):
    return executor.execute(**kw)


def handle(host, body):
    return forward(host.executor, **body)
