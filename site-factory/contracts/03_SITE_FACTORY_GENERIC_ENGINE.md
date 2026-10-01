# Generic Site Factory Engine v1

## 목적
공통 실행엔진과 업종별 Vertical Blueprint를 분리한다. 범용화는 꽃배달 규칙을 약화시키지 않고 공통 orchestration만 Core로 이동하는 방식으로 한다.

## Generic Core 책임
- Site/Blueprint 선택
- Page Plan → Draft → Review → Snapshot → Build → Deploy 순서
- architecture / publish-manifest / page-map 계약
- intentKey 중복 검사
- hub child threshold
- QA / Watchdog / IndexNow
- Growth cap과 retry

## Vertical Blueprint 책임
- category_schema
- page_type_catalog
- launch_mix_rule
- daily_rule
- fact_source_priority
- forbidden_patterns
- business_truth_requirements
- asset_contract
- template_key

Core는 업종 고유 허브명, 서비스 작업유형, 상품, 가격, CTA를 하드코딩하지 않는다.

## Shadow 원칙
새 업종은 production 전에 noindex shadow로 검증한다. Business Truth와 Asset Contract가 충족되지 않으면 production gate를 통과시키지 않는다.

## 첫 검증 Vertical
- blueprint: skycar-local
- template: skycar-local-v1
- test site: ansan-skycar-generic-shadow
- production: blocked
