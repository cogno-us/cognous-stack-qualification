# Trusted-host successor profile (PROPOSED, builder-prepared)

Status: proposal only. Not adopted, not qualified, non-authorizing; release and production HOLD. File: `environment-profile.trusted-host-successor.proposed.v1.json`.

Approved scope wording (architect, 2026-10-24, subject to operator adoption; verbatim):

> OCS MVP trusted-host, distinct-UID execution profile. The supported boundary assumes trusted host administration, an uncompromised Python runtime, a separately privileged ingress identity, and unprivileged clients restricted to the authenticated IPC interface. Same-UID hostile execution, ingress-UID compromise, privileged host compromise and interpreter tampering are outside the supported threat model.

Mandatory within it: distinct ingress/client UIDs; non-root ingress; restricted IPC and filesystem permissions; explicit SO_PEERCRED allowlisting; fail-closed ingress; standard Linux credential and ptrace restrictions; Yama is NOT mandatory. No host is provisioned or searched for: existing environments only, for bounded tests; any host-isolation property not independently exercised stays INCOMPLETE; container evidence is not substituted for host evidence without a justified equivalence assessment.

Why: the operator will not provision a Yama host (architect ruling 2026-10-24). The ORIGINAL restricted-host profile (`environment-profile.proposed.v1.json`, Yama `ptrace_scope >= 1`) and its INCOMPLETE NC4 host requirements are **unchanged**; this successor is a separate, separately identified file and does not edit, overwrite or replace them or their history.

What it keeps: distinct ingress/client uids; non-root ingress; IPC group and filesystem permissions (socket and parent directory); explicit SO_PEERCRED uid allowlist (`launch.py --allow-uid`); verified process credentials, capabilities and dumpability; the relevant standard Linux ptrace restrictions as observed (no mandatory Yama); launcher and dependency integrity (composite identity, G-15); negative tests for unauthorized IPC access; independently captured environment observations.

What it excludes: same-uid adversaries, any code running as the ingress uid, privileged/root host compromise, tampering with the trusted Python installation.

What it does not say: source review alone cannot establish deployed host isolation; without an environment with distinct identities the successor host-isolation claim is also INCOMPLETE; no successor qualification is claimed. It needs operator approval of the scope change and independent Qualification owner approval before any acceptance run.
