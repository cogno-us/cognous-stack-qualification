# EXPECT-RULE: NONLITERAL_KWARGS
# NEGATIVE FIXTURE (source only, never executed): client input reaches a protected API through an indirect or non-proven form.
def setup(tra, host):
    tra.go = lambda **k: host.executor.execute(**k)
