# Ansan Flower Site Factory — v1

Site Factory의 첫 실제 디자인/코드 골격 테스트입니다.

## 범위
- Astro 정적 사이트
- 반응형 홈페이지
- 5개 허브 페이지
- 공통 Header / Footer
- canonical / meta / Open Graph
- WebSite JSON-LD
- sitemap
- robots.txt
- INTERPIAD 운영자 표기(nofollow)
- webmaster@interpiad.com

## 아직 하지 않은 것
- 실제 도메인 연결
- Cloudflare 배포 검증
- 실제 주문 전화/폼 연결
- 승인된 30개 상세 콘텐츠 전부 생성
- LocalBusiness schema (실제 사업장 정보 확정 전 사용하지 않음)
- 이미지 생성/자동 업로드
- live HTTP QA

## 환경
SITE_URL 환경변수를 지정하지 않으면 canonical/sitemap 기준 도메인은
https://ansanflowerdelivery.com 으로 설정됩니다.

## 다음 단계
1. Factory Editor에서 첫 허브 콘텐츠 PASS
2. 상세 Article 레이아웃 + Content Collection 추가
3. Page Plan의 approved 항목을 Markdown으로 변환
4. build 검증
5. Cloudflare 테스트 배포
