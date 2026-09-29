import { existsSync } from 'node:fs';

const siteUrl = import.meta.env.SITE_URL || 'https://ansan.fwith.kr';
const indexableFlag = import.meta.env.SITE_INDEXABLE;
const productionMarker = existsSync('production-indexing.enabled');
const indexable =
  indexableFlag === 'true' ||
  (indexableFlag !== 'false' && productionMarker);

export const siteConfig = {
  siteKey: 'ansan-flower-test',
  brandKey: 'flower-fwith',
  businessTruthKey: 'flower-fwith-v1',
  brandBase: '꽃이랑',
  brand: '꽃이랑 안산',
  region: '안산',
  industry: '꽃배달·꽃집',
  deploymentMode: 'subdomain',
  rootDomain: 'fwith.kr',
  canonicalDomain: 'ansan.fwith.kr',
  primaryLandingSlug: '안산꽃배달',
  naverSiteVerification: '29e360fe4ae4a2cb72015166abc3b386c2e49974',
  siteUrl,
  indexable,
  defaultOgImage: '/images/ansan/hero-B-original.png',
  defaultOgImageAlt: '밝은 핑크 플라워 부케를 담은 꽃이랑 안산 꽃배달 대표 이미지',
  description:
    '안산에서 꽃을 준비할 때 사람, 상황, 장소에 맞는 선택 기준과 실제 화환 가격, 주문 정보를 함께 제공하는 지역 플라워 가이드입니다.',
  operator: {
    label: 'Powered by INTERPIAD',
    href: 'https://interpiad.com',
    rel: 'nofollow',
    email: 'webmaster@interpiad.com',
  },
  nav: [
    { href: '/안산꽃배달/', label: '안산 꽃배달', kind: 'core' },
    { href: '/guide/', label: '꽃 선택', category: 'guide', menuMinChildren: 5 },
    { href: '/funeral/', label: '장례식장', category: 'funeral', menuMinChildren: 5 },
    { href: '/places/', label: '장소별', category: 'places', menuMinChildren: 5 },
    { href: '/occasions/', label: '상황별', category: 'occasions', menuMinChildren: 5 },
    { href: '/flower-knowledge/', label: '꽃 관리', category: 'flower-knowledge', menuMinChildren: 5 },
    { href: '/order-help/', label: '주문 도움', category: 'order-help', menuMinChildren: 5 },
  ],
} as const;
