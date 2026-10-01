# Site Factory Generic Engine Contract v2 — Query-first

## 목적
Generic Engine의 제1목적은 지역 서비스 사이트의 검색어-문서 적합도를 높이는 것이다. 허브 숫자, 페이지 수, 정보량은 목적이 아니라 결과다.

## 실행 순서 — MUST
1. Query Universe 생성
2. keyword cluster 병합
3. primary_keyword 선정
4. query_class / query_priority 부여
5. 검색의도 분리·병합
6. Title / H1 / 첫 답변 정렬
7. page_role / page_type 결정
8. hub 배치
9. architecture / manifest / page-map 생성
10. Build / QA / Deploy

허브를 먼저 만들고 빈 칸을 채우기 위해 문서를 생성하지 않는다.

## Query Class
- core-commercial: 지역 + 대표 서비스
- commercial-modifier: 가격·비용·견적·대여·업체 등 문의 직전
- work-commercial: 작업유형 + 서비스
- local-commercial: 세부지역·생활권 + 서비스
- support-info: 장비·안전·체크리스트 등 정보 보조

초기 공개와 daily 확장은 위 순서를 기본 우선순위로 한다.

## Primary Keyword Alignment — HARD GATE
모든 indexable primary 문서는 primary_keyword를 1개 가진다.
- Title 전반부는 primary_keyword 원형을 가능한 한 유지한다.
- 핵심 지역+서비스 사이에 불필요한 수식어를 넣지 않는다.
- H1에도 동일 핵심 조합을 유지한다.
- 첫 120~180자에 검색의도를 직접 답한다.
- title_alignment_score < 90 이면 production PASS 금지.

예:
- primary: 안산 스카이차
- 권장: 안산 스카이차 | 간판·외벽 고소작업 문의
- 비권장: 안산 지역 스카이차 작업 전 현장정보 확인 가이드

## Cluster / Cannibalization
동의어·동일 CTA·동일 정보 요구는 하나의 cluster로 병합한다.
예: 안산 스카이차 가격 / 안산 스카이차 비용 → 한 PRICE_GUIDE 우선.
페이지를 분리하는 기준은 검색자의 행동 목적, CTA, 핵심 섹션이 실제로 달라야 한다.

## Hub 원칙
Hub는 Query Page를 조직하는 계층이다.
Hub별 최소 문서수를 채우기 위해 support-info를 생성하지 않는다.
0개이면 route를 만들지 않고, 적은 문서수는 Blueprint의 index/menu 정책을 따른다.

## 검색수요 근거
실측 검색량이 없으면 검색량이 높다고 단정하지 않는다.
query_evidence에 근거를 기록한다:
- 사용자 제공
- 광고 키워드 데이터
- 검색제안/연관검색
- SERP 관찰
- 기존 실험
- 검색형태 추론

## Vertical Blueprint 역할
Core는 업종 키워드를 하드코딩하지 않는다.
Blueprint가 query pattern, page_type, forbidden facts, source priority, Business Truth, asset contract를 제공한다.

## Regression
꽃배달 production 규칙은 Generic 전환 전후 결과가 동일해야 한다. Generic Shadow는 flower-local/flower-local-v2 production 레코드와 branch를 수정하지 않는다.
