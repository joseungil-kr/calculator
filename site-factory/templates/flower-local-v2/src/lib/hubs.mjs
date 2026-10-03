/** Decision help stays category-specific; it does not prescribe detail structure. */
/** @type {Record<string, {intro:string, decision:string[], families:string[], heading:string, cta:string}>} */
export const hubGuides = {
  funeral: {
    intro: '빈소에 조의를 전할 근조화환을 고른 뒤 장례식장·빈소·상주명과 보내는 분 표기를 준비하세요.',
    decision: ['기본·고급·특대 중 예산에 맞는 크기 선택', '병원 본관 주소와 장례식장·빈소를 구분', '위로 문구와 개인·회사·단체 발신자 표기 확인'],
    families: ['funeral'], heading: '조의를 전하는 근조화환', cta: '근조화환 상품 확인'
  },
  business: {
    intro: '개업과 이전을 축하하는 화환은 매장 앞에 둘 공간과 받는 곳의 상호명이 중요합니다.',
    decision: ['매장·사무실의 상호명과 층·호수 확인', '입구 설치 가능 여부와 수령 담당자 확인', '개업·이전에 맞는 짧은 축하 문구 선택'],
    families: ['congrats'], heading: '개업·이전 축하화환 비교', cta: '축하화환 상품 확인'
  },
  school: {
    intro: '졸업생에게 직접 건넬 꽃은 이동과 사진촬영을 고려해 고르세요.',
    decision: ['휴대할 크기와 원하는 색감 선택', '캠퍼스·행사 건물·만날 장소를 구분', '졸업식 시작시간과 실제 수령시간을 따로 확인'],
    families: ['bouquet'], heading: '졸업생에게 건네는 꽃다발', cta: '졸업 꽃다발 상품 확인'
  },
  event: {
    intro: '출연자에게 건네는 꽃다발과 행사장에 설치하는 축하화환은 준비할 정보가 다릅니다.',
    decision: ['직접 전달할 꽃다발인지 설치할 화환인지 선택', '공연명·홀 또는 전시장·받는 담당자 확인', '꽃 반입·설치 가능 여부와 전달시간을 주최 측에 확인'],
    families: ['bouquet', 'congrats', 'basket'], heading: '공연 전달용과 행사 설치용 비교', cta: '공연 꽃다발 상품 확인'
  },
  gift: {
    intro: '만나서 건넬 때는 꽃다발, 한곳에 두고 감상할 때는 꽃바구니를 비교해 보세요. 병문안은 병동의 생화 반입 가능 여부를 먼저 확인해야 합니다.',
    decision: ['꽃다발의 휴대성과 꽃바구니의 진열 용도 비교', '받는 분의 색감 취향과 보관할 공간 고려', '집·사무실·병동의 정확한 수령 지점 확인'],
    families: ['bouquet', 'basket'], heading: '기념일·약속·병문안 꽃선물', cta: '꽃선물 상품 확인'
  },
  order: {
    intro: '가격과 문구를 정하고 주소·수령자·희망시간을 준비하면 주문 상담이 간단해집니다.',
    decision: ['꽃다발·꽃바구니·화환의 상품가격 비교', '도로명주소와 건물명·층·호수·수령 연락처 준비', '당일 배송과 추가비용은 주문 전에 확인'],
    families: ['bouquet', 'basket', 'funeral', 'congrats'], heading: '목적에 맞는 상품부터 선택', cta: '꽃다발 상품 확인'
  }
};
export function hubProducts(category, products, limit = 3) {
  const families = hubGuides[category]?.families || [];
  const first = families.map(family => products.find(p => p.family === family)).filter(Boolean);
  const rest = families.flatMap(family => products.filter(p => p.family === family && !first.includes(p)));
  return [...first, ...rest].slice(0, limit);
}

/** Display copy follows the current frozen Catalog and Business Truth. */
export function hubGuide(category, products, site) {
  const guide=hubGuides[category];
  if (!guide) throw new Error('Unknown hub category: '+category);
  const selected=hubProducts(category,products,category==='school'?2:guide.families.length);
  const prices=selected.map(p=>`${p.name} ${p.price.toLocaleString('ko-KR')}원`).join(', ');
  const extra=category==='order'
    ? ` 온라인 ${site.onlineOrderHours}은 접수시간이며 배송 가능시간은 별도로 확인합니다.`
    : prices ? ` 현재 상품: ${prices}.` : '';
  return {...guide,intro:guide.intro+extra};
}
