# Site Factory Core Contract v2

## 목적
모든 지역·업종 사이트가 공통으로 지켜야 하는 기술, SEO, 데이터, 미디어, 배포 규칙이다. 업종별 내용은 Vertical Blueprint, 지역별 값은 Site Config에서 분리한다.

## Source of Truth
1. Business Truth: 전화, 주문시간, 사업자정보, 배송/서비스 범위처럼 AI가 추측하면 안 되는 값.
2. Product Catalog: 실제 상품/서비스명, 가격, 실제 이미지, 주문 연결.
3. Media Assets: 실제 이미지와 AI 생성 이미지를 역할별로 구분.
4. Page Plan / Draft / Publish Queue: 콘텐츠 기획, 검수, 불변 Snapshot.
5. Git Snapshot: 실제 공개 빌드의 최종 입력.

## 공개 단계 정책
- 1차 launch 페이지 수는 고정 30이 아니다.
- 각 사이트의 `initial_page_target`을 사용하며 허용 범위는 1~49페이지다.
- 지역·업종·엔티티 밀도에 따라 launch 목표를 조절한다.
- 업종 Blueprint의 launch mix는 비율 가이드이며 절대 개수가 아니다.
- 2차 growth는 누적 페이지 수 제한이 없다.
- `daily_count`는 growth의 일일 처리 속도만 제어하며 누적 상한으로 사용하지 않는다.
- 공개 메뉴/허브는 빈 화면이나 “준비중” placeholder로 남기지 않는다. 상세 문서가 없으면 즉시 활용 가능한 기준·내부링크를 제공하고, Orchestrator는 비어 있는 허브를 우선 채운다.

## 공통 SEO Contract
모든 indexable HTML 페이지는 다음을 가져야 한다.
- 고유 title
- 고유 meta description
- canonical
- H1 정확히 1개
- meta robots
- og:type, og:site_name, og:title, og:description, og:url
- og:image, og:image:alt
- twitter:card=summary_large_image
- twitter:title, twitter:description, twitter:image, twitter:image:alt
- 유효한 JSON-LD
- 모든 의미 있는 img의 alt
- sitemap 포함
- robots.txt 정책과 indexable 상태 일치
- 내부 링크는 실제 존재하는 URL만 사용

테스트/preview는 기본 noindex,nofollow,noarchive + robots Disallow:/ 이다.
Custom Domain 연결과 SITE_INDEXABLE=true는 별도의 운영 전환 단계로 취급한다.

## Sitemap / Internal Graph / IndexNow Contract
- 공개 HTML URL은 모두 sitemap에 포함한다.
- sitemap URL과 실제 생성 HTML은 1:1로 일치해야 한다.
- 홈페이지를 제외한 모든 공개 페이지는 최소 1개 이상의 내부 유입 링크를 가져야 하며 고아페이지를 허용하지 않는다.
- 메뉴에 노출된 허브/페이지는 실제 유용한 본문 또는 관련 문서 연결을 가져야 하며 빈 메뉴를 허용하지 않는다.
- 신규·수정 공개 URL은 Git Snapshot → Astro build → sitemap/내부링크 QA → production 배포 확인 순서를 통과한 뒤에만 IndexNow 대상으로 보낸다.
- 최초 production 전환 시 sitemap의 공개 URL을 기준으로 전체 제출할 수 있고, 이후에는 신규·수정 URL과 필요한 관련 허브만 증분 제출한다.
- preview/noindex 환경에서는 IndexNow를 호출하지 않는다.
- IndexNow는 발견 통지 수단이며 sitemap과 내부링크를 대체하지 않는다.

## UTF-8 Contract
- 소스 텍스트는 UTF-8로 저장한다.
- Build gate에서 invalid UTF-8, U+FFFD, C1 control, 흔한 mojibake 패턴을 검사한다.
- 한글 깨짐 징후가 있으면 Astro build 전에 실패시킨다.

## URL Contract
- 핵심 commercial/hub 페이지는 의미 있는 top-level slug 허용.
- 정보형 콘텐츠는 category path를 기본으로 한다.
- 모든 페이지를 지역명+키워드 치환형 URL로 만들지 않는다.
- 지역별 URL 패턴은 동일할 수 있으나 본문 질문·엔티티·구조는 독립적으로 계획한다.

## Business/CTA Contract
- 전화, 가격, 영업/주문시간, 주소, 사업자정보는 생성형 모델이 추측하지 않는다.
- 반드시 Business Truth/Product Catalog 값만 렌더링한다.
- CTA 우선순위는 Business Truth에서 결정한다.
- 전화 링크는 tel: 형식을 제공한다.
- 외부 주문 URL은 브랜드 Truth 값만 사용한다.

## Media Contract
- 실제 판매상품/실제 작업사례 이미지는 real asset만 사용한다.
- AI 이미지는 hero, OG, editorial illustration, infographic 등에 사용 가능하다.
- AI 이미지를 실제 배송상품, 실제 시공/작업현장, 실제 고객사례처럼 표현하지 않는다.
- 운영 이미지는 최종적으로 Git/public 또는 승인된 영구 CDN에 Snapshot한다.
- 외부 원본 URL은 provenance로 보존할 수 있으나 런타임 hotlink를 기본값으로 삼지 않는다.

## QA
Build gate에서 UTF-8, snapshot provenance, canonical/meta/H1/OG/Twitter/JSON-LD/ALT/internal links/sitemap/robots, sitemap-HTML 완전성, orphan, empty placeholder를 검사한다.
Live QA에서 Worker 실제 URL의 HTTP 200/404, exact Git revision marker, canonical, noindex/index 상태, 보안헤더를 다시 검사한다.
