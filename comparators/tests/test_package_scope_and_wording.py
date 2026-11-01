"""The scope text and the caveats appear unchanged; the package text is neutral and carries no internal labels."""
import json
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[2]
CMP = REPO / 'comparators'
PREREG = (REPO / 'docs/release-gate/pre-registration.md').read_text()
TWIN = json.loads((REPO / 'process/release-gate/preregistration.json').read_text())
RP8 = ('the corner plan was authored after inspection of the baseline code and is not blinded, and both plans had no independent review; '
       'the shared Cognous wire and signature helpers feed all three configurations')


def scope_from_page():
    line = next(l for l in PREREG.splitlines() if l.startswith('- **PC-7.**'))
    return line.split('The scope text is unchanged: ', 1)[1]


def package_text_files():
    skip = {'__pycache__'}
    return [p for p in CMP.rglob('*') if p.is_file() and not (skip & set(p.parts)) and p.suffix in ('.md', '.json', '.py', '.rego', '.txt', '.lock')
            and p.name != Path(__file__).name]


def test_scope_text_is_the_registered_text_in_the_readme_and_in_every_declaration_file():
    scope = scope_from_page()
    assert scope == TWIN['scope_text']
    assert ('**Scope.** ' + scope) in (CMP / 'README.md').read_text()
    for p in sorted((CMP / 'wiki/interface').glob('*.json')):
        assert json.loads(p.read_text())['scope_text'] == scope
    for p in (CMP / 'wiki/plans/wiki-subset-plan.json', CMP / 'wiki/expected-outcomes/outcomes-final.json', CMP / 'wiki/expected-outcomes/scenario-outcomes.json'):
        assert json.loads(p.read_text())['scope_text'] == scope, p.name


def test_rp8_caveats_appear_unchanged_in_the_readme():
    assert RP8 in PREREG and RP8 in (CMP / 'README.md').read_text()


def test_no_word_of_the_excluded_vocabulary_and_no_internal_label_in_the_package():
    words = ['vulner' + 'abil', 'exp' + 'loit', 'att' + 'ack', 'review' + 'er', 'work' + 'er', 'clau' + 'de', 'anthro' + 'pic', 'son' + 'net', 'op' + 'us',
             'hai' + 'ku', 'gem' + 'ini', 'humanzee', 'papa bear', 'andr' + 'é', 'de lima']
    pattern = re.compile('|'.join(words), re.I)
    internal = re.compile(r'\b[kK]\d{2}\b|\b[kK]\d{2}-|[kK]\d{2}_')
    bad = []
    for p in package_text_files():
        text = p.read_text(errors='replace')
        for pat, kind in ((pattern, 'word'), (internal, 'label')):
            m = pat.search(text)
            if m:
                bad.append((p.relative_to(REPO).as_posix(), kind, m.group(0)))
    assert not bad, bad


def test_the_package_modules_use_no_network_library():
    banned = re.compile(r'^\s*(?:import|from)\s+(urllib|requests|socket|http|httpx|aiohttp|ftplib|smtplib)\b', re.M)
    for p in (CMP / 'wiki').rglob('*.py'):
        assert not banned.search(p.read_text()), p.name
