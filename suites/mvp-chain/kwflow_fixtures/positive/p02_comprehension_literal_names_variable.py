# POSITIVE FIXTURE (source only, never executed): demonstrably fixed trusted forwarding; must be ACCEPTED.
NAMES = ["actor", "principal", "amount"]


def build(p, Op):
    names = ["actor", "principal", "target", "amount"]
    return Op(**{k: getattr(p, k) for k in names}, institution_id="i")
