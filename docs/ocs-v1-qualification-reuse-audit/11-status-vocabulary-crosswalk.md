# 11 Status vocabulary crosswalk

**Status: documentation-only crosswalk. No schema change, no migration, no new persisted status value. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.** Records Architect ruling D2 ([10](10-architect-dispositions-and-adoption-record.md)). Historical status records are preserved unchanged.

## 1. The closed vocabulary that stays

Result statuses in this repository: **PASS, FAIL, INCONCLUSIVE, NOT RUN, NOT APPLICABLE** (doc 01 section 4 lists the extra workflow outcomes RUNNING and CANCELLED, the MVP-chain verdict set and the other coexisting sets; none is changed here).

## 2. How the Risk-Based Testing Addendum's words map

The addendum's Level 3 reports "PASS / FAIL / BLOCKED / NOT EXECUTED (and N/A where supported)". Under ruling D2 those words are read as follows. The right-hand column is the only thing that is ever persisted.

| Addendum or colloquial term | Meaning (per D2) | Persisted as |
|---|---|---|
| PASS | Adjudicated pass against frozen expectations by the governed process | PASS |
| FAIL | Adjudicated failure | FAIL |
| INCONCLUSIVE | Execution or observation occurred, but the available evidence cannot establish PASS or FAIL | INCONCLUSIVE |
| NOT EXECUTED | A scheduled test has not actually executed | NOT RUN |
| NOT RUN | Same as above; the repository's own word | NOT RUN |
| NOT APPLICABLE / N/A | Explicitly outside the frozen applicable scope, with a recorded justification | NOT APPLICABLE |
| BLOCKED | **A reason** for non-execution or non-adjudication, not a result status | The existing applicable status (typically NOT RUN) **plus a separate explicit blocker or reason field** |

## 3. Rules from the ruling

1. Do not collapse BLOCKED into INCONCLUSIVE.
2. Do not report an unexecuted test as INCONCLUSIVE.
3. A required qualification gate that is blocked before execution must not be represented as PASS.
4. NOT APPLICABLE needs a recorded justification and a frozen scope; it is not a place to put blocked or unexecuted cases.
5. No new persisted status is introduced. No file written before this crosswalk is reinterpreted or rewritten.

## 4. Repository terms that already use the word

| Where | Word | Relationship |
|---|---|---|
| `suites/mvp-chain/verdict.py` and its README | `BLOCKED` is in that verdict set | Existing, historical, unchanged. It is a reason-like value in a verdict set that already exists; this crosswalk does not extend it to other places |
| ISSBench spec lines 449-454 | PASS, FAIL, BLOCKED, NOT IMPLEMENTED, NOT APPLICABLE, NOT RUN | ISSBench's own vocabulary, not adopted here (doc 02) |
| Constitution text | "BLOCKED or NOT ASSESSED" for unresolved mapping or unavailable evidence | Read as a reason per D2, not a status here |
| `catalog.json` all-NOT RUN versus crosswalk INCONCLUSIVE rows | A pre-existing mismatch (doc 01 section 6) | Reported, not edited |

## 5. What is not decided here

Where the separate blocker or reason field lives in each existing result record is **UNVERIFIED**; no field is added by this documentation. QPR-1 (doc 08) uses the existing vocabulary and records any blocker as a plain text reason in its own proposed table, with no change to any result schema.
