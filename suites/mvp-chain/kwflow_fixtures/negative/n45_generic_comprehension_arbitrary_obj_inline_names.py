# EXPECT-RULE: COMPREHENSION_NOT_FIXED
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def build(p, Op):
    return Op(**{k: getattr(p, k) for k in ("target", "amount", "unit")}, institution_id="i")
