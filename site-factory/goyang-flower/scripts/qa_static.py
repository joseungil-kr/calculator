"""Rendered-output gate. Does not infer quality from a fixed page count."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote, urljoin
import json, os, re, xml.etree.ElementTree as ET

class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids=set();self.meta={};self.h1=0;self.canonical=[];self.links=[];self.images=[];self.snapshots=[];self.title='';self.in_title=False
        self.visible=[];self.ignored=0;self.sections=[];self.journey_links=[];self.primary_families=[];self.product_families=[]
        self.first_answer=[];self.capture_answer=False;self.answer_done=False;self.product_records=[];self.elements=[];self.feed(text)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if a.get('id'):self.ids.add(a['id'])
        product=None
        if a.get('data-product-key'):
            product={'key':a['data-product-key'],'family':a.get('data-product-family'),'images':[],'links':[],'text':[]};self.product_records.append(product)
        if tag not in ['area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr']:self.elements.append((tag,product))
        context=next((p for _,p in reversed(self.elements) if p),None)
        if context and tag=='img':context['images'].append(a.get('src'))
        if context and tag=='a':context['links'].append(a.get('href'))
        if tag in ['script','style']:self.ignored+=1
        if tag=='section':self.sections.append(a.get('data-journey') or ('detail-hero' if 'detail-hero' in a.get('class','') else None))
        if tag=='p' and 'detail-hero' in self.sections and not self.answer_done:self.capture_answer=True
        if tag=='h1':self.h1+=1
        if tag=='title':self.in_title=True
        if tag=='meta':self.meta[a.get('name',a.get('property'))]=a.get('content','')
        if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a.get('href'))
        if tag=='a':
            self.links.append(a.get('href',''))
            if 'next-step' in self.sections:self.journey_links.append(a.get('href',''))
        if tag=='img':self.images.append(a)
        if 'data-product-family' in a:
            self.product_families.append(a['data-product-family'])
            if 'detail-product' in a.get('class','') or 'hero-product' in a.get('class',''):self.primary_families.append(a['data-product-family'])
        if 'data-snapshot-id' in a:self.snapshots.append(a['data-snapshot-id'])
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
        if tag=='p' and self.capture_answer:self.capture_answer=False;self.answer_done=True
        if tag in ['script','style']:self.ignored=max(0,self.ignored-1)
        if tag=='section' and self.sections:self.sections.pop()
        for i in range(len(self.elements)-1,-1,-1):
            if self.elements[i][0]==tag:del self.elements[i:];break
    def handle_data(self,data):
        if self.in_title:self.title+=data
        if not self.ignored:self.visible.append(data)
        if self.capture_answer:self.first_answer.append(data)
        context=next((p for _,p in reversed(self.elements) if p),None)
        if context and not self.ignored:context['text'].append(data)

def expected_robots(indexable, url, architecture):
    if not indexable:
        return 'noindex,nofollow,noarchive'
    thin_hub=any(h['url']==url and h['children']<3 for h in architecture['hubs'])
    return 'noindex,follow' if thin_hub else 'index,follow'

def check_customer_output(doc, url):
    text=' '.join(doc.visible)
    for forbidden in ['Business Truth','Product Catalog','Shadow','검색의도','문구은','주문 주문']:
        assert forbidden.lower() not in text.lower(),f'Internal/invalid customer copy leaked: {url} {forbidden}'

def check_customer_journey(doc, page, pages):
    route={p['url']:p for p in pages}
    gift=page['pageType'] in ['hospital-visit','personal-gift','school-event','station-transit'] or page.get('visualIntent')=='performance_venue'
    for link in doc.journey_links:
        target=route.get(link)
        assert target and target['pageType'] in ['order-help','price-guide','message-guide'],f'Invalid next-step destination: {page["url"]} -> {link}'
        assert target['category'] in ['order',page['category']],f'Invalid next-step category: {link}'
        assert not gift or target.get('visualIntent') not in ['wreath_order','wreath_message'],f'Gift intent leads to wreath order: {page["url"]} -> {link}'
    assert not gift or not any(route.get(link,{}).get('visualIntent')=='wreath_order' for link in doc.links),f'Gift intent leads to wreath order: {page["url"]}'

def check_rendered_intent(doc, page, products):
    text=' '.join(doc.visible)
    if page.get('visualIntent')=='performance_venue':
        first=' '.join(doc.first_answer)
        assert '꽃다발' in first and '축하화환은' not in first,f'Performance primary answer mismatch: {page["url"]}'
        prices={p['price'] for p in products if p['family']=='bouquet'}
        assert all(int(n.replace(',','')) in prices for n in re.findall(r'(\d{1,3}(?:,\d{3})+)원',first)),f'Performance primary price mismatch: {page["url"]}'
        assert '축하화환 상품을 선택해' not in text,f'Performance body product mismatch: {page["url"]}'
    if page['pageType']=='message-guide' and '화환' in page['primaryKeyword']:
        examples=re.findall(r'[“"]([^”"\n]{4,100})[”"]',text)
        for purpose,pattern in [('condolence',r'삼가|애도|명복|위로'),('opening',r'개업|개점|번창'),('relocation',r'이전|새로운 출발|새 보금자리'),('event',r'공연|행사|전시|무대')]:
            assert any(re.search(pattern,e) for e in examples),f'Missing rendered {purpose} examples: {page["url"]}'

def check_rendered_catalog(doc, url, products):
    catalog={p['key']:p for p in products}
    for rendered in doc.product_records:
        p=catalog.get(rendered['key'])
        assert p and rendered['family']==p['family'],f'Rendered catalog family mismatch: {url}'
        assert rendered['images']==[p['img']],f'Rendered catalog image mismatch: {url} {p["key"]}'
        assert p['orderUrl'] in rendered['links'] or p['orderUrl'] in doc.links,f'Rendered SKU order mismatch: {url} {p["key"]}'
        assert f'{p["price"]:,}원' in ''.join(rendered['text']),f'Rendered catalog price mismatch: {url} {p["key"]}'

def check(root=Path('.')):
    dist=root/'dist'; data=root/'src/data'
    pages=json.loads((data/'pages.json').read_text());manifest=json.loads((data/'publish-manifest.json').read_text())
    arch=json.loads((data/'architecture.json').read_text());truth=json.loads((data/'business-truth.json').read_text())
    products=json.loads((data/'products.json').read_text())
    site_config=json.loads((data/'site-config.json').read_text())
    base=(os.environ.get('SITE_URL') or site_config['previewUrl']).rstrip('/')
    indexable=os.environ.get('SITE_INDEXABLE')=='true' and site_config.get('productionApproved') is True
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
        assert doc.meta.get('robots')==expected_robots(indexable,url,arch),f'Wrong robots: {url}'
        for field in ['og:title','og:description','og:url','twitter:card']:assert doc.meta.get(field),f'Missing {field}: {url}'
        assert truth['phoneHref'] in doc.links,f'Missing real phone CTA: {url}'
        assert any(x.startswith(truth['onlineOrderUrl']) for x in doc.links),f'Missing order CTA: {url}'
        for img in doc.images:
            assert img.get('alt','').strip(),f'Empty image alt: {url}'
            src=img.get('src','');assert src.startswith('/'),f'Unexpected remote image: {url}'
            assert (root/'public'/src.lstrip('/')).is_file(),f'Missing asset: {src}'
        check_customer_output(doc,url)
        check_rendered_catalog(doc,url,products)
    for page in pages:
        check_customer_journey(docs[page['url']],page,pages)
        check_rendered_intent(docs[page['url']],page,products)
    assert {'bouquet','basket','funeral','congrats'} <= set(docs['/'].primary_families), 'Home hero omits advertised product purpose'
    assert {'bouquet','basket','funeral','congrats'} <= set(docs['/'].product_families), 'Home product selection omits advertised product purpose'
    for page in pages:
        if page['pageType']=='business-opening':
            doc=docs[page['url']]
            assert doc.images[0]['src'].startswith('/images/editorial/'),f'Opening hero communicates wedding sample: {page["url"]}'
            assert 'AI 일러스트' in ' '.join(doc.visible),f'Unlabeled editorial opening hero: {page["url"]}'
        if page.get('visualIntent')=='performance_venue':
            assert docs[page['url']].primary_families==['bouquet'],f'Performance primary product mismatch: {page["url"]}'
    for url,doc in docs.items():
        for href in doc.links:
            if href.startswith(('tel:','mailto:')):continue
            target=urlparse(urljoin(base+url,href))
            if target.netloc!=urlparse(base).netloc:continue
            path=unquote(target.path)
            assert path in expected,f'Broken internal link: {url} -> {path}'
            if target.fragment:assert unquote(target.fragment) in docs[path].ids,f'Broken internal fragment: {url} -> {href}'
            if path!=url:incoming[path].add(url)
    for url in expected-{'/'}:assert incoming[url],f'Orphan page: {url}'
    # Check the rendered regional graph, independently of planned coverage size.
    coverage=json.loads((data/'region-coverage.json').read_text())
    units={unit['pageKey']:unit for unit in coverage['units']}
    regional=[page for page in pages if page['category']=='regions']
    for page in regional:
        unit=units.get(page['pageKey'])
        assert unit and page['url']==unit['url'],f'Unknown regional route: {page["url"]}'
        assert unit['districtKey'] in docs['/regions/'].ids,f'Missing district section: {page["url"]}'
        assert page['url'] in docs['/regions/'].links,f'Missing regional hub link: {page["url"]}'
        assert '/regions/#'+unit['districtKey'] in docs['/'].links,f'Missing home district link: {page["url"]}'
    if not regional:
        assert '/regions/' not in expected and not (dist/'regions/index.html').exists(), 'Empty regional hub generated'
    for page in manifest['pages']:
        assert docs[page['url']].snapshots==[page['snapshotId']],f'Snapshot not rendered: {page["pageKey"]}'
    sitemap_urls=set()
    for file in dist.glob('sitemap-*.xml'):
        tree=ET.parse(file)
        for loc in tree.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
            if not (loc.text or '').endswith('.xml'):sitemap_urls.add(unquote(loc.text or ''))
    sitemap_expected={'/'}|{p['url'] for p in pages}|{h['url'] for h in arch['hubs'] if h['children']>=3}
    assert sitemap_urls=={base+u for u in sitemap_expected},f'Sitemap mismatch: {sitemap_urls ^ {base+u for u in sitemap_expected}}'
    headers=(dist/'_headers').read_text()
    assert ('X-Robots-Tag: noindex, nofollow, noarchive' not in headers) if indexable else ('X-Robots-Tag: noindex, nofollow, noarchive' in headers)
    robots=(dist/'robots.txt').read_text()
    assert ('Allow: /' in robots and 'Disallow: /' not in robots) if indexable else 'Disallow: /' in robots
    not_found=Document((dist/'404.html').read_text());assert 'noindex' in not_found.meta.get('robots','')
    print(f'STATIC QA PASSED: {len(pages)} details, {len(expected)} HTML routes; indexable={indexable}; exact metadata/sitemap/snapshot/link parity')

if __name__=='__main__':check()
