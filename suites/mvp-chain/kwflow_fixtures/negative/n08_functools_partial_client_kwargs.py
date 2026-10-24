# EXPECT-RULE: NONLITERAL_KWARGS
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
import functools


def handle(host, body):
    bound = functools.partial(host.executor.execute, **body)
    return bound()
