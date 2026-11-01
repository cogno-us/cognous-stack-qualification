"""Layout of suites/fix2-probes: runs in CI without any target checkout (no probe is executed here)."""
import re
from pathlib import Path

SUITE = Path(__file__).resolve().parents[1] / "suites" / "fix2-probes"


def conftest_modules():
    text = (SUITE / "conftest.py").read_text()
    block = text[text.index("MODULE_ENV = {"):text.index("}\n", text.index("MODULE_ENV = {"))]
    return dict(re.findall(r'"(test_\w+\.py)": \(([^)]*)\)', block))


def test_every_probe_module_is_mapped_to_its_checkouts_and_back():
    mapped = conftest_modules()
    present = {p.name for p in SUITE.glob("test_*.py")}
    assert present == set(mapped)
    for module, names in mapped.items():
        assert re.findall(r'"(PROBE2_\w+)"', names), module


def test_every_expected_failure_is_strict_and_neutrally_worded():
    support = (SUITE / "_support.py").read_text()
    assert 'PENDING = "pending hardening"' in support
    assert "strict=True" in support
    for path in SUITE.glob("*.py"):
        assert "mark.xfail" not in path.read_text() or path.name == "_support.py", path.name


def test_readme_names_every_checkout_variable():
    readme = (SUITE / "README.md").read_text()
    for names in conftest_modules().values():
        for var in re.findall(r'"(PROBE2_\w+)"', names):
            assert var in readme, var
