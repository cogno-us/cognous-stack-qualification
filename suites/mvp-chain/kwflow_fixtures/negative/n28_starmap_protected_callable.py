# EXPECT-RULE: PROTECTED_CALLABLE_ESCAPES
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
import itertools


def handle(host, body):
    return list(itertools.starmap(host.executor.execute, body["rows"]))
