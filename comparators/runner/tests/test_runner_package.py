"""Package rules for the files of the runner: scope text, wording, no network, no hard-coded scenario counts, digests current."""
import json
from pathlib import Path
import re

from comparators.runner import report

RUNNER = Path(__file__).resolve().parents[1]
REPO = RUNNER.parents[1]
FILES = sorted(p for p in RUNNER.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py', '.md', '.json'))
BANNED = ['vulner' + 'ability', 'exp' + 'loit', 'att' + 'ack', 'review' + 'er', 'work' + 'er', 'clau' + 'de', 'anthro' + 'pic', 'son' + 'net', 'op' + 'us',
          'hai' + 'ku', 'gem' + 'ini', 'human' + 'zee', 'papa ' + 'bear', 'andr' + 'é', 'de ' + 'lima', 'k' + 'NN']


def test_no_banned_wording_and_no_internal_labels():
    for f in FILES:
        text = f.read_text().lower()
        for w in BANNED:
            assert w.lower() not in text, '%s contains %r' % (f.name, w)


def test_no_network_imports():
    for f in FILES:
        if f.suffix == '.py':
            assert not re.search(r'^\s*(import|from)\s+(socket|http|urllib|requests|ssl|ftplib|smtplib)\b', f.read_text(), re.M), f.name


def test_no_scenario_count_is_hard_coded():
    for f in FILES:
        if f.suffix == '.py' and not f.name.startswith('test_'):
            for n, line in enumerate(f.read_text().splitlines(), 1):
                assert not re.search(r'(?<![\w.\-])(86|121|94)(?![\w.\-])', line), '%s:%d %s' % (f.name, n, line.strip())


def test_scope_text_is_the_registered_one():
    pre = json.loads((REPO / 'process/release-gate/preregistration.json').read_text())
    assert report.SCOPE_TEXT == pre['scope_text']
    assert 'HOLD' in (RUNNER / 'README.md').read_text()


def test_digests_of_the_runner_files_are_current():
    from comparators.runner import compute_digests
    assert compute_digests.check() == []
