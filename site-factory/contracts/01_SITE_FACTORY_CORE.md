# Site Factory Core Contract v2

## 목적
모든 지역·업종 사이트가 공통으로 지켜야 하는 기술, SEO, 데이터, 미디어, 배포 규칙이다. 업종별 내용은 Vertical Blueprint, 지역별 값은 Site Config에서 분리한다.

## Source of Truth
1. Business Truth: 전화, 주문시간, 사업자정보, 배송/서비스 범위처럼 AI가 추측하면 안 되는 값.
2. Product Catalog: 실제 상품/서비스명, 가격, 실제 이미지, 주문 연결.
3. Media Assets: 실제 이미지와 AI 생성 이미지를 역할별로 구분.
4. Page Plan / Draft / Publish Queue: 콘텐츠 기획, 검수, 불변 Snapshot.
5. Git Snapshot: 실제 공개 빌드의 최종 입력.

## 공개 단계
- 1차 launch 페이지 수는 고정값이 아니다.
- 각 사이트의 Sites.initial_page_target을 사용하며 허용 범위는 1~49페이지다.
- 30페이지는 특정 사이트의 현재 목표값일 수는 있으나 Site Factory 규칙이 아니다.
- launch 목표는 지역 엔티티 밀도, 서비스 범위, 실제로 채울 수 있는 고유 질문 수에 따라 조절한다.
- 2차 growth 단계는 누적 페이지 수 제한이 없다.
- Sites.daily_count는 growth의 처리 속도만 제어하며 전체 상한으로 사용하지 않는다.

## 공통 SEO Contract
모든 indexable HTML 페이지는 고유 title, meta description, canonical, H1 1개, meta robots, OG, Twitter Card, 유효한 JSON-LD, 이미지 alt, sitemap 포함, 유효한 내부링크를 가져야 한다.
테스트/preview는 기본 noindex,nofollow,noarchive + robots Disallow:/ 이다.
Custom Domain 연결과 SITE_INDEXABLE=true는 별도의 운영 전환 단계로 취급한다.

## UTF-8 Contract
- 모든 소스 텍스트는 UTF-8로 저장한다.
- build 전에 strict UTF-8 decode를 수행한다.
- U+FFFD, C1 control, 반복적인 Latin-1 mojibake 패턴이 있으면 build를 실패시킨다.
- 한글 깨짐은 배포 후 발견하는 문제가 아니라 배포 전 차단하는 문제로 취급한다.

## URL Contract
- 핵심 commercial/hub 페이지는 의미 있는 top-level slug를 허용한다.
- 정보형 콘텐츠는 category path를 기본으로 한다.
- 모든 페이지를 지역명+키워드 치환형 URL로 만들지 않는다.

## Internal Link / Sitemap Contract
- 공개 HTML 페이지는 고아페이지가 될 수 없다. 홈을 제외한 모든 공개 페이지는 최소 1개의 다른 공개 페이지에서 내부 링크를 받아야 한다.
- 공개 메뉴와 허브는 빈 페이지를 가리키지 않는다. 상세 글이 아직 없어도 허브 자체에 사용자가 활용할 수 있는 판단 기준과 다음 이동 링크가 있어야 한다.
- 생성된 모든 공개 HTML 페이지는 sitemap에 포함되어야 한다.
- sitemap에 들어간 URL은 실제 200 HTML과 1:1 대응해야 한다.
- placeholder, coming soon, 준비중 문구를 공개 페이지에 두지 않는다.

## IndexNow Contract
- IndexNow는 production custom domain이 실제 연결되고 indexable 상태일 때만 사용한다.
- preview/workers.dev/noindex 사이트에서는 절대 호출하지 않는다.
- 각 도메인/서브도메인은 별도 IndexNow key를 사용한다.
- 최초 production 공개 시 sitemap의 전체 공개 URL을 제출한다.
- 이후에는 신규·수정·삭제 URL만 선택해 제출한다. 사이트 공통 템플릿/사업정보 변경처럼 모든 문서가 바뀐 경우에는 전체 sitemap URL을 다시 제출할 수 있다.
- IndexNow 제출은 색인을 보장하지 않으며 sitemap을 대체하지 않는다.

## Business/CTA Contract
전화, 가격, 영업/주문시간, 주소, 사업자정보는 생성형 모델이 추측하지 않고 Business Truth/Product Catalog 값만 렌더링한다.

## Media Contract
실제 판매상품/실제 작업사례 이미지는 real asset만 사용한다. AI 이미지는 hero, OG, editorial illustration, infographic 등에 사용할 수 있으나 실제 배송상품·실제 작업현장·실제 고객사례처럼 표현하지 않는다.

## QA
Build gate에서 UTF-8, Snapshot, canonical/meta/H1/OG/Twitter/JSON-LD/ALT/internal links/sitemap/robots, sitemap 완전성, orphan graph, empty placeholder를 검사한다.
Live QA에서 실제 Worker URL의 HTTP 200/404, exact Git revision, canonical, noindex/index 상태, 보안헤더를 다시 검사한다.
