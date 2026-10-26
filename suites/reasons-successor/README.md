# reasons-successor

Pins Control Plane `fff27ebf356007e1eb3bb24198efc7e3e3f0c5eb` and asserts, separately, (a) the frozen 164-code `runtime-authority-reasons/0.2` registry and (b) the immutable 172-code `0.3` successor (the 164 unchanged and in order plus eight PROPOSED, NOT RATIFIED policy-binding codes). Negative controls show neither version can stand in for the other. The historical 164-code probe (`suites/v1-probes`, Control Plane `0a41faa9`) and all historical evidence are untouched.

Run: `REASONS_CP_DIR=<pristine full-history checkout at the pin> python -m pytest suites/reasons-successor`. The suite fails, never skips, if the variable is unset or the checkout is not at the pin and clean.

Builder-authored; not independently reviewed; not a Qualification verdict. RELEASE / PUBLICATION / PRODUCTION: HOLD. TIER 1: NOT STARTED.
