"""Import pinned Wiki test specifications without executing upstream code.

SPDX-License-Identifier: Apache-2.0
Imported content is separately licensed CC-BY-SA-4.0.
"""
import argparse
import hashlib
import json
import posixpath
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = Path('scenarios/ai-security-wiki')
LOCK = Path('sources/ai-security-wiki.lock.json')
CASE = re.compile(r'^### (TC-[A-Z]\d+-\d+): (.+)$', re.M)
REPO = 'https://github.com/nachi065/AI-Security-Wiki'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def authors(text):
    if not text.startswith('---\n'):
        raise ValueError('Missing page attribution metadata')
    front = text.split('---', 2)[1]
    values = []
    for field in ('author', 'coauthors'):
        match = re.search(r'^' + field + r':\s*(.+)$', front, re.M)
        if match:
            values.extend(v.strip().strip('"\'') for v in match[1].split(','))
    if not values:
        raise ValueError('Missing author')
    return values


def pinned_links(text, path, sha):
    # Retain local anchors; resolve relative Markdown links at the source commit.
    def replace(match):
        target = match[2]
        if re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:', target) or target.startswith(('#', '//')):
            return match[0]
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
        return match[1] + REPO + '/blob/' + sha + '/' + resolved + match[3]
    return re.sub(r'(\[[^\]\n]*\]\()([^\s)]+)(\))', replace, text)


def build(source, previous, accept_revision=False):
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    if not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise ValueError('Expected exact SHA')
    if sha != previous['source_commit'] and not accept_revision:
        raise ValueError('Source revision differs from lock; use --accept-revision to prepare a source update')
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=source, text=True)
    if dirty:
        raise ValueError('Source checkout must be clean')
    license_bytes = (source / 'LICENSE').read_bytes()
    if digest(license_bytes) != previous['approved_license_sha256']:
        raise ValueError('LICENSE changed: rights review required before import; lock is not automatically relaxed')
    if 'Attribution-ShareAlike 4.0 International' not in license_bytes.decode():
        raise ValueError('Unexpected upstream license')
    output = {DEST / 'LICENSE': license_bytes}
    pages, cases, seen = [], [], set()
    old_pages = {p['path']: p for p in previous.get('pages', [])}
    old_case_authors = {ident: page['authors'] for page in previous.get('pages', []) for ident in page.get('case_ids', [])}
    for path in sorted(source.glob(previous['source_glob'])):
        if path.is_symlink():
            raise ValueError('Symlink source rejected')
        original = path.read_bytes()
        text = original.decode('utf-8')
        matches = list(CASE.finditer(text))
        if not matches:
            continue
        rel = path.relative_to(source).as_posix()
        credit = authors(text)
        if not set(old_pages.get(rel, {}).get('authors', [])) <= set(credit):
            raise ValueError(f'Attribution removed from {rel}: manual review required')
        title_match = re.search(r'^title:\s*(.+)$', text, re.M)
        if not title_match:
            raise ValueError(f'Missing page title: {rel}')
        title = title_match[1].strip('"\'')
        local = DEST / 'pages' / path.name
        # Original metadata, safety boundaries, mappings and numeric caveats remain.
        notice = (f'<!-- SPDX-License-Identifier: CC-BY-SA-4.0\n'
                  f'AI Security Wiki; page authors: {", ".join(credit)}.\n'
                  f'Source: {REPO}/blob/{sha}/{rel}\n'
                  'Changes: pinned relative Markdown links and added this notice; no test execution.\n'
                  'No endorsement by the original authors is implied. -->\n\n')
        front_end = text.index('---', 4) + 3
        linked = pinned_links(text, rel, sha)
        # Keep YAML front matter at the beginning for GitHub rendering.
        generated = linked[:front_end] + '\n\n' + notice + linked[front_end:].lstrip('\n')
        output[local] = generated.encode()
        pages.append({'path': rel, 'title': title, 'authors': credit,
                      'sha256': digest(original), 'redistributed_path': local.as_posix(),
                      'redistributed_sha256': digest(output[local]), 'case_count': len(matches),
                      'case_ids': [m[1] for m in matches]})
        for index, match in enumerate(matches):
            ident, case_title = match.groups()
            if not set(old_case_authors.get(ident, [])) <= set(credit):
                raise ValueError('Attribution removed from case ' + ident + ': manual review required')
            if ident in seen:
                raise ValueError('Duplicate source test ID: ' + ident)
            seen.add(ident)
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            block = text[match.start():end]
            # Metadata and complete procedures remain in the attributed page.
            controls = sorted(set(re.findall(r'AI-CTRL-\d{3}', block)))
            cases.append({'id': ident, 'title': case_title, 'status': 'NOT RUN',
                          'implementation_status': 'UPSTREAM SPECIFICATION ONLY',
                          'applicability': 'UNASSESSED; determine against an exact supported profile before execution',
                          'license': 'CC-BY-SA-4.0', 'authors': credit,
                          'source': {'repository': 'nachi065/AI-Security-Wiki', 'commit': sha,
                                     'path': rel, 'anchor': ident.lower(),
                                     'url': f'{REPO}/blob/{sha}/{rel}#{ident.lower()}',
                                     'page_sha256': digest(original), 'case_block_sha256': digest(block.encode())},
                          'details': f'pages/{path.name}#{ident.lower()}',
                          'upstream_control_references': controls, 'results': []})
    if not cases:
        raise ValueError('No cases parsed; refusing empty update')
    previous_ids = set(previous.get('case_ids', []))
    removed = previous_ids - seen
    # Omitted cases need an explicit retirement decision rather than silent deletion.
    if removed:
        raise ValueError('Upstream cases removed: manual retirement review required: ' + ', '.join(sorted(removed)))
    lock = dict(previous, source_commit=sha, pages=pages, case_count=len(cases), case_ids=sorted(seen),
                license_source_url=f'{REPO}/blob/{sha}/LICENSE',
                readme_sha256=digest((source / 'README.md').read_bytes()),
                authors_sha256=digest((source / 'AUTHORS').read_bytes()))
    output[LOCK] = (json.dumps(lock, indent=2) + '\n').encode()
    output[DEST / 'catalog.json'] = (json.dumps({'catalog_version': '1.0.0',
              'source_commit': sha, 'license': 'CC-BY-SA-4.0',
              'changes': 'Extracted IDs and titles; added provenance, applicability, status and local detail links.',
              'scenarios': cases}, indent=2) + '\n').encode()
    index = ['<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->', '# AI Security Wiki scenarios', '',
             f'**{len(cases)} upstream specifications; all NOT RUN.** These are not implemented or executed Cognous tests.', '',
             f'Imported from [AI Security Wiki]({REPO}/tree/{sha}), commit `{sha}`.', '',
             'Original author: **Nachiket Sathaye**. Contributor credited by the upstream README: **Ankush Jain**. '
             'Each page and catalog entry retains its page-specific authors/coauthors. '
             'No upstream endorsement is implied.', '',
             'Content and adaptations in this directory are **[CC BY-SA 4.0](LICENSE)** '
             '([license link](https://creativecommons.org/licenses/by-sa/4.0/)). '
             'Changes: extracted machine-readable metadata, added status/provenance and attribution notices, '
             'and resolved relative Markdown links to the pinned source commit. Original procedures, '
             'safety notes, framework references and suggested thresholds are retained in the pages.', '',
             'Upstream numeric thresholds and framework mappings are reference material, not adopted Cognous gates or verified current standards. '
             'Check applicability, profile limits, actual interfaces and current mappings before execution. '
             'All activity must use synthetic data and authorized isolated targets. '
             'Importing browser, training, regional compliance or fleet cases does not imply those capabilities exist in Cognous.', '',
             'Use the [execution contract](../../docs/execution-contract.md), '
             '[source lock](../../sources/ai-security-wiki.lock.json), '
             '[machine-readable catalog](catalog.json), and [update instructions](../../docs/upstream-sync.md).', '',
             '| Source layer/domain | Cases | Page credit |', '|---|---:|---|']
    for page in pages:
        index.append(f'| [{page["title"]}](pages/{Path(page["path"]).name}) | {page["case_count"]} | {", ".join(page["authors"])} |')
    index += ['', '## Case index', '', '| ID | Scenario | Status |', '|---|---|---|']
    for case in cases:
        index.append(f'| [{case["id"]}]({case["details"]}) | {case["title"].replace("|", "&#124;")} | NOT RUN |')
    output[DEST / 'README.md'] = ('\n'.join(index) + '\n').encode()
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', required=True, type=Path)
    parser.add_argument('--accept-revision', action='store_true', help='Prepare generated update files; this command does not itself merge')
    parser.add_argument('--check', action='store_true', help='Verify generated files without writing')
    args = parser.parse_args()
    previous = json.loads((ROOT / LOCK).read_text())
    output = build(args.source_dir.resolve(), previous, args.accept_revision)
    for relative, data in output.items():
        target = ROOT / relative
        if args.check:
            if not target.is_file() or target.read_bytes() != data:
                raise ValueError('Generated file differs: ' + str(relative))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    print(f'{"Checked" if args.check else "Prepared"} {len(output)} files; upstream specifications only; no qualification scenarios executed.')


if __name__ == '__main__':
    main()
