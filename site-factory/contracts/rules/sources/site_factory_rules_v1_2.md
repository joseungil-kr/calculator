# Site Factory 상위노출 설계 규칙 v1.2

## 1. 제1목적
Site Factory의 제1목적은 페이지 수가 아니라 `검색어-문서 적합도 + 업종 고유성 + 업체 고유성 + 구매전환`이다.

범용 Core는 모든 업종을 같은 문장으로 만드는 템플릿이 아니다. Core는 품질·순서·검증을 강제하고, 실제 내용은 Vertical Blueprint와 Business Truth가 결정한다.

## 2. 역할 경계 — MUST

### Core
모든 업종에 공통 적용:
- Query-first
- 한 primary URL = 한 intentKey
- Title/H1/첫 답변 정렬
- 고객 화자/구매여정
- 지역 고유성
- 업체 고유성
- 출처등급
- 이미지/CTA/반응형/접근성
- 중복·카니발리제이션·품질 Gate

### Vertical Blueprint
업종마다 결정:
- 고객이 돈을 지불하는 서비스
- Query pattern
- page type / page role
- 구매결정 정보
- 가격·견적 구조
- 금지·주의 주장
- 필요한 지역근거
- 이미지 visual_intent
- 업종별 업계 기본값

### Business Truth
업체마다 결정:
- 상호/브랜드
- 전화/주문/상담수단
- 실제 서비스지역
- 실제 상품/장비/서비스
- 가격/배송비/출장비
- 상담시간
- 당일/긴급 조건
- 보험/자격/허가
- 실제 사진/후기/실적
- 차별점과 제외조건

## 3. 사이트 시작 전 Bootstrap

### 새 업종
active Blueprint가 없으면 Page Plan을 만들지 않는다.
먼저 사용자에게 업종 핵심 질문을 하고 웹 조사로 Blueprint를 완성한다.

최소 질문:
1. 업종과 대표서비스
2. 핵심 유료서비스 3~10개
3. 지역형/전국형/복수지역형
4. 최종 CTA
5. 가격방식
6. 고객에게 필요한 입력정보
7. 구매결정요소
8. 금지/법적/안전 제한
9. 실제 사진/상품/장비 자료
10. 업계 관행/가격/경쟁업체

### Blueprint가 있는 새 업체
brand_key가 새로우면 업체지문을 묻는다.
최소한 브랜드와 실제 전환수단은 Production에 필수다.

업체지문:
상호, 전화/문자/카톡/주문URL, 사업자정보, 영업시간, 서비스지역, 실제 상품/장비/서비스, 가격, 추가비용, 당일/긴급조건, 차별점, 보험/자격/허가, 실제 사진, 실제 후기, 제외조건.

## 4. 부족정보 처리 — 작업중단 대신 Research Fallback
Business Truth가 부족하다고 thin page나 일반론 페이지를 만들지 않는다.

순서:
`operator confirmed → official business source → industry default → unknown`

### industry_default
웹 조사로 업계에서 반복되는 일반값을 보강한다.
- 최신 자료 우선
- 독립 근거 3개 이상 우선
- 공식/협회/대형플랫폼/복수 사업자 공개값 우선
- 한 업체 정책을 업계표준으로 일반화 금지
- 가격은 단일 고정값보다 범위/대표값/결정요소
- 무료/당일/보장 문구는 조건·예외까지 조사

industry_default는 완성도 있는 시안/Draft를 만드는 데 사용하되 업체 확정정책으로 둔갑시키지 않는다.
사용자 승인 시 operator_confirmed로 승격한다.

## 5. Query-first 실행 순서
`Blueprint/Business Fingerprint 확인 → Research Fallback → Query Universe → Cluster → Primary Keyword → Intent → Page Role/Type → Customer Decision Requirements → Title/H1/First Answer → Content Plan → Visual Intent → Conversion Path → Draft → QA → Publish`

허브를 먼저 만들고 페이지 수를 채우는 방식은 금지한다.

## 6. Primary Keyword Alignment
- indexable primary 문서는 primary_keyword 1개
- Title 전반부에 핵심 검색조합을 직접 표현
- H1은 같은 지역/서비스/의도
- 첫 120~180자는 직접답변
- 다른 intent로 새면 REVISE
- exact match 반복을 순위공식으로 취급하지 않음

## 7. Content / Customer Journey
화자=서비스 제공업체, 독자=잠재고객.

기본 구매여정:
`즉답·공감 → 서비스 설명 → 장점/고객이점/증거 → 지역·현장 정보 → 가격/비용 → 신청·견적·주문 방법 → 실제 CTA`

고객화면에 SEO/검색의도/페이지역할/cluster/QA/Business Truth/허브 설계이유를 설명하지 않는다.

## 8. Title / Summary 역할 분리
- Title: 검색어+핵심 구매의도
- H1: 같은 타깃의 자연스러운 확장
- Meta: 클릭할 이유/혜택/조건
- Card Summary: 제목 반복이 아니라 얻을 가치
- First Answer: 상세페이지 즉답

Gate:
- card_summary가 primary_keyword로 시작하면 FAIL
- Title과 공통 선두문구 8자 초과 시 REVISE
- card_summary↔first_answer 70% 이상 유사 시 REVISE
- 형제 카드요약이 지역명만 치환된 동일틀이면 REVISE

## 9. Vertical Specificity Gate
범용문장으로 도망가지 않는다.

검사:
- 업종명을 다른 업종으로 바꾸어도 대부분 성립하는가? → FAIL
- 지역명을 다른 지역으로 바꾸어도 지역문서의 대부분이 그대로 성립하는가? → REVISE/FAIL
- 서비스명을 바꾸어도 CTA/핵심정보가 같나? → intent 재검토

업종 고유 구매결정정보는 Blueprint에서, 업체 고유 소구점은 Business Truth에서 반드시 들어와야 한다.

## 10. Local Evidence Gate
지역 페이지는 실제 서비스 수행과 연결되는 고유정보를 가져야 한다.
관광·역사·인구 같은 장식정보는 제외한다.

예:
- 접근/주차/진입
- 산업단지/상권/시설
- 반입/배송/작업 조건
- 공공 데이터
- 실제 장소/사업장 정보

출처 URL/이름/확인일을 기록한다.

## 11. 내부링크 = 구매동선
사이트 트리는 유지하지만 본문 링크는 고객의 다음 결정으로 연결한다.

`필요성 → 서비스/상품 → 증거/장점 → 가격/견적/배송 → 실제 CTA`

링크 개수 자체를 SEO 공식으로 사용하지 않는다.
Breadcrumb는 계층, 본문링크는 구매결정 역할을 담당한다.

## 12. 이미지/디자인 범용성 — HARD GATE
지역별 복제에 사용하는 생성이미지에는 동적값을 굽지 않는다.

금지:
- 지역명
- 지역 출동문구
- 전화번호/URL
- 가격/할인
- 날짜/영업시간
- 실제 버튼처럼 보이는 UI/CTA
- 특정 지역 Title 전체

허용:
- 업종 공통 설명문구
- 작업/상품 범주
- 일반적인 장점/상황 표현

동적값은 HTML 텍스트와 실제 <a>/<button>으로 렌더링한다.
브랜드 자산은 같은 brand_key 안에서만 공유하고 Generic Asset은 브랜드명도 제외한다.

## 13. Visual Intent / Asset Slot
`primary_keyword → page_role → customer_decision → visual_intent → asset_slot`

슬롯:
- HERO_WIDE 16:9/16:7
- SPLIT_VISUAL 4:3/3:2
- CONTENT_IMAGE 4:3/3:2
- CTA_BANNER 16:5/3:1
- CARD_THUMBNAIL 4:3
- REAL_PROOF 원본비율 존중

다른 슬롯용 이미지를 cover로 억지 재사용하여 텍스트/피사체를 자르지 않는다.
주요 검색·접근성 이미지는 <img>/<picture> 우선, CSS background는 장식용으로 제한한다.

## 14. 생성이미지와 실제증거 분리
생성이미지: Hero, 설명, 분위기, CTA 배너.
실제사진: 작업, 상품, 장비, 배송, 시공결과, 매장/시설.
생성이미지를 실제 작업실적처럼 표시하면 FAIL.

## 15. CTA
전화/문자/카톡/주문/예약/사진견적 등은 실제 동작하는 HTML CTA여야 한다.
이미지 속 버튼은 CTA로 인정하지 않는다.
Navigation 링크와 Action CTA를 구분한다.

## 16. 중단 기준
세부정보 부족만으로는 중단하지 않는다. 업계 기본값을 조사해 완성도 있는 Draft를 만든다.

다음만 BLOCK/질의:
- 새 업종인데 Blueprint 없음
- 새 업체인데 브랜드 또는 최소1개의 전환수단 없음
- 법적/안전 중요사실을 추정해야만 함
- 신뢰할 수 있는 업계 기본값조차 없음

## 17. Production Gate
Production PASS는 다음을 모두 만족해야 한다.
- Query/Title/H1/intent 정렬
- Vertical Specificity
- Local Evidence
- Provider Voice
- 업체/시장 출처등급 명확
- 구매전환 동선
- 실제 CTA
- 이미지 지역복제 안전성
- 생성/실제 이미지 구분
- 중복 intent/cluster 없음
- architecture/manifest/page-map/HTML/sitemap 일치

## 최종 원칙
범용 규칙은 강력하게 적용하되 범용 콘텐츠를 만들지 않는다.
Core는 품질과 검증을 강제하고, Vertical Blueprint가 업종의 언어를 만들며, Business Truth가 업체의 지문을 만든다.
