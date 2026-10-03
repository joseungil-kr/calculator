"""Rendered-output gate. Does not infer quality from a fixed page count."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote, urljoin
import hashlib, json, os, re, xml.etree.ElementTree as ET

class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.cta_links=[];self.ids=set();self.meta={};self.meta_entries=[];self.order_banner_count=0;self.h1=0;self.canonical=[];self.links=[];self.images=[];self.snapshots=[];self.title='';self.in_title=False
        self.visible=[];self.ignored=0;self.sections=[];self.journey_links=[];self.primary_families=[];self.product_families=[]
        self.first_answer=[];self.capture_answer=False;self.answer_done=False;self.product_records=[];self.elements=[];self.banner_depth=0;self.banner_links=[];self.banner_labels=[];self.feed(text)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if a.get('id'):self.ids.add(a['id'])
        product=None
        if a.get('data-product-key'):
            product={'key':a['data-product-key'],'family':a.get('data-product-family'),'images':[],'links':[],'text':[]};self.product_records.append(product)
        if tag not in ['area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr']:self.elements.append((tag,product,tag=='footer' or 'mobile-bar' in a.get('class','').split()))
        context=next((p for _,p,_ in reversed(self.elements) if p),None)
        if context and tag=='img':context['images'].append(a.get('src'))
        if context and tag=='a':context['links'].append(a.get('href'))
        if tag in ['script','style']:self.ignored+=1
        if tag=='section':self.sections.append(a.get('data-journey') or ('detail-hero' if 'detail-hero' in a.get('class','') else None))
        if tag=='p' and 'detail-hero' in self.sections and not self.answer_done:self.capture_answer=True
        if tag=='h1':self.h1+=1
        if tag=='title':self.in_title=True
        if tag=='meta':
            self.meta_entries.append((a.get('name',a.get('property')),a.get('content','')))
            self.meta[a.get('name',a.get('property'))]=a.get('content','')
        if tag=='aside' and a.get('data-order-banner')=='inline':
            self.order_banner_count+=1;self.banner_depth=len(self.elements);self.banner_links.append([]);self.banner_labels.append(a.get('aria-label',''))
        if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a.get('href'))
        if tag=='a':
            self.links.append(a.get('href',''))
            if self.banner_depth:self.banner_links[-1].append(a.get('href',''))
            if context or 'btn' in a.get('class','').split() or any(order for _,_,order in self.elements):self.cta_links.append(a.get('href',''))
            if 'next-step' in self.sections:self.journey_links.append(a.get('href',''))
        if tag=='img':self.images.append(a)
        if 'data-product-family' in a:
            self.product_families.append(a['data-product-family'])
            if 'detail-product' in a.get('class','') or 'hero-product' in a.get('class',''):self.primary_families.append(a['data-product-family'])
        if 'data-snapshot-id' in a:self.snapshots.append(a['data-snapshot-id'])
    def handle_endtag(self,tag):
        if tag=='aside' and len(self.elements)==self.banner_depth:self.banner_depth=0
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
        context=next((p for _,p,_ in reversed(self.elements) if p),None)
        if context and not self.ignored:context['text'].append(data)

def image_metadata(data):
    if data[:2]==b'\xff\xd8':
        i=2
        while i+9<len(data):
            assert data[i]==255, 'Invalid JPEG marker'
            while data[i]==255:i+=1
            marker=data[i];i+=1
            if marker in (0xD9,0xDA):break
            length=int.from_bytes(data[i:i+2],'big');assert length>=2
            if marker in (0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF):
                return [int.from_bytes(data[i+5:i+7],'big'),int.from_bytes(data[i+3:i+5],'big')], 'image/jpeg'
            i+=length
    elif data[:4]==b'RIFF' and data[8:12]==b'WEBP':
        kind=data[12:16]
        if kind==b'VP8 ' and data[23:26]==b'\x9d\x01\x2a':
            return [int.from_bytes(data[26:28],'little')&0x3fff,int.from_bytes(data[28:30],'little')&0x3fff], 'image/webp'
        if kind==b'VP8L' and data[20]==0x2f:
            bits=int.from_bytes(data[21:25],'little')
            return [(bits&0x3fff)+1,((bits>>14)&0x3fff)+1], 'image/webp'
        if kind==b'VP8X':
            return [int.from_bytes(data[24:27],'little')+1,int.from_bytes(data[27:30],'little')+1], 'image/webp'
    raise AssertionError('Unsupported social asset format')


def check_social_provenance(root, products, proof):
    records=proof['products']
    assert len({p['key'] for p in records})==len(records)==len(products),'Social provenance set mismatch'
    for product in products:
        record=next((p for p in records if p['key']==product['key']),None)
        assert record and record['name']==product['name'] and record['sourceUrl']==product['sourceUrl'] and record['verifiedAt']==product['verifiedAt'],'Social provenance identity mismatch'
        image=record['image']
        assert image['path']==product['img'] and re.fullmatch(r'/images/products/[a-z0-9-]+\.(jpg|webp)',image['path']),'Unsafe social asset path'
        raw=(root/'public'/image['path'].lstrip('/')).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==image['sha256'],'Social asset bytes changed'
        dimensions,mime=image_metadata(raw)
        assert dimensions==image['dimensions'] and mime==image['type'],'Social asset dimensions/MIME mismatch'


def check_social_image(doc, url, base, products, proof, brand):
    names=['og:image','og:image:secure_url','og:image:alt','og:image:type','og:image:width','og:image:height','twitter:image','twitter:image:alt']
    for name in names:assert sum(key==name for key,_ in doc.meta_entries)==1,f'Missing/duplicate {name}: {url}'
    image=doc.meta['og:image'];parsed=urlparse(image)
    assert parsed.scheme=='https' and parsed.netloc==urlparse(base).netloc and not parsed.query and not parsed.fragment,f'Unsafe/noncanonical social image: {url}'
    product=next((p for p in products if p['img']==parsed.path),None)
    assert product and product.get('assetType')=='real_product' and product.get('sourceLevel')=='official_business_source',f'Unverified social image: {url}'
    source=next((p for p in proof['products'] if p['key']==product['key']),None)
    assert source and source['image']['path']==product['img'],f'Social image provenance mismatch: {url}'
    assert doc.meta['og:image:secure_url']==image==doc.meta['twitter:image'],f'Social image URL drift: {url}'
    assert doc.meta['og:image:alt']==doc.meta['twitter:image:alt']==brand+' '+product['name'],f'Social image alt mismatch: {url}'
    assert [doc.meta['og:image:width'],doc.meta['og:image:height']]==[str(n) for n in source['image']['dimensions']],f'Social image dimensions mismatch: {url}'
    assert doc.meta['og:image:type']==source['image']['type'],f'Social image MIME mismatch: {url}'


def check_purchase_banner(doc, url, truth):
    assert doc.order_banner_count==1,f'Expected one purchase banner: {url}'
    assert doc.banner_links==[[truth['phoneHref'],truth['onlineOrderUrl']]],f'Purchase banner CTA mismatch: {url}'
    assert len(doc.banner_labels)==1 and truth['brand'] in doc.banner_labels[0],f'Purchase banner brand/label missing: {url}'


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

def check_order_ctas(doc, url, truth):
    assert truth['onlineOrderUrl'] in doc.cta_links,f'Missing Business Truth online CTA: {url}'
    assert truth['phoneHref'] in doc.cta_links,f'Missing Business Truth phone CTA: {url}'
    for href in doc.cta_links:
        if href.startswith('#') or (href.startswith('/') and not href.startswith('//')):continue  # Local navigational button.
        expected=truth['phoneHref'] if href.startswith('tel:') else truth['onlineOrderUrl']
        assert href==expected,f'Order CTA contradicts Business Truth: {url} -> {href}'

def check_rendered_catalog(doc, url, products, order_url):
    catalog={p['key']:p for p in products}
    for rendered in doc.product_records:
        p=catalog.get(rendered['key'])
        assert p and rendered['family']==p['family'],f'Rendered catalog family mismatch: {url}'
        assert rendered['images']==[p['img']],f'Rendered catalog image mismatch: {url} {p["key"]}'
        assert all(href==order_url for href in rendered['links']) and order_url in doc.cta_links,f'Rendered product CTA mismatch: {url} {p["key"]}'
        assert f'{p["price"]:,}원' in ''.join(rendered['text']),f'Rendered catalog price mismatch: {url} {p["key"]}'

def check(root=Path('.')):
    dist=root/'dist'; data=root/'src/data'
    pages=json.loads((data/'pages.json').read_text());manifest=json.loads((data/'publish-manifest.json').read_text())
    arch=json.loads((data/'architecture.json').read_text());truth=json.loads((data/'business-truth.json').read_text())
    products=json.loads((data/'products.json').read_text())
    social_proof=json.loads((data/'social-image-provenance.json').read_text())
    check_social_provenance(root,products,social_proof)
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
        check_rendered_catalog(doc,url,products,truth['onlineOrderUrl'])
        check_order_ctas(doc,url,truth)
        check_social_image(doc,url,base,products,social_proof,truth['brand'])
        check_purchase_banner(doc,url,truth)
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
    assert not not_found.order_banner_count and 'og:image' not in not_found.meta and 'twitter:image' not in not_found.meta,'404 must not advertise a normal page'
    print(f'STATIC QA PASSED: {len(pages)} details, {len(expected)} HTML routes; indexable={indexable}; exact metadata/sitemap/snapshot/link parity')

if __name__=='__main__':check()
