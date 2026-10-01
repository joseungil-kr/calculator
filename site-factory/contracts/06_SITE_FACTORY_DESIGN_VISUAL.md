# Site Factory Design & Visual Portability Contract v1

## 1. 목적
한 지역에서 만든 시안을 다른 지역·서브도메인으로 복제해도 잘못된 지역명·전화번호·가격·CTA가 이미지에 남지 않도록
디자인 자산과 동적 사업정보를 분리한다.

## 2. 이미지 속 동적정보 금지 — HARD GATE
범용으로 재사용할 생성 이미지에는 다음을 넣지 않는다.
- 지역명: 안산/부산/수원/고잔동 등
- 지역 출동문구: 안산·시흥 출동, 서울 전지역 등
- 전화번호/카카오ID/URL
- 가격/할인율
- 실제 버튼처럼 보이는 UI
- 클릭을 유도하는 가짜 CTA 버튼
- 날짜·영업시간
- 지역별 배송/출장 조건
- 특정 페이지 Title 전체

이 값들은 HTML 텍스트·실제 링크·실제 버튼으로 렌더링한다.

## 3. 이미지에 허용되는 문구
지역/업체 복제에 안전한 공통문구만 허용한다.

예:
- "간판 · 외벽 작업"
- "공장 · 산업현장 작업"
- "현장 조건에 맞는 장비 상담"
- "사진으로 현장 조건 확인"
- "빠른 견적 상담"
- "안전한 고소작업 준비"

브랜드 로고/브랜드명은 같은 brand_key 내 여러 지역사이트에서 공통사용할 때만 별도 Brand Asset으로 허용한다.
다른 업체까지 재사용하는 Generic Asset에는 브랜드명도 넣지 않는다.

## 4. CTA는 HTML
전화/문자/카톡/주문/예약/견적은 반드시 실제 <a> 또는 <button>으로 구현한다.
이미지 속 버튼을 CTA로 간주하지 않는다.

Action:
- 전화하기
- 문자로 견적
- 주문하기
- 예약하기
- 사진 보내기

Navigation:
- 가격
- 작업유형
- 지역
- 관련 서비스

Action과 Navigation을 시각·기능적으로 구분한다.

## 5. Visual Intent
Page Plan은 visual_intent를 가진다.
primary_keyword → page_role → customer_decision → visual_intent → asset_slot 순서로 자산을 결정한다.

예:
- 간판 스카이차 → signboard_work
- 외벽 스카이차 → facade_work
- 성곡동/반월공단 → industrial_site
- 꽃배달 장례식장 → funeral_flower_delivery
- 누수탐지 아파트 → apartment_leak_diagnosis

카테고리가 같다는 이유만으로 한 이미지를 모든 페이지에 재사용하지 않는다.
visual_intent가 같을 때만 Asset Cluster를 공유한다.

## 6. Asset Slot / Aspect Ratio
이미지는 슬롯 목적에 맞는 비율로 생성·사용한다.

- HERO_WIDE: 16:9 또는 16:7
- SPLIT_VISUAL: 4:3 또는 3:2
- CONTENT_IMAGE: 4:3 또는 3:2
- CTA_BANNER: 16:5 또는 3:1
- CARD_THUMBNAIL: 4:3
- REAL_PROOF: 원본비율 존중, 과도한 crop 금지

다른 슬롯의 자산을 cover로 억지 사용해 핵심문구·피사체를 자르는 것을 금지한다.

## 7. HTML Image Rule
Production에서는 검색·접근성이 필요한 주요 이미지에 <img> 또는 <picture>를 우선한다.
CSS background는 순수 장식 목적에 한정한다.
alt는 이미지의 실제 의미를 설명하며 keyword stuffing 금지.

## 8. Generated vs Real Proof
생성 이미지는:
- Hero
- 분위기/설명 비주얼
- CTA 배너
- 개념 설명
에 사용한다.

실제 사진은:
- 실제 작업
- 실제 상품
- 실제 장비
- 실제 매장/시설
- 실제 배송/시공 결과
에 사용하며 고객이 혼동하지 않게 영역과 캡션을 구분한다.

생성 이미지를 실제 작업사례·실적처럼 표시하면 FAIL.

## 9. 지역복제 안전성 검사
새 지역사이트 생성 전 모든 visual asset을 검사한다.

FAIL 예:
- 부산 사이트 이미지에 "안산 스카이차"
- 수원 사이트 이미지에 "안산·시흥 출동"
- 다른 업체 사이트 이미지에 영진스카이 전화번호
- 지역별 가격이 다른데 이미지에 고정 가격
- 이미지 속 CTA와 실제 링크 동작이 불일치

검사 실패 시 이미지 재생성보다 먼저 지역/업체 동적값을 HTML overlay로 분리할 수 있는지 검토한다.

## 10. 디자인 목표
범용 디자인은 업종을 평준화하는 것이 아니라 공통 UX 품질을 강제한다.
Core가 강제:
- 반응형
- 빠른 로딩
- 실제 CTA
- 가독성
- 접근성
- 이미지 슬롯
- 카드/요약 역할
- 모바일 고정 CTA 여부
- 생성/실제 이미지 구분

Vertical Blueprint가 결정:
- 어떤 이미지가 필요한가
- 어떤 서비스/상품 카드가 중요한가
- 어떤 proof가 구매결정에 중요한가
- 어떤 CTA가 핵심인가
