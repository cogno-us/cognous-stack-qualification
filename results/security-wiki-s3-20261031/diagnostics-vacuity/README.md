Scratch observer plugin (vac_diag.py) run on 3 node ids (the 2 TC-L06-039 out-of-scope params and TC-L07-012 redirect) AFTER the primary run to see whether
"exception counted as refusal" branches were taken. It only logs the return values of run_decision/attempt/request_for; vac.json is its output.
Finding: 039 out-of-scope: 5 of 6 requests per phrasing were assessed by the Exchange and held at the Control Plane decision; 1 of 6 (tool_not_in_the_manifest)
ended with ExportError 'proposal action must identify exactly one declared Manifest action' (exception-only branch of the test). 012 redirect: route A legs returned typed status=denied attempted=False (no exception).
These diagnostic runs are not verdict runs and were not used to change any verdict.
