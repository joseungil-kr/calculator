// Bound to verified local catalog assets; hero selection and image bytes are untouched.
export function productSocialImage(product, provenance, origin, brand) {
  const base = new URL(origin);
  if (base.protocol !== 'https:' || base.username || base.password) throw new Error('Social images require the canonical HTTPS origin');
  const proof = provenance.products.find(row => row.key === product?.key);
  if (!proof || product.assetType !== 'real_product' || product.sourceLevel !== 'official_business_source'
      || product.img !== proof.image.path || product.name !== proof.name
      || product.sourceUrl !== proof.sourceUrl || product.orderUrl !== proof.orderUrl
      || !/^\/images\/products\/[a-zA-Z0-9_/-]+\.(?:jpe?g|png|webp)$/.test(product.img)
      || product.img.includes('..')) throw new Error('Social image must match a verified local catalog asset');
  const [width, height] = proof.image.dimensions;
  if (![width, height].every(value => Number.isInteger(value) && value > 0)
      || !['image/jpeg','image/png','image/webp'].includes(proof.image.type)
      || !/^[0-9a-f]{64}$/.test(proof.image.sha256)) throw new Error('Missing verified image metadata');
  return {url:new URL(product.img,base.origin).href,alt:`${brand} ${product.name}`,width,height,type:proof.image.type};
}
