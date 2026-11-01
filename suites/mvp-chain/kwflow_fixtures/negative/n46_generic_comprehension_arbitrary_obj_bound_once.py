# EXPECT-RULE: COMPREHENSION_NOT_FIXED
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def build(client_obj, Op):
    names = ["target", "amount"]
    return Op(**{k: getattr(client_obj, k) for k in names})
