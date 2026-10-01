import { existsSync } from 'node:fs';
const siteUrl=import.meta.env.SITE_URL||'https://suwon.fwith.kr';
const f=import.meta.env.SITE_INDEXABLE;
const indexable=f==='true'||(f!=='false'&&existsSync('production-indexing.enabled'));
export const siteConfig={
  siteKey:'suwon-flower-test',brandKey:'flower-fwith',businessTruthKey:'flower-fwith-v1',
  brandBase:'꽃이랑',brand:'꽃이랑 수원',region:'수원',industry:'꽃배달·꽃집',
  deploymentMode:'subdomain',rootDomain:'fwith.kr',canonicalDomain:'suwon.fwith.kr',
  naverSiteVerification:'80fedf144567fea99fe833d2937731a190854c41',
  siteUrl,indexable,defaultOgImage:'/images/suwon/hero-B-original.png',
  defaultOgImageAlt:'핑크 계열 꽃다발을 담은 꽃배달 대표 이미지',
  description:'수원 꽃배달을 장례·개업·졸업·공연·병문안·기념일·주문 상황에 맞춰 안내하고 실제 화환 가격과 주문 방법을 제공합니다.',
  operator:{label:'Powered by INTERPIAD',href:'https://interpiad.com',rel:'nofollow',email:'webmaster@interpiad.com'},
  nav:[
    {href:'/funeral/',label:'근조·장례',category:'funeral',menuMinChildren:5},
    {href:'/business/',label:'개업·이전',category:'business',menuMinChildren:5},
    {href:'/school/',label:'졸업·입학',category:'school',menuMinChildren:5},
    {href:'/event/',label:'공연·행사',category:'event',menuMinChildren:5},
    {href:'/gift/',label:'선물·병문안',category:'gift',menuMinChildren:5},
    {href:'/order/',label:'가격·주문',category:'order',menuMinChildren:5}
  ]
} as const;