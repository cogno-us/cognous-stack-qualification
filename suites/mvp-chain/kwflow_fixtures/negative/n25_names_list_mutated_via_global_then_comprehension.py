# EXPECT-RULE: COMPREHENSION_NOT_FIXED
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
NAMES = ["amount", "unit"]


def add(extra):
    NAMES.append(extra)


def handle(host, body, envelope):
    add(body["k"])
    return host.executor.execute(envelope=envelope, **{k: getattr(body, k) for k in NAMES})
