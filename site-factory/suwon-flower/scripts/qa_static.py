"""Rendered-output gate. Does not infer quality from a fixed page count."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote, urljoin
import json, os, xml.etree.ElementTree as ET

class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.meta={};self.h1=0;self.canonical=[];self.links=[];self.images=[];self.snapshots=[];self.title='';self.in_title=False;self.feed(text)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='h1':self.h1+=1
        if tag=='title':self.in_title=True
        if tag=='meta':self.meta[a.get('name',a.get('property'))]=a.get('content','')
        if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a.get('href'))
        if tag=='a':self.links.append(a.get('href',''))
        if tag=='img':self.images.append(a)
        if 'data-snapshot-id' in a:self.snapshots.append(a['data-snapshot-id'])
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
    def handle_data(self,data):
        if self.in_title:self.title+=data

def check(root=Path('.')):
    dist=root/'dist'; data=root/'src/data'
    pages=json.loads((data/'pages.json').read_text());manifest=json.loads((data/'publish-manifest.json').read_text())
    arch=json.loads((data/'architecture.json').read_text());truth=json.loads((data/'business-truth.json').read_text())
    base=os.environ.get('SITE_URL','https://suwon.fwith.kr').rstrip('/')
    indexable=os.environ.get('SITE_INDEXABLE')=='true'
    expected={'/'}|{p['url'] for p in pages}|{h['url'] for h in arch['hubs'] if any(p['category']==h['category'] for p in pages)}
    docs={};titles=set();descriptions=set();incoming={u:set() for u in expected}
    for url in expected:
        file=dist/url.strip('/')/'index.html'
        assert file.exists(),f'Missing generated page: {url}'
        text=file.read_text();doc=Document(text);docs[url]=doc
        assert doc.h1==1,f'Expected exactly one H1: {url}'
        assert doc.title and doc.title not in titles,f'Duplicate/missing title: {url}';titles.add(doc.title)
        description=doc.meta.get('description','')
        assert description and description not in descriptions,f'Duplicate/missing description: {url}';descriptions.add(description)
        assert doc.canonical==[base+url],f'Canonical mismatch: {url} {doc.canonical}'
        assert doc.meta.get('robots')==('index,follow' if indexable else 'noindex,nofollow,noarchive'),f'Wrong robots: {url}'
        for field in ['og:title','og:description','og:url','twitter:card']:assert doc.meta.get(field),f'Missing {field}: {url}'
        assert truth['phoneHref'] in doc.links,f'Missing real phone CTA: {url}'
        assert any(x.startswith(truth['onlineOrderUrl']) for x in doc.links),f'Missing order CTA: {url}'
        for img in doc.images:
            assert img.get('alt','').strip(),f'Empty image alt: {url}'
            src=img.get('src','');assert src.startswith('/'),f'Unexpected remote image: {url}'
            assert (root/'public'/src.lstrip('/')).is_file(),f'Missing asset: {src}'
        for forbidden in ['Business Truth','Shadow','검색의도']:assert forbidden not in text,f'Internal copy leaked: {url}'
    for url,doc in docs.items():
        for href in doc.links:
            if href.startswith(('tel:','mailto:','#')):continue
            target=urlparse(urljoin(base+url,href))
            if target.netloc!=urlparse(base).netloc:continue
            path=unquote(target.path)
            assert path in expected,f'Broken internal link: {url} -> {path}'
            if path!=url:incoming[path].add(url)
    for url in expected-{'/'}:assert incoming[url],f'Orphan page: {url}'
    for page in manifest['pages']:
        assert docs[page['url']].snapshots==[page['snapshotId']],f'Snapshot not rendered: {page["pageKey"]}'
    sitemap_urls=set()
    for file in dist.glob('sitemap-*.xml'):
        tree=ET.parse(file)
        for loc in tree.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
            if not (loc.text or '').endswith('.xml'):sitemap_urls.add(unquote(loc.text or ''))
    assert sitemap_urls=={base+u for u in expected},f'Sitemap mismatch: {sitemap_urls ^ {base+u for u in expected}}'
    headers=(dist/'_headers').read_text()
    assert ('X-Robots-Tag: noindex, nofollow, noarchive' not in headers) if indexable else ('X-Robots-Tag: noindex, nofollow, noarchive' in headers)
    robots=(dist/'robots.txt').read_text()
    assert ('Allow: /' in robots and 'Disallow: /' not in robots) if indexable else 'Disallow: /' in robots
    not_found=Document((dist/'404.html').read_text());assert 'noindex' in not_found.meta.get('robots','')
    print(f'STATIC QA PASSED: {len(pages)} details, {len(expected)} HTML routes; indexable={indexable}; exact metadata/sitemap/snapshot/link parity')

if __name__=='__main__':check()
