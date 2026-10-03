// Dimensions and MIME types are verified against the unchanged catalog image bytes.
const catalogImages = {
  "/images/products/funeral-basic.webp": {
    "path": "/images/products/funeral-basic.webp",
    "alt": "꽃이랑 공식 상품 · 근조 3단 화환",
    "width": 480,
    "height": 480,
    "type": "image/webp"
  },
  "/images/products/funeral-premium.webp": {
    "path": "/images/products/funeral-premium.webp",
    "alt": "꽃이랑 공식 상품 · 근조 고급 3단 화환",
    "width": 480,
    "height": 480,
    "type": "image/webp"
  },
  "/images/products/funeral-large.webp": {
    "path": "/images/products/funeral-large.webp",
    "alt": "꽃이랑 공식 상품 · 근조 특대 3단 화환",
    "width": 480,
    "height": 480,
    "type": "image/webp"
  },
  "/images/products/congrats-basic.jpg": {
    "path": "/images/products/congrats-basic.jpg",
    "alt": "꽃이랑 공식 상품 · 축하 3단 화환",
    "width": 1000,
    "height": 1000,
    "type": "image/jpeg"
  },
  "/images/products/congrats-premium.jpg": {
    "path": "/images/products/congrats-premium.jpg",
    "alt": "꽃이랑 공식 상품 · 축하 고급 3단 화환",
    "width": 1000,
    "height": 1000,
    "type": "image/jpeg"
  },
  "/images/products/congrats-large.jpg": {
    "path": "/images/products/congrats-large.jpg",
    "alt": "꽃이랑 공식 상품 · 축하 특대 3단 화환",
    "width": 1000,
    "height": 1000,
    "type": "image/jpeg"
  },
  "/images/products/bouquet-happiness.jpg": {
    "path": "/images/products/bouquet-happiness.jpg",
    "alt": "꽃이랑 공식 상품 · 소소한 행복",
    "width": 500,
    "height": 500,
    "type": "image/jpeg"
  },
  "/images/products/bouquet-blue.jpg": {
    "path": "/images/products/bouquet-blue.jpg",
    "alt": "꽃이랑 공식 상품 · 블루톤 시즌플라워",
    "width": 500,
    "height": 500,
    "type": "image/jpeg"
  },
  "/images/products/bouquet-rose.jpg": {
    "path": "/images/products/bouquet-rose.jpg",
    "alt": "꽃이랑 공식 상품 · 러블리 자나장미",
    "width": 500,
    "height": 500,
    "type": "image/jpeg"
  },
  "/images/products/basket-sunshine.jpg": {
    "path": "/images/products/basket-sunshine.jpg",
    "alt": "꽃이랑 공식 상품 · 햇살 한가득",
    "width": 500,
    "height": 500,
    "type": "image/jpeg"
  }
};

export function socialImageFor(product) {
  const path = product?.img;
  return typeof path === "string" && Object.hasOwn(catalogImages, path)
    ? catalogImages[path]
    : catalogImages["/images/products/bouquet-happiness.jpg"];
}
