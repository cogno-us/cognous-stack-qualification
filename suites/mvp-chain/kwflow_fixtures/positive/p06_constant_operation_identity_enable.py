# POSITIVE FIXTURE (source only, never executed): demonstrably fixed trusted forwarding; must be ACCEPTED.
def make(E, workflow, dest, policy):
    return E(workflow=workflow, destination=dest, policy=policy, operation_identity=True)
