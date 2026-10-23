# EXPECT-RULE: OPAQUE_KWARGS_TO_PROTECTED
# NEGATIVE FIXTURE (source only, never executed): ** is assembled indirectly and carries client input into a protected API.
import functools


def handle(host, body):
    bound = functools.partial(host.executor.execute, **body)
    return bound()
