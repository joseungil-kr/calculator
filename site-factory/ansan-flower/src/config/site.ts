const siteUrl = import.meta.env.SITE_URL || 'https://ansan.fwith.kr';
const indexable = import.meta.env.SITE_INDEXABLE === 'true';

export const siteConfig = {
  siteKey: 'ansan-flower-test',
  brand: '꽃이랑 안산',
  region: '안산',
  industry: '꽃배달·꽃집',
  deploymentMode: 'subdomain',
  rootDomain: 'fwith.kr',
  canonicalDomain: 'ansan.fwith.kr',
  siteUrl,
  indexable,
  description:
    '안산에서 꽃을 준비할 때 사람, 상황, 장소에 맞는 선택 기준을 설명하는 지역 플라워 가이드입니다.',
  operator: {
    label: 'Powered by INTERPIAD',
    href: 'https://interpiad.com',
    rel: 'nofollow',
    email: 'webmaster@interpiad.com',
  },
  nav: [
    { href: '/안산꽃배달/', label: '안산 꽃배달' },
    { href: '/guide/', label: '꽃 선택 가이드' },
    { href: '/places/', label: '장소별' },
    { href: '/occasions/', label: '상황별' },
    { href: '/flower-knowledge/', label: '꽃 이야기' },
    { href: '/order-help/', label: '주문 준비' },
  ],
} as const;
