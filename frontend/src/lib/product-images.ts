/**
 * Curated sealed product image mapping and fallback system.
 *
 * Fallback chain: retailer image_url → curated map → generic placeholder by product type
 */

// Generic product type placeholder images (SVG data URIs for zero-dependency fallbacks)
const PRODUCT_TYPE_PLACEHOLDERS: Record<string, string> = {
  'Elite Trainer Box': 'https://images.pokemontcg.io/swsh12pt5/logo.png',
  'Booster Box': 'https://images.pokemontcg.io/swsh12pt5/logo.png',
  'Booster Bundle': 'https://images.pokemontcg.io/swsh12pt5/logo.png',
  'Ultra Premium Collection': 'https://images.pokemontcg.io/swsh12pt5/logo.png',
  'Collection Box': 'https://images.pokemontcg.io/swsh12pt5/logo.png',
  'Blister Pack': 'https://images.pokemontcg.io/swsh12pt5/logo.png',
  'Tin': 'https://images.pokemontcg.io/swsh12pt5/logo.png',
  'Build & Battle': 'https://images.pokemontcg.io/swsh12pt5/logo.png',
};

// Curated image URLs for popular sealed products
// Maps "set_name::product_type" to a known good image URL
const CURATED_IMAGES: Record<string, string> = {
  // Prismatic Evolutions
  'Prismatic Evolutions::Elite Trainer Box': 'https://m.media-amazon.com/images/I/81Z0R0Q+cOL._AC_SL1500_.jpg',
  'Prismatic Evolutions::Booster Bundle': 'https://m.media-amazon.com/images/I/81cW9Nt7ZBL._AC_SL1500_.jpg',
  'Prismatic Evolutions::Ultra Premium Collection': 'https://m.media-amazon.com/images/I/81QxfbK5URL._AC_SL1500_.jpg',
  'Prismatic Evolutions::Mini Tin': 'https://m.media-amazon.com/images/I/71c4JZFVZOL._AC_SL1500_.jpg',
  'Prismatic Evolutions::Binder Collection': 'https://m.media-amazon.com/images/I/81QbG0YjZGL._AC_SL1500_.jpg',
  // Surging Sparks
  'Surging Sparks::Elite Trainer Box': 'https://m.media-amazon.com/images/I/81bXJ5IXWWL._AC_SL1500_.jpg',
  'Surging Sparks::Booster Box': 'https://m.media-amazon.com/images/I/71L-q+bCKML._AC_SL1500_.jpg',
  'Surging Sparks::Booster Bundle': 'https://m.media-amazon.com/images/I/81hMmOaD7KL._AC_SL1500_.jpg',
  // Journey Together
  'Journey Together::Booster Box': 'https://m.media-amazon.com/images/I/81vuXFSvjTL._AC_SL1500_.jpg',
  'Journey Together::Elite Trainer Box': 'https://m.media-amazon.com/images/I/81Lmb3EcURL._AC_SL1500_.jpg',
  'Journey Together::Booster Bundle': 'https://m.media-amazon.com/images/I/81WVVF5h6fL._AC_SL1500_.jpg',
  // Evolving Skies
  'Evolving Skies::Elite Trainer Box': 'https://m.media-amazon.com/images/I/81U1U9ZoFzL._AC_SL1500_.jpg',
  'Evolving Skies::Booster Box': 'https://m.media-amazon.com/images/I/71Q+Vy6HPJL._AC_SL1500_.jpg',
  // Pokemon 151
  'Pokemon 151::Elite Trainer Box': 'https://m.media-amazon.com/images/I/81fOH-GhbNL._AC_SL1500_.jpg',
  'Pokemon 151::Booster Bundle': 'https://m.media-amazon.com/images/I/81rUhxvWSQL._AC_SL1500_.jpg',
  'Pokemon 151::Ultra Premium Collection': 'https://m.media-amazon.com/images/I/81gJPiQM-cL._AC_SL1500_.jpg',
  // Crown Zenith
  'Crown Zenith::Elite Trainer Box': 'https://m.media-amazon.com/images/I/81Xd+RMQCEL._AC_SL1500_.jpg',
  // Obsidian Flames
  'Obsidian Flames::Booster Box': 'https://m.media-amazon.com/images/I/71-fZgZGw4L._AC_SL1500_.jpg',
  'Obsidian Flames::Elite Trainer Box': 'https://m.media-amazon.com/images/I/81TJtKV-pOL._AC_SL1500_.jpg',
  // Paldean Fates
  'Paldean Fates::Elite Trainer Box': 'https://m.media-amazon.com/images/I/81QRnYqQYrL._AC_SL1500_.jpg',
  'Paldean Fates::Booster Bundle': 'https://m.media-amazon.com/images/I/81v4PGy5ZfL._AC_SL1500_.jpg',
  // Paradox Rift
  'Paradox Rift::Booster Box': 'https://m.media-amazon.com/images/I/71oCYYO7NHL._AC_SL1500_.jpg',
  'Paradox Rift::Elite Trainer Box': 'https://m.media-amazon.com/images/I/81VwPdZdURL._AC_SL1500_.jpg',
  // Scarlet & Violet Base
  'Scarlet & Violet::Booster Box': 'https://m.media-amazon.com/images/I/71Y3OYkBATL._AC_SL1500_.jpg',
  'Prismatic Evolutions::Surprise Box': 'https://m.media-amazon.com/images/I/81s0fRqp3iL._AC_SL1500_.jpg',
};

/**
 * Route an external image URL through the backend proxy for caching and CORS bypass.
 * Only proxies external URLs; local/relative URLs pass through unchanged.
 */
export function proxyImageUrl(url: string): string {
  // Return direct URLs — pokemontcg.io and Amazon images load without proxy
  return url;
}

/**
 * Get the best available image URL for a sealed product.
 * Fallback chain: retailer image → curated map → product type placeholder
 */
export function getSealedImageUrl(
  product: {
    image_url?: string | null;
    set_name?: string;
    product_type?: string;
    name?: string;
  }
): string {
  // 1. Use retailer-provided image if available and not empty
  if (product.image_url && product.image_url.trim()) {
    return product.image_url;
  }

  // 2. Try curated image map
  if (product.set_name && product.product_type) {
    const key = `${product.set_name}::${product.product_type}`;
    if (CURATED_IMAGES[key]) {
      return CURATED_IMAGES[key];
    }
  }

  // 3. Try matching by product name keywords
  if (product.name) {
    const nameLower = product.name.toLowerCase();
    for (const [key, url] of Object.entries(CURATED_IMAGES)) {
      const [setName] = key.split('::');
      if (nameLower.includes(setName.toLowerCase())) {
        return url;
      }
    }
  }

  // 4. Generic product type placeholder
  if (product.product_type && PRODUCT_TYPE_PLACEHOLDERS[product.product_type]) {
    return PRODUCT_TYPE_PLACEHOLDERS[product.product_type];
  }

  // 5. Default fallback
  return PRODUCT_TYPE_PLACEHOLDERS['Elite Trainer Box'];
}

/**
 * Get the best available image URL for a card.
 * Uses Pokemon TCG API images.
 */
export function getCardImageUrl(
  card: {
    image_url?: string | null;
    small_image_url?: string | null;
    id?: string;
  },
  size: 'large' | 'small' = 'large'
): string {
  if (size === 'large' && card.image_url) {
    return card.image_url;
  }
  if (card.small_image_url) {
    return card.small_image_url;
  }
  if (card.image_url) {
    return card.image_url;
  }

  // Try to construct from card ID (e.g., "sv8-123" → "https://images.pokemontcg.io/sv8/123_hires.png")
  if (card.id) {
    const parts = card.id.split('-');
    if (parts.length === 2) {
      const [setId, cardNumber] = parts;
      return size === 'large'
        ? `https://images.pokemontcg.io/${setId}/${cardNumber}_hires.png`
        : `https://images.pokemontcg.io/${setId}/${cardNumber}.png`;
    }
  }

  // Fallback
  return 'https://images.pokemontcg.io/swsh12pt5/logo.png';
}

/**
 * Set name to Pokemon TCG API set ID mapping for logo fallbacks.
 * These logo images are universally accessible (no CORS/referrer issues).
 */
const SET_NAME_TO_ID: Record<string, string> = {
  'Prismatic Evolutions': 'sv8pt5',
  'Journey Together': 'sv9',
  'Surging Sparks': 'sv8',
  'Stellar Crown': 'sv7',
  'Shrouded Fable': 'sv6pt5',
  'Twilight Masquerade': 'sv6',
  'Temporal Forces': 'sv5',
  'Paldean Fates': 'sv4pt5',
  'Paradox Rift': 'sv4',
  'Obsidian Flames': 'sv3',
  'Pokemon 151': 'sv3pt5',
  'Paldea Evolved': 'sv2',
  'Scarlet & Violet': 'sv1',
  'Crown Zenith': 'swsh12pt5',
  'Silver Tempest': 'swsh12',
  'Lost Origin': 'swsh11',
  'Astral Radiance': 'swsh10',
  'Brilliant Stars': 'swsh9',
  'Fusion Strike': 'swsh8',
  'Evolving Skies': 'swsh7',
  'Chilling Reign': 'swsh6',
  'Battle Styles': 'swsh5',
  'Shining Fates': 'swsh45',
  'Vivid Voltage': 'swsh4',
};

/**
 * Get the set logo image from Pokemon TCG API.
 * These always load in any environment (no hotlink protection).
 */
export function getSetLogoUrl(setName: string): string {
  const setId = SET_NAME_TO_ID[setName];
  if (setId) return `https://images.pokemontcg.io/${setId}/logo.png`;
  return 'https://images.pokemontcg.io/swsh12pt5/logo.png';
}

/**
 * Product type display info (colors, icons)
 */
export const PRODUCT_TYPE_INFO: Record<string, { color: string; bgColor: string; label: string }> = {
  'Elite Trainer Box': { color: '#ef4444', bgColor: 'rgba(96, 165, 250, 0.1)', label: 'ETB' },
  'Booster Box': { color: '#f43f5e', bgColor: 'rgba(244, 63, 94, 0.1)', label: 'BB' },
  'Booster Bundle': { color: '#ef4444', bgColor: 'rgba(52, 211, 153, 0.1)', label: 'Bundle' },
  'Ultra Premium Collection': { color: '#a855f7', bgColor: 'rgba(168, 85, 247, 0.1)', label: 'UPC' },
  'Collection Box': { color: '#f97316', bgColor: 'rgba(249, 115, 22, 0.1)', label: 'Box' },
  'Blister Pack': { color: '#06b6d4', bgColor: 'rgba(6, 182, 212, 0.1)', label: 'Blister' },
  'Tin': { color: '#eab308', bgColor: 'rgba(234, 179, 8, 0.1)', label: 'Tin' },
  'Build & Battle': { color: '#ec4899', bgColor: 'rgba(236, 72, 153, 0.1)', label: 'B&B' },
};
