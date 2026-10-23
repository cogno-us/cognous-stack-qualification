# EXPECT-RULE: MODEL_COPY_KWARGS_FORBIDDEN
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(p, body):
    return p.model_copy(**{"update": body})
