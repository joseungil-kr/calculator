import { existsSync } from 'node:fs';

const siteUrl = import.meta.env.SITE_URL || 'https://suwon.fwith.kr';
const indexableFlag = import.meta.env.SITE_INDEXABLE;
const productionMarker = existsSync('production-indexing.enabled');
const indexable =
  indexableFlag === 'true' ||
  (indexableFlag !== 'false' && productionMarker);

export const siteConfig = {
  siteKey: 'suwon-flower-test',
  brandKey: 'flower-fwith',
  businessTruthKey: 'flower-fwith-v1',
  brandBase: '꽃이랑',
  brand: '꽃이랑 수원',
  region: '수원',
  industry: '꽃배달·꽃집',
  deploymentMode: 'subdomain',
  rootDomain: 'fwith.kr',
  canonicalDomain: 'suwon.fwith.kr',
  primaryLandingSlug: '수원꽃배달',
  naverSiteVerification: '',
  siteUrl,
  indexable,
  defaultOgImage: '/images/suwon/hero-B-original.png',
  defaultOgImageAlt: '밝은 핑크 플라워 부케를 담은 꽃이랑 수원 꽃배달 대표 이미지',
  description:
    '수원에서 꽃을 준비할 때 사람, 상황, 장소에 맞는 선택 기준과 실제 화환 가격, 주문 정보를 함께 제공하는 지역 플라워 가이드입니다.',
  operator: {
    label: 'Powered by INTERPIAD',
    href: 'https://interpiad.com',
    rel: 'nofollow',
    email: 'webmaster@interpiad.com',
  },
  nav: [
    { href: '/수원꽃배달/', label: '수원 꽃배달' },
    { href: '/guide/', label: '꽃 선택 가이드' },
    { href: '/places/', label: '장소별' },
    { href: '/occasions/', label: '상황별' },
    { href: '/flower-knowledge/', label: '꽃 이야기' },
    { href: '/order-help/', label: '주문 준비' },
  ],
} as const;
