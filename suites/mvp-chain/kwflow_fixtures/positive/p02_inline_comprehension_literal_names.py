# POSITIVE FIXTURE (source only, never executed): a statically proven fixed form; must be ACCEPTED.
def build(p, Op):
    return Op(**{k: getattr(p, k) for k in ("target", "amount", "unit")}, institution_id="i")
