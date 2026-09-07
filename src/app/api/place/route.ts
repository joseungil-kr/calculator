import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('q');

  if (!query) {
    return NextResponse.json({ error: '검색어를 입력해주세요.' }, { status: 400 });
  }

  try {
    const searchUrl = `https://m.map.naver.com/search2/search.naver?query=${encodeURIComponent(query)}`;
    const response = await fetch(searchUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
      }
    });

    const html = await response.text();
    
    // 네이버 모바일 지도는 SSR 스트리밍 상태에 검색 결과를 포함합니다.
    const rqMatches = [...html.matchAll(/window\.__RQ_STREAMING_STATE__\.push\((\{[\s\S]*?\})\);/g)];
    
    let bestMatch = null;

    for (const match of rqMatches) {
        try {
            const data = JSON.parse(match[1]);
            // queries 안에서 결과 배열을 찾습니다.
            for (const q of data.queries || []) {
                const items = q?.state?.data?.items || q?.state?.data?.place?.list;
                if (items && Array.isArray(items) && items.length > 0) {
                    const item = items[0];
                    bestMatch = {
                        name: item.name || '',
                        category: Array.isArray(item.category) ? item.category.join(' > ') : (item.category || ''),
                        address: item.roadAddress || item.address || '',
                        phone: item.phone || item.tel || '',
                        id: item.id
                    };
                    break;
                }
            }
            if (bestMatch) break;
        } catch (e) {
            console.error("JSON 파싱 에러", e);
        }
    }

    if (bestMatch) {
      return NextResponse.json(bestMatch);
    }

    // fallback: __RQ_STREAMING_STATE__ 가 없을 경우 (구형 UI 등)
    const smapsRegex = /window\.smaps = (\{[\s\S]*?\});/;
    const smatch = html.match(smapsRegex);
    if (smatch && smatch[1]) {
        try {
            const smapsData = JSON.parse(smatch[1]);
            if (smapsData?.result?.site?.list?.length > 0) {
                const item = smapsData.result.site.list[0];
                bestMatch = {
                    name: item.name || '',
                    category: item.category || '',
                    address: item.address || item.roadAddress || '',
                    phone: item.tel || '',
                };
                return NextResponse.json(bestMatch);
            }
        } catch {}
    }

    return NextResponse.json({ error: '검색 결과가 없습니다. 다시 시도하거나 수기로 입력해주세요.' }, { status: 404 });
  } catch (error) {
    console.error('크롤링 에러:', error);
    return NextResponse.json({ error: '검색 중 오류가 발생했습니다.' }, { status: 500 });
  }
}
