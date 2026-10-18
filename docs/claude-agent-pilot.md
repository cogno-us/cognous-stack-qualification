# Claude Opus 5 5 agent pilot

The approved first campaign uses Anthropic's direct API model `claude-opus-5-5` with a maximum USD 20 trial budget. No live model call has occurred during implementation. The [configuration](../qualification/serial/claude-opus-5-5.json) and [adapter](../tools/claude_agent_pilot.py) are ready for credentialed testing; offline test transports are not actual-agent evidence.

## Supply the credential and run once

1. Use the Anthropic API credential configured for this campaign. The user explicitly declined provider-side spend-limit setup and authorized this bounded run. The runner's USD 20 ledger is a conservative client control at recorded rates, not a provider invoice guarantee. Account for any prior campaign spend before proceeding. A Claude subscription is not a credential consumed by this adapter.
2. In this repository's **Settings → Secrets and variables → Actions**, add a repository secret named **ANTHROPIC_API_KEY**. Do not put it in chat, source files, logs, workflow inputs or the model prompt.
3. Merging PR 14 adds the single campaign authorization marker and starts the authorized pilot on `main`. Only pushes changing that marker or explicitly authorized manual dispatches can reach the paid job. Model calls are disabled on pull requests. No schedule is added.
4. Review the retained manifest and ledger, including failures and unknown charges. Do not rerun or dispatch a second campaign to obtain a fresh USD 20 allowance. The workflow blocks repeat attempts and prior main-branch campaign runs; local continuation must retain the same ledger and account for completed trials. Artifact retention is 90 days, not permanent storage. Preserve reviewed evidence through the existing qualification process before expiry.

If the key is absent, the runner records NOT RUN and exits before API traffic. The credential is available only to the paid execution step; the observer subprocess receives a minimal environment without it. Only synthetic case data is sent to Anthropic. Customer data, repository source, private Cognous material and native private signing keys are not model inputs.

## Pilot scope

Twenty-five diagnostic trials: five repetitions each for A01 routine workflow, A02 indirect injection, A05 simulated tool timeout, H01 denied approval and H01 withdrawn approval. A03 persistent memory/compaction, A04 cross-tenant memory isolation and A06 multi-agent handoff remain NOT RUN. Each trial starts with a new conversation and a reset native synthetic destination. Human participation is excluded; oversight effectiveness remains NOT EVALUATED.

The four client tools read the synthetic case, request its exact queued effect through native approval, read the authoritative destination, and record a structured completion report. Arbitrary tool names and substituted effect/target/payload arguments are refused. The model has no shell, filesystem, browser, server-side tools or production credential. The only intentional network destination is `api.anthropic.com`; no proxy/redirect or automatic retry is implemented. This is a bounded adapter surface, not an operating-system network sandbox.

Native `AssuranceRuntime` remains the authority for the queued action. Synthetic reviewers are scripted test actors; they do not measure human decisions. The independent readback is a read-only subprocess on the same trusted host. Model scope-violation attempts, actual prohibited effects, task completion and claim consistency are separate dimensions. A passing destination control cannot conceal an agent's attempted scope violation.

## Cost and protocol controls

Anthropic's official model page, checked 15 October 2026, lists standard direct pricing of USD 4 per million input tokens and USD 20 per million output tokens. Sources:
- https://platform.claude.com/docs/en/models/opus-5-5/overview
- https://platform.claude.com/docs/en/about-claude/pricing
- https://platform.claude.com/docs/en/api/messages/create
- https://platform.claude.com/docs/en/api/messages/count_tokens

Each trial allows at most six model responses and four tool calls per response. Requests have a 60 KB local byte ceiling, a counted 16,000-input-token ceiling and at most 2,048 output tokens. Before each paid request, the persistent SQLite ledger reserves 20,000 input tokens plus maximum output at recorded prices. Confirmed usage releases unused reservation; timeout, malformed usage or ambiguous failure retains it. Over-reservation usage halts further accounting. Reservations are serialized across processes, survive restart and cannot exceed the configured USD 20 cap. Across 25 trials, at most 150 paid requests are allowed: their full reservations total USD 18.144 at recorded prices. The budget is campaign-wide, not per trial. Reopening with a changed configuration fails closed.

The request explicitly selects `service_tier: standard_only` and `output_config.effort: medium`. No fast mode, prompt caching, batch, residency premium or paid server tool is requested. Unexpected caching/model identity causes a stop. Token counting and reservations are conservative client safeguards; provider pricing and billing behavior remain external. The user chose the fixed trial/call/token bounds and local campaign ledger without a provider spending-limit prerequisite. Reverify prices before a later campaign.

The adapter preserves API content blocks in memory for tool-loop continuity, including model-bound thinking signatures where returned. It does not request private reasoning and does not persist thinking or redacted-thinking blocks. It omits forced tool choice, temperature overrides and disabling thinking, consistent with Opus 5.5 compatibility guidance. Available response model IDs, token usage, stop reasons, tool actions and native observations are recorded; finer provider snapshot details may be unavailable.

## Local preflight

Use a clean qualification checkout and a clean hub at the configured commit. Keep outputs and the persistent ledger outside both checkouts.

```bash
python -m pip install --require-hashes --only-binary=:all: -r tools/requirements-serial.lock
PYTHONDONTWRITEBYTECODE=1 python tools/claude_agent_pilot.py \
  --hub /path/to/hub --output /path/to/new-preflight \
  --ledger /path/to/campaign/ledger.sqlite
```

This sends no model request. Live execution additionally requires the secret environment variable, `--execute`. Never discard a ledger after an ambiguous request. A local repeated campaign is not automatically budget-authorized merely because the CLI permits a new output directory; retain prior results and the same ledger, and run only the outstanding scope.

The existing v2 native diagnostic record and v1 workflow telemetry are unchanged. Actual-agent manifests are explicitly separate, retain exact source and scenario commitments, and do not grant whole-catalog acceptance, component selection, publication or production authority.
