// Use the existing verified product asset, without cropping or changing any hero.
export function productSocialImage(product, provenance, origin, brand) {
  const base = new URL(origin);
  if (base.protocol !== 'https:' || base.username || base.password) throw new Error('Social images require the canonical HTTPS origin');
  const proof = provenance.products.find(row => row.key === product?.key);
  if (!proof || product.assetType !== 'real_product' || product.sourceLevel !== 'official_business_source'
      || product.img !== proof.image.path || product.name !== proof.name
      || !/^\/images\/products\/seongnam-official-20261002\/[A-Z]\d+\.jpg$/.test(product.img)) {
    throw new Error('Social image must be an existing verified product asset');
  }
  const [width, height] = proof.image.dimensions;
  if (![width, height].every(value => Number.isInteger(value) && value > 0)) throw new Error('Missing verified image dimensions');
  return {url:new URL(product.img,base.origin).href,alt:`${brand} ${product.name}`,width,height,type:'image/jpeg'};
}
