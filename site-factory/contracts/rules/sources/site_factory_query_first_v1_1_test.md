# Site Factory 상위노출 설계 규칙 v1.1 — Query-first 보강안 + 안산 스카이차 테스트 설계

## 핵심 원칙

Site Factory의 제1목적은 페이지 수가 아니라 검색어-문서 적합도다.

기존 v1의 방향을 자동화가 더 강하게 지키도록 순서를 다음처럼 고정한다.

Query Universe → Keyword Cluster → Primary Keyword → Query Class/Priority → Intent → Title/H1 → Page Role/Page Type → Hub

허브를 먼저 만들고 문서 수를 채우는 방식은 금지한다.

## Query Class

1. core-commercial
   - 지역 + 대표 서비스
   - 예: 안산 스카이차

2. commercial-modifier
   - 가격·비용·견적·대여·업체 등 문의 직전 검색
   - 예: 안산 스카이차 가격, 안산 스카이차 견적

3. work-commercial
   - 작업 목적 + 서비스
   - 예: 안산 간판 스카이차, 안산 외벽 스카이차

4. local-commercial
   - 세부 지역/생활권 + 서비스
   - 예: 고잔동 스카이차, 안산 반월공단 스카이차

5. support-info
   - 장비·안전·체크리스트 등 보조 정보
   - 초기 핵심 페이지 숫자를 채우기 위해 만들지 않는다.

## Primary Keyword Alignment — HARD GATE

모든 indexable primary 문서는 다음 필드를 가진다.

- primary_keyword
- secondary_keywords
- keyword_cluster
- query_class
- query_priority
- query_evidence
- title_alignment_score

Production PASS 기준:

- Title 전반부에 primary_keyword 원형을 가능한 한 유지
- 지역+서비스 사이에 불필요한 수식어 삽입 금지
- H1에 핵심 지역+서비스 조합 유지
- 첫 120~180자에서 검색의도에 직접 답변
- title_alignment_score 90 미만이면 REVISE

예:

primary_keyword = 안산 스카이차

권장:
안산 스카이차 | 간판·외벽 고소작업 문의

비권장:
안산 지역 스카이차 작업 전 현장정보 확인 가이드

## Keyword Cluster

안산 스카이차 가격 + 안산 스카이차 비용
→ PRICE cluster 한 URL 우선

안산 스카이차 견적 + 안산 스카이차 견적문의
→ QUOTE cluster 한 URL 우선

안산 스카이차 업체
→ HOME의 업체탐색 의도와 같다면 별도 URL을 만들지 않음

## 안산 스카이차 Query-first Shadow 테스트 트리

HOME
- primary_keyword: 안산 스카이차
- title: 안산 스카이차 | 간판·외벽·고소작업 문의

가격/견적
- 안산 스카이차 가격 | 비용과 견적 확인사항
- 안산 스카이차 견적 | 현장정보와 문의 준비

작업유형
- 안산 간판 스카이차 | 설치·철거 고소작업 문의
- 안산 외벽 스카이차 | 외벽 고소작업 문의
- 안산 실외기 스카이차 | 설치·교체 작업 문의
- 안산 CCTV 스카이차 | 고소 설치작업 문의

세부지역
- 고잔동 스카이차 | 간판·외벽 고소작업
- 선부동 스카이차 | 건물 고소작업 문의
- 원곡동 스카이차 | 상가·공장 고소작업
- 성곡동 스카이차 | 공장 고소작업 문의
- 안산 반월공단 스카이차 | 공장·산업단지 고소작업

총 12 Query Page = HOME 1 + 상세 11.

## 설계 테스트용 샘플 문서

Primary Keyword:
안산 스카이차 가격

Title:
안산 스카이차 가격 | 비용과 견적 확인사항

H1:
안산 스카이차 가격과 비용 확인사항

Query Class:
commercial-modifier

Keyword Cluster:
ansan-skycar-price

Secondary Keyword:
안산 스카이차 비용

Page Role:
PRICE_GUIDE

첫 답변:
안산 스카이차 가격은 작업시간만으로 정하기보다 작업 높이, 현장 접근성, 작업 목적, 대기시간과 장비 조건을 확인한 뒤 견적을 받아야 합니다.

H2 구조:
1. 안산 스카이차 가격을 결정하는 입력정보
2. 가격과 비용 검색어를 한 페이지로 처리하는 이유
3. 견적에 필요한 주소·높이·현장사진
4. 고정 가격을 임의로 만들지 않는 이유
5. 안산 스카이차 견적 페이지로 연결

금지:
- 근거 없는 최저가
- 고정 가격
- 무조건 가능
- 확인되지 않은 장비 높이/톤수
- 허위 출동시간

## Shadow PASS 조건

- Query Page 12개
- primary_keyword ↔ Title alignment 12/12 PASS
- primary_keyword ↔ H1 alignment 12/12 PASS
- 첫 답변에 primary query 12/12 PASS
- duplicate keyword cluster 0
- support-info quota filler 0
- HOME = 안산 스카이차
- robots = noindex / Disallow
- Business Truth/실제 작업사진 없음 → Production Gate 차단 유지

## 최종 원칙

검색어가 페이지를 만들고, 페이지가 허브를 만든다.
허브가 페이지를 만들면 안 된다.
