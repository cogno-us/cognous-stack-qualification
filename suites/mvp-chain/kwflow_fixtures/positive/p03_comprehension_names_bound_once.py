# POSITIVE FIXTURE (source only, never executed): a statically proven fixed form; must be ACCEPTED.
def build(p, Op):
    names = ["target", "amount", "unit"]
    return Op(**{k: getattr(p, k) for k in names})
