package comparative.wiki
import rego.v1

# Wiki-subset policy for the OPA transactional application (comparator).
# Written from the text of the registered Wiki cases (pass statements, test
# data, edge cases), not from the behaviour of any other configuration.
# Authentication, effect-id idempotency, durable audit and state mutation are
# application responsibilities (adapter); OPA only decides over the facts the
# application hands it. Each rule belongs to one named family so a control
# removal probe can switch exactly that family off (input.disabled).

skip(f) if f in input.disabled

req := input.request
claims := req.claims
agent := input.agent
tool := input.tool
grant := input.grant
cfg := input.config
payload := req.payload

has(obj, k) if { _ := obj[k] }

is_obj if is_object(payload)

# ---- credential and grant lifecycle (D09-009, L02-011, L06-022/023, L09-003, L09-014)
reasons contains "CREDENTIAL_BINDING_CLOSED" if { not skip("revocation"); grant.revoked == true }
reasons contains "CREDENTIAL_BINDING_CLOSED" if { not skip("budget"); grant.consumed >= grant.max_effects }
reasons contains "CREDENTIAL_EXPIRED" if { not skip("expiry"); input.now >= grant.expires_at }
reasons contains "VERIFIER_INVALID" if { not skip("verifier"); input.verifier_valid != true }
reasons contains "CREDENTIAL_PIN_CHANGED" if { not skip("credential_pin"); grant.credential != grant.provisioned_credential }
reasons contains "CREDENTIAL_PIN_CHANGED" if { not skip("credential_pin"); grant.dependency != grant.provisioned_dependency }
reasons contains "CREDENTIAL_PIN_CHANGED" if { not skip("credential_pin"); grant.grants != grant.provisioned_grants }
reasons contains "CLOCK_REGRESSION" if { not skip("clock"); input.now < input.last_now }
reasons contains "AGENT_STOPPED" if { not skip("stop"); agent.stopped == true }
reasons contains "AGENT_STOPPED" if { not skip("stop"); agent == null }

# ---- tool identity, definition, name, allow-list (L06-008/009/011/013, L07-008, L09-007)
reasons contains "TOOL_NOT_REGISTERED" if { not skip("tool_registry"); tool == null }
reasons contains "TOOL_DEFINITION_CHANGED" if { not skip("tool_definition"); tool != null; tool.approved != tool.current }
reasons contains "TOOL_DEFINITION_CHANGED" if { not skip("tool_definition"); tool != null; tool.status != "approved" }
reasons contains "TOOL_NAME_COLLISION" if {
    not skip("name_collision"); tool != null; tool.trusted != true
    some other in input.tool_norm_peers
}
reasons contains "TOOL_NAME_COLLISION" if {
    not skip("name_collision"); tool != null; cfg.require_qualified_names == true
    not contains(input.request.target, "/")
}
reasons contains "TOOL_NOT_ALLOWED" if {
    not skip("allow_list"); agent != null; tool != null
    not req.target in agent.allowed_targets
    not exception_ok
}
exception_ok if {
    some e in agent.exceptions
    e.target == req.target
    input.now < e.until
}
reasons contains "PRIVILEGE_ELEVATION_REQUIRED" if {
    not skip("elevation"); req.target in cfg.privileged_targets
    not exception_ok
}
reasons contains "ESCALATION_BLOCKED" if { not skip("escalation"); req.target in cfg.never_via_agent }
reasons contains "AGENT_PENDING_REAPPROVAL" if {
    not skip("agent_change"); agent != null; agent.pending_reapproval == true
    not req.target in agent.read_targets
}
reasons contains "OPERATION_NOT_PERMITTED" if {
    not skip("operation"); agent != null; is_obj; has(payload, "operation")
    not payload.operation in agent.operations
}

# ---- environment, scope, resource (L09-019, L09-004)
reasons contains "ENVIRONMENT_MISMATCH" if { not skip("environment"); grant.environment != input.environment }
reasons contains "ENVIRONMENT_MISMATCH" if { not skip("environment"); has(claims, "environment"); claims.environment != input.environment }
reasons contains "SCOPE_NOT_GRANTED" if {
    not skip("scope"); is_obj; has(payload, "scope")
    not payload.scope in grant.scopes
}
reasons contains "SCOPE_NOT_GRANTED" if {
    not skip("scope"); is_obj; has(payload, "resource"); not has(payload, "scope")
}
reasons contains "SCOPE_NOT_GRANTED" if {
    not skip("scope"); is_obj; has(payload, "scope"); has(payload, "resource")
    split(payload.scope, ":")[1] != payload.resource
}

# ---- user, identity, delegation records (L06-019, L06-039, L09-006, L09-018, D09-011)
reasons contains "USER_REQUIRED" if {
    not skip("user_entitlement"); req.target in cfg.user_required_targets
    not has(claims, "user")
}
reasons contains "USER_NOT_ENTITLED" if {
    not skip("user_entitlement"); has(claims, "user")
    not input.user_known
}
reasons contains "USER_NOT_ENTITLED" if {
    not skip("user_entitlement"); has(claims, "user"); input.user_known
    input.user.active != true
}
reasons contains "USER_NOT_ENTITLED" if {
    not skip("user_entitlement"); has(claims, "user"); input.user_known
    not req.target in input.user.allowed_targets
}
reasons contains "IDENTITY_SUBSTITUTION" if {
    not skip("claims_consistency"); is_obj; some k in cfg.identity_payload_keys
    has(payload, k); payload[k] != claims.user
}
reasons contains "IDENTITY_SUBSTITUTION" if {
    not skip("claims_consistency"); has(claims, "agent"); claims.agent != grant.agent
}
reasons contains "CROSS_USER_DATA" if {
    not skip("claims_consistency"); is_obj; has(payload, "data_owner")
    payload.data_owner != claims.user
}
reasons contains "TASK_EXPIRED" if {
    not skip("task_expiry"); has(claims, "task_expires_at"); input.now >= claims.task_expires_at
}
reasons contains "DELEGATION_INVALID" if { not skip("delegation_record"); has(claims, "delegation_id"); input.delegation == null }
reasons contains "DELEGATION_INVALID" if { not skip("delegation_record"); input.delegation != null; input.delegation.revoked == true }
reasons contains "DELEGATION_INVALID" if { not skip("delegation_record"); input.delegation != null; input.now >= input.delegation.expires_at }
reasons contains "DELEGATION_INVALID" if { not skip("delegation_record"); input.delegation != null; input.delegation.user != claims.user }
reasons contains "DELEGATION_INVALID" if { not skip("delegation_record"); input.delegation != null; input.delegation.user_active != true }
reasons contains "DELEGATION_INVALID" if { not skip("delegation_record"); input.delegation != null; not req.target in input.delegation.targets }
reasons contains "DELEGATION_INVALID" if {
    not skip("delegation_record"); input.delegation != null; is_obj; has(payload, "data_class")
    not payload.data_class in input.delegation.data_classes
}

# ---- delegation chain (L06-017)
chain := object.get(claims, "chain", [])
reasons contains "DELEGATION_DEPTH" if { not skip("delegation_chain"); count(chain) > cfg.max_delegation_depth }
reasons contains "DELEGATION_CYCLE" if { not skip("delegation_chain"); count(chain) != count({a | some a in chain}) }
reasons contains "DELEGATION_CHAIN_INVALID" if {
    not skip("delegation_chain"); count(chain) > 0
    chain[count(chain) - 1] != grant.agent
}
reasons contains "DELEGATION_CHAIN_INVALID" if {
    not skip("delegation_chain")
    some i
    input.chain_agents[i] == null
}
reasons contains "DELEGATION_CHAIN_INVALID" if {
    not skip("delegation_chain")
    some ca in input.chain_agents
    ca != null
    ca.stopped == true
}
reasons contains "DELEGATION_WIDENING" if {
    not skip("delegation_chain")
    some ca in input.chain_agents
    ca != null
    not req.target in ca.allowed_targets
}

# ---- argument schema and parameter rules (L05-022, L06-014)
common_keys := {"scope", "resource", "operation", "user", "claimed_user", "on_behalf_of", "data_owner", "data_class"}
reasons contains "SCHEMA_VIOLATION" if {
    not skip("schema"); cfg.schemas[req.target]
    not is_obj
}
reasons contains "SCHEMA_VIOLATION" if {
    not skip("schema"); schema := cfg.schemas[req.target]; is_obj
    some k, _ in payload
    not k in (object.keys(schema.required) | object.keys(schema.optional) | common_keys)
}
reasons contains "SCHEMA_VIOLATION" if {
    not skip("schema"); schema := cfg.schemas[req.target]; is_obj
    some k, _ in schema.required
    not has(payload, k)
}
reasons contains "SCHEMA_VIOLATION" if {
    not skip("schema"); schema := cfg.schemas[req.target]; is_obj
    some k, t in object.union(schema.required, schema.optional)
    has(payload, k)
    type_name(payload[k]) != t
}
reasons contains "PARAMETER_RULE_VIOLATION" if {
    not skip("parameter"); is_obj; has(payload, "recipient")
    not recipient_ok(payload.recipient)
}
reasons contains "PARAMETER_RULE_VIOLATION" if {
    not skip("parameter"); is_obj; has(payload, "path")
    not path_ok(payload.path)
}
reasons contains "PARAMETER_RULE_VIOLATION" if {
    not skip("parameter"); is_obj; has(payload, "amount")
    not amount_ok(payload.amount)
}
reasons contains "PARAMETER_RULE_VIOLATION" if {
    not skip("parameter"); is_obj; has(payload, "records")
    not records_ok(payload.records)
}

recipient_ok(r) if {
    is_string(r)
    regex.match(`^[a-z0-9._+-]+@[a-z0-9-]+(\.[a-z0-9-]+)+$`, r)
    domain := split(r, "@")[1]
    domain in cfg.allowed_domains
}
path_ok(p) if {
    is_string(p)
    regex.match(`^/[A-Za-z0-9_./-]*$`, p)
    not contains(p, "..")
    not contains(p, "//")
    not regex.match(`(^|/)\.(/|$)`, p)
    some prefix in cfg.allowed_path_prefixes
    startswith(p, prefix)
}
amount_ok(a) if { type_name(a) == "number"; a > 0; a <= cfg.amount_limit }
records_ok(n) if { type_name(n) == "number"; n == floor(n); n >= 1; n <= cfg.max_records }

type_name(v) := "string" if is_string(v)
type_name(v) := "number" if is_number(v)
type_name(v) := "boolean" if is_boolean(v)
type_name(v) := "object" if is_object(v)
type_name(v) := "array" if is_array(v)

# ---- caps, windows, aggregate, hierarchy (L06-016, L06-024, D13-003)
reasons contains "WINDOW_CAP_EXCEEDED" if {
    not skip("window"); input.window != null
    input.window.used >= input.window.cap
}
reasons contains "AGGREGATE_CAP_EXCEEDED" if {
    not skip("aggregate"); input.aggregate != null
    input.aggregate.used + input.aggregate.amount > input.aggregate.cap
}
reasons contains "BUDGET_LEVEL_EXHAUSTED" if {
    not skip("hierarchy")
    some lv in input.budget_levels
    lv.used >= lv.cap
}
reasons contains "BUDGET_LEVEL_EXHAUSTED" if {
    not skip("hierarchy")
    count(input.budget_unknown) > 0
}

# ---- hold for approval (L06-015, D09-009 slow approval fails safe)
# A live exception record for the same agent and target (L02-011, exception to an approval step) waives only the
# absence of an approval for its validity; a recorded rejection, timeout or self-approval is never waived, and at
# the expiry instant of the exception the hold applies again (an expiry instant is outside the bound).
reasons contains "APPROVAL_PENDING" if {
    not skip("approval"); req.target in cfg.approval_required_targets
    not exception_ok
    input.approval == null
}
reasons contains "APPROVAL_REJECTED" if {
    not skip("approval"); req.target in cfg.approval_required_targets
    input.approval.status == "rejected"
}
reasons contains "APPROVAL_TIMED_OUT" if {
    not skip("approval"); req.target in cfg.approval_required_targets
    input.approval.status == "timed_out"
}
reasons contains "APPROVAL_SELF_APPROVAL" if {
    not skip("approval"); req.target in cfg.approval_required_targets
    input.approval.status == "self_approval"
}
reasons contains "APPROVAL_TIMED_OUT" if {
    not skip("approval"); req.target in cfg.approval_required_targets
    input.approval.status == "approved"
    input.now - input.approval.at > cfg.approval_ttl
}

default allow := false
allow if count(reasons) == 0
