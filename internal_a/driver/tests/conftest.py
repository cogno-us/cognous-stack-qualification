import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_IA = _HERE.parent.parent                       # internal_a/
for p in (str(_IA), str(_HERE.parent), str(_HERE)):   # ia_eval, ia_driver, tests
    if p not in sys.path:
        sys.path.insert(0, p)
sys.dont_write_bytecode = True
