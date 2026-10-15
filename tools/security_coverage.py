"""Revision-bound file screening receipts, never a security clearance.

Reads Git objects, not executable worktrees. No imports or target code execution.
Every tracked path has a disposition; historical reviewer identities are never
inferred from aggregate counts. Sensitive match values are not emitted.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

MAX_PARSE_BYTES = 2 * 1024 * 1024
RULES = {
    'private-key-marker': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'credential-format': re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|sk-proj-[A-Za-z0-9_-]{40,})'),
    'process-execution': re.compile(rb'\b(?:subprocess\.(?:run|Popen|call|check_output)|child_process|execSync|spawnSync|os\.system)\b'),
    'dynamic-evaluation': re.compile(rb'\b(?:eval|exec)\s*\('),
    'network-listener': re.compile(rb'\b(?:Flask\(|FastAPI\(|HTTPServer\(|ThreadingHTTPServer\(|\.listen\(|\.bind\(|serve\()'),
    'archive-handling': re.compile(rb'\b(?:extractall|tarfile|zipfile)\b'),
    'deserialization': re.compile(rb'\b(?:pickle\.loads?|yaml\.(?:unsafe_load|load))\s*\('),
}
CODE = {'.py','.ts','.tsx','.js','.mjs','.cjs','.sh','.swift','.kt','.go','.rs'}


def git(root, *args):
    return subprocess.check_output(['git','-C',str(root),*args])


def tree_inventory(root, revision):
    if not re.fullmatch(r'[0-9a-f]{40}',revision):
        raise ValueError('exact forty-character source revision required')
    git(root,'cat-file','-e',revision+'^{commit}')
    rows=[]
    for record in git(root,'ls-tree','-rz','--long',revision).split(b'\0'):
        if not record:continue
        metadata,path=record.split(b'\t',1);mode,kind,oid,size=metadata.decode().split()
        rows.append({'path':path.decode('utf-8'),'mode':mode,'git_type':kind,'git_blob':oid,'bytes':None if size=='-' else int(size)})
    return rows


def inspect_blob(data, path, mode):
    methods=['sha256-byte-commitment']; flags=[]; details={}
    if mode=='120000':
        return methods, [{'rule':'symlink-target-not-followed','lines':[]}], {'semantic_review':'deferred'}
    try:text=data.decode('utf-8')
    except UnicodeError:
        kind='sqlite' if data.startswith(b'SQLite format 3\0') else 'xz' if data.startswith(b'\xfd7zXZ\0') else 'pdf' if data.startswith(b'%PDF') else 'binary'
        return methods+['binary-format-identification'],[],{'format':kind,'semantic_review':'deferred'}
    methods.append('utf8-text-screen')
    if len(data)>MAX_PARSE_BYTES:
        return methods,[{'rule':'parse-budget-exceeded','lines':[]}],{'semantic_review':'deferred'}
    for rule,pattern in RULES.items():
        matches=list(pattern.finditer(data))
        if matches:
            flags.append({'rule':rule,'count':len(matches),'lines':[data.count(b'\n',0,m.start())+1 for m in matches[:50]]})
    ext=Path(path).suffix
    if ext=='.py':
        try:
            module=ast.parse(text,filename=path)
            methods.append('python-ast-parse')
            details['python_functions']=sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) for n in ast.walk(module))
        except (SyntaxError,ValueError,RecursionError):
            flags.append({'rule':'python-parse-unavailable','lines':[]})
    elif ext=='.json':
        try:json.loads(text);methods.append('json-syntax-parse')
        except (ValueError,RecursionError):flags.append({'rule':'json-parse-unavailable','lines':[]})
    details['semantic_review']='not_established_by_automated_screen'
    return methods,flags,details


def screen(root, revision, *, label):
    root=Path(root).resolve();rows=tree_inventory(root,revision)
    proc=subprocess.Popen(['git','-C',str(root),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    try:
        for row in rows:
            if row['git_type']!='blob':
                row.update(methods=['git-tree-inventory'],flags=[],semantic_review='deferred-submodule');continue
            proc.stdin.write((row['git_blob']+'\n').encode());proc.stdin.flush()
            header=proc.stdout.readline().split()
            if len(header)!=3 or header[1]!=b'blob':raise ValueError('Git blob unavailable')
            size=int(header[2]);h=hashlib.sha256();parts=[];remaining=size
            while remaining:
                chunk=proc.stdout.read(min(65536,remaining))
                if not chunk:raise ValueError('truncated Git object')
                h.update(chunk)
                if size<=MAX_PARSE_BYTES:parts.append(chunk)
                remaining-=len(chunk)
            if proc.stdout.read(1)!=b'\n':raise ValueError('invalid Git batch delimiter')
            row['sha256']=h.hexdigest()
            if size>MAX_PARSE_BYTES:
                row.update(methods=['sha256-byte-commitment'],flags=[{'rule':'parse-budget-exceeded','lines':[]}],semantic_review='deferred');continue
            methods,flags,details=inspect_blob(b''.join(parts),row['path'],row['mode'])
            row.update(methods=methods,flags=flags,**details)
    finally:
        proc.stdin.close();proc.stdout.close();proc.wait(timeout=10)
    return {'contract':'security-path-screen/1','label':label,'revision':revision,
            'git_tree':git(root,'rev-parse',revision+'^{tree}').decode().strip(),
            'tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'reviewer':'automated structural and pattern screen; no human review inferred',
            'files':rows,'totals':{'paths':len(rows),'rules':dict(Counter(f['rule'] for row in rows for f in row.get('flags',[])))},
            'security_clearance':False,'production_authorized':False}


def delta(before, after):
    old={r['path']:r['git_blob'] for r in before['files']};new={r['path']:r['git_blob'] for r in after['files']}
    return {key:sorted(paths) for key,paths in {
        'added':new.keys()-old.keys(),'removed':old.keys()-new.keys(),
        'changed':{p for p in old.keys()&new.keys() if old[p]!=new[p]},
        'unchanged':{p for p in old.keys()&new.keys() if old[p]==new[p]},}.items()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository',type=Path,required=True);parser.add_argument('--revision',required=True)
    parser.add_argument('--label',required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    result=screen(args.repository,args.revision,label=args.label)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({'label':args.label,**result['totals'],'security_clearance':False}))


if __name__=='__main__':main()
