# Vertical Blueprint: Flower Local v3

## 역할
지역별 꽃배달/꽃 선택 사이트에 공통 적용한다. 지역명만 치환하는 페이지 공장이 아니라, 한 지역 안에서 서비스·장소·상황·주문 의도를 각각 정확한 문서와 연결하는 정보구조를 만든다.

## 1. 꽃배달 단일 지역 사이트 정보구조
서브도메인 자체가 하나의 지역을 담당하므로 별도의 /region/<지역>/ 경로를 강제하지 않는다. 공통 Contract의 REGION HUB를 다음처럼 구현한다.

HOME(/) — 지역 꽃배달 commercial landing
→ /<지역>꽃배달/ — REGION_SERVICE_LANDING / informational pillar
→ /funeral/ — 근조화환·장례식장 SERVICE/PLACE hub
→ /places/ — 병원·역·대학·행사장 PLACE hub
→ /occasions/ — 개업·이전·졸업·행사 INTENT hub
→ /order-help/ — 주문·시간·문구·가격·배송 INTENT/PRICE hub
→ /flower-knowledge/ — 꽃 선택·보관·관리 INFORMATION hub
→ /guide/ — 범용 선택/비교 INFORMATION hub
→ 각 category detail landing

HOME과 /<지역>꽃배달/의 역할을 중복시키지 않는다. HOME은 상품/가격/전화/온라인 주문과 대표 서비스를 중심으로 하고, 지역 랜딩은 장소·상황·서비스·주문 가이드를 연결하는 informational pillar로 유지한다.

## 2. 공통 Page Role → 현재 flower page_type 매핑
- REGION_SERVICE_LANDING → general-guide + routeType=top_level
- PLACE_LANDING → funeral-facility / hospital / station-transit / event-venue
- INTENT_LANDING → opening-business / order-help / 필요 시 general-guide
- PRICE_GUIDE → order-help
- INFORMATION_GUIDE → flower-knowledge / order-help / general-guide
- HUB → Astro HubIndex 및 regional top-level pillar

새 page_type enum을 무리하게 늘리지 않고 위 의미 역할을 Page Plan의 content_role, search_intent, required_sections, internal_link_hub와 함께 사용한다.

## 3. 키워드/의도 설계
기본 식: 지역 × 서비스 × 의도.

예:
- 지역 × 근조화환 × 주문
- 지역 × 축하화환 × 개업
- 지역 × 꽃배달 × 당일
- 역/병원/장례식장 × 꽃/화환 × 수령·반입·배송
- 꽃/화환 × 가격·문구·관리 × 정보 탐색

동의어이고 CTA/기대정보가 같은 검색은 하나로 통합한다. 근조화환과 개업화환처럼 상품/목적/CTA 또는 필수 정보가 다르면 분리한다.

## 4. Title / H1 / 본문
Title 기본: [지역/장소] + [정확한 서비스] + [핵심 의도].
H1은 1개이며 Title과 핵심 지역·서비스가 일치해야 한다.
본문 첫 구간은 검색자의 핵심 질문에 직접 답하고, 글자 수를 맞추기 위한 지역 역사/관광/맛집/인구 설명을 넣지 않는다.

지역 고유정보는 실제 주문 판단에 필요한 범위에서 사용한다:
- 장례식장/병원/역/상권/행사장
- 접근·수령·반입·주차·진입
- 주문에 필요한 빈소/받는사람/담당자 정보
- 공식 근거가 있는 운영/시설 정보
- 검증된 배송 추가조건

## 5. 내부링크
링크 개수를 목표로 하지 않는다. 우선순위:
1. 지역 랜딩 /<지역>꽃배달/
2. 현재 서비스/의도의 상위 hub
3. 같은 지역의 실제 관련 서비스/장소
4. 사용자의 다음 질문에 해당하는 문서
5. 필요 시 인접 지역 또는 공통 정보 문서

모든 상세 페이지는 region landing과 category hub의 계층 안에서 발견 가능해야 한다. Breadcrumb는 HOME → REGION LANDING → HUB → DETAIL 순서를 기본으로 한다.

## 6. launch / growth / batch
- initial_page_target은 launch 완성도 목표이며 검색 순위 공식이 아니다.
- 신규 사이트는 지역 데이터와 intent 다양성에 따라 보통 30~49 범위에서 설정한다. 기존 사이트의 이미 정해진 target은 remediation 시 존중한다.
- launch에서는 하루 1페이지/1지역 제한을 사용하지 않는다.
- launch_batch_size는 5~10 범위의 내부 처리단위다.
- production 공개는 Launch Gate를 통과한 상태에서 수행한다.
- growth 누적 상한은 없다.

### 현재 기본 공개 속도
- daily_count: 10 pages/site/24h
- batch_size: 5 pages/run
- daily runs: 2
- site rotation: round-robin
- batch 내부: page_type, search_intent, hub를 섞는다.
- 같은 page_type은 한 batch에서 원칙적으로 2개 이하. 미충족 핵심 허브 remediation은 예외.

live 사이트가 initial_page_target 미달 또는 launch_gate_status != passed이면 새 growth보다 launch remediation을 먼저 한다.

## 7. launch 기본 믹스
고정 개수가 아니라 다양성 가이드:
- funeral 장례식장·근조화환 약 20%
- places 실제 장소/시설/역/대학/병원/행사장 약 20%
- occasions 개업·이전·졸업·행사 약 20%
- order-help 문구·주문시간·배송·받는사람·가격 약 15%
- flower-knowledge 선택·관리 약 15%
- guide 핵심 비교/이용 가이드 약 10%

핵심은 비율 준수가 아니라 지역×서비스×의도 충돌 없이 사이트 구조를 완성하는 것이다.

## 8. 허브 정책
- approved/published 자식 0: 허브 생성/공개 금지
- 1~2: noindex,follow + sitemap 제외 + 메인메뉴 비노출
- 3~4: index 가능, 메인메뉴 비노출
- 5+: 메인메뉴 노출 가능
- 핵심 허브는 launch 완료 전 최소 3개 실제 자식을 확보한다.

## 9. 꽃배달 Business Truth / Asset
- Business Truth: flower-fwith-v1
- Product Catalog: brand_key=flower-fwith
- 전화주문 CTA 우선
- 온라인 주문 URL은 Business Truth 값만 사용
- 실제 배송상품은 지역·계절에 따라 구성/형태가 달라질 수 있음을 고지
- 추가배송비/반입 제한 가능성은 검증된 조건 안에서 안내
- 실제 상품 카드는 real asset만 사용
- AI 이미지는 hero/OG/editorial/infographic에 한정하며 실제 배송 실적처럼 표현하지 않는다.

## 10. Batch Quality Gate
각 공개 후보는 다음을 만족해야 한다.
- SEO>=90 / GEO>=85 / AEO>=90
- source requirement 충족
- Business Truth 위반 없음
- same-intent collision 없음
- duplicate slug 없음
- 최소 1 inbound internal link
- parent hub 존재
- sitemap 반영 가능
- canonical/robots/indexability 정상
- related_page_keys가 실제 approved/published 문서이며 다음 질문으로 자연스러움

하나의 문서가 FAIL이면 그 문서를 REVISE/REJECT하고 무리하게 PASS시키지 않는다. 기술적 오류가 batch 전체에 영향을 줄 경우 남은 batch를 중단한다.

## 11. 지역 차별화
각 Site Config는 지역 엔티티, 장소, 행사, 동선, 계절/공간 맥락을 별도로 가진다. 구체 지역 사실은 최신 공식/1차 자료를 우선한다. 새 지역 사이트는 기존 지역 본문을 지역명만 바꿔 복제하지 않는다.

## 12. Existing-city regional adapter opt-in (2026-10-03)

This additive adapter follows the fixed rules bundle at revision 8986a1936615cd0d814b816db7816488e40bacc1, with v1.2 precedence. It does not change those source documents, create a page quota, resume growth, reopen completed launches, or authorize publication.

- The registered pair is category `regions`, pageType `regional-service`, routeType `category`, pageRole `REGION_SERVICE_LANDING`, parentHub `/regions/`, localizationPolicy `local-required`, queryClass `local-commercial`. Five existing source roots opt in through their explicit `regionalService.scopeKey`, source `region-policy.json` and `region-coverage.json`; all added candidates are disabled until their existing scope review is bound. Goyang's strict v1 coverage and frozen canary stay on the existing path.
- Official geographic inventory does not assign new URLs. A reviewed query/intent has one representative canonical with explicit unitKeys. Administrative names, historical names, eup/myeon ri names and cross-district relations do not silently become pages. Unknown mappings remain unresolved and never become links. Ansan Seonbu reserves the existing launch14 lineage; an additional regional canonical for the same unit is rejected until an explicit migration decision.
- Only actual approved frozen manifest pages generate the regional hub and inbound links. Zero children means no hub route/link. One or two means noindex and sitemap exclusion; three or four may be indexable but stay outside the main menu; five or more may enter the menu. Preview noindex always wins. Geographic records without approved content never generate future links.
- Source formats remain separate: legacy Markdown-v1 collection enum/ArticleLayout and structured JSON-v12 pages/architecture. No generic-guide disguise or body rewrite is permitted. Regional business source names, URLs, type and verifiedAt are preserved instead of being relabeled as generic references.
- Existing Publisher headers remain sufficient. Optional scope or OG headers, when present, must agree with the reviewed source binding. Existing frozen-snapshot approval is reused; there is no new user approval, all-city hash, image generation requirement, or separate Publisher approval workflow. Source mapping and asset selection are reviewed through the existing source-revision path.
- Each regional representative has an explicit verified existing product/brand social-image binding (path, source URL, exact bytes, dimensions/type, alt, verification date). It uses real HTML phone/official-order CTA and a body purchase banner. It never activates global draft catalog products or interprets a generic bouquet hero as a specific fulfillment promise.
- Purchase mode must be explicit. `catalog` requires exact keys from the existing site catalog, family matching, and independent Writer/Reviewer confirmation that each promised family can actually be ordered. `consultation-only` requires empty product keys/families and may only describe service-availability consultation; it rejects named flower-family offers, prices, free-delivery or guaranteed-delivery promises. It is not a fallback that makes an unmapped bouquet/basket sales page pass. Missing catalog mapping blocks that ordinary sales intent until scoped verified products are available.
- Writer prepares real local-order query evidence, local customer decision facts and Draft. Reviewer checks content, duplicate/canonical decisions, catalog/CTA/asset fit and source evidence. Publisher alone uses the existing frozen Queue path after review. These code candidates do not create Drafts, Queue records, commits, branch updates or deployments.
