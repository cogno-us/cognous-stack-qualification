# POSITIVE FIXTURE (source only, never executed): a statically proven fixed form; must be ACCEPTED.
def handle(p):
    return p.model_copy(update={"amount": 10.0, "unit": "USD"})
