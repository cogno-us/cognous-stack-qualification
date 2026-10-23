# EXPECT-RULE: PROHIBITED_KEYWORD_NON_LITERAL
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def handle(host, body, envelope):
    return host.executor.execute(envelope=envelope, action_id=body["a"])
