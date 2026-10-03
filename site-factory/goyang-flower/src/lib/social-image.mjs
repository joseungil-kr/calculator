// Metadata only: reuse the exact existing verified product asset, without cropping.
export function productSocialImage(product, provenance, origin, brand) {
  const base=new URL(origin);
  if(base.protocol!=='https:' || base.username || base.password || base.pathname!=='/' || base.search || base.hash)
    throw new Error('Social images require the canonical HTTPS origin');
  const matches=provenance.products.filter(row=>row.key===product?.key);
  const proof=matches[0];
  if(matches.length!==1 || !product || product.assetType!=='real_product' || product.sourceLevel!=='official_business_source'
      || product.img!==proof.image.path || product.name!==proof.name || product.sourceUrl!==proof.sourceUrl
      || product.verifiedAt!==proof.verifiedAt || !/^\/images\/products\/[a-z0-9-]+\.(jpg|webp)$/.test(product.img))
    throw new Error('Social image must be an existing verified product asset');
  const [width,height]=proof.image.dimensions;
  const type=product.img.endsWith('.webp')?'image/webp':'image/jpeg';
  if(![width,height].every(value=>Number.isInteger(value)&&value>0) || proof.image.type!==type
      || !/^[0-9a-f]{64}$/.test(proof.image.sha256))
    throw new Error('Missing verified image metadata');
  return {url:new URL(product.img,base.origin).href,alt:`${brand} ${product.name}`,width,height,type};
}
