# EXPECT-RULE: PROHIBITED_KEY_IN_FIXED_FORM
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(p, body):
    return p.model_copy(update={"effects": body["e"], "amount": 1})
