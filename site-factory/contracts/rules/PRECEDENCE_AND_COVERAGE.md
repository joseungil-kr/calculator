# Site Factory 규칙 버전 차이와 적용 범위

이 묶음의 기준은 v1.2다. v1과 v1.1에서는 v1.2에 빠진 부분만 보완한다. 서로 충돌하는 예시·순서·판정은 v1.2가 우선하며, 최신판 전체를 이전판으로 다시 덮지 않는다. 이 결합은 새 SEO 실증 결과나 v1.3 발표가 아니다.

## 원본 확인

세 원본을 처음부터 끝까지 읽었다. 원본 본문은 sources/ 아래 보존한다. source-manifest.json의 SHA-256은 UTF-8, CRLF/CR을 LF로 바꾸고 마지막 LF를 하나로 정규화한 본문을 고정한다. 업로드 파일의 외부 저장소 메타데이터·비공개 대화·개인 식별자는 저장소 묶음에 넣지 않는다.

- v1: 지역/서비스/의도별 페이지, 우선순위, 역할, 기술 상태, 색인·순위 학습의 기본 규칙
- v1.1: Query-first 강화, query class, keyword metadata, alignment 검토, 안산 스카이차 한정 시험안
- v1.2: Core/Blueprint/Truth 역할, 부족정보 조사, 구매여정, 요약 구분, 업종·지역 고유성, 이미지/CTA, 최신 Production Gate

## 최신판을 그대로 유지하는 영역

C01 목적과 역할 분리 | v1.2 §§1–2 | 작성: 업종/브랜드/고객결정 입력 | 검토: 범용 Core와 실제 업종·업체 내용의 분리 | 차단: 업종명만 치환해도 본문이 대부분 성립
C02 Bootstrap와 부족정보 조사 | v1.2 §§3–4,16 | 작성: 기존 입력 조회 후 부족 항목만 조사 | 검토: source level/미확인 조건/질의 필요성 | 차단: Blueprint 없음, 브랜드·CTA 없음, 법적/안전 추정, 신뢰할 업계값 없음
C03 Query-first 계획 | v1.2 §5 | 작성: query→cluster→intent→고객결정→구성 | 검토: 검색 근거와 선택 이유 | 차단: 허브/페이지 수를 먼저 채움
C04 검색어 정렬 | v1.2 §6 | 작성: primary keyword/Title/H1/first answer | 검토: 원문 직접 대조 | 차단: 다른 의도/서비스로 이탈
C05 고객 화자와 구매여정 | v1.2 §7 | 작성: 제공자 화자, 실제 고객 문제 | 검토: 고객 노출 원문 | 차단: 내부 제작 용어/절차가 본문에 노출
C06 Title·summary 구분 | v1.2 §8 | 작성: 다섯 필드 별도 생성 | 검토: 공통 선두/유사도/형제 틀 | 차단·수정: 명시된 gate 위반
C07 업종·업체 고유성 | v1.2 §9 | 작성: Blueprint 결정정보와 Truth 장점 | 검토: 다른 업종/지역/서비스 치환 검사 | 차단·수정: 범용 문장 회피
C08 지역 근거 | v1.2 §10 | 작성: 서비스 수행에 필요한 사실+출처 | 검토: 실제 source와 주장 | 차단: local-required에 일반론만 존재
C09 구매동선 내부링크 | v1.2 §11 | 작성: 다음 구매결정 링크 | 검토: 클릭의 목적/도착지 | 차단·수정: 다른 시설 읽기를 주문 단계처럼 표시
C10 지역 복제 안전 이미지 | v1.2 §12 | 작성: 동적값 없는 범용 자산, 브랜드 범위 | 검토: 실제 이미지 픽셀/HTML | 차단: baked 지역/전화/가격/가짜 버튼
C11 Visual intent·asset slot | v1.2 §13 | 작성: 고객결정에 맞는 슬롯/비율 | 검토: crop/반응형/접근성 | 차단·수정: 피사체·글자 잘림, 의미 이미지 background 처리
C12 생성물과 실제 증거 | v1.2 §14 | 작성: 생성/실제 분리 | 검토: provenance·표시 | 차단: 생성 이미지를 실제 상품/실적 증거로 표현
C13 실제 CTA | v1.2 §15 | 작성: 검증된 실제 HTML 연락/주문 수단 | 검토: href/전화/도착지 | 차단: navigation/그림 버튼만 있음
C14 공개 gate | v1.2 §17 | 작성: 모든 요구 산출물 | 검토: 원문과 렌더/manifest/map/architecture/sitemap | 차단: 미일치·근거 없는 PASS

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
