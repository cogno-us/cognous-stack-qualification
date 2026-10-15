# OpenAI bounded agent pilot

The user added `OPENAI_API_KEY` and requested a retry after the Claude pilot. GPT-6.1 Sol (`gpt-6.1-sol`) is the chosen default OpenAI model, using the Responses API and medium reasoning. This is a separate provider run, not a rerun or replacement of Claude evidence.

The retry is capped at the USD 19.908 remaining allowance stated in the conversation. Earlier evidence and accounting remain in their existing location and are not republished by this change.

## Scope and run authorization

Five repetitions of each existing synthetic native variant: routine A01, indirect injection A02, simulated first-read timeout A05, denied approval H01, and withdrawn approval H01. The tools, native hub pin, prompt and observer are shared with the Claude adapter. Persistent memory, tenant-memory isolation and multi-agent handoff remain NOT RUN; human participation is excluded and oversight effectiveness is NOT EVALUATED.

Merging the OpenAI implementation adds `qualification/serial/openai-campaign-20261015.json` and starts exactly the authorized campaign on `main`. Pull requests run offline controls only. No scheduled trigger or manual dispatch is added. The first-attempt and prior-main-run guard blocks replay. The credential is injected only into the model execution step. No provider-side spending-limit setup is required, per the user's instruction.

## Accounting and protocol

The [configuration](../qualification/serial/openai-gpt-6.1-sol.json) fixes at most 25 trials, six paid Responses calls per trial, four client tools per response, 2,048 output tokens including reasoning, 16,000 counted input tokens, 60 KB request bodies, and a 60-second network timeout. No SDK or automatic retry is used. A provider/protocol/budget failure stops the campaign and leaves remaining trials explicitly unexecuted.

Official pricing checked 15 October 2026: input USD 2/million, cached input USD 0.10/million, cache writes USD 2.50/million and output USD 10/million. Each request reserves 20,000 inputs at the higher cache-write price plus maximum output: USD 0.07048. Full reservations across 150 possible calls total USD 10.572, below the remaining allowance. The durable SQLite ledger reserves before each paid request, charges reported input/cache/output usage rounded upward to a microdollar, includes reasoning in output exactly once, and retains unknown charges. Changed configuration cannot reopen the ledger. This ledger covers only the remaining allowance and grants no fresh USD 20 budget. Pricing-based client dispatch control is not an invoice-level provider cap.

The transport fixes TLS to `api.openai.com` and only `/v1/responses/input_tokens` and `/v1/responses`. It disables response storage (`store: false`), implicit prompt caching (`prompt_cache_options.mode: explicit`, with no explicit breakpoints), parallel tool calls, and context truncation; it explicitly selects standard processing (`service_tier: default`). Tools are strict client functions with local schema/scope validation. No hosted tool, browser, shell, production credential, customer data or repository source is given to the model. Encrypted reasoning and output items remain in memory for protocol replay and are excluded from evidence. The same-host read-only observer receives no API key.

Refusal, incomplete output and provider errors cannot dispatch tool calls. Trial records retain response model IDs, usage, refusal/status metadata, tool actions and independent observations. All verdicts, partial evidence and the ledger are uploaded on failure and retained for 90 days. A failed campaign must not be reset to gain a fresh budget.

## Sources

- https://developers.openai.com/api/docs/models/gpt-6.1-sol
- https://developers.openai.com/api/docs/guides/function-calling
- https://developers.openai.com/api/docs/guides/reasoning
- https://developers.openai.com/api/docs/guides/token-counting
- https://developers.openai.com/api/reference/resources/responses/methods/create

These diagnostic trials do not change component selection, full-catalog acceptance, publication or production decisions.
