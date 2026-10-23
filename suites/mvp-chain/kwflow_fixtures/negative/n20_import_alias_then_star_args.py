# EXPECT-RULE: OPAQUE_POSITIONAL_UNPACK
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
from engine.executor import execute as go


def handle(body):
    return go(*body["args"])
