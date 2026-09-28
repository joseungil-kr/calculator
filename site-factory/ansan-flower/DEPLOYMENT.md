# Cloudflare 배포 준비

현재 상태: **코드/빌드 QA 완료 전 단계이며 실제 Cloudflare 배포는 아직 수행하지 않음.**

## 권장 첫 테스트: Cloudflare Pages

첫 1~5개 사이트 검증은 Pages로 단순하게 시작하고, 대량 사이트 단계에서 Workers/Static Assets 구조를 별도로 검토한다.

### Git 연결 시 설정

- Repository: `joseungil-kr/calculator`
- Branch: `site-factory-ansan-v1`
- Root directory: `site-factory/ansan-flower`
- Build command: `npm run build`
- Build output directory: `dist`
- Node.js: 22
- Environment variable:
  - `SITE_URL=https://<Cloudflare preview 또는 실제 도메인>`

## 실제 도메인 전환 전

현재 코드 기본 canonical은 `https://ansanflowerdelivery.com`이다.
실제 도메인 연결 전 preview를 공개 검색엔진에 제출하지 않는다.

실제 도메인이 확정되면:
1. SITE_URL 확정
2. robots.txt sitemap URL 확인
3. canonical 확인
4. Cloudflare custom domain 연결
5. live HTTP QA
6. sitemap live 확인
7. 검색엔진 등록

## 아직 필요한 외부 작업

Cloudflare 계정에서 Git 저장소 연결 또는 API token/account ID 설정이 필요하다.
현재 ChatGPT 환경에는 Cloudflare 계정 커넥터가 없으므로 이 단계는 계정 측 연결이 필요하다.
