export interface StoreResult {
  store: string
  retailer: string
  address?: string
  city?: string
  state?: string
  zip?: string
  distance?: number
  products: StoreProduct[]
  inStock: boolean
  lastChecked?: string
  url?: string
}

export interface StoreProduct {
  name: string
  sku?: string
  upc?: string
  price?: number
  quantity?: number
  inStock: boolean
  url?: string
  image?: string
}

export interface StockStats {
  stores: number
  inStock: number
  products: number
  totalUnits: number
}

export interface SealedProduct {
  name: string
  type: string
  msrp: number
  set?: string
  image?: string
  upc?: string
  skus?: Record<string, string>
}

// ===== Sealed Products (API response) =====

export interface SealedProductListing {
  id: number
  name: string
  set_name: string
  product_type: string
  msrp: number
  current_price: number
  image_url: string | null
  in_print: boolean
  premium_pct: number
  notes?: string
  updated_at: string
}

export interface SealedPriceHistoryPoint {
  sealed_product_id: number
  price: number
  source: string
  recorded_at: string
}

// ===== Trending =====

export interface TrendingCard {
  id: string
  name: string
  set_id: string
  set_name: string
  rarity: string
  image_url: string | null
  small_image_url: string | null
  tcgplayer_market: number
  tcgplayer_low: number | null
  tcgplayer_mid: number | null
  tcgplayer_high: number | null
  change_7d: number
  change_30d: number
}
