"""Rendered-output gate. Does not infer quality from a fixed page count."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote, urljoin
import hashlib, json, os, re, xml.etree.ElementTree as ET

class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.meta={};self.meta_entries=[];self.order_banner_count=0;self.h1=0;self.canonical=[];self.links=[];self.images=[];self.snapshots=[];self.title='';self.in_title=False
        self.visible=[];self.ignored=0;self.sections=[];self.journey_links=[];self.primary_families=[];self.product_families=[]
        self.journey_aside=0;self.purpose_cards=[];self.active_purpose=None
        self.markdown_blocks=[];self.markdown_depth=0;self.active_markdown_block=None
        self.source_cards=[];self.active_source=None;self.source_depth=0;self.source_field=None
        self.first_answer=[];self.capture_answer=False;self.answer_done=False;self.product_records=[];self.elements=[];self.feed(text)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        product=None
        if a.get('data-product-key'):
            product={'key':a['data-product-key'],'family':a.get('data-product-family'),'images':[],'links':[],'text':[]};self.product_records.append(product)
        if tag not in ['area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr']:self.elements.append((tag,product))
        if tag=='div' and 'markdown-content' in a.get('class','').split():self.markdown_depth=len(self.elements)
        if self.markdown_depth and tag in ['p','h2','h3','li']:
            self.active_markdown_block={'type':tag,'text':[]};self.markdown_blocks.append(self.active_markdown_block)
        context=next((p for _,p in reversed(self.elements) if p),None)
        if context and tag=='img':context['images'].append(a.get('src'))
        if context and tag=='a':context['links'].append(a.get('href'))
        if tag in ['script','style']:self.ignored+=1
        if tag=='section':self.sections.append(a.get('data-journey') or ('detail-hero' if 'detail-hero' in a.get('class','') else None))
        if tag=='section' and 'source-card' in a.get('class','').split():
            self.active_source={'type':a.get('data-source-type'),'name':[],'links':[],'dates':[],'date_text':[],'text':[]}
            self.source_cards.append(self.active_source);self.source_depth=len(self.sections)
        if self.active_source is not None:
            if tag=='h2':self.source_field='name'
            if tag=='time':self.source_field='date_text';self.active_source['dates'].append(a.get('datetime'))
            if tag=='a':self.active_source['links'].append(a)
        if tag=='aside' and 'journey-link' in a.get('class','').split():self.journey_aside+=1
        if tag=='p' and 'detail-hero' in self.sections and not self.answer_done:self.capture_answer=True
        if tag=='h1':self.h1+=1
        if tag=='title':self.in_title=True
        if tag=='meta':
            self.meta_entries.append((a.get('name',a.get('property')),a.get('content','')))
            self.meta[a.get('name',a.get('property'))]=a.get('content','')
        if tag=='aside' and a.get('data-order-banner')=='inline':self.order_banner_count+=1
        if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a.get('href'))
        if tag=='a':
            self.links.append(a.get('href',''))
            if 'next-step' in self.sections or self.journey_aside:self.journey_links.append(a.get('href',''))
            if 'purpose-card' in a.get('class','').split():
                self.active_purpose={'href':a.get('href'),'text':[]};self.purpose_cards.append(self.active_purpose)
        if tag=='img':self.images.append(a)
        if 'data-product-family' in a:
            self.product_families.append(a['data-product-family'])
            if 'detail-product' in a.get('class','') or 'hero-product' in a.get('class',''):self.primary_families.append(a['data-product-family'])
        if 'data-snapshot-id' in a:self.snapshots.append(a['data-snapshot-id'])
    def handle_endtag(self,tag):
        if self.active_markdown_block is not None and tag==self.active_markdown_block['type']:self.active_markdown_block=None
        if tag=='div' and len(self.elements)==self.markdown_depth:self.markdown_depth=0
        if tag=='title':self.in_title=False
        if tag=='p' and self.capture_answer:self.capture_answer=False;self.answer_done=True
        if tag in ['script','style']:self.ignored=max(0,self.ignored-1)
        if tag in ['h2','time']:self.source_field=None
        if tag=='section' and self.sections:
            if self.active_source is not None and len(self.sections)==self.source_depth:self.active_source=None
            self.sections.pop()
        if tag=='aside':self.journey_aside=max(0,self.journey_aside-1)
        if tag=='a':self.active_purpose=None
        for i in range(len(self.elements)-1,-1,-1):
            if self.elements[i][0]==tag:del self.elements[i:];break
    def handle_data(self,data):
        if self.in_title:self.title+=data
        if not self.ignored:self.visible.append(data)
        if self.capture_answer:self.first_answer.append(data)
        if self.active_markdown_block is not None and not self.ignored:self.active_markdown_block['text'].append(data)
        if self.active_purpose is not None:self.active_purpose['text'].append(data)
        if self.active_source is not None and not self.ignored:
            self.active_source['text'].append(data)
            if self.source_field:self.active_source[self.source_field].append(data)
        context=next((p for _,p in reversed(self.elements) if p),None)
        if context and not self.ignored:context['text'].append(data)

SOURCE_TYPE_LABELS={'official':'공공·기관','business':'사업자','facility':'시설','education':'교육기관','professional':'전문자료','reference':'참고자료'}

def check_social_image(doc, url, base, products, proof, brand):
    names=['og:image','og:image:secure_url','og:image:alt','og:image:type','og:image:width','og:image:height','twitter:image','twitter:image:alt']
    for name in names:
        assert sum(key==name for key,_ in doc.meta_entries)==1,f'Missing/duplicate {name}: {url}'
    image=doc.meta['og:image'];parsed=urlparse(image)
    assert parsed.scheme=='https' and parsed.netloc==urlparse(base).netloc and not parsed.query and not parsed.fragment,f'Unsafe/noncanonical social image: {url}'
    product=next((p for p in products if p['img']==parsed.path),None)
    assert product and product.get('assetType')=='real_product' and product.get('sourceLevel')=='official_business_source',f'Unverified social image: {url}'
    source=next((p for p in proof['products'] if p['key']==product['key']),None)
    assert source and source['image']['path']==product['img'],f'Social image provenance mismatch: {url}'
    assert doc.meta['og:image:secure_url']==image==doc.meta['twitter:image'],f'Social image URL drift: {url}'
    assert doc.meta['og:image:alt']==doc.meta['twitter:image:alt']==brand+' '+product['name'],f'Social image alt mismatch: {url}'
    assert [doc.meta['og:image:width'],doc.meta['og:image:height']]==[str(n) for n in source['image']['dimensions']],f'Social image dimensions mismatch: {url}'
    assert doc.meta['og:image:type']=='image/jpeg',f'Social image MIME mismatch: {url}'

def check_rendered_sources(doc, page):
    sources=page.get('sources')
    if sources is None:sources=[page['source']] if page.get('source') else []
    assert isinstance(sources,list),f'Invalid source array: {page["url"]}'
    assert len(doc.source_cards)==len(sources),f'Rendered source count mismatch: {page["url"]}'
    for expected,card in zip(sources,doc.source_cards):
        source_url=expected['url'];parsed=urlparse(source_url)
        assert parsed.scheme=='https' and parsed.hostname and not parsed.username and not parsed.password,f'Unsafe source URL: {page["url"]}'
        assert not re.search(r'[\x00-\x20\x7f\\\\]',source_url),f'Invalid source URL characters: {page["url"]}'
        assert ''.join(card['name'])==expected['name'],f'Rendered source name/order mismatch: {page["url"]}'
        assert card['type']==expected['type'],f'Rendered source type mismatch: {page["url"]}'
        assert len(card['links'])==1 and card['links'][0].get('href')==source_url,f'Rendered source URL/order mismatch: {page["url"]}'
        assert 'nofollow' in card['links'][0].get('rel','').split(),f'Source link rel mismatch: {page["url"]}'
        assert card['links'][0].get('aria-label')==expected['name']+' 확인',f'Source link label mismatch: {page["url"]}'
        assert card['dates']==[expected['verifiedAt']] and ''.join(card['date_text'])==expected['verifiedAt'],f'Rendered source date mismatch: {page["url"]}'
        assert f"출처 유형: {SOURCE_TYPE_LABELS[expected['type']]}" in ''.join(card['text']),f'Rendered source type label missing: {page["url"]}'

def check_rendered_answer(doc, page, expected_blocks):
    assert ''.join(doc.first_answer)==page.get('firstAnswer',''),f'Hero first answer changed: {page["url"]}'
    if not page.get('contentMarkdown'):return
    rendered=[{'type':block['type'],'text':''.join(block['text'])} for block in doc.markdown_blocks]
    assert rendered==expected_blocks,f'Rendered Markdown block mismatch: {page["url"]}'

def check_customer_output(doc, url):
    text=' '.join(doc.visible)
    for forbidden in ['Business Truth','Product Catalog','Shadow','검색의도','문구은','주문 주문']:
        assert forbidden.lower() not in text.lower(),f'Internal/invalid customer copy leaked: {url} {forbidden}'

def check_customer_journey(doc, page, pages, family_by_key=None):
    route={p['url']:p for p in pages}
    gift=page['pageType'] in ['hospital-visit','personal-gift','school-event','station-transit'] or page.get('visualIntent')=='performance_venue'
    for link in doc.journey_links:
        target=route.get(link)
        assert target and target['pageType'] in ['order-help','price-guide','message-guide'],f'Invalid next-step destination: {page["url"]} -> {link}'
        assert target.get('status')=='approved' and target.get('approvalVerified') is True and target.get('snapshotId'),f'Unapproved next-step destination: {page["url"]} -> {link}'
        assert target['pageKey']!=page['pageKey'] and target['url']!=page['url'],f'Self next-step destination: {page["url"]}'
        assert not (page['pageType']=='price-guide' and target['pageType']=='price-guide'),f'Price-guide next-step loop: {page["url"]} -> {link}'
        if family_by_key is not None:
            source_families=set(family_by_key[page['pageKey']]);target_families=set(family_by_key[target['pageKey']])
            assert source_families and source_families.issubset(target_families),f'Cross-family next-step destination: {page["url"]} -> {link}'
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

def check_opening_visual(doc, page, products, root):
    if page['pageType']!='business-opening':return
    url=page['url']
    real=page.get('assetSlot')=='REAL_PROOF' or page.get('visualIntent') in ['congrats_wreath','funeral_wreath']
    if real:
        assert page.get('assetSlot') in [None,'','REAL_PROOF'],f'Opening product cannot satisfy a different asset slot: {url}'
        assert doc.primary_families==['congrats'],f'Opening primary product mismatch: {url}'
        hero=doc.product_records[0]
        product=next((p for p in products if p['key']==hero['key']),None)
        assert product and product['family']=='congrats' and product['assetType']=='real_product',f'Unverified opening product: {url}'
        assert doc.images[0]['src']==product['img'],f'Opening REAL_PROOF hero is not its official product image: {url}'
        proof=json.loads((root/'src/data/catalog-provenance.json').read_text())
        source=next(p for p in proof['products'] if p['key']==product['key'])
        assert source['officialSku']==product['officialSku'] and source['image']['path']==product['img'],f'Opening SKU/image provenance mismatch: {url}'
        assert hashlib.sha256((root/'public'/product['img'].lstrip('/')).read_bytes()).hexdigest()==source['image']['sha256'],f'Opening image hash mismatch: {url}'
        width,height=source['image']['dimensions'];image=doc.images[0]
        assert int(image['width'])*height==int(image['height'])*width,f'Opening REAL_PROOF aspect ratio changed: {url}'
        css=(root/'src/styles/global.css').read_text()
        assert '.hero-products img,.detail-product img,.product-card img{object-fit:contain' in css,f'Opening REAL_PROOF must not be cropped: {url}'
        caption=' '.join(hero['text'])
        assert '공식 상품 이미지' in caption and '사진 속 리본 문구는 예시' in caption,f'Opening product/reference ribbon disclosure missing: {url}'
    else:
        assert not page.get('assetSlot'),f'No compatible opening illustration for asset slot: {url}'
        asset=json.loads((root/'src/data/editorial-assets.json').read_text())['openingWreath']
        assert asset['assetType']=='editorial_illustration' and doc.images[0]['src']==asset['img'],f'Opening editorial provenance mismatch: {url}'
        assert 'AI 일러스트' in asset['caption'] and asset['caption'] in ' '.join(doc.visible),f'Unlabeled editorial opening hero: {url}'

def check(root=Path('.')):
    dist=root/'dist'; data=root/'src/data'
    pages=json.loads((data/'pages.json').read_text());manifest=json.loads((data/'publish-manifest.json').read_text())
    arch=json.loads((data/'architecture.json').read_text());truth=json.loads((data/'business-truth.json').read_text())
    products=json.loads((data/'products.json').read_text())
    social_proof=json.loads((data/'catalog-provenance.json').read_text())
    import subprocess
    subprocess.run(['node', 'scripts/qa_seongnam_catalog.mjs'], cwd=root, check=True)
    navigation=json.loads(subprocess.check_output(['node','--input-type=module','-e',
        "import fs from 'node:fs'; import {productFamilies} from './src/lib/catalog.mjs'; import {hubGuide} from './src/lib/hubs.mjs'; import {displayMarkdownBlocks,inlineTokens} from './src/lib/content.mjs'; const pages=JSON.parse(fs.readFileSync('src/data/pages.json')); const cats=[...new Set(pages.map(p=>p.category))]; console.log(JSON.stringify({body:Object.fromEntries(pages.map(p=>[p.pageKey,displayMarkdownBlocks(p.contentMarkdown||'',p.firstAnswer).map(b=>({type:b.type,text:inlineTokens(b.text).map(t=>t.text).join('')}))])),families:Object.fromEntries(pages.map(p=>[p.pageKey,productFamilies(p)])),purpose:Object.fromEntries(cats.map(c=>['/'+c+'/',hubGuide(c,pages).decision[0]]))}));"],cwd=root,text=True))
    site_config=json.loads((data/'site-config.json').read_text())
    base=(os.environ.get('SITE_URL') or site_config['previewUrl']).rstrip('/')
    indexable=os.environ.get('SITE_INDEXABLE')=='true'
    hubs={h['url']:h for h in arch['hubs'] if any(p['category']==h['category'] for p in pages)}
    expected={'/'}|{p['url'] for p in pages}|set(hubs)
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
        thin_hub=url in hubs and hubs[url]['children']<3
        assert doc.meta.get('robots')==('index,follow' if indexable and not thin_hub else 'noindex,nofollow,noarchive'),f'Wrong robots: {url}'
        for field in ['og:title','og:description','og:url','twitter:card']:assert doc.meta.get(field),f'Missing {field}: {url}'
        check_social_image(doc,url,base,products,social_proof,truth['brand'])
        if url=='/' or url in hubs:assert doc.order_banner_count==1,f'Expected one mid-page order banner: {url}'
        assert truth['phoneHref'] in doc.links,f'Missing real phone CTA: {url}'
        assert any(x.startswith(truth['onlineOrderUrl']) for x in doc.links),f'Missing order CTA: {url}'
        for img in doc.images:
            assert img.get('alt','').strip(),f'Empty image alt: {url}'
            src=img.get('src','');assert src.startswith('/'),f'Unexpected remote image: {url}'
            assert (root/'public'/src.lstrip('/')).is_file(),f'Missing asset: {src}'
        check_customer_output(doc,url)
        check_rendered_catalog(doc,url,products)
    for page in pages:
        check_customer_journey(docs[page['url']],page,pages,navigation['families'])
        check_rendered_intent(docs[page['url']],page,products)
        check_rendered_sources(docs[page['url']],page)
        check_rendered_answer(docs[page['url']],page,navigation['body'][page['pageKey']])
    assert {p['href'] for p in docs['/'].purpose_cards}==set(navigation['purpose']), 'Home purpose-card route mismatch'
    for card in docs['/'].purpose_cards:
        assert navigation['purpose'][card['href']] in ''.join(card['text']),f'Home purpose-card promise differs from actual hub children: {card["href"]}'
    assert {'funeral','congrats'} == set(docs['/'].primary_families), 'Home hero omits advertised product purpose'
    assert {'funeral','congrats'} == set(docs['/'].product_families), 'Home product selection omits advertised product purpose'
    for page in pages:
        check_opening_visual(docs[page['url']],page,products,root)
        if page.get('visualIntent')=='performance_venue':
            assert docs[page['url']].primary_families==['bouquet'],f'Performance primary product mismatch: {page["url"]}'
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
    sitemap_expected={'/'}|{p['url'] for p in pages}|{h['url'] for h in arch['hubs'] if h['children']>=3}
    assert sitemap_urls=={base+u for u in sitemap_expected},f'Sitemap mismatch: {sitemap_urls ^ {base+u for u in sitemap_expected}}'
    headers=(dist/'_headers').read_text()
    if not indexable:
        assert 'X-Robots-Tag: noindex, nofollow, noarchive' in headers
    else:
        for hub in hubs.values():
            if hub['children']<3:
                assert f"{hub['url']}\n  X-Robots-Tag: noindex, nofollow, noarchive" in headers, f"Thin hub header missing: {hub['url']}"
    robots=(dist/'robots.txt').read_text()
    assert ('Allow: /' in robots and 'Disallow: /' not in robots) if indexable else 'Disallow: /' in robots
    not_found=Document((dist/'404.html').read_text());assert 'noindex' in not_found.meta.get('robots','') and not not_found.canonical
    assert not_found.order_banner_count==0 and 'og:image' not in not_found.meta, '404 must not become a purchase/share landing page'
    print(f'STATIC QA PASSED: {len(pages)} details, {len(expected)} HTML routes; indexable={indexable}; exact metadata/sitemap/snapshot/link parity')

if __name__=='__main__':check()
