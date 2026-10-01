# Site Factory Content Writing Contract v1.1

## 1. 목적
이 계약은 Site Factory가 생성하는 모든 고객 노출 문구의 작성 기준이다.

- 화자: 해당 서비스 제공업체
- 독자: 검색으로 유입된 잠재고객
- 목표: 검색질문 해결 → 필요성/공감 → 서비스 이해 → 신뢰 → 가격·견적·주문 → 실제 문의·구매 전환

SEO 설계와 내부 데이터 구조는 고객에게 설명하지 않는다.

## 2. 고객용 문장 원칙
고객 노출 본문에 다음 내부 제작 관점을 사용하지 않는다.
- 검색어/검색의도/SEO/상위노출
- 페이지 역할/페이지를 분리한 이유/중복문서/카니발리제이션
- cluster/query/Business Truth/Production/Shadow/QA
- 허브로 돌아가기, 페이지에서 임의로 표현하지 않는다 같은 제작 설명

고객에게는 다음만 말한다.
- 어떤 문제를 해결하는 서비스인지
- 어떤 현장/상황에서 필요한지
- 어떤 장점과 이점이 있는지
- 지역·현장 조건은 무엇인지
- 가격/비용은 무엇으로 달라지는지
- 무엇을 준비하면 되는지
- 어떻게 문의/주문하는지

## 3. 문서 기본 구매여정
Page Role에 맞게 다음 순서를 기본으로 한다.

1. 즉답 + 필요성 환기/공감
2. 서비스 설명과 적합한 현장/상황
3. 서비스 장점·고객 이점·검증된 증거
4. 실제 지역/현장 정보와 이용조건
5. 가격/비용 결정요소 또는 확인된 실제 가격
6. 신청·주문·견적 방법
7. 실제 전환 CTA

FAQ와 관련글은 보조이며 이 흐름을 대체하지 않는다.

## 4. Title / Summary / First Answer 역할 분리
### Title
primary_keyword + 핵심 구매의도를 직접 표현한다.

### H1
Title과 같은 타깃을 자연스럽게 확장한다.

### Meta Description
검색결과에서 클릭할 이유를 설명한다. 혜택·조건·핵심정보를 1~2문장으로 제시하고 Title 전체를 복사하지 않는다.

### Card Summary
목록/허브에서 다음 클릭을 유도한다.
- primary_keyword로 시작하지 않는다.
- 제목을 다른 어순으로 반복하지 않는다.
- 페이지에서 얻는 가치, 해결되는 문제, 중요한 차이를 1~2문장으로 설명한다.

### First Answer
상세페이지 진입 후 검색질문에 직접 답한다.
Card Summary와 동일 문장을 재사용하지 않는다.

### Title–Summary Differentiation Gate
- card_summary가 primary_keyword로 시작하면 FAIL
- card_summary와 Title의 공통 선두문구가 8자 초과면 REVISE
- card_summary와 first_answer가 70% 이상 유사하면 REVISE
- 같은 허브의 card_summary가 지역명만 치환한 동일 문장틀이면 REVISE

## 5. Business Truth와 웹 리서치
1. 저장된 Business Truth가 있으면 최우선 사용한다.
2. 부족하면 웹 검색으로 공식 홈페이지, 공식 지도/플레이스 사업자 정보, 공공기관, 제조사/협회, 실제 사업자 SNS 등 공개 출처를 조사한다.
3. 확인된 값은 source_url/source_name/verified_at과 함께 candidate truth로 기록한다.
4. 업체명/도메인/전화 등 운영주체 식별자가 없으면 경쟁업체 사실을 우리 업체 사실로 가져오지 않는다.
5. 보유장비, 경력, 가격, 보험, 자격, 출동시간, 고객수, 실제 작업실적, 고객후기처럼 업체 고유 사실은 공개 출처로 확인되지 않으면 human_check_required로 남긴다.
6. 업체 고유정보가 없어도 Draft/Shadow 작성은 계속할 수 있다. 이때 확인 가능한 지역·업종 사실과 일반적인 고객 이점을 중심으로 provisional commercial copy를 작성한다.
7. 확인되지 않은 사실을 Production/indexable 문서에 실제 사실처럼 쓰지 않는다.
8. 실제 고객후기는 출처가 확인될 때만 사용한다. 근거가 없으면 가짜 후기를 만들지 않고 검증된 장점·작업방식·선택기준으로 대체한다.
9. 사람의 후속 지시로 candidate/provisional 값을 Business Truth로 승격·수정한다.

## 6. 내부링크 = 구매동선
사이트 URL/허브 트리는 구조대로 유지하되, 본문 내부링크는 고객의 다음 결정으로 이어지게 한다.

기본 동선:
필요성·공감
→ 내 상황에 맞는 서비스/작업유형
→ 검증된 장점·실제 증거
→ 가격/비용/견적
→ 신청·주문·전화·사진견적

좋은 링크:
- 지역 작업 페이지 → 해당 작업유형 → 가격/견적
- 정보 가이드 → 관련 서비스 랜딩 → 주문/상담
- 가격 페이지 → 실제 견적/주문 CTA

금지:
- 허브로 돌아갈 수 있습니다
- 다른 페이지도 확인하세요
- 검색의도별로 분리했습니다
- 관련 페이지 수를 채우기 위한 무관한 링크

## 7. Conversion CTA
정보페이지 이동만으로 전환 CTA를 충족한 것으로 보지 않는다.

Business Truth에 실제 연락/주문 수단이 있으면:
- 전화
- 주문 링크
- 상담 링크
- 사진견적
- 예약/신청
중 실제 가능한 CTA를 사용한다.

연락수단이 없는 Shadow/Draft는 CTA를 provisional 상태로 두고 production gate를 닫는다.

## 8. Human Check
다음은 human_check_required:
- 웹에서 확인할 수 없는 업체 고유 장점
- 가격/최저가/할인
- 장비 보유·높이·톤수
- 경력/고객수
- 보험/자격/허가
- 당일/즉시 출동 보장
- 실제 작업사례
- 고객후기

Shadow에서 가정형 초안 메모는 허용하지만 사용자에게 사실처럼 노출하거나 Production으로 발행하지 않는다.


## 9. Truth Source Level / Industry Default
새 업종·새 업체·부족정보의 조사와 source_level은 `05_SITE_FACTORY_BLUEPRINT_BOOTSTRAP.md`를 따른다. Business Truth가 부족하다고 thin page를 만들거나 작업을 중단하지 않는다. official business source와 industry_default를 조사해 완성도 있는 Draft를 만들되, industry_default를 업체 확정정책으로 표현하지 않는다.
