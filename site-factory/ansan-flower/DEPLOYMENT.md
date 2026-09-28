# Cloudflare Workers Static Assets 배포 준비

현재 상태: **Astro 정적 빌드 및 정적 SEO QA 완료. 실제 Cloudflare 계정 배포는 아직 수행하지 않음.**

## 배포 플랫폼

새 프로젝트는 Cloudflare Workers + Static Assets를 기준으로 한다.

이 사이트는 Astro SSG이므로 서버 Worker 코드는 필요하지 않으며,
`dist/` 정적 결과물을 Worker의 assets로 배포한다.

## Wrangler 설정

`wrangler.jsonc`

- Worker name: `ansan-flower-guide-test`
- assets directory: `./dist/`
- 404 handling: `404-page`
- HTML handling: `auto-trailing-slash`
- workers.dev: enabled for deployment test

## Cloudflare Git 연결 시

Repository:
`joseungil-kr/calculator`

Branch:
`site-factory-ansan-v1`

Root directory:
`site-factory/ansan-flower`

Build command:
`npm run build`

Deploy command:
`npx wrangler deploy`

현재 GitHub Actions에서도 별도로:
- astro check
- astro build
- deterministic static SEO QA
- wrangler deploy --dry-run

을 검증한다.

## 첫 실제 배포 순서

1. Cloudflare Dashboard > Workers & Pages
2. Create application
3. Import a repository
4. GitHub의 joseungil-kr/calculator 선택
5. Root directory를 `site-factory/ansan-flower`로 지정
6. Build command `npm run build`
7. Deploy command `npx wrangler deploy`
8. 먼저 `*.workers.dev` 테스트 주소에서 확인
9. live HTTP / 404 / canonical / sitemap / robots 검수
10. 실제 도메인 확정 후 custom domain 연결

## 도메인 주의

현재 코드의 기본 canonical/sitemap 도메인은
`https://ansanflowerdelivery.com`이다.

실제 도메인이 아직 확정·연결되지 않았다면 workers.dev 테스트 주소를 검색엔진에 등록하지 않는다.
실제 도메인 연결 시 SITE_URL/canonical/robots/sitemap을 최종 도메인으로 다시 확인한다.

## Site Factory 확장 원칙

각 지역 사이트를 별도 Worker 프로젝트로 만들더라도
코드 엔진은 공통화하고 Sites Registry에서:
- Worker project name
- production branch
- domain
- site_key

를 관리하도록 확장한다.

대량 사이트 단계에서는 Worker 프로젝트/도메인 생성 자동화를 별도 배포 계층으로 분리한다.
