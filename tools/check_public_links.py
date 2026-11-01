"""Anonymous bounded public-navigation checks; unavailable is never a pass.

SPDX-License-Identifier: Apache-2.0
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import ipaddress
import json
from pathlib import Path
import re
import socket
import urllib.error
import urllib.parse
import urllib.request


TRUSTED_PUBLIC_HOSTS = {'github.com','raw.githubusercontent.com','api.github.com','docs.github.com',
    'arxiv.org','cogno.us','doi.org','edge.sagepub.com','genai.owasp.org','papers.ssrn.com',
    'www.cogno.us','www.oecd.org','oecd.org','journals.sagepub.com'}


def safe_url(url):
    value=urllib.parse.urlsplit(url)
    if value.scheme!='https' or not value.hostname or value.username or value.password or value.port not in (None,443):
        raise ValueError('public HTTPS URL without credentials required')
    try:addresses=socket.getaddrinfo(value.hostname,443,type=socket.SOCK_STREAM)
    except socket.gaierror:
        # Managed hosts may resolve through their HTTPS proxy only. In that
        # case permit only this explicit reviewed public-host allowlist.
        if value.hostname not in TRUSTED_PUBLIC_HOSTS:raise ValueError('DNS unavailable')
        addresses=None
    if addresses is not None and (not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses)):
        raise ValueError('nonpublic network target excluded')
    return urllib.parse.urlunsplit(value._replace(fragment=''))


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    max_redirections=5
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        safe_url(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def check(url):
    row={'url':url,'checked_at':datetime.now(timezone.utc).isoformat(),'method':'anonymous HEAD with GET fallback only on 405','anchor_checked':False}
    try:
        target=safe_url(url);opener=urllib.request.build_opener(SafeRedirect())
        request=urllib.request.Request(target,method='HEAD',headers={'User-Agent':'Cognous-public-link-audit/1'})
        try:response=opener.open(request,timeout=8)
        except urllib.error.HTTPError as exc:
            if exc.code!=405:raise
            request=urllib.request.Request(target,method='GET',headers={'User-Agent':'Cognous-public-link-audit/1','Range':'bytes=0-1023'})
            response=opener.open(request,timeout=8)
        with response:
            row.update(http_status=response.status,final_url=response.url)
        final=urllib.parse.urlsplit(row['final_url'])
        row['disposition']='authentication_required' if final.hostname=='github.com' and final.path.startswith(('/login','/session','/signup')) else 'reachable'
    except urllib.error.HTTPError as exc:
        row.update(http_status=exc.code,disposition='unverified_http_failure')
    except (OSError,ValueError,urllib.error.URLError,TimeoutError) as exc:
        row.update(disposition='unverified_network_or_target',failure_class=type(exc).__name__)
    return row


def links(root,paths):
    sources={}
    for name in paths:
        path=(root/name).resolve()
        if not path.is_relative_to(root.resolve()):raise ValueError('escaping document path')
        text=path.read_text()
        for url in re.findall(r'https?://[^\s<>"\)\]]+',text):
            url=url.rstrip('.,;`')
            if any(host in urllib.parse.urlsplit(url).hostname for host in ('example.invalid','example.com')):continue
            sources.setdefault(url,[]).append(name)
    return sources


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('paths',nargs='+');a=p.parse_args()
    sources=links(a.root,a.paths)
    with ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(check,sorted(sources)))
    for r in results:r['source_paths']=sorted(set(sources[r['url']]))
    value={'contract':'anonymous-public-links/1','scope':a.paths,'checked':results,'network_access_authorizes_deployment':False,'all_reachable':all(r['disposition']=='reachable' for r in results)}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    print(json.dumps({'urls':len(results),'unverified':sum(r['disposition']!='reachable' for r in results)}))


if __name__=='__main__':main()
