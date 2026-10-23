# POSITIVE FIXTURE (source only, never executed): demonstrably fixed trusted forwarding; must be ACCEPTED.
def setup(tra):
    original = tra.proposal
    tra.proposal = lambda *a, **k: original(*a, **k).model_copy(update={"amount": 10.0})
