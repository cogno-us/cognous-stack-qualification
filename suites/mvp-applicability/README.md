# mvp-applicability suite (proposed)

Route C (Exchange) is declared **EXCLUDED and NOT INVOKED** in the MVP candidate by
[`process/mvp-acceptance/mvp-applicability.proposed.v1.json`](../../process/mvp-acceptance/mvp-applicability.proposed.v1.json) (a new file; the
historical SCN-D09 expectations and MVP expectations v1-v3 are untouched, and their hashes are checked). These tests **verify** the exclusion
instead of omitting tests. They say nothing about Exchange's own correctness; the Route C 5/32 failures and the determinism flake stay in the
defect register as unchanged raw history, and the Exchange investigation is separate.

| Test | Check |
|---|---|
| `test_ap01_*` | the mapping states EXCLUDED / NOT INVOKED / distinct from a skip; the candidate identity has no Exchange component |
| `test_ap02_*` | the resolved tuple pin file has no Exchange component |
| `test_ap03_*` | AST scan of every pinned hub ingress file (`tools/mvp_ingress/*.py`): no Exchange import, dynamic import, eval/exec/compile or string constant (docstrings excluded); the scanner is itself tested on a positive and a negative sample |
| `test_ap04_*` | the real ingress parser (`proposal.py`, loaded by path) has the closed six-member vocabulary and refuses six route C selector bodies with `UNKNOWN_MEMBER`; the same body without the selector is accepted |
| `test_ap05_*` | `suites/v1-scenarios/test_scn_d09.py` and expectations v1-v3 are byte-identical to the recorded sha256 |
| AP-06 (`plugin/exchange_exclusion_plugin.py`) | at the end of each battery pytest invocation, no Exchange module is in `sys.modules`, no Exchange path is on `sys.path`; judged by the gate (G-08), which also fails if the observation file is absent or any Exchange test was collected |

```bash
MVP_HUB_DIR=<hub checkout> MVP_PIN_FILE=<resolved pin file> python -m pytest -q -p no:cacheprovider suites/mvp-applicability
```

Every test fails (nothing skips) when `MVP_HUB_DIR` is unset. Run it as its own pytest invocation: it has its own `conftest.py`, and
`suites/mvp-chain` imports its sibling `conftest` by name.
