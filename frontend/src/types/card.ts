export interface PokemonCard {
  id: string
  name: string
  supertype?: string
  subtypes?: string[]
  hp?: string
  types?: string[]
  set: {
    id: string
    name: string
    series: string
    printedTotal: number
    total: number
    releaseDate: string
    images: { symbol: string; logo: string }
  }
  number: string
  rarity?: string
  images: { small: string; large: string }
  tcgplayer?: {
    url: string
    prices: Record<string, { low?: number; mid?: number; high?: number; market?: number }>
  }
  cardmarket?: {
    url: string
    prices: { averageSellPrice?: number; trendPrice?: number }
  }
}

export interface CardPrice {
  raw?: number
  psa10?: number
  psa9?: number
  psa8?: number
  cgc10?: number
  bgs10?: number
  market?: number
  low?: number
  high?: number
}

export interface GradedPrice {
  grade: string
  company: string
  price: number
  lastSold?: string
  change?: number
}

export interface PriceHistory {
  date: string
  price: number
  grade?: string
}

export interface CardSet {
  id: string
  name: string
  series: string
  printedTotal: number
  total: number
  releaseDate: string
  images: { symbol: string; logo: string }
}

export interface ChaseCard {
  id: string
  name: string
  rarity: string
  image: string
  price?: number
}

export interface RecentSale {
  date: string
  price: number
  grade?: string
  condition?: string
  platform?: string
}

// ===== Price History for Charts =====

export interface CardPriceHistoryPoint {
  card_id: string
  price_raw: number | null
  price_psa10: number | null
  price_psa9: number | null
  price_psa8: number | null
  price_cgc10: number | null
  price_cgc95: number | null
  price_cgc9: number | null
  price_bgs10: number | null
  price_bgs95: number | null
  price_bgs9: number | null
  recorded_at: string
}

export interface GradedPricesStructured {
  [grader: string]: {
    [grade: string]: {
      market: number | null
      low: number | null
      high: number | null
      grade_label?: string
      source?: string
      updated_at?: string
    }
  }
}
