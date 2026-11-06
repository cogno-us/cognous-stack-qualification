"""Execution authorization gate. SUBJECT mode is closed unless ALL of the following hold:
  1. this package was shipped with SUBJECT_EXECUTION_PERMITTED_BY_THIS_PACKAGE = True (a successor change,
     which changes the driver hash and therefore needs a new freeze root);
  2. a well-formed authorization record is supplied (an environment flag alone is never sufficient);
  3. the record is bound to THIS package/oracle/freeze (no reuse across freezes);
  4. the record is unexpired and its single_shot_id has not been consumed (create-only marker).
An authorization file is an UNAUTHENTICATED local record: anyone who can write a file can write one. The
real authority is the Architect's attributable decision (decision_url, decision_text_sha256); this gate
only enforces binding, scope and single-shot. See README 'Residual trust'.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

SUBJECT_EXECUTION_PERMITTED_BY_THIS_PACKAGE = False      # shipped DISABLED (Architect: no subject execution in this assignment)
AUTH_SCHEMA = "ia-execution-authorization/1"
SCOPE = "Q-A-internal-single-shot"
_URL = re.compile(r"^https://github\.com/cogno-us/cognous-stack-qualification/issues/271#issuecomment-[0-9]+$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED = ("schema", "mode", "scope", "decision_url", "decision_text_sha256", "authorizer_claim", "freeze_root", "oracle_sha256",
             "driver_package_root", "single_shot_id", "issued_at", "expires_at", "output_dir", "consumed_registry", "no_effect", "no_network", "no_paid_calls")
MAX_VALIDITY_SECONDS = 24 * 3600


class AuthorizationError(Exception):
    """SUBJECT mode refused. Always fail closed."""


def _ts(v, name):
    try:
        d = datetime.fromisoformat(v)
    except (TypeError, ValueError):
        raise AuthorizationError(f"{name} is not an ISO-8601 timestamp")
    if d.tzinfo is None:
        raise AuthorizationError(f"{name} must be timezone-aware")
    return d.astimezone(timezone.utc)


def check_subject_authorization(path, *, bound_freeze_root, bound_oracle_sha256, bound_driver_package_root, now=None):
    """Return the validated record or raise AuthorizationError. Does NOT consume the single-shot marker."""
    if not SUBJECT_EXECUTION_PERMITTED_BY_THIS_PACKAGE:
        raise AuthorizationError("this driver package is shipped with SUBJECT execution disabled; a successor package and freeze are required")
    if not path:
        raise AuthorizationError("SUBJECT mode requires --authorization <record>; an environment flag is not an authorization")
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise AuthorizationError("authorization record missing or not a regular file")
    try:
        from ia_eval.oracle import load_json_strict
        rec = load_json_strict(p.read_bytes())
    except Exception as e:  # noqa: BLE001 - any parse problem is a refusal
        raise AuthorizationError(f"authorization record unreadable: {type(e).__name__}")
    if not isinstance(rec, dict):
        raise AuthorizationError("authorization record must be a JSON object")
    extra = sorted(set(rec) - set(_REQUIRED))
    missing = [k for k in _REQUIRED if k not in rec]
    if missing or extra:
        raise AuthorizationError(f"authorization record fields wrong: missing={missing} unexpected={extra}")
    if rec["schema"] != AUTH_SCHEMA or rec["mode"] != "SUBJECT" or rec["scope"] != SCOPE:
        raise AuthorizationError("authorization schema/mode/scope mismatch")
    if not (isinstance(rec["decision_url"], str) and _URL.match(rec["decision_url"])):
        raise AuthorizationError("decision_url must be an issue-271 comment URL")
    for k in ("decision_text_sha256", "freeze_root", "oracle_sha256", "driver_package_root"):
        if not (isinstance(rec[k], str) and _HEX64.match(rec[k])):
            raise AuthorizationError(f"{k} must be 64 lowercase hex")
    if rec["freeze_root"] != bound_freeze_root or rec["oracle_sha256"] != bound_oracle_sha256 or rec["driver_package_root"] != bound_driver_package_root:
        raise AuthorizationError("authorization is not bound to this freeze root / oracle / driver package")
    for k in ("no_effect", "no_network", "no_paid_calls"):
        if rec[k] is not True:
            raise AuthorizationError(f"{k} must be true")
    if not (isinstance(rec["single_shot_id"], str) and re.fullmatch(r"[A-Za-z0-9._-]{8,80}", rec["single_shot_id"])):
        raise AuthorizationError("single_shot_id malformed")
    now = now or datetime.now(timezone.utc)
    issued, expires = _ts(rec["issued_at"], "issued_at"), _ts(rec["expires_at"], "expires_at")
    if not issued <= now < expires:
        raise AuthorizationError("authorization is not currently valid (issued_at/expires_at)")
    if (expires - issued).total_seconds() > MAX_VALIDITY_SECONDS:
        raise AuthorizationError("authorization validity window exceeds 24 hours")
    out = Path(rec["output_dir"])
    if not out.is_absolute() or out.exists():
        raise AuthorizationError("output_dir must be an absolute path that does not exist yet")
    reg = Path(rec["consumed_registry"])
    if not reg.is_absolute() or not reg.is_dir() or reg.is_symlink():
        raise AuthorizationError("consumed_registry must be an existing absolute directory")
    if (reg / rec["single_shot_id"]).exists():
        raise AuthorizationError("single_shot_id already consumed")
    return rec


def consume(rec):
    """Create-only consumption marker (O_EXCL). Call immediately before the first native call."""
    marker = Path(rec["consumed_registry"]) / rec["single_shot_id"]
    try:
        fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise AuthorizationError("single_shot_id already consumed")
    with os.fdopen(fd, "w") as fh:
        fh.write(json.dumps({"single_shot_id": rec["single_shot_id"], "decision_url": rec["decision_url"]}) + "\n")
    return str(marker)
