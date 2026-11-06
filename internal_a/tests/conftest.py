import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for p in (str(_HERE.parent), str(_HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)
sys.dont_write_bytecode = True
