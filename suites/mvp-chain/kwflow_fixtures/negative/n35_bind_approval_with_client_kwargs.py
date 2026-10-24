# EXPECT-RULE: NONLITERAL_KWARGS
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(tra, body, resolver, cfg):
    return tra.bind_approval(resolver, cfg, **body)
