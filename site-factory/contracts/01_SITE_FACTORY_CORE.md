# Site Factory Core Contract v3

## 목적
모든 지역·업종 사이트가 공통으로 지켜야 하는 정보구조, SEO, 데이터, 미디어, 발행, 배포 규칙이다. 업종별 내용은 Vertical Blueprint, 지역별 값은 Site Config에서 분리한다.

이 Contract는 검색엔진 알고리즘의 정답표가 아니다. 실증에서 반복 관찰된 패턴과 운영상 안전한 구조 원칙을 구분하며, 고정 숫자나 형식보다 검색의도-문서 대응, 기술적 indexability, 사이트 내부 발견 가능성을 우선한다.

## 1. 설계 우선순위

### MUST
- 검색지역 + 정확한 서비스 + 검색의도 조합에 대응하는 전용 랜딩을 만든다.
- 한 페이지는 하나의 핵심 검색의도에 집중한다.
- Title, H1, 본문 첫 구간에서 핵심 지역·서비스·의도를 일치시킨다.
- 검색어와 실제 제공 정보/CTA가 어긋나지 않게 한다.
- 동일 검색의도를 여러 URL이 중복 타깃하지 않게 한다.
- indexable 페이지는 canonical, robots, HTTP status 등 기본 기술 요건을 만족한다.
- 모든 공개 상세 페이지는 최소 1개 이상의 실제 내부 유입 링크를 가진다. orphan을 허용하지 않는다.

### SHOULD
- 지역 허브 → 서비스/의도 허브 → 장소/상황/의도 상세의 계층을 사용한다.
- breadcrumb로 상하위 계층을 표현한다.
- 본문 문맥에 맞는 관련 지역/서비스/장소 문서를 연결한다.
- sitemap과 내부링크를 함께 유지한다.
- 자동생성 문서도 목적과 CTA를 명확히 유지한다.
- 템플릿은 일관되게 운영하되 검색의도에 필요한 섹션은 page type마다 달리한다.

### OPTIONAL
FAQ, Schema, 다수 이미지, 긴 본문, 후기/사례, 가격표, 체크리스트, 표/리스트, 동영상, 작성일/수정일, OG metadata는 필요할 때 사용한다. 이 항목의 존재 자체를 순위 보장 요소로 취급하지 않는다.

### NOT SUPPORTED AS RANKING FORMULA
- 무조건 3,000자 이상
- 내부링크를 특정 개수 이상 삽입
- footer에 전국 지역 링크 수백 개 삽입
- 키워드 특정 횟수 반복
- URL에 반드시 키워드 삽입
- FAQ/Schema/이미지 수 자체로 상위노출 보장
- sitemap URL 수 자체를 순위 신호로 간주
- 자동생성 자체를 페널티 요소로 간주
- 커스텀 도메인 자체를 랭킹 우위로 간주
- 하루 1페이지 또는 하루 N페이지를 검색엔진 공식 규칙으로 간주

## 2. 키워드 → 페이지 매핑
Site Factory의 기본 식은 다음과 같다.

지역 × 서비스 × 의도

서비스 목적, 사용자의 행동 목적, 기대 정보, CTA, 가격/배송/주문/후기 등 핵심 섹션이 달라져야 하면 별도 페이지를 우선한다. 동의어 수준이며 검색의도와 CTA가 동일하면 한 페이지로 통합한다.

## 3. 공통 Page Role
업종별 실제 page_type은 다음 공통 역할 중 하나에 매핑한다.
- REGION_SERVICE_LANDING: 지역 + 핵심 서비스 랜딩
- PLACE_LANDING: 시설/장소 단위 랜딩
- INTENT_LANDING: 당일, 주문, 개업, 이전 등 행동/상황 의도 랜딩
- PRICE_GUIDE: 가격/비용 판단 문서
- INFORMATION_GUIDE: 예절, 관리, 선택법 등 정보 문서
- HUB: 지역·서비스·장소·상황 문서를 정리하는 구조 노드

HUB는 모든 키워드를 먹는 장문 페이지나 링크 창고가 아니다. 하위 문서를 발견하고 역할을 구분하는 중심 노드다.

## 4. 기본 정보구조
권장 논리 계층은 다음과 같다.

HOME / commercial landing
→ REGION HUB
→ SERVICE 또는 INTENT HUB
→ PLACE / SITUATION / INTENT DETAIL

실제 URL 모양은 업종/배포형태에 따라 달라질 수 있다. 중요한 것은 URL 문자열보다 실제 내부링크, breadcrumb, 허브-상세 역할 분리다.

## 5. Source of Truth
1. Business Truth: 전화, 주문시간, 사업자정보, 배송/서비스 범위처럼 AI가 추측하면 안 되는 값
2. Product Catalog: 실제 상품/서비스명, 가격, 실제 이미지, 주문 연결
3. Media Assets: 실제 이미지와 AI 생성 이미지를 역할별로 구분
4. Page Plan / Draft / Publish Queue: 기획, 검수, 불변 Snapshot
5. Git Snapshot: 실제 공개 빌드의 최종 입력

## 6. 공개 단계와 Batch / Rotation 정책
- 초기 공개 페이지 수 자체를 순위요인으로 취급하지 않는다.
- initial_page_target은 사이트 launch 완성도를 위한 운영 목표일 뿐 최종 페이지 상한이 아니다.
- growth는 누적 페이지 수 제한이 없다.
- 하루 1페이지 고정 규칙을 사용하지 않는다.
- daily_count는 검색엔진의 공식 한도가 아니라 사이트별 24시간 운영 cap이다.
- 공개 대상은 Quality Gate를 통과한 READY 문서만이다.
- Site Factory는 사이트 간 round-robin과 사이트 내부 page type/intent/hub rotation을 사용한다.
- 한 batch에서 동일 검색의도·동일 구조·동일 page type이 과도하게 몰리지 않게 한다.
- page generation과 production publication은 분리한다. Draft/approved backlog는 많이 보유할 수 있지만 공개는 gate를 통과한 batch만 수행한다.

### 꽃배달 v3 기본 운영값
Vertical Blueprint가 별도 값을 지정하지 않는 한 현재 검증값은:
- site daily cap: 10
- per-run batch cap: 5
- runs per day: 2

이 숫자는 SEO 공식이 아니라 현재 자동화/QA 처리량을 기준으로 한 운영 안전값이며 자체 데이터가 쌓이면 조정한다.

### Batch 중단 조건
다음 중 하나가 발생하면 해당 사이트의 남은 batch를 중단하고 Repair/Watchdog를 우선한다.
- orphan 증가
- 내부 404
- canonical/robots/sitemap 불일치
- intent collision/cannibalization
- 동일 구조 대량반복
- 필수 출처/Business Truth 부족
- 연속 배포 실패
- 품질 gate 미달

## 7. 공통 SEO Contract
모든 indexable HTML 페이지는 다음을 가져야 한다.
- 고유 title / meta description
- canonical
- H1 정확히 1개
- meta robots
- 유효한 OG/Twitter metadata
- 유효한 JSON-LD(사용하는 경우 실제 내용과 일치)
- 의미 있는 img alt
- sitemap 포함
- robots.txt 정책과 indexable 상태 일치
- 실제 존재하는 내부 링크만 사용

테스트/preview는 기본 noindex,nofollow,noarchive + robots Disallow:/ 이다. Custom Domain 연결과 production indexable 전환은 별도 운영 단계다.

## 8. Sitemap / Internal Graph / IndexNow
- 공개 HTML URL은 sitemap과 실제 생성 HTML이 일치해야 한다.
- 홈페이지를 제외한 모든 공개 페이지는 최소 1개 inbound internal link를 가진다.
- 신규·수정 URL은 Git Snapshot → build → sitemap/internal graph QA → production 확인 후 IndexNow 대상으로 보낸다.
- preview/noindex에서는 IndexNow를 호출하지 않는다.
- IndexNow는 발견 통지 수단이며 sitemap/internal link를 대체하지 않는다.

## 9. URL Contract
- 핵심 commercial/hub 페이지는 의미 있는 top-level slug를 허용한다.
- 정보형 콘텐츠는 category path를 기본으로 한다.
- 지역별 URL 패턴은 일관될 수 있지만 본문 질문·엔티티·의도는 독립적으로 계획한다.
- 사람이 이해 가능한 안정적 URL을 우선하되 키워드 삽입 자체를 필수로 보지 않는다.

## 10. Programmatic SEO
허용: 동일 디자인, 동일 데이터 필드, 동일 CTA 프레임, 업종/지역에 따른 자동 조합.
반드시 달라져야 함: Title, H1, 핵심 의도, 실제 지역/장소/서비스 정보, 관련 내부링크, 의도별 핵심 섹션.
금지: 지역명만 치환한 의미 없는 복제, 존재하지 않는 서비스/장소/가격 생성, 서로 다른 URL의 동일 intent 중복 타깃.

## 11. Business / Media Contract
- 전화, 가격, 영업/주문시간, 주소, 사업자정보는 Business Truth/Product Catalog만 사용한다.
- AI 이미지는 hero, OG, editorial illustration, infographic 등에 사용할 수 있다.
- AI 이미지를 실제 배송상품/실제 작업현장/실제 고객사례처럼 표현하지 않는다.
- 실제 상품/실제 작업사례는 승인된 real asset만 사용한다.

## 12. Quality Gate
공개 전 필수:
- HTTP 200 예상 경로/빌드 성공
- index 가능 상태
- canonical 정상
- Title/H1 존재 및 의도 일치
- 지역/서비스/의도 확인
- CTA 존재(해당 page role에 필요한 경우)
- 최소 1 inbound internal link
- 중복 slug 없음
- 동일 intent 충돌 없음
- sitemap 반영 가능
- 필수 Source/Business Truth 충족

경고(단독 차단조건 아님): 짧은 본문, 지역정보 부족, 이미지 alt 부족, meta description/FAQ/Schema 부재 등. 경고는 page role에 따라 판단한다.

## 13. 학습 루프
페이지별 URL, target keyword/intent, 발행일, 색인일, 첫 노출일, 첫 클릭일, 최고/현재 순위, impressions, CTR을 기록한다. 자체 데이터가 충분히 쌓이면 외부 경쟁사이트 추정보다 자사 실증 결과를 우선하여 Contract를 v3.x로 갱신한다.


## 14. Content Writing Contract
모든 사용자 노출 문구는 `site-factory/contracts/04_SITE_FACTORY_CONTENT_WRITING.md`를 필수 하위계약으로 따른다.

Core/Vertical Blueprint가 검색어·정보구조·사실 범위를 결정하고, Content Writing Contract가 실제 고객용 문장, Title–Summary 역할 분리, Provider Voice, 웹 리서치 fallback, 구매전환 내부링크, CTA 및 human-check 규칙을 결정한다.

검색어/구조/SEO Gate가 PASS해도 Content Writing Contract를 위반하면 production PASS 금지다.
