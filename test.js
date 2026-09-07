const axios = require('axios');
async function testSearch(query) {
    try {
        const mUrl = `https://m.map.naver.com/search2/search.naver?query=${encodeURIComponent(query)}`;
        const mRes = await axios.get(mUrl, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36'
            }
        });
        const html = mRes.data;
        const matches = html.match(/<script.*?>(.*?)<\/script>/gs);
        if (matches) {
            matches.forEach((m, i) => {
                if (m.length > 200) {
                    console.log(`Script ${i} length: ${m.length}`);
                    console.log(m.substring(0, 200));
                }
            });
        }
    } catch(e) {
        console.log("Mobile Error:", e.message);
    }
}
testSearch('강남역 스타벅스');
