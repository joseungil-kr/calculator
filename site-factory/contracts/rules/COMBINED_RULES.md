# Site Factory 통합 적용 규칙

적용 기준은 v1.2이며 이전판에서는 빠진 비충돌 규칙만 보완한다. v1.2의 전체 원문을 아래에 보존했고, 이전판 보완 항목은 맨 뒤에 별도 표시했다. 버전 명칭은 v1.2+omissions-2026-10-01이며 새 연구 결과인 v1.3으로 부르지 않는다. 세 원본과 정확한 hash는 source-manifest.json, 조항별 출처와 적용 판단은 PRECEDENCE_AND_COVERAGE.md를 함께 읽는다.

## 최신 기준 원문

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


## 이전판에서 추가로 보완하는 영역

A01 규칙 강도 구분 | v1 §§1,16,20 | MUST/SHOULD/OPTIONAL/NOT SUPPORTED를 구분한다. 최신판의 명시적 hard gate는 과거 warning보다 우선한다. FAQ·Schema·긴 글·이미지 개수 등은 자체가 SEO 발행 의무가 아니다.
A02 순위 공식 금지 | v1 §§1,20 | 3,000자, 키워드 반복 횟수, 임의 링크 개수, 전국 footer 링크, keyword URL, FAQ/Schema/이미지/sitemap 수, custom domain 우월성, 자동생성 자체 페널티를 순위 공식으로 삼지 않는다.
A03 Query class와 우선순위 | v1.1 Query Class | core-commercial/commercial-modifier/work-commercial/local-commercial/support-info 다섯 값과 commercial-first 선택을 유지한다. support-info로 초기 개수를 채우지 않는다.
A04 keyword 데이터와 정렬 검토 | v1.1 Primary Keyword Alignment/Keyword Cluster | secondary_keywords, keyword_cluster, query_class, query_priority, query_evidence, title_alignment_score를 기록한다. >=90은 내부 정렬 검토 기준이며 실제 Title/H1/첫 답변 증거와 재현 가능한 rubric을 함께 남긴다. 임의 자기점수는 PASS 증거가 아니다.
A05 페이지 분리·병합 | v1 §2 | 상품/목적/기대정보/CTA/핵심 섹션 차이를 판정한다. 동의어·동일 intent·동일 CTA는 한 URL을 우선한다.
A06 역할별 필수 결정정보 | v1 §4 | 지역서비스의 대응 범위, 장소의 접근/실무조건/주문정보, 의도 문서의 가능 여부/조건/시간/절차, 가격 문서의 요인/옵션/추가비용/검증된 예시 또는 범위, 정보 문서의 직접 답변을 유지한다. 확인되지 않은 가격을 채우라는 뜻이 아니다.
A07 URL·발견·중복 | v1 §§1,10–12,15–17 | 고유·안정 URL, 최소 한 곳의 내부 inbound, breadcrumb/계층, title/H1/slug/intent/content 중복 후보 검사를 유지한다. URL 키워드나 과도한 깊이를 강제하지 않는다.
A08 기술·색인 상태 분리 | v1 §§14,16 | HTTP200/robots/canonical/sitemap/inbound/404/orphan을 실제 검사한다. draft/published/indexable/submitted/crawled/indexed/impression_detected/ranking_detected/needs_revision를 구분한다. 접수·색인·노출·순위를 서로 대신 보고하지 않는다.
A09 학습 데이터 | v1 §§19,21 | URL/타깃/발행·색인·노출·클릭 날짜/현재·최고 순위/impressions/CTR를 실제 출처가 있을 때 기록한다. template/업종/지역/service/intent별 성공·실패를 비교하고 자사 실증을 개선에 사용한다.
A10 구조·확장 메타데이터 | v1 §17 | region/parent_region/service/intent/type/slug/hub/관련 대상/cta_type/status와 source_data/local_facts/price_info/delivery_conditions/last_verified를 유지한다. 비적용은 이유를 남기고 없는 값을 만들지 않는다.

## 이전판에서 채택하지 않는 항목 또는 범위 제한

X01 v1 생성순서의 hub/page_type 우선 구성은 v1.2 Query-first 순서로 대체한다.
X02 v1 본문 링크 우선순위에서 무조건 상위 허브/인접 지역을 앞세우는 방식은 v1.2의 구매동선으로 대체한다. 계층과 발견성은 breadcrumb/허브에 유지한다.
X03 v1의 지역정보 없음 warning을 local-required 페이지의 발행 허용 근거로 쓰지 않는다. v1.2 Local Evidence Gate가 우선한다.
X04 v1.1의 안산 스카이차 12페이지/11상세 시험 수량은 그 시험에만 해당한다. 꽃배달·신규 지역 quota로 복사하지 않는다.
X05 v1.1 시험 H2 중 “검색어를 한 페이지로 처리하는 이유”, “고정 가격을 임의로 만들지 않는 이유”는 제작자 예시이며 최신 provider voice에 맞게 실제 고객 정보로 바꾼다.
X06 v1의 index 가능 요구는 production에 적용한다. v1.1 Shadow/현재 승인된 격리 테스트는 noindex/Disallow가 정상이며 production 완료로 보고하지 않는다.
X07 v1.1의 Business Truth/실제 작업사진 없음 production 차단은 그 안산 시험의 결손이다. 모든 업종·페이지에 실제 작업사진을 강제하는 규칙으로 확대하지 않는다. 실제 증거를 주장할 때에는 최신 v1.2의 provenance가 필수다.
X08 v1의 30 indexed/20 impressions/10 rankings는 기존 실험의 규칙 재검토 관찰 기준이다. 새 사이트 초기 생성 수·공개 quota나 상위노출 약속이 아니다.

## 운영 구현에 추가하는 검증 장치

O01 모든 실행은 읽은 원본 세 개와 combined contract의 hash/revision을 남긴다. 버전명만 쓰거나 일부 검색 snippet을 읽고 전문을 소비했다고 기록하지 않는다.
O02 C/A 항목마다 적용 여부·실제 Draft 필드/문단·출처/HTML/검사 결과를 연결한다. 생략은 이유가 있는 NOT_APPLICABLE만 허용한다. REQUIRED 항목의 미확인은 PASS가 아니다.
O03 작성자는 pending Draft까지, 검토자는 독립 검토와 frozen 승인까지 담당한다. 검토자의 새 문장은 작성자 수정 경로로 되돌린다. 기존 배포 코드는 승인된 내용만 소비한다.
O04 factual review/내용 정렬 점수와 기계적 무결성 hash, 배포/실제 화면 검증은 서로 다른 증거다. 하나로 나머지를 대체하지 않는다.
O05 고양 1문서 canary의 scope/중복 방지/noindex/보호 지역/완료 guard는 별도 실행 제약이다. 일반 SEO 규칙을 변경하거나 모든 지역의 영구 운영 정책으로 만들지 않는다.
