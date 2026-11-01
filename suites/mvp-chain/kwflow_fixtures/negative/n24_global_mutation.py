# EXPECT-RULE: NONLITERAL_KWARGS
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
KW = {"envelope": None}


def taint(body):
    global KW
    KW = {**KW, **body}


def handle(host, body):
    taint(body)
    return host.executor.execute(**KW)
